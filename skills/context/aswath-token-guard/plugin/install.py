#!/usr/bin/env python3
"""Idempotent installer for the MiniMax Code token guard hook.

Copies two wrapper scripts into the runtime's data directory and adds three
hook groups to <dataDir>/hooks.json:

  SessionStart      the orientation, once per session
  UserPromptSubmit  the live numbers, once the session passes 200k tokens and
                    then only after another 25k of growth
  PreToolUse        an exact repeat read of an unchanged file is denied

Existing content is preserved: unknown JSON keys stay, existing hook groups
stay, and only the groups this installer owns are replaced. Running it twice
changes nothing.

Usage:
    python install.py [--data-dir <path>] [--dry-run]
    python install.py uninstall [--data-dir <path>] [--dry-run]
"""

import argparse
import json
import os
import shutil
import sys

TIMEOUT_SECONDS = 5

# event, matcher, name
SPECS = [
    ("SessionStart", None, "Token guard orientation"),
    ("UserPromptSubmit", "*", "Token guard context check"),
    ("PreToolUse", "read", "Token guard repeat-read blocker"),
]

SCRIPT_NAMES = ("token_guard-hook.sh", "token_guard-hook.ps1", "token_guard_hook.py")


def data_dir(explicit=None):
    if explicit:
        return os.path.abspath(explicit)
    for key in ("MINIMAX_DATA_DIR", "MAVIS_DATA_DIR"):
        value = os.environ.get(key)
        if value and value.strip():
            return os.path.abspath(value.strip())
    return os.path.join(os.path.expanduser("~"), ".minimax")


def plugin_scripts():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")


def commands_for(root):
    sh = 'sh "%s"' % os.path.join(root, "token_guard-hook.sh").replace("\\", "/")
    ps = (
        "powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass"
        ' -File "%s"' % os.path.join(root, "token_guard-hook.ps1")
    )
    return sh, ps


def make_group(matcher, name, sh, ps):
    group = {}
    if matcher is not None:
        group["matcher"] = matcher
    group["hooks"] = [
        {
            "type": "command",
            "name": name,
            "command": sh,
            "commandWindows": ps,
            "timeout": TIMEOUT_SECONDS,
        }
    ]
    return group


def group_matches(group, matcher):
    if matcher is None:
        return "matcher" not in group
    return group.get("matcher") == matcher


def is_ours(group):
    for hook in (group.get("hooks") or []):
        if "token-guard-hook" in str(hook.get("command", "")) or \
           "token-guard-hook" in str(hook.get("commandWindows", "")):
            return True
    return False


def copy_scripts(root, dry_run=False):
    src = plugin_scripts()
    copied = []
    for name in SCRIPT_NAMES:
        source = os.path.join(src, name)
        if not os.path.isfile(source):
            continue
        target = os.path.join(root, name)
        if not dry_run:
            os.makedirs(root, exist_ok=True)
            shutil.copyfile(source, target)
            if name.endswith(".sh"):
                try:
                    os.chmod(target, 0o755)
                except OSError:
                    pass
        copied.append(target)
    return copied


def patch_hooks(path, root, install, dry_run=False):
    created = not os.path.isfile(path)
    data = {}
    if not created:
        try:
            data = json.loads(open(path, "r", encoding="utf-8").read())
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}

    container = data.get("hooks")
    if not isinstance(container, dict):
        container = {}
        data["hooks"] = container

    sh, ps = commands_for(root)
    added = []
    for event, matcher, name in SPECS:
        groups = container.get(event)
        if not isinstance(groups, list):
            groups = []
        keep = []
        replaced = False
        for group in groups:
            if not isinstance(group, dict):
                keep.append(group)
                continue
            if is_ours(group):
                if install and not replaced:
                    keep.append(make_group(matcher, name, sh, ps))
                    replaced = True
                continue
            if group_matches(group, matcher) and not is_ours(group):
                # only replace a group we own, never someone else's
                keep.append(group)
                continue
            keep.append(group)
        if install and not replaced:
            keep.append(make_group(matcher, name, sh, ps))
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
    parser.add_argument("action", nargs="?", default="install", choices=("install", "uninstall"))
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = data_dir(args.data_dir)
    hooks_path = os.path.join(root, "hooks.json")
    install = args.action == "install"

    if install:
        copied = copy_scripts(root, args.dry_run)
        for path in copied:
            print("script    : %s" % path)

    created, added = patch_hooks(hooks_path, root, install, args.dry_run)
    print("hooks.json: %s" % ("created" if created else "updated"))
    if install:
        print("  added: " + (", ".join(added) if added else "already present"))
    else:
        print("  removed: the token guard groups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
