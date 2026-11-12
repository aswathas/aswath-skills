#!/usr/bin/env python3
"""
The token guard hook for MiniMax Code.

Three events:

  SessionStart      inject the orientation once: the live context number and
                    the four habits that cut it.
  UserPromptSubmit  stay silent until the session passes the threshold, then
                    speak once more, and only after another step of growth.
                    A silent hook is the point.
  PreToolUse        block an exact repeat read of a file that has not changed
                    since the session started.

The numbers come from the runtime's own records: context_usage.usedTokens on
the session's messages, and the tool calls in the same rows. Nothing is
estimated.

Usage:
    token_guard_hook.py --event <Event> --payload-file <path>
    token_guard_hook.py --event <Event> --payload-stdin
"""

import argparse
import json
import os
import sqlite3
import sys

THRESHOLD_TOKENS = 200_000
STEP_TOKENS = 25_000
READ_TOOLS = ("read", "view", "read_file")

HABITS = [
    "Read once. Do not re-read a region you already read; cite it instead.",
    "Reference, do not re-send. Point at a path, an identifier, a line number.",
    "Summarise, do not re-quote. Large tool output becomes one line, not a paste.",
    "Read narrow. grep or glob with a pattern before opening a whole file.",
]


def data_dir():
    for key in ("MINIMAX_DATA_DIR", "MAVIS_DATA_DIR"):
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    return os.path.join(os.path.expanduser("~"), ".minimax")


def db_path():
    return os.path.join(data_dir(), "v2", "sqlite", "runtime-state.sqlite")


def state_path():
    return os.path.join(data_dir(), "token-guard-state.json")


def read_state():
    try:
        with open(state_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(state):
    try:
        os.makedirs(os.path.dirname(state_path()), exist_ok=True)
        with open(state_path(), "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
    except OSError:
        pass


def connect():
    path = db_path()
    if not os.path.isfile(path):
        return None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True)
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.Error:
        return None


def session_rows(session_id):
    con = connect()
    if con is None or not session_id:
        return []
    try:
        rows = con.execute(
            "select created_at_ms, data_json from local_runtime_message_rows"
            " where session_id=? order by created_at_ms",
            (session_id,),
        ).fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        con.close()
    out = []
    for row in rows:
        try:
            data = json.loads(row["data_json"])
        except (json.JSONDecodeError, TypeError):
            continue
        data["_created_at_ms"] = row["created_at_ms"]
        out.append(data)
    return out


def live_window(session_id, rows):
    """The context the session is carrying right now."""
    for data in reversed(rows):
        usage = data.get("context_usage")
        if isinstance(usage, dict) and usage.get("usedTokens") is not None:
            try:
                return int(usage["usedTokens"])
            except (TypeError, ValueError):
                pass
    # fall back to the usage table: the last turn's window
    con = connect()
    if con is None or not session_id:
        return 0
    try:
        row = con.execute(
            "select input_tokens, cache_read_tokens, cache_write_tokens"
            " from local_runtime_token_usage where session_id=?"
            " order by ts desc limit 1",
            (session_id,),
        ).fetchone()
    except sqlite3.Error:
        row = None
    finally:
        con.close()
    if not row:
        return 0
    return int(row[0] or 0) + int(row[1] or 0) + int(row[2] or 0)


def prior_reads(rows):
    """(path, offset, limit) for every read tool call so far in the session."""
    out = []
    for data in rows:
        for call in data.get("tool_calls") or []:
            if str(call.get("tool_name") or "").lower() not in READ_TOOLS:
                continue
            args = call.get("tool_call_args")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, ValueError):
                    args = {}
            if not isinstance(args, dict):
                args = {}
            path = args.get("path") or args.get("file_path")
            if path:
                out.append((str(path), args.get("offset"), args.get("limit")))
    return out


def unchanged_since_session(path, rows):
    """True when the file has not been touched since the session began."""
    if not rows:
        return False
    started = rows[0].get("_created_at_ms")
    if not started:
        return False
    try:
        mtime_ms = int(os.path.getmtime(path) * 1000)
    except OSError:
        return False
    return mtime_ms < int(started)


def orientation(session_id, window):
    lines = [
        "Context guard is on.",
        "  session context: %s tokens" % f"{window:,}",
        "  the four habits, in order of what they save:",
    ]
    for i, habit in enumerate(HABITS, 1):
        lines.append("    %d. %s" % (i, habit))
    lines.append("  Measure the session with the token-guard skill before you claim a saving.")
    return "\n".join(lines)


def repeat_read_notice(session_id, window, path):
    lines = [
        "Context guard: %s was already read in this session and has not changed." % path,
        "  session context: %s tokens" % f"{window:,}",
        "  Cite the earlier read instead of repeating it, or read a different range.",
    ]
    return "\n".join(lines)


def deny(reason):
    """The Claude Code hook response for a denied tool call."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def read_payload(args):
    if args.payload_file and args.payload_file != "-":
        try:
            with open(args.payload_file, "r", encoding="utf-8", errors="replace") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}
    raw = sys.stdin.read()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", default="")
    parser.add_argument("--payload-file", default="-")
    args = parser.parse_args()

    payload = read_payload(args)
    event = args.event or payload.get("hook_event_name") or ""
    session_id = str(payload.get("session_id") or payload.get("sessionId") or "default")

    if event == "SessionStart":
        rows = session_rows(session_id)
        window = live_window(session_id, rows)
        print(orientation(session_id, window))
        return 0

    if event == "UserPromptSubmit":
        rows = session_rows(session_id)
        window = live_window(session_id, rows)
        if window < THRESHOLD_TOKENS:
            return 0
        state = read_state()
        entry = state.get(session_id) or {}
        last = int(entry.get("notified") or 0)
        if last and window - last < STEP_TOKENS:
            return 0
        state[session_id] = {"notified": window, "at": window}
        write_state(state)
        print(repeat_read_notice(session_id, window, "the context")) if False else None
        print(orientation(session_id, window))
        return 0

    if event == "PreToolUse":
        tool = str(payload.get("tool_name") or payload.get("toolName") or "").lower()
        if tool not in READ_TOOLS:
            return 0
        tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
        if not isinstance(tool_input, dict):
            return 0
        path = tool_input.get("file_path") or tool_input.get("path")
        if not path:
            return 0
        rows = session_rows(session_id)
        offset = tool_input.get("offset")
        limit = tool_input.get("limit")
        for seen_path, seen_offset, seen_limit in prior_reads(rows):
            if os.path.abspath(seen_path) != os.path.abspath(str(path)):
                continue
            if (seen_offset or None) != (offset or None) or (seen_limit or None) != (limit or None):
                continue
            if unchanged_since_session(str(path), rows):
                window = live_window(session_id, rows)
                deny(repeat_read_notice(session_id, window, str(path)))
            break
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
