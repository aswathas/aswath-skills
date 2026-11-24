#!/usr/bin/env python3
"""Switch the Claude Code auto-compact window and the compaction rules by template.

Templates: basic (200k), medium (300k), hard (400k).

    python autocompact.py apply medium
    python autocompact.py status
    python autocompact.py uninstall

What "apply" does:
  1. writes autoCompactWindow into the user settings file, both as the top-level
     default and per model entry, so the window is the same whichever model id the
     runtime canonicalises to;
  2. writes the active template to ~/.claude/autocompact-template.json;
  3. registers a PreCompact hook that prints that template's rules, which the
     runtime feeds into the compaction summary.

It never touches anything it does not own: unknown settings keys, other hooks and
other model settings are preserved.
"""

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
PRESETS_FILE = SKILL_DIR / "presets.json"

HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".")
CLAUDE_DIR = HOME / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
STATE_FILE = CLAUDE_DIR / "autocompact-template.json"
# The installed junction, not the repo path - it survives the repo moving.
HOOK_SCRIPT = HOME / ".agents" / "skills" / "aswath-autocompact" / "scripts" / "compaction_rules.py"
if not HOOK_SCRIPT.exists():
    HOOK_SCRIPT = SKILL_DIR / "scripts" / "compaction_rules.py"

MIN_WINDOW = 100_000
HOOK_MARKER = "aswath-autocompact"


def load_presets():
    data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
    return data["templates"]


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}")


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def model_keys(settings):
    """Model ids the runtime may canonicalise the session model to.

    The runtime looks a per-model entry up by canonical id, which it derives from
    the model string. The exact spelling differs per model, so every known spelling
    gets the same value - the extra entries are ignored, never wrong.
    """
    keys = set(settings.get("modelSettings", {}) or {})
    model = settings.get("model")
    if isinstance(model, str) and model:
        keys.add(model)
        keys.add(model.split("[")[0])
        keys.add(model.lower())
    picker = settings.get("modelPicker") or {}
    for row in picker.get("options", []) or []:
        name = row.get("model")
        if isinstance(name, str) and name:
            keys.add(name)
            keys.add(name.split("[")[0])
    return sorted(k for k in keys if k)


def set_window(settings, window):
    settings["autoCompactWindow"] = window
    model_settings = settings.setdefault("modelSettings", {})
    for key in model_keys(settings):
        entry = model_settings.setdefault(key, {})
        if not isinstance(entry, dict):
            continue
        entry["autoCompactWindow"] = window


def register_hook(settings):
    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreCompact", [])
    command = f'python "{HOOK_SCRIPT}"'
    for group in pre:
        for hook in group.get("hooks", []) or []:
            if HOOK_MARKER in str(hook.get("command", "")):
                hook["command"] = command
                hook.setdefault("type", "command")
                hook.setdefault("timeout", 10)
                return
    pre.append({"hooks": [{"type": "command", "command": command, "timeout": 10}]})


def unregister_hook(settings):
    hooks = settings.get("hooks", {}) or {}
    pre = hooks.get("PreCompact", []) or []
    kept_groups = []
    for group in pre:
        kept = [h for h in group.get("hooks", []) or [] if HOOK_MARKER not in str(h.get("command", ""))]
        if kept:
            kept_groups.append({**group, "hooks": kept})
    if kept_groups:
        settings["hooks"]["PreCompact"] = kept_groups
    else:
        settings["hooks"].pop("PreCompact", None)
        if not settings["hooks"]:
            settings.pop("hooks", None)


def apply(name):
    presets = load_presets()
    if name not in presets:
        raise SystemExit(f"unknown template {name!r}; choose from {', '.join(presets)}")
    preset = presets[name]
    window = int(preset["window"])

    settings = load_json(SETTINGS_FILE, {})
    if not isinstance(settings, dict):
        raise SystemExit(f"{SETTINGS_FILE} is not a JSON object")
    set_window(settings, window)
    register_hook(settings)
    save_json(SETTINGS_FILE, settings)

    save_json(
        STATE_FILE,
        {
            "template": name,
            "label": preset["label"],
            "window": window,
            "use_when": preset["use_when"],
            "rules": preset["rules"],
        },
    )

    env_block = settings.get("env", {}) or {}
    blocked = "CLAUDE_CODE_AUTO_COMPACT_WINDOW" in env_block
    print(f"template      {name} ({preset['label']})")
    print(f"window        {window} tokens")
    print(f"settings      {SETTINGS_FILE}")
    print(f"state         {STATE_FILE}")
    print(f"rules hook    PreCompact -> {HOOK_SCRIPT}")
    if blocked:
        print(
            "WARNING       CLAUDE_CODE_AUTO_COMPACT_WINDOW is set in settings env and outranks "
            "the settings file. Remove it or the window will not change."
        )
    print(
        "NOTE          the running session keeps the old window; the new one applies to the "
        "next launch."
    )


def status():
    presets = load_presets()
    settings = load_json(SETTINGS_FILE, {})
    state = load_json(STATE_FILE, {})
    window = settings.get("autoCompactWindow")
    env_window = (settings.get("env", {}) or {}).get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    print("templates")
    for name, preset in presets.items():
        print(f"  {name:<8} {preset['window']:>7} tokens  {preset['label']}")
    print(f"settings window      {window}")
    print(f"settings env window  {env_window if env_window else 'unset'}")
    print(f"active template      {state.get('template') or 'none'}")
    print(f"state file           {STATE_FILE if state else 'missing'}")
    hook_ok = False
    for group in (settings.get("hooks", {}) or {}).get("PreCompact", []) or []:
        for hook in group.get("hooks", []) or []:
            if HOOK_MARKER in str(hook.get("command", "")):
                hook_ok = True
    print(f"rules hook installed  {'yes' if hook_ok else 'no'}")


def uninstall():
    settings = load_json(SETTINGS_FILE, {})
    unregister_hook(settings)
    settings.pop("autoCompactWindow", None)
    for entry in (settings.get("modelSettings", {}) or {}).values():
        if isinstance(entry, dict):
            entry.pop("autoCompactWindow", None)
    save_json(SETTINGS_FILE, settings)
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print("removed the window override and the rules hook")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("template", choices=sorted(load_presets()))
    sub.add_parser("status")
    sub.add_parser("uninstall")
    args = parser.parse_args()

    if args.command == "apply":
        apply(args.template)
    elif args.command == "status":
        status()
    else:
        uninstall()


if __name__ == "__main__":
    main()
