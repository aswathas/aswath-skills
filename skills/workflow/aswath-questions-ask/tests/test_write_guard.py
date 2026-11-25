"""Tests for the aswath-questions-ask write guard.

Run: python tests/test_write_guard.py
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(os.path.dirname(HERE), "hooks", "write_guard.py")

STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "state")
STATE_FILE = os.path.join(STATE_DIR, "questions-ask.json")

LEDGER = "/tmp/project/docs/understanding/blockchain ledger.md"
OTHER = "/tmp/project/notes/topic.md"


def run(event, payload):
    proc = subprocess.run(
        [sys.executable, HOOK, "--event", event, "--payload-stdin"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stderr


def set_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as handle:
        json.dump({"state": state, "ledger": None}, handle)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def main():
    saved = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            saved = handle.read()

    try:
        # 1. INTERVIEW blocks Write
        set_state("INTERVIEW")
        code, err = run("PreToolUse", {
            "tool_name": "Write",
            "tool_input": {"file_path": OTHER, "content": "x"},
        })
        check("interview blocks Write", code == 2, "code=%s" % code)

        # 2. INTERVIEW blocks Bash redirection
        code, err = run("PreToolUse", {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi > /tmp/out.txt"},
        })
        check("interview blocks Bash redirect", code == 2, "code=%s" % code)

        # 3. INTERVIEW allows read-only Bash
        code, err = run("PreToolUse", {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la /tmp"},
        })
        check("interview allows read-only Bash", code == 0, "code=%s" % code)

        # 4. LOCKED allows the ledger path
        set_state("LOCKED")
        code, err = run("PreToolUse", {
            "tool_name": "Write",
            "tool_input": {"file_path": LEDGER, "content": "x"},
        })
        check("locked allows ledger path", code == 0, "code=%s" % code)

        # 5. LOCKED blocks another path
        code, err = run("PreToolUse", {
            "tool_name": "Write",
            "tool_input": {"file_path": OTHER, "content": "x"},
        })
        check("locked blocks other path", code == 2, "code=%s" % code)

        # 6. INACTIVE allows everything
        set_state("INACTIVE")
        code, err = run("PreToolUse", {
            "tool_name": "Write",
            "tool_input": {"file_path": OTHER, "content": "x"},
        })
        check("inactive allows Write", code == 0, "code=%s" % code)

        # 7. skill invocation opens the interview
        set_state("INACTIVE")
        code, err = run("UserPromptSubmit", {"prompt": "/aswath-questions-ask go"})
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            state = json.load(handle)["state"]
        check("skill marker opens interview", state == "INTERVIEW", state)

        # 8. LOCK in the prompt flips state
        code, err = run("UserPromptSubmit", {"prompt": "LOCK"})
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            state = json.load(handle)["state"]
        check("LOCK flips state to LOCKED", state == "LOCKED", state)

        # 9. "enough" closes the interview
        code, err = run("UserPromptSubmit", {"prompt": "ok, enough"})
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            state = json.load(handle)["state"]
        check("enough closes interview", state == "CLOSED", state)

        # 10. QA_OVERRIDE escapes the Bash block
        set_state("INTERVIEW")
        code, err = run("PreToolUse", {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi > /tmp/out.txt  # QA_OVERRIDE"},
        })
        check("QA_OVERRIDE escapes", code == 0, "code=%s" % code)

        # 11. INTERVIEW blocks git checkout
        set_state("INTERVIEW")
        code, err = run("PreToolUse", {
            "tool_name": "Bash",
            "tool_input": {"command": "git checkout -- ."},
        })
        check("interview blocks git checkout", code == 2, "code=%s" % code)

        # 12. INTERVIEW allows git commit
        code, err = run("PreToolUse", {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'x'"},
        })
        check("interview allows git commit", code == 0, "code=%s" % code)
    finally:
        if saved is None:
            clear_state()
        else:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as handle:
                handle.write(saved)

    print("")
    if FAILURES:
        print("%d failed: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
