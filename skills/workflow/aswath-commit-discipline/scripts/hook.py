#!/usr/bin/env python3
"""Cross-harness hook for the commit discipline.

One runner for every harness that speaks a stdin/JSON hook protocol:
MiniMax Code, Claude Code, Codex, Cursor and Command Code.

Two jobs:

* Prompt events - when the prompt looks like commit/push/GitHub work, print the
  contract (reference/contract.txt) so the agent writes the records first.
* Tool events - when a shell command is about to run ``git commit`` or ``git push``,
  run the push-time checker (scripts/check_push.py) and print the gaps.

Nothing here blocks. Every path exits 0, a parse error exits 0 silently, and no
harness is ever refused. The checker is read-only apart from one ``git ls-remote
--heads`` call per branch, which it makes to learn what the remote really has.

Payload shapes handled:

* ``{"hook_event_name": "UserPromptSubmit", "prompt": "..."}`` - MiniMax Code,
  Claude Code, Codex.
* ``{"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "..."}}``
  - Claude Code, Codex.
* ``{"hook_event_name": "beforeSubmitPrompt", "prompt": "..."}`` and
  ``{"hook_event_name": "beforeShellExecution", "command": "..."}`` - Cursor.
* ``{"tool_input": {"command": "..."}, "cwd": "..."}`` - Command Code.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_push.py"
CONTRACT = HERE.parent / "reference" / "contract.txt"

FALLBACK_CONTRACT = """Commit discipline: this work does not leave the machine undocumented.

Before it is committed and pushed, every one of these must be written down:

- Every decision spoken with an AI (including the prompt that produced it) -> docs/reviews/decision-log.md
- Every changed file -> one row in docs/reviews/change-inventory.md (what changed, why, how verified)
- Every prompt that shaped the work -> logged (aswath-chronicle keeps this record)
- Every skill added or changed -> what it answers, its triggers, its scripts, how it was verified

Then push it: branch first, push on explicit instruction, never amend a published commit.

The commit count is free. 100 documented commits are fine. The detail is not optional.

Full contract and templates: /aswath-commit-discipline
"""

# Words that mean "this prompt is about shipping work".
PROMPT_PATTERNS = (
    r"\bpush(es|ed|ing)?\b",
    r"\bcommit(s|ted|ting)?\b",
    r"\bgithub\b",
    r"\bpull\s+request\b",
    r"\bpr\b",
    r"\bbranch(es|ed|ing)?\b",
    r"\bmerge\b",
    r"\bpublish(ing|ed)?\b",
    r"\bship(ping|ped)?\b",
    r"\bmass\s+push\b",
    r"\bdocument(ation|ed|ing)?\b",
    r"\bdecision\s+log\b",
    r"\bchange\s+inventory\b",
)

GIT_WRITE = re.compile(r"(?i)\bgit\b[^\n]*\b(commit|push)\b")

PROMPT_KEYS = ("prompt", "user_prompt", "userPrompt", "message", "text", "input", "content")
COMMAND_KEYS = ("command", "cmd", "script", "shell_command", "shellCommand")

# Cursor wants a JSON verdict on its shell hooks; other harnesses take plain text.
CURSOR_SHELL_EVENTS = ("beforeShellExecution", "afterShellExecution")


def read_stdin() -> str:
    try:
        if sys.stdin is None or sys.stdin.closed:
            return ""
        return sys.stdin.read()
    except (OSError, ValueError, UnicodeDecodeError):
        return ""


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(as_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(as_text(v) for v in value.values())
    return str(value)


def first_text(payload: dict, keys) -> str:
    for key in keys:
        if key in payload:
            text = as_text(payload.get(key)).strip()
            if text:
                return text
    return ""


def command_of(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        text = first_text(tool_input, COMMAND_KEYS)
        if text:
            return text
        args = tool_input.get("args")
        if isinstance(args, (list, tuple)):
            return " ".join(as_text(a) for a in args)
    return first_text(payload, COMMAND_KEYS)


def contract_text() -> str:
    try:
        text = CONTRACT.read_text(encoding="utf-8").strip()
        if text:
            return text
    except (OSError, UnicodeDecodeError):
        pass
    return FALLBACK_CONTRACT.strip()


def is_prompt_event(event: str, payload: dict, command: str) -> bool:
    if event in ("beforeSubmitPrompt", "UserPromptSubmit", "user_prompt_submit", "PromptSubmit"):
        return True
    if command:
        return False
    return bool(first_text(payload, PROMPT_KEYS))


def prompt_hits(prompt: str) -> bool:
    return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in PROMPT_PATTERNS)


def repo_of(payload: dict) -> str:
    cwd = as_text(payload.get("cwd")).strip()
    if not cwd:
        cwd = os.getcwd()
    if not os.path.isdir(cwd):
        cwd = os.getcwd()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
        )
        root = out.stdout.strip()
        if root:
            return root
    except (OSError, subprocess.SubprocessError):
        pass
    return cwd


def run_checker(repo: str) -> str:
    try:
        out = subprocess.run(
            [sys.executable, str(CHECKER), "--repo", repo],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return "[commit-discipline] WARN: checker could not run: %s" % exc
    return (out.stdout or "").strip()


def emit(text: str, cursor_json: bool) -> None:
    if not text:
        return
    if cursor_json:
        sys.stdout.write(json.dumps({"permission": "allow", "userMessage": text}) + "\n")
    else:
        sys.stdout.write(text + "\n")
    sys.stdout.flush()


def main() -> int:
    raw = read_stdin()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    event = as_text(payload.get("hook_event_name") or payload.get("event") or payload.get("event_name"))
    command = command_of(payload)
    cursor_json = event in CURSOR_SHELL_EVENTS

    try:
        if is_prompt_event(event, payload, command):
            prompt = first_text(payload, PROMPT_KEYS)
            if prompt and prompt_hits(prompt):
                emit(contract_text(), False)
            return 0

        if command and GIT_WRITE.search(command):
            repo = repo_of(payload)
            text = run_checker(repo)
            if text:
                emit(text, cursor_json)
                # Claude Code shows a PreToolUse hook's stderr to the user; its stdout
                # is transcript-only. Print both so every harness shows the warning.
                sys.stderr.write(text + "\n")
                sys.stderr.flush()
        return 0
    except Exception:  # never break a harness session
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
