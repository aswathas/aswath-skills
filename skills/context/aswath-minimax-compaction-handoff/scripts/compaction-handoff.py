#!/usr/bin/env python3
"""MiniMax Code compaction handoff hook.

Events handled:
  PreCompact   - write HANDOFF.md (context-compression structure) BEFORE compaction.
  PostCompact  - append a compaction record to the session handoff log.
  SessionStart - when source == "compact", re-inject HANDOFF.md as agent context.

The hook is deterministic: it reads the session transcript from the local runtime
sqlite database and extracts facts verbatim. No model call, no network.

Sections follow the context-compression skill structure:
  Session Intent, Files Modified, Decisions Made, Current State, Next Steps.

Merging is anchored and iterative: an existing HANDOFF.md is merged into, not
replaced, so repeated compactions do not lose earlier facts.

Stdlib only. Works on Python 3.8+ (Windows 3.13 and WSL 3.12 both fine).
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

SECTIONS = [
    "Session Intent",
    "Files Modified",
    "Decisions Made",
    "Current State",
    "Next Steps",
]

DECISION_MARKERS = (
    "decid", "chose", "choos", "instead of", "switch", "will use", "using ",
    "approach", "plan:", "reject", "kept ", "because ", "prefer", "went with",
    "opted", "settled on", "target",
)

MAX_CONTEXT_CHARS = 8000
MAX_DECISIONS = 12
MAX_FILES = 40
MAX_INTENT = 600


def data_dir():
    for key in ("MINIMAX_DATA_DIR", "MAVIS_DATA_DIR"):
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    return os.path.join(os.path.expanduser("~"), ".minimax")


def db_path():
    return os.path.join(data_dir(), "v2", "sqlite", "runtime-state.sqlite")


def handoff_root():
    return os.path.join(data_dir(), "v2", "session-handoff")


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_stdin():
    """Read the hook payload from stdin as UTF-8 bytes.

    The runtime, and PowerShell pipes, can prepend one or more UTF-8 BOMs, so
    they are stripped before decoding. Decoding bytes instead of using
    sys.stdin.read() keeps the payload intact regardless of the console
    codepage.
    """
    try:
        raw = sys.stdin.buffer.read()
    except Exception:
        try:
            raw = sys.stdin.read().encode("utf-8", "replace")
        except Exception:
            return {}
    if not raw or not raw.strip():
        return {}
    while raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8", "replace").strip()
    except Exception:
        return {}
    if not text:
        return {}
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def session_rows(session_id):
    path = db_path()
    if not session_id or not os.path.isfile(path):
        return []
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "select role, data_json from local_runtime_message_rows"
            " where session_id=? order by created_at_ms",
            (session_id,),
        ).fetchall()
        con.close()
    except Exception:
        return []
    out = []
    for row in rows:
        try:
            out.append(json.loads(row["data_json"]))
        except Exception:
            continue
    return out


def tool_args(call):
    raw = call.get("tool_call_args")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def collect(rows):
    intent = []
    files = []
    reads = []
    decisions = []
    context_usage = None
    todos = []

    for data in rows:
        role = data.get("role")
        text = data.get("msg_content")
        text = text if isinstance(text, str) else ""

        if role == "user" and text.strip():
            flat = " ".join(text.split())
            if not flat.startswith("<questionnaire-response>"):
                intent.append(flat)

        if role == "assistant":
            for line in text.splitlines():
                clean = line.strip().lstrip("-* ").strip()
                if not clean or len(clean) < 12:
                    continue
                low = clean.lower()
                if any(marker in low for marker in DECISION_MARKERS):
                    if clean not in decisions:
                        decisions.append(clean)

        for call in data.get("tool_calls") or []:
            name = call.get("tool_name")
            args = tool_args(call)
            if name == "write":
                target = args.get("path") or args.get("file_path")
                if target:
                    files.append(target + ": written")
            elif name == "edit":
                target = args.get("file_path") or args.get("path")
                if target:
                    files.append(target + ": edited")
            elif name == "read":
                target = args.get("path") or args.get("file_path")
                if target:
                    reads.append(target)
            elif name == "todowrite":
                items = args.get("todos")
                if isinstance(items, list):
                    todos = items

        usage = data.get("context_usage")
        if isinstance(usage, dict) and usage.get("usedTokens") is not None:
            context_usage = usage

    def dedupe(items):
        seen = set()
        out = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    return {
        "intent": dedupe(intent),
        "files": dedupe(files),
        "reads": dedupe(reads),
        "decisions": dedupe(decisions),
        "context_usage": context_usage,
        "todos": todos if isinstance(todos, list) else [],
    }


def parse_sections(text):
    """Split a markdown doc into {section_name: [lines]} preserving order."""
    sections = {}
    current = None
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        sections[current].append(line)
    return sections


def render_section(name, lines):
    body = [line for line in lines if line.strip()]
    if not body:
        body = ["- (none recorded)"]
    return ["## " + name, ""] + body + [""]


def merge_sections(existing, fresh):
    """Anchored merge: keep prior bullets, append new ones, dedupe by exact line."""
    merged = {}
    for name in SECTIONS:
        prior = [line for line in existing.get(name, []) if line.strip()]
        prior = [line for line in prior if not line.startswith("<!--")]
        added = [line for line in fresh.get(name, []) if line.strip()]
        seen = set(line.strip() for line in prior)
        out = list(prior)
        for line in added:
            if line.strip() in seen:
                continue
            seen.add(line.strip())
            out.append(line)
        merged[name] = out
    return merged


def build_sections(facts):
    intent_lines = []
    if facts["intent"]:
        intent_lines.append("- First request: " + facts["intent"][0][:MAX_INTENT])
        if len(facts["intent"]) > 1:
            intent_lines.append("- Latest request: " + facts["intent"][-1][:MAX_INTENT])
    else:
        intent_lines.append("- (no user request captured)")

    file_lines = ["- " + item for item in facts["files"][:MAX_FILES]]
    if not file_lines:
        file_lines = ["- (no file writes recorded)"]
    if facts["reads"]:
        read_preview = facts["reads"][:15]
        file_lines.append("- Read only (not modified): " + ", ".join(read_preview))

    decision_lines = ["- " + item for item in facts["decisions"][:MAX_DECISIONS]]
    if not decision_lines:
        decision_lines = ["- (no explicit decision statement captured)"]

    state_lines = []
    usage = facts["context_usage"] or {}
    used = usage.get("usedTokens")
    window = usage.get("contextWindowTokens")
    if used is not None:
        state_lines.append("- Context before compaction: %s / %s tokens" % (used, window))
        components = usage.get("components") or []
        if components:
            breakdown = ", ".join(
                "%s=%s" % (c.get("kind"), c.get("tokens"))
                for c in components
                if isinstance(c, dict) and c.get("kind")
            )
            if breakdown:
                state_lines.append("- Breakdown: " + breakdown)

    todo_state = {"pending": [], "in_progress": [], "completed": []}
    for todo in facts["todos"]:
        if not isinstance(todo, dict):
            continue
        status = str(todo.get("status") or "pending")
        if status not in todo_state:
            todo_state[status] = []
        todo_state[status].append(todo)
    state_lines.append(
        "- Todo state: %d completed, %d in progress, %d pending"
        % (
            len(todo_state.get("completed", [])),
            len(todo_state.get("in_progress", [])),
            len(todo_state.get("pending", [])),
        )
    )

    next_lines = []
    for todo in todo_state.get("in_progress", []) + todo_state.get("pending", []):
        if not isinstance(todo, dict):
            continue
        content = str(todo.get("content") or "").strip()
        if not content:
            continue
        priority = todo.get("priority")
        status = todo.get("status")
        label = "%s [%s]" % (content, status) if status else content
        if priority:
            label += " priority=%s" % priority
        next_lines.append("- " + label)
    if not next_lines:
        next_lines = ["- (no pending todos)"]

    return {
        "Session Intent": intent_lines,
        "Files Modified": file_lines,
        "Decisions Made": decision_lines,
        "Current State": state_lines,
        "Next Steps": next_lines,
    }


def read_existing(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except Exception:
        return ""


def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def render_document(sections, header_lines):
    parts = ["# HANDOFF.md", ""]
    parts.extend(header_lines)
    parts.append("")
    for name in SECTIONS:
        parts.extend(render_section(name, sections.get(name, [])))
    return "\n".join(parts).rstrip() + "\n"


def project_root(payload):
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return cwd.strip()
    return os.path.expanduser("~")


def log_event(session_id, event, extra=""):
    try:
        records = os.path.join(handoff_root(), "records", session_id or "unknown")
        os.makedirs(records, exist_ok=True)
        with open(os.path.join(records, "events.log"), "a", encoding="utf-8") as handle:
            handle.write("%s event=%s%s\n" % (now_iso(), event, extra))
    except Exception:
        pass


def handle_pre_compact(payload):
    session_id = payload.get("session_id") or payload.get("sessionId") or ""
    trigger = payload.get("trigger") or "auto"
    facts = collect(session_rows(session_id))
    fresh = build_sections(facts)

    root = project_root(payload)
    target = os.path.join(root, "HANDOFF.md")
    existing = parse_sections(read_existing(target))
    merged = merge_sections(existing, fresh)

    header = [
        "<!-- generated by the MiniMax Code compaction handoff hook -->",
        "<!-- scratch file: do not commit -->",
        "- Updated: " + now_iso(),
        "- Session: " + (session_id or "unknown"),
        "- Trigger: " + str(trigger),
        "- Compaction threshold: 100000 tokens (contextManagement.compactionTriggerAt)",
    ]
    write_file(target, render_document(merged, header))

    records = os.path.join(handoff_root(), "records", session_id or "unknown")
    write_file(os.path.join(records, "HANDOFF.md"), render_document(merged, header))
    return 0


def handle_post_compact(payload):
    session_id = payload.get("session_id") or payload.get("sessionId") or "unknown"
    trigger = payload.get("trigger") or "auto"
    records = os.path.join(handoff_root(), "records", session_id)
    os.makedirs(records, exist_ok=True)
    with open(os.path.join(records, "compactions.log"), "a", encoding="utf-8") as handle:
        handle.write("%s trigger=%s\n" % (now_iso(), trigger))
    return 0


def handle_session_start(payload):
    if payload.get("source") != "compact":
        return 0
    root = project_root(payload)
    target = os.path.join(root, "HANDOFF.md")
    if not os.path.isfile(target):
        return 0
    try:
        with open(target, "r", encoding="utf-8") as handle:
            body = handle.read()
    except Exception:
        return 0
    body = body.strip()
    if not body:
        return 0
    if len(body) > MAX_CONTEXT_CHARS:
        body = body[:MAX_CONTEXT_CHARS] + "\n\n<!-- truncated: full file at %s -->" % target
    sys.stdout.write(body + "\n")
    return 0


def handle_cli(argv):
    """Manual mode: write the handoff for a session without waiting for a hook.

    compaction-handoff.py --session-id <id> [--cwd <dir>]

    Same five sections, same extraction, same document as the PreCompact hook.
    """
    session_id = ""
    cwd = ""
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--session-id" and i + 1 < len(argv):
            session_id = argv[i + 1]
            i += 2
            continue
        if arg == "--cwd" and i + 1 < len(argv):
            cwd = argv[i + 1]
            i += 2
            continue
        i += 1
    if not session_id:
        print("usage: compaction-handoff.py --session-id <id> [--cwd <dir>]", file=sys.stderr)
        return 2
    rows = session_rows(session_id)
    if not rows:
        print("no messages found for session %s" % session_id, file=sys.stderr)
        return 1
    facts = collect(rows)
    sections = build_sections(facts)
    header = [
        "<!-- generated by the MiniMax Code compaction handoff hook -->",
        "<!-- scratch file: do not commit -->",
        "- Updated: " + now_iso(),
        "- Session: " + session_id,
        "- Trigger: manual",
        "- Compaction threshold: 100000 tokens (contextManagement.compactionTriggerAt)",
    ]
    target = os.path.join(cwd or os.path.expanduser("~"), "HANDOFF.md")
    write_file(target, render_document(sections, header))
    records = os.path.join(handoff_root(), "records", session_id)
    write_file(os.path.join(records, "HANDOFF.md"), render_document(sections, header))
    print(target)
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--session-id", "--handoff"):
        return handle_cli(sys.argv[1:])
    payload = read_stdin()
    event = payload.get("hook_event_name") or ""
    session_id = payload.get("session_id") or payload.get("sessionId") or ""
    try:
        if event == "SessionStart" and payload.get("source") != "compact":
            return 0
        log_event(session_id, event)
        if event == "PreCompact":
            return handle_pre_compact(payload)
        if event == "PostCompact":
            return handle_post_compact(payload)
        if event == "SessionStart":
            return handle_session_start(payload)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
