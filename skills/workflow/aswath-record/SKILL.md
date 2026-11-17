---
name: aswath-record
description: Use when something ran and what it produced has to be written down — a build, a delivery, a failure — or when a secret may have reached a commit. Keeps the run and artifact ledger in the private store, reports the metrics, and checks that no secret file is tracked by git.
---

# aswath-record

What ran, what it produced, where the secrets are.

The failure this exists to prevent: work that happened, produced files, was delivered, and then
left no trace — so the next session cannot tell which artifact is current, cannot tell what
failed, and cannot tell that a secret was committed.

## The ledger

`~/.agents/ledger/<project>.jsonl` — one JSON object per line, in the private store, tracked in
git so both PCs carry it. The code is public; the data is private.

```json
{"id": "a1b2", "ts": "2026-11-17T22:00:00Z", "project": "demo", "kind": "run", "job": "build", "outcome": "ok"}
{"id": "a2c3", "ts": "2026-11-17T22:05:00Z", "project": "demo", "kind": "artifact", "path": "/out/report.pdf", "sha256": "…", "supersedes": "a1b2"}
{"id": "d4e5", "ts": "2026-11-17T22:06:00Z", "project": "demo", "kind": "delivery", "artifact": "a2c3", "channel": "whatsapp", "message_id": "M1"}
```

**Append-only.** A mistake is corrected by appending a new record, never by editing a line. Git
holds the history of what was believed when. A record that could not be appended is written to
`~/.agents/state/ledger-failed.ndjson` and flushed into the ledger on the next successful
append, so a failed write is never silently lost.

## Commands

```bash
L=skills/workflow/aswath-record/scripts/ledger.py

python $L add --project X --kind run --job Y --outcome ok
python $L add --project X --kind artifact --path P --sha256 H --supersedes OLD_ID
python $L superseded --project X      # what the ledger marks superseded, and what is current
python $L deliver --project X --id ARTIFACT --channel whatsapp --message-id M
python $L import --since 2026-11-01   # harvest the runs MiniMax Code already recorded
python $L stats --project X
python $L doctor secrets
```

`add` takes `--kind run|artifact|delivery|note`, and the fields that kind needs: `--job`,
`--outcome`, `--path`, `--sha256`, `--supersedes` (repeatable), `--channel`, `--message-id`,
`--artifact`, `--id`.

## The metrics

`stats` counts what the ledger holds: runs, failures, artifacts, superseded, delivered, and the
delivery completion rate — delivered over produced. It is the number that says whether the work
reached a person or only reached a disk.

## The import

Runs that happened inside MiniMax Code are already recorded by that runtime, in
`~/.minimax/v2/sqlite/runtime-state.sqlite`. `import` reads that database **read-only** and
appends one run line per task, skipping ids already in the ledger, so a second import adds
nothing. The command fails if the database's modification time changed.

## The secrets convention

New project secrets live in `~/.agents/secrets/<project>.env`, one file per project, gitignored.
They are not moved from the old per-tool `.env` files (`~/.claude-mem/.env`,
`~/.claude/channels/telegram/.env`); the doctor reports them as outside the convention so the
gap is visible without breaking the tools that read them.

## The doctor

`doctor secrets` prints variable **names** and never a value. It fails when a file that holds
credentials is tracked by git, and it reports the secret-looking assignments it finds in tracked
files with the value redacted. A template — `.env.example`, `env.sample` — is not a secret and
is left alone.

## When to run it

- after a build produced something, and after it was delivered
- when a job failed and the failure should be findable later
- before a push, to check that no secret reached a commit
- when someone asks how much of the work actually got delivered

## Self-check

```bash
python skills/workflow/aswath-record/scripts/selftest.py
```

Runs against a scratch directory: a run appended and counted, the delivery completion rate, the
superseded list, the doctor's redaction, and the tracked-versus-ignored secret file. It never
touches the real ledger.
