#!/usr/bin/env python3
"""Self-check for the aswath-autocompact skill.

Runs against a throwaway HOME, never the real settings file.

    python selftest.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTOCOMPACT = HERE / "autocompact.py"
RULES_HOOK = HERE / "compaction_rules.py"

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"ok   {name}")
    else:
        failed += 1
        print(f"FAIL {name} {detail}")


def run(args, home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(AUTOCOMPACT), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        settings_file = home / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(
            json.dumps(
                {
                    "model": "MiniMax-M3.1-Flash[1m]",
                    "env": {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "204800"},
                    "modelSettings": {"MiniMax-M3.1-Flash[1m]": {"effortLevel": "low"}},
                    "hooks": {"PreCompact": [{"hooks": [{"type": "command", "command": "other"}]}]},
                    "unrelated": {"keep": True},
                }
            ),
            encoding="utf-8",
        )

        result = run(["apply", "medium"], home)
        check("apply medium exits 0", result.returncode == 0, result.stderr)
        settings = read(settings_file)
        check("window written", settings.get("autoCompactWindow") == 300000, settings.get("autoCompactWindow"))
        check(
            "per-model window written",
            settings["modelSettings"]["MiniMax-M3.1-Flash[1m]"].get("autoCompactWindow") == 300000,
        )
        check("effort level preserved", settings["modelSettings"]["MiniMax-M3.1-Flash[1m]"].get("effortLevel") == "low")
        check("unrelated keys preserved", settings.get("unrelated") == {"keep": True})
        check("env block untouched", "CLAUDE_CODE_AUTO_COMPACT_WINDOW" in settings["env"])
        check("warning about env override printed", "takes precedence" in result.stdout or "outranks" in result.stdout, result.stdout)

        commands = [
            h["command"]
            for group in settings["hooks"]["PreCompact"]
            for h in group.get("hooks", [])
        ]
        check("rules hook registered", any("compaction_rules.py" in c for c in commands), commands)
        check("other hook preserved", any(c == "other" for c in commands), commands)

        state_file = home / ".claude" / "autocompact-template.json"
        check("state file written", state_file.exists())
        state = read(state_file)
        check("state template is medium", state.get("template") == "medium")
        check("state carries rules", bool(state.get("rules")))

        hook = subprocess.run(
            [sys.executable, str(RULES_HOOK)],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(home), "USERPROFILE": str(home)},
        )
        check("rules hook exits 0", hook.returncode == 0, hook.stderr)
        check("rules hook prints the template rules", "MEDIUM task" in hook.stdout, hook.stdout)

        again = run(["apply", "hard"], home)
        check("re-apply exits 0", again.returncode == 0, again.stderr)
        settings = read(settings_file)
        check("window switched to hard", settings.get("autoCompactWindow") == 400000)
        commands = [
            h["command"]
            for group in settings["hooks"]["PreCompact"]
            for h in group.get("hooks", [])
        ]
        check("rules hook not duplicated", sum(1 for c in commands if "compaction_rules.py" in c) == 1, commands)

        status = run(["status"], home)
        check("status exits 0", status.returncode == 0, status.stderr)
        check("status lists the active template", "hard" in status.stdout)

        uninstall = run(["uninstall"], home)
        check("uninstall exits 0", uninstall.returncode == 0, uninstall.stderr)
        settings = read(settings_file)
        check("window removed", "autoCompactWindow" not in settings)
        commands = [
            h["command"]
            for group in settings.get("hooks", {}).get("PreCompact", [])
            for h in group.get("hooks", [])
        ]
        check("rules hook removed", not any("compaction_rules.py" in c for c in commands), commands)
        check("other hook still there after uninstall", any(c == "other" for c in commands), commands)

        # rules hook with no state file must be silent, not an error
        no_state = subprocess.run(
            [sys.executable, str(RULES_HOOK)],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(tmp + "-empty"), "USERPROFILE": str(tmp + "-empty")},
        )
        check("rules hook silent without state", no_state.returncode == 0 and not no_state.stdout.strip())

    print(f"\npassed {passed}, failed {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
