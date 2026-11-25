#!/usr/bin/env python3
"""Register the write-guard hooks in ~/.claude/settings.json.

Text-level surgery, not a JSON round trip: the settings file on this machine
has case-variant duplicate keys (PowerShell's ConvertFrom-Json rejects those,
and a full parse would silently drop one of them). Inserting text leaves
every byte of the rest of the file alone.

    python hooks/install_hooks.py            # register
    python hooks/install_hooks.py --remove   # unregister
"""

import json
import os
import re
import sys

MARKER = "write-guard.ps1"


def settings_path():
    return os.path.join(os.path.expanduser("~"), ".claude", "settings.json")


def hook_command(event):
    hook = os.path.join(os.path.dirname(os.path.abspath(__file__)), "write-guard.ps1")
    return 'powershell -NoProfile -File "%s" %s' % (hook, event)


def pre_block():
    cmd = json.dumps(hook_command("PreToolUse"))[1:-1]
    return (
        '    {\n'
        '      "matcher": "Bash|Edit|Write|MultiEdit|NotebookEdit",\n'
        '      "hooks": [\n'
        '        {\n'
        '          "type": "command",\n'
        '          "command": "%s"\n'
        '        }\n'
        '      ]\n'
        '    },\n' % cmd
    )


def prompt_block():
    cmd = json.dumps(hook_command("UserPromptSubmit"))[1:-1]
    return (
        '  "UserPromptSubmit": [\n'
        '    {\n'
        '      "hooks": [\n'
        '        {\n'
        '          "type": "command",\n'
        '          "command": "%s"\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ],\n' % cmd
    )


def prompt_entry():
    cmd = json.dumps(hook_command("UserPromptSubmit"))[1:-1]
    return (
        '    {\n'
        '      "hooks": [\n'
        '        {\n'
        '          "type": "command",\n'
        '          "command": "%s"\n'
        '        }\n'
        '      ]\n'
        '    },\n' % cmd
    )


def register(text):
    if MARKER in text:
        return text, False
    # PreToolUse entry: insert as the first element of the array.
    m = re.search(r'("PreToolUse"\s*:\s*\[)', text)
    if not m:
        raise SystemExit("no PreToolUse array in settings.json")
    text = text[: m.end()] + "\n" + pre_block() + text[m.end():]

    # UserPromptSubmit: append to the existing array if there is one,
    # otherwise add the key inside the hooks object.
    m = re.search(r'("UserPromptSubmit"\s*:\s*\[)', text)
    if m:
        text = text[: m.end()] + "\n" + prompt_entry() + text[m.end():]
    else:
        m = re.search(r'("hooks"\s*:\s*\{)', text)
        if not m:
            raise SystemExit("no hooks object in settings.json")
        text = text[: m.end()] + "\n" + prompt_block() + text[m.end():]
    return text, True


def unregister(text):
    if MARKER not in text:
        return text, False
    cmd = r'(?:[^"\\]|\\.)*' + re.escape(MARKER) + r'(?:[^"\\]|\\.)*'
    # The PreToolUse entry.
    pattern = re.compile(
        r'\{\s*"matcher"\s*:\s*"Bash\|Edit\|Write\|MultiEdit\|NotebookEdit"\s*,'
        r'\s*"hooks"\s*:\s*\[\s*\{\s*"type"\s*:\s*"command"\s*,\s*"command"\s*:\s*"'
        + cmd + r'"\s*\}\s*\]\s*\},?\s*',
        re.S,
    )
    text = pattern.sub("", text)
    # The UserPromptSubmit entry, wherever it sits.
    pattern = re.compile(
        r'\{\s*"hooks"\s*:\s*\[\s*\{\s*"type"\s*:\s*"command"\s*,\s*"command"\s*:\s*"'
        + cmd + r'"\s*\}\s*\]\s*\},?\s*',
        re.S,
    )
    text = pattern.sub("", text)
    return text, True


def main():
    path = settings_path()
    with open(path, "r", encoding="utf-8") as handle:
        original = handle.read()

    if "--remove" in sys.argv:
        text, changed = unregister(original)
        action = "removed"
    else:
        text, changed = register(original)
        action = "registered"

    if changed:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    print("write guard %s (%s)" % (action, "changed" if changed else "already in place"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
