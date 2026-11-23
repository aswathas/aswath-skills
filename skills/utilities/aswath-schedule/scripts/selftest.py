#!/usr/bin/env python3
"""Self-check for aswath-schedule.

The pure parts are checked against scratch files: the task XML, the Claude Code
task list, the MiniMax cron table. On Windows one live task is created, seen
and removed, because "the task appears in schtasks /query and is gone after
remove" is the whole point of the skill. On other systems that case is skipped.
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEDULE = HERE / "schedule.py"

spec = importlib.util.spec_from_file_location("aswath_schedule", SCHEDULE)
schedule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schedule)

results = []


def case(name):
    def wrap(fn):
        results.append((name, fn))
        return fn
    return wrap


def build_cron_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute("create table local_runtime_v2_scheduler_jobs "
                "(scheduler_id text, schedule_json text, run_count integer, "
                "state text, next_run_at_ms integer)")
    con.execute("create table local_runtime_v2_cron_definitions "
                "(cron_id text, name text, agent_name text, deleted_at_ms integer)")
    con.execute("create table local_runtime_v2_cron_runs "
                "(run_id text, cron_id text, scheduler_trigger_id text, status text)")
    con.executemany(
        "insert into local_runtime_v2_scheduler_jobs values (?,?,?,?,?)",
        [
            ("one", json.dumps({"kind": "once", "runAtMs": 1}), 1, "completed", None),
            ("every", json.dumps({"kind": "cron", "expr": "0 9 * * *"}), 4, "scheduled", 99),
        ],
    )
    con.executemany(
        "insert into local_runtime_v2_cron_definitions values (?,?,?,?)",
        [("one", "Task follow-up (one)", "mavis", 1234),
         ("every", "the nightly check", "mavis", None)],
    )
    con.executemany(
        "insert into local_runtime_v2_cron_runs values (?,?,?,?)",
        [("r1", "one", "one:0:1", "delivered"), ("r2", "every", "every:0:1", "delivered")],
    )
    con.commit()
    con.close()


@case("a task is named Aswath\\<name>")
def t_name(_root: Path) -> None:
    assert schedule.task_name("improve") == "Aswath\\improve"


@case("the task carries the run-as-soon-as-possible flag")
def t_flag(_root: Path) -> None:
    xml = schedule.task_xml("improve", "echo hello", at="09:30")
    assert "<StartWhenAvailable>true</StartWhenAvailable>" in xml, xml
    assert "\\Aswath\\improve" in xml, xml


@case("the task runs through the hidden runner, not a console")
def t_command(_root: Path) -> None:
    xml = schedule.task_xml("probe", "echo a & b", at="09:30")
    cmd = xml.split("<Command>")[1].split("</Command>")[0]
    args = xml.split("<Arguments>")[1].split("</Arguments>")[0]
    assert "wscript.exe" in cmd, cmd
    assert "run-hidden.vbs" in args, args
    assert "cmd" in args, args


@case("the command is kept in a file so its quotes survive")
def t_command_file(root: Path) -> None:
    old = schedule.CMD_DIR
    schedule.CMD_DIR = root / "cmds"
    try:
        path = schedule.command_file("probe")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('echo "a & b"\n', encoding="utf-8")
        assert path.read_text(encoding="utf-8").strip() == 'echo "a & b"'
    finally:
        schedule.CMD_DIR = old


@case("the hidden runner is installed where the tasks point at it")
def t_runner(_root: Path) -> None:
    assert schedule.RUNNER_SRC.is_file(), schedule.RUNNER_SRC
    schedule.install_runner()
    assert schedule.RUNNER.is_file(), schedule.RUNNER
    assert schedule.RUNNER.read_bytes() == schedule.RUNNER_SRC.read_bytes()


@case("the daily trigger starts in the future")
def t_boundary(_root: Path) -> None:
    xml = schedule.task_xml("probe", "echo hi", at="23:59")
    start = xml.split("<StartBoundary>")[1].split("</StartBoundary>")[0]
    import datetime
    when = datetime.datetime.fromisoformat(start)
    assert when > datetime.datetime.now(), start


@case("the Claude Code task list is read as it is on disk")
def t_claude(root: Path) -> None:
    path = root / "scheduled_tasks.json"
    path.write_text(json.dumps({"tasks": [{"name": "the nudge", "cron": "0 9 * * *"}]}),
                    encoding="utf-8")
    tasks = schedule.claude_tasks(path)
    assert len(tasks) == 1, tasks
    assert tasks[0]["name"] == "the nudge", tasks
    assert schedule.claude_tasks(root / "missing.json") == []


@case("the MiniMax cron table marks the finished one-shots dead")
def t_crons(root: Path) -> None:
    db = root / "runtime.sqlite"
    build_cron_db(db)
    crons = schedule.minimax_crons(db)
    assert len(crons) == 2, crons
    dead = [c for c in crons if c["dead"]]
    assert len(dead) == 1, crons
    assert dead[0]["id"] == "one", dead
    assert dead[0]["name"] == "Task follow-up (one)", dead
    assert dead[0]["agent"] == "mavis", dead
    alive = [c for c in crons if not c["dead"]][0]
    assert alive["id"] == "every", alive
    assert alive["last_status"] == "delivered", alive


@case("a task appears in schtasks /query and is gone after remove")
def t_live(_root: Path) -> None:
    if os.name != "nt" or not shutil.which("schtasks"):
        print("   (skipped: no Task Scheduler here)")
        return
    name = "Aswath\\selftest-probe"
    subprocess.run(["schtasks", "/delete", "/tn", name, "/f"],
                   capture_output=True, text=True)
    out = subprocess.run([sys.executable, str(SCHEDULE), "add", "--name", "selftest-probe",
                          "--command", "echo probe", "--at", "23:59"],
                         capture_output=True, text=True)
    assert out.returncode == 0, (out.stdout, out.stderr)
    listed = subprocess.run(["schtasks", "/query", "/fo", "CSV", "/v"],
                            capture_output=True, text=True).stdout
    assert name.lower() in listed.lower(), listed[:500]
    out = subprocess.run([sys.executable, str(SCHEDULE), "remove", "--name", "selftest-probe"],
                         capture_output=True, text=True)
    assert out.returncode == 0, (out.stdout, out.stderr)
    listed = subprocess.run(["schtasks", "/query", "/fo", "CSV", "/v"],
                            capture_output=True, text=True).stdout
    assert name.lower() not in listed.lower(), listed[:500]


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="schedule-selftest-"))
    failed = 0
    try:
        for index, (name, fn) in enumerate(results):
            case_root = root / f"case{index}"
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
