#!/usr/bin/env python3
"""Self-check for aswath-token-guard. Runs against a scratch tree; touches nothing real.

The two hook scripts are exercised the way the harnesses run them: as a
subprocess, with the scratch directory pointed at by an environment variable.
The MiniMax hook reads a SQLite runtime state under MINIMAX_DATA_DIR; the
Claude Code hook reads a transcript under the user's home, so HOME and
USERPROFILE are pointed at the scratch tree for its run.

The installer is imported and called directly, because patch_hooks is the
function the uninstall path depends on.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PLUGIN = SKILL / "plugin"
MINIMAX_HOOK = PLUGIN / "scripts" / "token_guard_hook.py"
CLAUDE_HOOK = PLUGIN / "scripts" / "claude-context-hook.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


install = load("tg_install", PLUGIN / "install.py")

results = []


def case(name):
    def wrap(fn):
        results.append((name, fn))
        return fn

    return wrap


# ---------------------------------------------------------------- the installer


def hook_counts(data):
    """(event, matcher) -> number of groups."""
    out = {}
    for event, groups in (data.get("hooks") or {}).items():
        for group in groups:
            key = (event, group.get("matcher"))
            out[key] = out.get(key, 0) + 1
    return out


def run_install(path, root, install_it=True):
    created, added = install.patch_hooks(str(path), str(root), install_it, False)
    return json.loads(Path(path).read_text(encoding="utf-8")), added


@case("a fresh hooks file gets exactly one group per event")
def t_fresh(root: Path) -> None:
    path = root / "hooks.json"
    data, added = run_install(path, root)
    counts = hook_counts(data)
    assert counts.get(("SessionStart", None)) == 1, counts
    assert counts.get(("UserPromptSubmit", "*")) == 1, counts
    assert counts.get(("PreToolUse", "read")) == 1, counts


@case("installing twice leaves one group per event")
def t_idempotent(root: Path) -> None:
    path = root / "hooks.json"
    run_install(path, root)
    data, _ = run_install(path, root)
    counts = hook_counts(data)
    assert counts.get(("SessionStart", None)) == 1, counts
    assert counts.get(("UserPromptSubmit", "*")) == 1, counts
    assert counts.get(("PreToolUse", "read")) == 1, counts


@case("a hook the installer does not own survives both runs")
def t_foreign_kept(root: Path) -> None:
    path = root / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "enabled": True,
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": None,
                            "hooks": [{"type": "command", "name": "Someone else", "command": "echo hi"}],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "bash",
                            "hooks": [{"type": "command", "name": "Other", "command": "echo other"}],
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    run_install(path, root)
    data, _ = run_install(path, root)
    names = [
        h.get("name")
        for groups in data["hooks"].values()
        for group in groups
        for h in group.get("hooks", [])
    ]
    assert "Someone else" in names, names
    assert "Other" in names, names
    assert data.get("enabled") is True, data
    assert hook_counts(data).get(("PreToolUse", "bash")) == 1, data["hooks"]


@case("uninstall removes only the token guard groups")
def t_uninstall(root: Path) -> None:
    path = root / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [{"type": "command", "name": "Someone else", "command": "echo hi"}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    run_install(path, root)
    data, _ = run_install(path, root, install_it=False)
    names = [
        h.get("name")
        for groups in data["hooks"].values()
        for group in groups
        for h in group.get("hooks", [])
    ]
    assert "Someone else" in names, names
    assert "Token guard" not in " ".join(str(n) for n in names), names


# ------------------------------------------------------- the MiniMax Code hook


def minimax_home(root: Path, rows, created_at_ms=None):
    """A scratch MINIMAX_DATA_DIR with a runtime state DB holding `rows`.

    Every row lands under one session id, so the hook's session filter has
    something to match.
    """
    home = root / "minimax"
    (home / "v2" / "sqlite").mkdir(parents=True, exist_ok=True)
    db = home / "v2" / "sqlite" / "runtime-state.sqlite"
    con = sqlite3.connect(str(db))
    con.execute(
        "create table local_runtime_message_rows"
        " (session_id text, created_at_ms integer, data_json text)"
    )
    con.execute(
        "create table local_runtime_token_usage"
        " (session_id text, ts integer, input_tokens integer,"
        " cache_read_tokens integer, cache_write_tokens integer)"
    )
    stamp = created_at_ms if created_at_ms is not None else int(time.time() * 1000)
    for row in rows:
        con.execute(
            "insert into local_runtime_message_rows values (?,?,?)",
            (row.get("session_id", "s"), stamp, json.dumps(row)),
        )
    con.commit()
    con.close()
    return home


def run_minimax(home: Path, event: str, payload: dict) -> str:
    payload_file = home / "payload.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")
    env = dict(os.environ)
    env["MINIMAX_DATA_DIR"] = str(home)
    proc = subprocess.run(
        [sys.executable, str(MINIMAX_HOOK), "--event", event, "--payload-file", str(payload_file)],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout


def usage_row(tokens, session_id="s", tool_use=None):
    row = {"session_id": session_id, "context_usage": {"usedTokens": tokens}}
    if tool_use:
        row["tool_calls"] = [
            {"tool_name": "read", "tool_call_args": {"path": tool_use}}
        ]
    return row


@case("SessionStart prints the orientation with the live context number")
def t_orientation(root: Path) -> None:
    home = minimax_home(root, [usage_row(250000, "s1")])
    out = run_minimax(home, "SessionStart", {"session_id": "s1"})
    assert "Context guard is on." in out, out
    assert "250,000" in out, out


@case("UserPromptSubmit stays silent below the threshold")
def t_prompt_quiet(root: Path) -> None:
    home = minimax_home(root, [usage_row(1000, "s2")])
    out = run_minimax(home, "UserPromptSubmit", {"session_id": "s2"})
    assert out.strip() == "", out


@case("UserPromptSubmit speaks once over the threshold and then waits for a step")
def t_prompt_step(root: Path) -> None:
    home = minimax_home(root, [usage_row(250000, "s3")])
    first = run_minimax(home, "UserPromptSubmit", {"session_id": "s3"})
    assert "Context guard is on." in first, first
    second = run_minimax(home, "UserPromptSubmit", {"session_id": "s3"})
    assert second.strip() == "", second
    con = sqlite3.connect(str(home / "v2" / "sqlite" / "runtime-state.sqlite"))
    con.execute(
        "update local_runtime_message_rows set data_json=?",
        (json.dumps(usage_row(300000)),),
    )
    con.commit()
    con.close()
    third = run_minimax(home, "UserPromptSubmit", {"session_id": "s3"})
    assert "300,000" in third, third


@case("a repeat read of an unchanged file is denied")
def t_repeat_denied(root: Path) -> None:
    target = root / "notes.md"
    target.write_text("hello\n", encoding="utf-8")
    future = int((time.time() + 60) * 1000)
    home = minimax_home(root, [usage_row(1000, "s4", str(target))], created_at_ms=future)
    out = run_minimax(
        home,
        "PreToolUse",
        {
            "session_id": "s4",
            "tool_name": "read",
            "tool_input": {"file_path": str(target)},
        },
    )
    decision = json.loads(out)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny", decision
    assert str(target) in decision["permissionDecisionReason"], decision


@case("a first read of a file is allowed")
def t_first_read_allowed(root: Path) -> None:
    target = root / "fresh.md"
    target.write_text("hello\n", encoding="utf-8")
    home = minimax_home(root, [usage_row(1000, "s5")])
    out = run_minimax(
        home,
        "PreToolUse",
        {
            "session_id": "s5",
            "tool_name": "read",
            "tool_input": {"file_path": str(target)},
        },
    )
    assert out.strip() == "", out


@case("a read of a file changed since the session began is allowed")
def t_changed_allowed(root: Path) -> None:
    target = root / "moved.md"
    target.write_text("hello\n", encoding="utf-8")
    home = minimax_home(root, [usage_row(1000, "s6", str(target))], created_at_ms=1)
    out = run_minimax(
        home,
        "PreToolUse",
        {
            "session_id": "s6",
            "tool_name": "read",
            "tool_input": {"file_path": str(target)},
        },
    )
    assert out.strip() == "", out


@case("a tool that is not a read is never denied")
def t_other_tool(root: Path) -> None:
    home = minimax_home(root, [usage_row(1000, "s7")])
    out = run_minimax(
        home,
        "PreToolUse",
        {
            "session_id": "s7",
            "tool_name": "bash",
            "tool_input": {"command": "ls"},
        },
    )
    assert out.strip() == "", out


# -------------------------------------------------------- the Claude Code hook


def claude_home(root: Path, rows):
    """A scratch HOME with a Claude Code transcript holding `rows`."""
    home = root / "home"
    project = home / ".claude" / "projects" / "scratch"
    project.mkdir(parents=True, exist_ok=True)
    with (project / "s.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    return home


def run_claude(home: Path, payload: dict) -> str:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["CLAUDE_PROJECT_DIR"] = "scratch"
    env["TOKEN_GUARD_THRESHOLD"] = "32000"
    env["TOKEN_GUARD_STEP"] = "16000"
    proc = subprocess.run(
        [sys.executable, str(CLAUDE_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout


def claude_row(tokens):
    return {
        "type": "assistant",
        "timestamp": "2026-01-01T00:00:00Z",
        "message": {"usage": {"input_tokens": tokens}},
    }


@case("the Claude Code hook stays silent below the threshold")
def t_claude_quiet(root: Path) -> None:
    home = claude_home(root, [claude_row(1000)])
    out = run_claude(home, {"hook_event_name": "UserPromptSubmit", "session_id": "c1"})
    assert out.strip() == "", out


@case("the Claude Code hook speaks once the context passes the threshold")
def t_claude_speaks(root: Path) -> None:
    home = claude_home(root, [claude_row(50000)])
    out = run_claude(home, {"hook_event_name": "UserPromptSubmit", "session_id": "c2"})
    assert "Token guard" in out, out
    assert "50000" in out, out


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="token-guard-selftest-"))
    failed = 0
    try:
        for name, fn in results:
            case_root = root / name.replace(" ", "-")[:40]
            case_root.mkdir(parents=True, exist_ok=True)
            try:
                fn(case_root)
                print(f"ok   {name}")
            except AssertionError as exc:
                failed += 1
                print(f"FAIL {name}: {exc}")
        print(f"{len(results) - failed}/{len(results)} case(s) passed")
        return 1 if failed else 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
