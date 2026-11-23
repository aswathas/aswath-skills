#!/usr/bin/env python3
"""aswath-schedule: the machine-level clock for the estate.

    python schedule.py add --name NAME --command CMD [--at HH:MM | --every N]
    python schedule.py remove --name NAME
    python schedule.py list

Tasks are named `Aswath\\<name>` and are created with the "run as soon as
possible after a missed start" flag, so a job whose slot came while the PC was
asleep runs late instead of never.

`list` shows the three schedulers in one place: the Windows tasks, the Claude
Code task list, and the MiniMax cron table with its dead one-shots.

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

HOME = Path.home()
PREFIX = "Aswath\\"
CMD = Path(os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"))
SCHEDULER_DB = HOME / ".minimax/v2/sqlite/runtime-state.sqlite"
CLAUDE_TASKS = HOME / ".claude/scheduled_tasks.json"

# A task that runs cmd.exe in the user's session opens a console window on the
# desktop. The command is therefore handed to wscript.exe, which runs it with
# no window at all. The command itself lives in a file so that quotes in the
# command survive the trip through the task's Arguments field.
WSCRIPT = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32/wscript.exe"
RUNNER_SRC = Path(__file__).resolve().parent / "run-hidden.vbs"
RUNNER = HOME / ".claude/tools/run-hidden.vbs"
CMD_DIR = HOME / ".claude/scheduled-tasks"


# ---------------------------------------------------------------- the task


def task_name(name: str) -> str:
    return PREFIX + name


def whoami() -> str:
    out = subprocess.run(["whoami"], capture_output=True, text=True)
    return out.stdout.strip() or os.environ.get("USERNAME", "SYSTEM")


def next_boundary(at: str = "", every: int = 0) -> str:
    """The ISO time the task's schedule starts from."""
    now = datetime.datetime.now().replace(second=0, microsecond=0)
    if every:
        return now.isoformat()
    hour, minute = (int(x) for x in at.split(":"))
    start = now.replace(hour=hour, minute=minute)
    if start <= now:
        start += datetime.timedelta(days=1)
    return start.isoformat()


def trigger_xml(at: str, every: int) -> str:
    if every:
        return (
            "  <Triggers>\n"
            "    <TimeTrigger>\n"
            f"      <StartBoundary>{next_boundary(every=every)}</StartBoundary>\n"
            "      <Enabled>true</Enabled>\n"
            f"      <Repetition><Interval>PT{every}M</Interval><StopAtDurationEnd>false"
            "</StopAtDurationEnd></Repetition>\n"
            "    </TimeTrigger>\n"
            "  </Triggers>\n"
        )
    return (
        "  <Triggers>\n"
        "    <CalendarTrigger>\n"
        f"      <StartBoundary>{next_boundary(at=at)}</StartBoundary>\n"
        "      <Enabled>true</Enabled>\n"
        "      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>\n"
        "    </CalendarTrigger>\n"
        "  </Triggers>\n"
    )


def command_file(name: str) -> Path:
    """Where the command for one task is kept."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return CMD_DIR / f"{safe}.cmd"


def install_runner() -> None:
    """Put the hidden runner where the tasks point at it."""
    RUNNER.parent.mkdir(parents=True, exist_ok=True)
    if RUNNER.is_file() and RUNNER.read_bytes() == RUNNER_SRC.read_bytes():
        return
    RUNNER.write_bytes(RUNNER_SRC.read_bytes())


def task_xml(name: str, command: str, at: str = "", every: int = 0) -> str:
    """The task definition. StartWhenAvailable is the point of the whole thing."""
    cmd_file = command_file(name)
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        "  <RegistrationInfo>\n"
        f"    <Description>{escape(name)}</Description>\n"
        f"    <URI>\\{PREFIX}{escape(name)}</URI>\n"
        "  </RegistrationInfo>\n"
        + trigger_xml(at, every)
        + "  <Principals>\n"
        '    <Principal id="Author">\n'
        f"      <UserId>{escape(whoami())}</UserId>\n"
        "      <LogonType>InteractiveToken</LogonType>\n"
        "      <RunLevel>LeastPrivilege</RunLevel>\n"
        "    </Principal>\n"
        "  </Principals>\n"
        "  <Settings>\n"
        "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>\n"
        "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>\n"
        "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>\n"
        "    <AllowHardTerminate>true</AllowHardTerminate>\n"
        "    <StartWhenAvailable>true</StartWhenAvailable>\n"
        "    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>\n"
        "    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd>"
        "<RestartOnIdle>false</RestartOnIdle></IdleSettings>\n"
        "    <Enabled>true</Enabled>\n"
        "    <Hidden>false</Hidden>\n"
        "    <WakeToRun>false</WakeToRun>\n"
        "    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>\n"
        "    <Priority>7</Priority>\n"
        "  </Settings>\n"
        "  <Actions Context=\"Author\">\n"
        "    <Exec>\n"
        f"      <Command>{escape(str(WSCRIPT))}</Command>\n"
        f"      <Arguments>//nologo \"{escape(str(RUNNER))}\" \"{escape(str(cmd_file))}\"</Arguments>\n"
        f"      <WorkingDirectory>{escape(str(HOME))}</WorkingDirectory>\n"
        "    </Exec>\n"
        "  </Actions>\n"
        "</Task>\n"
    )


def schtasks(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["schtasks", *args], capture_output=True, text=True)


# ---------------------------------------------------------------- the three schedulers


def windows_tasks() -> list:
    """Every task under the Aswath\\ folder, with its next run and its command."""
    out = subprocess.run(
        ["schtasks", "/query", "/fo", "CSV", "/v"], capture_output=True, text=True
    )
    if out.returncode != 0:
        return []
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(out.stdout)))
    tasks = []
    for row in rows:
        name = (row.get("TaskName") or "").strip()
        if not name.lstrip("\\").startswith(PREFIX):
            continue
        tasks.append({
            "name": name,
            "status": (row.get("Status") or "").strip(),
            "next_run": (row.get("Next Run Time") or "").strip(),
            "command": (row.get("Task To Run") or "").strip(),
        })
    return tasks


def claude_tasks(path: Path = CLAUDE_TASKS) -> list:
    """The Claude Code task list, read as it is on disk."""
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tasks = data.get("tasks", [])
    return tasks if isinstance(tasks, list) else []


def minimax_crons(db: Path = SCHEDULER_DB) -> list:
    """The MiniMax cron table, with each job marked alive or dead."""
    if not db.is_file():
        return []
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        jobs = con.execute(
            "select scheduler_id, schedule_json, run_count, state, next_run_at_ms "
            "from local_runtime_v2_scheduler_jobs"
        ).fetchall()
        names = {
            row[0]: row[1:]
            for row in con.execute(
                "select cron_id, name, agent_name, deleted_at_ms "
                "from local_runtime_v2_cron_definitions"
            )
        }
        # The run names the scheduler job it came from as "<scheduler_id>:0:1".
        runs = {}
        for cron_id, trigger_id, status in con.execute(
            "select cron_id, scheduler_trigger_id, status from local_runtime_v2_cron_runs"
        ):
            runs[trigger_id.split(":")[0]] = (cron_id, status)
    finally:
        con.close()
    out = []
    for scheduler_id, schedule_json, run_count, state, next_run_ms in jobs:
        try:
            kind = (json.loads(schedule_json or "{}")).get("kind", "")
        except json.JSONDecodeError:
            kind = ""
        run = runs.get(scheduler_id)
        definition = names.get(run[0]) if run else None
        dead = state == "completed" and next_run_ms is None
        out.append({
            "id": scheduler_id,
            "name": definition[0] if definition else "",
            "agent": definition[1] if definition else "",
            "deleted": bool(definition and definition[2]),
            "kind": kind,
            "state": state,
            "runs": run_count,
            "last_status": run[1] if run else "",
            "dead": dead,
        })
    return out


# ---------------------------------------------------------------- commands


def cmd_add(args) -> int:
    if bool(args.at) == bool(args.every):
        print("schedule: give exactly one of --at HH:MM or --every MINUTES.", file=sys.stderr)
        return 1
    name = task_name(args.name)
    cmd_file = command_file(args.name)
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    cmd_file.write_text(args.command.strip() + "\n", encoding="utf-8")
    install_runner()
    xml = task_xml(args.name, args.command, args.at, args.every)
    handle, path = tempfile.mkstemp(prefix="aswath-task-", suffix=".xml")
    with os.fdopen(handle, "wb") as fh:
        fh.write(xml.encode("utf-16"))
    try:
        out = schtasks("/create", "/tn", name, "/xml", path, "/f")
    finally:
        Path(path).unlink(missing_ok=True)
    if out.returncode != 0:
        print(f"schedule: the task was not created: {out.stderr.strip() or out.stdout.strip()}",
              file=sys.stderr)
        return 1
    print(f"schedule: {name} created. It runs late rather than not at all.")
    print(f"  {args.command}")
    return 0


def cmd_remove(args) -> int:
    name = task_name(args.name)
    out = schtasks("/delete", "/tn", name, "/f")
    if out.returncode != 0:
        print(f"schedule: {name} was not removed: {out.stderr.strip() or out.stdout.strip()}",
              file=sys.stderr)
        return 1
    print(f"schedule: {name} removed.")
    command_file(args.name).unlink(missing_ok=True)
    return 0


def cmd_list(_args) -> int:
    tasks = windows_tasks()
    print(f"windows tasks ({len(tasks)}):")
    if not tasks:
        print("  (none)")
    for task in tasks:
        print(f"  {task['name']}  {task['status']}  next {task['next_run']}")
        print(f"    {task['command']}")

    claude = claude_tasks()
    print(f"\nclaude code task list ({len(claude)}):")
    if not claude:
        print("  (none)")
    for task in claude:
        if isinstance(task, dict):
            print(f"  {task.get('name', task.get('id', '?'))}  {task.get('cron', task.get('schedule', ''))}")
        else:
            print(f"  {task}")

    crons = minimax_crons()
    dead = [c for c in crons if c["dead"]]
    print(f"\nminimax cron table ({len(crons)}, {len(dead)} dead):")
    if not crons:
        print("  (none)")
    for cron in crons:
        mark = "dead" if cron["dead"] else "alive"
        print(f"  {cron['name'] or cron['id']}  agent {cron['agent']}  "
              f"{cron['kind']}  {cron['state']}  last {cron['last_status']}  {mark}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="schedule.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="create a task")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--command", required=True)
    p_add.add_argument("--at", default="", help="HH:MM, every day")
    p_add.add_argument("--every", type=int, default=0, help="minutes")
    p_add.set_defaults(func=cmd_add)

    p_rm = sub.add_parser("remove", help="delete a task")
    p_rm.add_argument("--name", required=True)
    p_rm.set_defaults(func=cmd_remove)

    p_ls = sub.add_parser("list", help="the three schedulers in one place")
    p_ls.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
