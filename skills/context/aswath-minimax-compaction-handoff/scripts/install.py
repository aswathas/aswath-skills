#!/usr/bin/env python3
"""Idempotent installer for the MiniMax Code compaction handoff hook.

Patches two files, in place, without touching anything else:

  1. <dataDir>/config.yaml   -> contextManagement.compactionTriggerAt: 100000
  2. <dataDir>/hooks.json    -> PreCompact, PostCompact and SessionStart(compact) groups

Existing content is preserved: unknown YAML keys stay, unknown JSON keys stay,
existing hook groups stay, and only matching entries are replaced. Running it
twice changes nothing.

Usage:
    python install.py [--data-dir <path>] [--trigger <tokens>] [--dry-run]
"""

import argparse
import json
import os
import sys

DEFAULT_TRIGGER = 100000
TIMEOUT_SECONDS = 10

SH_COMMAND = 'sh "$HOME/.minimax/compaction-handoff.sh"'
PS_COMMAND = (
    "powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass"
    ' -File "C:\\Users\\ADMIN\\.minimax\\compaction-handoff.ps1"'
)

TRIGGER_BLOCK = "contextManagement:\n  compactionTriggerAt: %d\n"


def data_dir(explicit=None):
    if explicit:
        return os.path.abspath(explicit)
    for key in ("MINIMAX_DATA_DIR", "MAVIS_DATA_DIR"):
        value = os.environ.get(key)
        if value and value.strip():
            return os.path.abspath(value.strip())
    return os.path.join(os.path.expanduser("~"), ".minimax")


def patch_config(path, trigger, dry_run=False):
    """Ensure contextManagement.compactionTriggerAt is set to trigger."""
    created = not os.path.isfile(path)
    original = "" if created else open(path, "r", encoding="utf-8").read()
    lines = original.splitlines()

    out = []
    i = 0
    patched = False
    while i < len(lines):
        line = lines[i]
        if line.strip() == "contextManagement:":
            out.append(line)
            i += 1
            while i < len(lines) and lines[i].strip() and lines[i][:1] in (" ", "\t"):
                i += 1
            out.append("  compactionTriggerAt: %d" % trigger)
            patched = True
            continue
        out.append(line)
        i += 1

    text = "\n".join(out)
    if not patched:
        if text and not text.endswith("\n"):
            text += "\n"
        text += TRIGGER_BLOCK % trigger
    elif text and not text.endswith("\n"):
        text += "\n"

    if not dry_run:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    return created, patched, text


def make_group(matcher, name):
    group = {}
    if matcher is not None:
        group["matcher"] = matcher
    group["hooks"] = [
        {
            "type": "command",
            "name": name,
            "command": SH_COMMAND,
            "commandWindows": PS_COMMAND,
            "timeout": TIMEOUT_SECONDS,
        }
    ]
    return group


def group_matches(group, matcher):
    if matcher is None:
        return "matcher" not in group
    return group.get("matcher") == matcher


def patch_hooks(path, dry_run=False):
    """Ensure the three hook groups exist exactly once each."""
    created = not os.path.isfile(path)
    data = {}
    if not created:
        try:
            data = json.loads(open(path, "r", encoding="utf-8").read())
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}

    # Events live under the top-level "hooks" object in the MiniMax layout.
    container = data.get("hooks")
    if not isinstance(container, dict):
        container = {}
        data["hooks"] = container

    specs = [
        ("PreCompact", None, "Write HANDOFF.md before compaction"),
        ("PostCompact", None, "Log compaction to session handoff records"),
        ("SessionStart", "compact", "Re-inject HANDOFF.md after compaction"),
    ]

    added = []
    for event, matcher, name in specs:
        groups = container.get(event)
        if not isinstance(groups, list):
            groups = []
        keep = []
        replaced = False
        for group in groups:
            if not isinstance(group, dict):
                keep.append(group)
                continue
            if group_matches(group, matcher):
                if replaced:
                    continue  # drop duplicate
                keep.append(make_group(matcher, name))
                replaced = True
                continue
            keep.append(group)
        if not replaced:
            keep.append(make_group(matcher, name))
            added.append("%s%s" % (event, "" if matcher is None else "[%s]" % matcher))
        container[event] = keep

    if not dry_run:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
    return created, added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--trigger", type=int, default=DEFAULT_TRIGGER)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = data_dir(args.data_dir)
    config_path = os.path.join(root, "config.yaml")
    hooks_path = os.path.join(root, "hooks.json")

    config_created, _patched, text = patch_config(config_path, args.trigger, args.dry_run)
    print("config.yaml : %s (trigger=%d)" % ("created" if config_created else "updated", args.trigger))
    for line in text.splitlines():
        if "compactionTriggerAt" in line or line.strip() == "contextManagement:":
            print("  " + line)

    hooks_created, added = patch_hooks(hooks_path, args.dry_run)
    print("hooks.json  : %s" % ("created" if hooks_created else "updated"))
    if added:
        print("  added: " + ", ".join(added))
    else:
        print("  already present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
