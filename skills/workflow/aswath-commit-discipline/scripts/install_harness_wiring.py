#!/usr/bin/env python3
"""Install the commit-discipline wiring into every harness on this PC.

Two jobs:

1. Hook wiring - add one prompt hook and one pre-commit/pre-push hook to each
   harness that speaks a hook protocol, so the contract is stated before the work
   and the gaps are reported before the push.
2. Skill links - make the skill resolvable in the plain-dir harnesses and in the
   MiniMax app's curated skills dir, by junctioning it from the canonical store.

Idempotent: a second run reports "already wired" and changes nothing. Every
config file is backed up once, next to itself, before it is written.

Nothing here blocks. The hooks warn; the global git pre-push hook is the floor.

Usage:
    python install_harness_wiring.py            # apply
    python install_harness_wiring.py --dry-run  # report only
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
STORE = HOME / ".agents" / "skills"
SKILL = "aswath-commit-discipline"
HOOK_REL = "skills/%s/scripts/hook.py" % SKILL
HOOK_CMD = 'python "%s"' % (STORE / SKILL / "scripts" / "hook.py").as_posix()

# Harnesses with no hook surface at all: only the skill link is possible.
PLAIN_DIR_HARNESSES = (
    ".continue", ".trae", ".roo", ".kiro", ".qoder", ".codebuddy",
    ".augment", ".iflow", ".junie", ".zcode", ".grok", ".vibe", ".openclaw",
)

BACKUP_SUFFIX = ".pre-commit-discipline.bak"


def log(msg: str) -> None:
    print(msg)


# ---------------------------------------------------------------- config files


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data, dry_run: bool) -> None:
    if not dry_run:
        backup = path.with_suffix(path.suffix + BACKUP_SUFFIX)
        if not backup.exists():
            shutil.copy2(str(path), str(backup))
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")


def group_has_command(group) -> bool:
    if not isinstance(group, dict):
        return False
    for hook in group.get("hooks", []) or []:
        if isinstance(hook, dict) and hook.get("command") == HOOK_CMD:
            return True
    return False


def flat_has_command(entry) -> bool:
    return isinstance(entry, dict) and entry.get("command") == HOOK_CMD


def add_hook_group(config: dict, event: str, matcher, timeout_prompt: int, timeout_tool: int) -> bool:
    """Add the prompt hook and the pre-commit hook to one event group list."""
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        return False

    changed = False

    # Prompt side: a group with no matcher (or the harness default matcher).
    prompt_groups = hooks.setdefault("UserPromptSubmit", [])
    if not any(group_has_command(g) for g in prompt_groups):
        prompt_groups.append({
            "hooks": [{
                "type": "command",
                "command": HOOK_CMD,
                "timeout": timeout_prompt,
            }]
        })
        changed = True

    # Tool side: matched on the shell tool.
    tool_groups = hooks.setdefault("PreToolUse", [])
    if not any(group_has_command(g) for g in tool_groups):
        tool_groups.append({
            "matcher": matcher,
            "hooks": [{
                "type": "command",
                "command": HOOK_CMD,
                "timeout": timeout_tool,
            }]
        })
        changed = True

    return changed


def wire_claude_like(path: Path, dry_run: bool) -> None:
    """Claude Code and the store's copy of its settings use the same schema."""
    if not path.exists():
        log("  skip %s (not found)" % path)
        return
    config = load_json(path)
    if add_hook_group(config, "UserPromptSubmit", "Bash", 10, 20):
        save_json(path, config, dry_run)
        log("  wired %s" % path)
    else:
        log("  already wired %s" % path)


def wire_codex(path: Path, dry_run: bool) -> None:
    if not path.exists():
        log("  skip %s (not found)" % path)
        return
    config = load_json(path)
    if add_hook_group(config, "UserPromptSubmit", "Bash", 10, 20):
        save_json(path, config, dry_run)
        log("  wired %s" % path)
    else:
        log("  already wired %s" % path)


def wire_cursor(path: Path, dry_run: bool) -> None:
    """Cursor takes a flat list per event and answers with JSON."""
    if not path.exists():
        log("  skip %s (not found)" % path)
        return
    config = load_json(path)
    hooks = config.setdefault("hooks", {})
    changed = False

    prompt_entries = hooks.setdefault("beforeSubmitPrompt", [])
    if not any(flat_has_command(e) for e in prompt_entries):
        prompt_entries.append({"command": HOOK_CMD, "timeout": 10})
        changed = True

    shell_entries = hooks.setdefault("beforeShellExecution", [])
    if not any(flat_has_command(e) for e in shell_entries):
        shell_entries.append({
            "matcher": "^git\\s+(commit|push)",
            "command": HOOK_CMD,
            "timeout": 20,
        })
        changed = True

    if changed:
        save_json(path, config, dry_run)
        log("  wired %s" % path)
    else:
        log("  already wired %s" % path)


def wire_command_code(path: Path, dry_run: bool) -> None:
    """Command Code uses the Claude-style group schema, but its shell tool is
    named bash or powershell."""
    if not path.exists():
        log("  skip %s (not found)" % path)
        return
    config = load_json(path)
    hooks = config.setdefault("hooks", {})
    changed = False

    prompt_groups = hooks.setdefault("UserPromptSubmit", [])
    if not any(group_has_command(g) for g in prompt_groups):
        prompt_groups.append({
            "hooks": [{
                "type": "command",
                "command": HOOK_CMD,
                "timeout": 10,
            }]
        })
        changed = True

    tool_groups = hooks.setdefault("PreToolUse", [])
    if not any(group_has_command(g) for g in tool_groups):
        tool_groups.append({
            "matcher": "bash|powershell",
            "hooks": [{
                "type": "command",
                "command": HOOK_CMD,
                "timeout": 20,
            }]
        })
        changed = True

    if changed:
        save_json(path, config, dry_run)
        log("  wired %s" % path)
    else:
        log("  already wired %s" % path)


# ------------------------------------------------------------------ junctions


def make_junction(link: Path, target: Path, dry_run: bool) -> None:
    if not target.exists():
        log("  skip %s (target missing: %s)" % (link, target))
        return
    if link.exists():
        try:
            current = (link.resolve() if link.is_symlink() else Path(os.readlink(str(link))))
            log("  already linked %s -> %s" % (link, current))
        except (OSError, ValueError):
            log("  already present %s" % link)
        return

    link.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        log("  would link %s -> %s" % (link, target))
        return
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        log("  linked %s -> %s" % (link, target))
    else:
        log("  FAILED %s: %s" % (link, (result.stderr or result.stdout).strip()))


def link_skill(dry_run: bool) -> None:
    target = STORE / SKILL
    log("skill links -> %s" % target)
    for harness in PLAIN_DIR_HARNESSES:
        make_junction(HOME / harness / "skills" / SKILL, target, dry_run)
    # The MiniMax app's curated skills dir is recreated by the app; the link is
    # best effort and is re-created by this script after an app reset.
    make_junction(HOME / ".minimax" / "skills" / SKILL, target, dry_run)


# ----------------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report what would change")
    args = ap.parse_args()
    dry_run = args.dry_run

    hook_script = STORE / SKILL / "scripts" / "hook.py"
    if not hook_script.exists():
        log("hook script not found: %s" % hook_script)
        log("run install.ps1 in the skills repo first, or point the harness at the repo path")
        return 1

    log("hook wiring (command: %s)" % HOOK_CMD)
    wire_claude_like(HOME / ".claude" / "settings.json", dry_run)
    wire_claude_like(HOME / ".agents" / "config" / "settings.json", dry_run)
    wire_codex(HOME / ".codex" / "hooks.json", dry_run)
    wire_cursor(HOME / ".cursor" / "hooks.json", dry_run)
    wire_command_code(HOME / ".commandcode" / "settings.json", dry_run)

    log("")
    link_skill(dry_run)

    log("")
    log("done%s" % (" (dry run)" if dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
