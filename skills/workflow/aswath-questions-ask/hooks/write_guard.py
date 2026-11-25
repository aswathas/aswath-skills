#!/usr/bin/env python3
"""
The write guard for aswath-questions-ask.

Two events:

  UserPromptSubmit  move the state machine forward. The skill invocation opens
                    the interview, LOCK lets the ledger be written, "enough" or
                    "understand completely" closes the interview.

  PreToolUse        deny file writes while the interview is running. Exit code 2
                    blocks the tool call and the reason goes back to the agent.

The state file is owned by this script. The agent never writes it.

Usage:
    write_guard.py --event <Event> [--payload-stdin | --payload-file <path>]
"""

import argparse
import json
import os
import re
import sys

STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "state")
STATE_FILE = os.path.join(STATE_DIR, "questions-ask.json")

INACTIVE = "INACTIVE"
INTERVIEW = "INTERVIEW"
LOCKED = "LOCKED"
CLOSED = "CLOSED"

# The skill invocation. Matched loosely so "/aswath-questions-ask" and
# "aswath questions ask" both open the interview.
SKILL_MARKER = re.compile(r"aswath[-_ ]questions[-_ ]ask", re.I)
LOCK_TOKEN = re.compile(r"\block\b", re.I)
ENOUGH = re.compile(
    r"(enough|that'?s enough|no more questions|understand completely|"
    r"i understand (it )?(now|completely)|stop questioning)",
    re.I,
)

# A ledger path. Pattern-based on purpose: during the interview the agent
# cannot write, so it cannot declare where the ledger lives.
LEDGER_PATTERNS = [
    re.compile(r"[/\\]docs[/\\]understanding[/\\][^/\\]+\.md$", re.I),
    re.compile(r"[/\\]Understanding[/\\][^/\\]*ledger[^/\\]*\.md$", re.I),
    re.compile(r"understanding ledger\.md$", re.I),
]

WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

# Shell fragments that change files. Narrow on purpose: a false positive blocks
# a command the user wanted. QA_OVERRIDE in the command line escapes the block.
BASH_WRITE = re.compile(
    r"(^|\s)(\>\>|\>)|(^|\s)tee(\s|$)|sed\s+-i|(^|\s)(cp|mv|rm|mkdir|rmdir|touch|install|chmod|chown)(\s|$)"
    r"|python\s+-c|node\s+-e|python3\s+-c"
    r"|curl\s+[^\s]*\s*-o|(^|\s)wget\s|(^|\s)tar\s+(-\w*x|x)|(^|\s)unzip(\s|$)"
    # Git is accepted, but the subcommands that rewrite working-tree files are not.
    r"|(^|\s)git\s+(checkout|restore|reset|apply|clean|stash)",
    re.I,
)
OVERRIDE = re.compile(r"QA_OVERRIDE", re.I)


# --- state ------------------------------------------------------------------


def read_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {"state": INACTIVE, "ledger": None}
    if not isinstance(data, dict):
        return {"state": INACTIVE, "ledger": None}
    data.setdefault("state", INACTIVE)
    data.setdefault("ledger", None)
    return data


def write_state(data):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    os.replace(tmp, STATE_FILE)


def is_ledger_path(path):
    if not path:
        return False
    for pattern in LEDGER_PATTERNS:
        if pattern.search(path):
            return True
    return False


# --- events -----------------------------------------------------------------


def on_user_prompt(payload):
    prompt = payload.get("prompt") or payload.get("user_prompt") or ""
    if not isinstance(prompt, str):
        prompt = str(prompt)
    state = read_state()
    current = state.get("state", INACTIVE)

    if SKILL_MARKER.search(prompt):
        # A fresh invocation always reopens the interview.
        write_state({"state": INTERVIEW, "ledger": state.get("ledger")})
        return

    if current in (INTERVIEW, LOCKED):
        if ENOUGH.search(prompt):
            write_state({"state": CLOSED, "ledger": state.get("ledger")})
            return
        if LOCK_TOKEN.search(prompt):
            write_state({"state": LOCKED, "ledger": state.get("ledger")})
            return


def on_pre_tool_use(payload):
    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    state = read_state()
    current = state.get("state", INACTIVE)
    if current in (INACTIVE, CLOSED):
        return

    if current == INTERVIEW:
        if tool in WRITE_TOOLS:
            deny(
                "aswath-questions-ask is running and the interview has not been "
                "locked. No file may be written during the interview. "
                "Continue the interview in chat. Say LOCK when the ledger "
                "should be written."
            )
        if tool == "Bash":
            command = str(tool_input.get("command") or "")
            if BASH_WRITE.search(command) and not OVERRIDE.search(command):
                deny(
                    "aswath-questions-ask is running and the interview has not "
                    "been locked. This command would change files. "
                    "Read-only commands are fine. Add QA_OVERRIDE to the "
                    "command if you truly need it."
                )
        return

    if current == LOCKED:
        if tool in WRITE_TOOLS:
            path = str(
                tool_input.get("file_path")
                or tool_input.get("path")
                or tool_input.get("notebook_path")
                or ""
            )
            if not is_ledger_path(path):
                deny(
                    "aswath-questions-ask is locked, so only the understanding "
                    "ledger may be written. This path is not a ledger path: %s" % path
                )
        if tool == "Bash":
            command = str(tool_input.get("command") or "")
            if BASH_WRITE.search(command) and not OVERRIDE.search(command):
                deny(
                    "aswath-questions-ask is locked, so only the understanding "
                    "ledger may be written. This command would change other "
                    "files. Add QA_OVERRIDE if you truly need it."
                )


def deny(reason):
    sys.stderr.write(reason + "\n")
    sys.exit(2)


# --- entry ------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--payload-stdin", action="store_true")
    group.add_argument("--payload-file")
    args = parser.parse_args()

    raw = ""
    if args.payload_file:
        try:
            with open(args.payload_file, "r", encoding="utf-8") as handle:
                raw = handle.read()
        except OSError:
            raw = ""
    elif args.payload_stdin:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    if args.event == "UserPromptSubmit":
        on_user_prompt(payload)
    elif args.event == "PreToolUse":
        on_pre_tool_use(payload)

    return 0


if __name__ == "__main__":
    sys.exit(main())
