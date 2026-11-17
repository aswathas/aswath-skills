---
name: aswath-schedule
description: Use when work should run without a human - the learning loop, the catalogue check, a job that must run late rather than never, or when the machine's scheduled jobs need seeing. Creates and removes Windows Task Scheduler jobs named Aswath\<name>, reports the Claude Code task list and the MiniMax cron table in one place, and marks the dead one-shots.
---

# aswath-schedule

The machine's clock.

The failure this exists to prevent: a job that has to run daily is run by hand, so it runs on the
day somebody remembers. The other failure: a job that fired while the PC was asleep never ran at
all, and nobody noticed for a week.

Both are closed the same way. The job goes into Windows Task Scheduler with the "run as soon as
possible after a missed start" flag, so a missed slot runs late instead of never.

## The jobs

Windows Task Scheduler. The tasks are named `Aswath\<name>`, so they are one folder in
`schtasks /query` and never mixed with the rest of the machine's jobs.

The harness schedulers are read, not used:

- **Claude Code's task list** (`~/.claude/scheduled_tasks.json`) — a job there only fires while
  that harness is running and idle on that PC. It is the right tool for an in-session nudge.
- **MiniMax Code's cron table** (`local_runtime_v2_scheduler_jobs` in the runtime database) — a
  cron there is a prompt aimed at a session, not a script with an exit code, and it lives in one
  harness's private database. Its current rows are nine finished one-shot pairing prompts: all
  dead.

`list` prints all three, so the machine's three schedulers are seen in one place instead of
three.

## The commands

```bash
S=skills/utilities/aswath-schedule/scripts/schedule.py

python $S add --name improve --command "<the command>" --at 09:30   # every day at 09:30
python $S add --name poll --command "<the command>" --every 15      # every 15 minutes
python $S remove --name improve
python $S list
```

`add` takes exactly one of `--at HH:MM` (every day) or `--every MINUTES`. The task is written
as UTF-16 task XML and created with `schtasks /create /xml`, because the plain command form
cannot set the missed-start flag.

## The two estate jobs

The runtime design gives this skill two jobs to schedule:

| Task | Command | What it does |
|---|---|---|
| `Aswath\improve` | `improve.py --run` | the learning loop: propose, PR, gate, merge |
| `Aswath\catalog-verify` | `catalog.py verify` | this machine's skill map against the remote's |

Both re-read their state and re-derive, so a late run converges instead of double-applying.

A task runs as the logged-on user. A job that must run with the PC locked or unlocked needs an
elevated shell and a different principal.

## When to run it

- when a job has to run daily and nobody is there to run it
- when a job keeps missing its slot because the PC is asleep
- when the machine's scheduled jobs need seeing in one place
- when a harness cron has to be found, dated or cleaned up

## Self-check

```bash
python skills/utilities/aswath-schedule/scripts/selftest.py
```

Checks the task name, the missed-start flag, the escaped command and the trigger boundary against
scratch files; reads a scratch Claude Code task list and a scratch MiniMax cron table; and on
Windows creates one live task, sees it in `schtasks /query` and removes it again.
