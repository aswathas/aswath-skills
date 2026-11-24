#!/usr/bin/env python3
"""PreCompact hook: prints the active template's compaction rules.

Claude Code feeds a PreCompact hook's stdout into the compaction summary as
instructions. So the rules of the active template travel with every compaction
that happens, without anyone re-typing them.

Reads the template state written by autocompact.py apply. If there is no state
file, it prints nothing and exits 0 - an uninstalled skill must not break
compaction.
"""

import json
import os
import sys
from pathlib import Path

HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".")
STATE_FILE = HOME / ".claude" / "autocompact-template.json"


def main():
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return 0

    rules = state.get("rules") or []
    if not rules:
        return 0

    template = state.get("template", "unknown")
    label = state.get("label", "")
    print(f"Compaction rules for this session - template '{template}' ({label}).")
    for rule in rules:
        print(f"- {rule}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
