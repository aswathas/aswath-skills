# Agent runtime — Spec

Status: Draft for user review
Date: 2026-11-17
Slug: `runtime` — the skills it mints are `aswath-catalog`, `aswath-record`, `aswath-improve`, `aswath-schedule`.

This spec lives in the public skills repo (`aswathas/aswath-skills`) because the skill code lives
there. The data it governs — the run ledger, the shared skill state, the skill map — lives in the
private store (`aswathas/agent-store`, `~/.agents`) and is git-tracked there.

## 1. Problem & user

Aswath runs one agent estate across several harnesses (Claude Code, MiniMax Code, Codex,
Command Code) on two Windows PCs. The skills, the state and the history of that estate are real,
but nothing in the system knows the truth about them. Eight gaps, each observed on this machine
today:

1. **Skill-location truth.** `~/.claude/skills/<name>` → `~/.agents/skills-active/<name>` →
   `~/.agents/skills/<name>` → sometimes a junction into the public repo, sometimes a real copy.
   The copy wins on the live path. Proof: the live `aswath-capability` `SKILL.md`
   (`~/.agents/skills/aswath-capability/SKILL.md`, 265 lines) is **ahead** of the published copy
   (`~/Projects/aswath-skills-wk/skills/orchestration/aswath-capability/SKILL.md`, 252 lines). The
   published catalogue describes a skill that is not the one running, and the published copy also
   has a duplicated `registry/ledger.json` row the live copy does not.
2. **Run/artifact ledger.** Nothing records that a build produced file X at path Y, that X
   superseded X′, or that X was delivered to WhatsApp. `aswath-delivery` cleans the chat by
   reading the chat — "a chat is a shelf, not a ledger" — so the chat is the only source of truth
   about what is current, and it is the one place that silently truncates. MiniMax Code does keep
   a run ledger of its own — `local_runtime_background_tasks` in
   `~/.minimax/v2/sqlite/runtime-state.sqlite` holds 3683 background-task records (3118 succeeded,
   505 failed, 30 canceled, 3 lost) — but it is harness-local, it records bash and subagent calls
   rather than artifacts, and no other harness can see it. Our ledger imports those records
   instead of duplicating them.
3. **Secrets home.** No convention and no check. `~/.claude-mem/.env` (438 bytes) exists because
   one tool needed one. Nothing stops a token from being pasted into a chat, a commit, or a
   skill. The store's `.gitignore` covers caches and vendored binaries, not secrets.
4. **Learning loop.** The skill-router plugin already observes skill use into
   `observations.ndjson` and scores skills in `ledger.json`. Nothing reads that back to change a
   skill. The loop records; it never learns.
5. **Shared skill state.** The router's state lives in `~/.minimax/local-runtime/skill-learning/`
   — a MiniMax-named path, not git-tracked. The second PC has a different state. The store's own
   `.gitignore` states the rule for claude-mem ("the database stays on the machine that wrote it"),
   but the router's derived scores are the part that *should* travel and do not.
6. **Scheduling.** Two schedulers exist and neither is used for recurring work.
   `~/.claude/scheduled_tasks.json` holds `{"tasks": []}`. MiniMax Code has a real scheduler in its
   runtime database — `local_runtime_v2_scheduler_jobs`, `local_runtime_v2_cron_definitions` and
   `local_runtime_v2_cron_runs` hold nine jobs — but all nine are `kind: once` "Task follow-up"
   prompts for one WhatsApp pairing check, and all nine are already flagged deleted. Windows Task
   Scheduler holds no tasks of ours. No recurring job has ever run on this machine.
7. **Two-PC coordination.** `~/.agents/sync.sh` pulls, pushes and reports, but there is no lease:
   both PCs can write shared state at the same moment and the merge is guesswork.
8. **Metrics.** Token spend is measurable (`aswath-token-evaluator`, `aswath-token-guard`,
   `aswath-token-ledger`, `agent-cost-report`), but no metric says how much of the work we
   actually shipped. The count of things produced versus things delivered is unmeasured.

The user gains: one place that says what exists, what ran, what failed, what is safe to leak,
what should change, and when the loop runs — and a machine that keeps those answers true on both
PCs without anyone remembering to update them by hand.

## 2. Scope — in / out

**In.** All eight gaps above, in one design, built as four skills plus edits to two existing
skills:

- `aswath-catalog` (new, utilities) — gap 1, gap 5, gap 7: the skill map, the drift detector, the
  shared state location, the two-PC lease and sync verification.
- `aswath-record` (new, workflow) — gap 2, gap 3, gap 8: the run/artifact ledger, the secrets home
  and its doctor, the ledger metrics.
- `aswath-improve` (new, workflow) — gap 4: the learning loop, ledger/observation → skill diff →
  pull request → gate → merge or stop, with an auto-revert on post-merge failure.
- `aswath-schedule` (new, utilities) — gap 6: scheduled jobs on Windows Task Scheduler.
- Edit `aswath-delivery` — read the ledger instead of reading the chat, to learn what is
  superseded and what is current.
- Edit `aswath-capability` — its registry state moves to the shared, tracked location.

**Out.**

- No agent framework, no new harness, no plugin runtime. This is a set of files and one scheduled
  task, not a platform.
- No adopting `swamp` (AGPLv3, a Deno-compiled automation runtime). It is not vendored, not
  wrapped, not executed. Nothing in this spec links against it.
- No rewrite of `aswath-commit-discipline`, `aswath-chronicle` or the token skills. They are read
  by the new skills; they are not changed.
- No multi-user or multi-tenant story. Two PCs, one owner.
- No secrets manager, no keyring, no vault. A convention and a check, nothing more.
- No CI on GitHub. The gate suite runs locally on the machine that proposes the change.
- The existing per-tool `.env` files (for example `~/.claude-mem/.env`, the Telegram channel
  `.env`) are **not** moved. New project secrets follow the new convention; the doctor reports the
  old ones.

## 3. Success criteria (measurable)

1. `aswath-catalog check` exits 0 on this machine after the build, and exits non-zero before it,
   naming at least the `aswath-capability` store copy and the four duplicated
   `skills-active` copies. Verified by running the script before and after the fix.
2. Every skill in `manifest.json` resolves to exactly one canonical path, and
   `~/.agents/skills-active/<name>` is a junction (never a real directory) for every active skill.
   Verified by `catalog check` and by listing the junctions.
3. `aswath-record add --project X --kind run --job Y --outcome fail` appends one JSON line to
   `~/.agents/ledger/X.jsonl`, and `aswath-record stats --project X` counts it. Verified by a
   scratch project and a line count.
4. `aswath-delivery` deletes from the chat exactly the artifact ids the ledger marks superseded,
   and no other message. Verified by a seeded ledger with one superseded and one current artifact
   and a stubbed channel client that records which ids were deleted.
5. `aswath-record doctor secrets` prints variable **names** only, and the value of a seeded fake
   token does not appear anywhere in stdout or stderr. Verified by asserting the value string is
   absent from the captured output.
6. `aswath-record doctor secrets` exits non-zero when a file matching a secret pattern is tracked
   by git, and exits 0 when the same file is gitignored. Verified with a scratch repo.
7. `aswath-improve --dry-run` on a seeded ledger failure produces a concrete skill diff and opens
   no pull request. Verified by asserting a diff file is written and the PR count does not change.
8. The gate suite passes on `main` of the public repo today, before auto-merge is enabled.
   Verified by running it on a clean checkout of `main`.
9. `aswath-improve` merges a PR whose changes are confined to `skills/**` and `docs/**` and whose
   gate passed, and refuses to merge a PR that touches `manifest.json`, `install.ps1` or deletes a
   skill directory. Verified by a PR that changes only `SKILL.md` (merges) and one that changes
   `manifest.json` (does not merge, and says which path was forbidden).
10. When the post-merge verification fails, a revert commit exists on `main` and the failing check
    output is attached to an issue. Verified by forcing the post-merge check to fail in a scratch
    clone of the public repo.
11. `aswath-schedule add` creates a Windows scheduled task visible in `schtasks /query`, and
    `remove` deletes it. Verified by querying the task list before and after.
12. Two processes cannot hold the lease at once: the second writer is refused and names the holder
    and the expiry. Verified by taking the lease in one process and attempting to take it in
    another.
13. `aswath-record stats` reports a delivery-completion rate (delivered ÷ produced). Verified
    against a seeded ledger where 1 of 3 artifacts was delivered.

## 4. Constraints & environment

- **Platform**: Windows 11, PowerShell and Git Bash. Two PCs. The store is a git repo with remote
  `aswathas/agent-store` (private); the skills repo is `aswathas/aswath-skills` (public).
- **Harnesses**: Claude Code, MiniMax Code, Codex, Command Code. All resolve skills through
  `~/.agents/skills-active`, which `~/.claude/skills` points at as a junction.
- **Authentication**: `gh` is logged in as `aswathas` with scopes `repo`, `workflow`, `gist`,
  `read:org`. `main` on the public repo is **not** branch-protected (API says "Branch not
  protected"), so a direct merge is technically possible — which is precisely why the gate and the
  revert path are required rather than optional.
- **Python 3** is available and is what the existing skills' scripts use
  (`check_push.py`, `build-registry.py`, the token-guard hook). No new dependency.
- **Windows Task Scheduler** (`schtasks`) is present and is the only scheduler available on both
  PCs that survives a reboot and a logged-out session.
- **Existing scripts to reuse, not rewrite**: `aswath-commit-discipline/scripts/check_push.py`
  (push-time warnings), `aswath-capability/scripts/build-registry.py` (registry index),
  `aswath-delivery` (chat cleanup order).
- **Windows path reality**: the store's `skills-active` currently holds 57 junctions and 4 real
  directories. Git Bash and PowerShell disagree about separators; every script must accept
  forward-slash paths and must not depend on a drive letter.
- **Token discipline**: the 61 injected skill descriptions are paid for on every turn. Four new
  skills add to that bill, so each `description` is written to trigger narrowly.

## 5. Approach — chosen, with rejected alternatives and why

### 5.1 One spec, four skills

Chosen: one spec covering all eight gaps, built as four skills with one question each.

- `aswath-catalog` — "what exists where, and do both PCs agree?"
- `aswath-record` — "what did we run, what did it produce, where are the secrets?"
- `aswath-improve` — "what failed, what should change in a skill, did the change land safely?"
- `aswath-schedule` — "when should this run without a human?"

Rejected: **one mega-skill `aswath-runtime`.** Fewer files, but the skill would answer five
questions, its `description` would have to list all of them (so it fires on every vaguely
operational prompt and costs tokens on every turn), and no single question would be greppable in
the catalogue. The repo's own rule is to pick the category by the question the skill answers; four
skills with one question each is what that rule implies.

Rejected: **eight skills, one per gap.** Gaps 1, 5 and 7 are one mechanism (a map of what exists
where, and a lock over the shared part of it); gaps 2, 3 and 8 are one mechanism (a ledger and the
checks around it). Splitting them finer would duplicate the same state files across skills.

Rejected: **a shared `aswath-runtime` Python package** imported by all four skills. A shared
package needs an install path on every harness; the existing convention is that each skill carries
its own `scripts/` and runs from the junction. Duplicating a small amount of code is cheaper than
an install step.

### 5.2 The ledger: append-only JSONL in the private store

Chosen: `~/.agents/ledger/<project>.jsonl`, one JSON object per line, git-tracked in the private
store.

Rejected: **SQLite.** It is a binary, git merges it badly, and a plain file is readable with `cat`
when something goes wrong. The store already ships JSON state files.
Rejected: **a GitHub Issue per artifact.** The artefact of record should live where the work lives.
Rejected: **the chat as the ledger.** That is the gap.

### 5.3 Secrets: a convention and a check, not a manager

Chosen: `~/.agents/secrets/<project>.env`, gitignored, one file per project, plus
`aswath-record doctor secrets` which reports variable names, flags tracked secret-looking files,
and never prints a value.

Rejected: **Windows Credential Manager / DPAPI.** It would be the correct answer for a machine
that must not keep plaintext secrets at all, but it breaks the "pull the store on the second PC
and it works" property that the rest of the estate depends on, and the user's own tools already
keep plaintext `.env` files. The convention plus a leak check is the smallest thing that closes
the actual gap (a secret reaching a commit or a chat).

### 5.4 Learning loop: pull request, gate, merge, revert

Chosen: the loop proposes a **skill diff on a branch**, opens a PR, runs the gate suite locally,
and merges only when the gate passes and the diff is confined to `skills/**` and `docs/**`. If the
post-merge verification then fails, the loop opens a **revert commit** — never an amend.

Rejected: **editing the skill file directly.** No audit trail; the failure mode is invisible.
Rejected: **a pull request that waits for a human.** The user chose auto-merge; this spec makes
that safe by construction (forbidden-path list, local gate, post-merge check, revert) rather than
by trust.
Rejected: **amend the bad commit after the fact.** The commit is public. Reverting is the only
honest repair; the commit-discipline rule already forbids amending a published commit.
Rejected: **run the loop on a schedule only.** The loop must also be runnable on demand, and the
schedule must be one implementation of the trigger, not the only one.

### 5.5 Scheduling: Windows Task Scheduler

Chosen: `schtasks` wrappers in `aswath-schedule`, tasks named `Aswath\<name>`, created with the
"run as soon as possible after a missed start" flag.

Rejected: **Claude Code's own scheduler** (`~/.claude/scheduled_tasks.json`, currently
`{"tasks": []}`). Its durable form exists and its schema is available in the harness, but a job
only fires while that harness is running and idle on that PC. It cannot drive work on the second
PC or with the PC unlocked at 3am. It stays the right tool for in-session nudges; it is not the
right tool for a machine-level job.
Rejected: **MiniMax Code's scheduler** (`local_runtime_v2_scheduler_jobs` in the runtime
database). It works — nine jobs are stored and nine runs are recorded — but a cron there is a
*prompt* aimed at a *session*, not a script we can audit or a job with an exit code. It lives in
one harness's private database, so nothing the other harnesses or the other PC can read or
schedule. Its nine current crons show the other failure: they were all one-shot WhatsApp
pairing prompts and all nine are now dead rows.
Rejected: **a long-running Python daemon.** A permanent background process that must be restarted
after every reboot, on two PCs, for one daily job. Task Scheduler already is that daemon.

`aswath-schedule` also reports the harness schedulers it finds — the Claude Code task list and
the MiniMax cron table, including the dead one-shots — so the three schedulers can be seen in one
place instead of three.

### 5.6 Shared state: derived scores travel, raw events stay

Chosen: canonical shared state at `~/.agents/state/`. The router's **derived** quality scores
travel as one file per skill (`~/.agents/state/scores/<skill>.json`) so two PCs never conflict on
the same file. The **raw** observation stream (`observations.ndjson`) stays per machine and is
gitignored, exactly as the store already does for the claude-mem database. A junction from
`~/.minimax/local-runtime/skill-learning` → `~/.agents/state` keeps the existing plugin working
with no code change to it.

Rejected: **tracking `observations.ndjson` in git.** Two PCs appending to one tracked file
conflict on every pull; the store's `.gitignore` already states the rule that raw event streams
stay local.
Rejected: **one tracked `ledger.json` for all scores.** Two PCs write the same file; the merge is
a JSON conflict. One file per key merges cleanly.

The migration is a move, not a copy: `~/.minimax/local-runtime/skill-learning/` holds
`capabilities.json` (41 KB), `ledger.json` (4.9 KB), `observations.ndjson` (2 KB), a
`ledger.json.pre-fix` and eight `session-*.json` files today. All of them move into
`~/.agents/state/` first, then the old path becomes a junction to the new one, so the router keeps
its history and needs no code change. The files the router *generates* (`skills.json`, the
published `capabilities.json`, `session-*.json`) are gitignored in the new location; only the
derived per-skill scores are tracked.

### 5.7 Two PCs: a lease over the shared writes, a version check over everything

Chosen: `~/.agents/state/lease.json` (gitignored — it is a lock, not data) is taken before a job
writes shared state and released after. A tracked `~/.agents/config/pc.json` records hostname,
last sync time and the skill-map version, committed once per sync, not once per job.

Rejected: **file locking only.** Windows `msvcrt` locking is per-process and dies with the
process; it cannot express "held until 14:30" across two machines.
Rejected: **git as the lock.** A lock is a merge conflict waiting for a human.

## 6. Architecture, components & data flow

### 6.1 Files

| Path | Home | Git | Holds |
|---|---|---|---|
| `~/.agents/config/skill-map.json` | store | tracked (private) | for every skill: name, canonical path, origin (`public-repo` / `store` / `vendored`), link chain |
| `~/.agents/config/pc.json` | store | tracked (private) | this PC's hostname, last sync time, skill-map version |
| `~/.agents/state/lease.json` | store | ignored | current writer, task, expiry |
| `~/.agents/state/scores/<skill>.json` | store | tracked (private) | per-skill quality scores, one file per key |
| `~/.agents/state/observations.ndjson` | store | ignored | raw learning events, per machine |
| `~/.agents/ledger/<project>.jsonl` | store | tracked (private) | the run/artifact ledger |
| `~/.agents/secrets/<project>.env` | store | ignored | project secrets, one file per project |
| `~/.agents/state/ledger-failed.ndjson` | store | ignored | records whose append failed, flushed on the next write |
| `skills/<cat>/aswath-<name>/SKILL.md` | public repo | tracked (public) | the four new skills |
| `skills/workflow/aswath-delivery/SKILL.md` | public repo | tracked (public) | edited to read the ledger |
| `skills/orchestration/aswath-capability/SKILL.md` | public repo | tracked (public) | edited for the shared state path |
| `~/.minimax/v2/sqlite/runtime-state.sqlite` | MiniMax runtime | read-only | a source of run records to import; never written by us |

The map sits at `~/.agents/config/skill-map.json` because the store's `config/` directory already
holds the harness mirrors, so this is where a machine-readable map belongs. One file, one
canonical location — the map is never mirrored to a second path.

### 6.2 The link chain, fixed

```
~/.claude/skills/<name>            junction
   └── ~/.agents/skills-active/<name>    junction  (always; never a real directory)
          ├── ~/.agents/skills/<name>    junction  (when origin = public-repo)
          │      └── ~/Projects/aswath-skills-wk/skills/<cat>/<name>/   real dir, public git
          └── ~/.agents/skills/<name>    real dir  (when origin = store or vendored)
```

`aswath-catalog check` reads `skill-map.json` and asserts, for every entry: the canonical path
exists, the `skills-active` entry is a junction, the `skills` entry is a junction exactly when the
origin is `public-repo`, and the content at a junction target matches the canonical copy byte for
byte. It also asserts every row in `manifest.json` has a map entry and vice versa.

### 6.3 Data flow — the ledger

```
a run happens
   → aswath-record add --project X --kind run --job Y --outcome ok|failed
   → append one line to ~/.agents/ledger/X.jsonl
   → runs that happened in MiniMax Code are also harvested:
     aswath-record import --since <ts>
       reads ~/.minimax/v2/sqlite/runtime-state.sqlite read-only
       (local_runtime_background_tasks: kind, status, timestamps, session)
       appends one run line per task, skipping ids already in the ledger
   → a build produces files
   → aswath-record add --project X --kind artifact --path P --sha256 H --supersedes <id>
   → aswath-delivery reads the ledger for X
        → superseded ids = artifacts whose id appears in some --supersedes
        → deletes exactly those messages/files from the channel
        → sends the current artifacts once
        → aswath-record deliver --id <id> --channel whatsapp --message-id M
   → aswath-record stats --project X
        → runs, failures, artifacts, superseded, delivered, delivery completion rate
```

The ledger is append-only. A mistake is corrected by appending a new record, never by editing a
line; git holds the history of what was believed when.

### 6.4 Data flow — the learning loop

```
~/.agents/ledger/*.jsonl (failures)   ┐
~/.agents/state/scores/*.json (scores)├─→ aswath-improve
~/.agents/state/observations.ndjson    ┘        │
        │                                        ├─ propose a SKILL.md diff
        │                                        ├─ branch + commit + push
        │                                        ├─ open a PR
        │                                        ├─ gate.py (manifest/README consistency, skill self-check)
        │                                        ├─ allowed paths? (skills/**, docs/**)
        │                                        │      yes + green → gh pr merge
        │                                        │      no  → stop, comment the reason on the PR
        │                                        └─ after merge: catalog check on the merged tree
        │                                                 green → done
        │                                                 red   → git revert the merge commit, push, open an issue
        └─ and: on the next run, the merged skill is the one that gets used
```

The router's `SKILL_ROUTER_STATE_DIR` is pointed at `~/.agents/state`; the old path stays as a
junction so the plugin needs no change.

### 6.5 Data flow — two PCs

```
PC-A  ~/.agents/sync.sh pull     → git pull --rebase + skillhub doctor + catalog check
PC-A  a job starts                → take lease (O_CREAT|O_EXCL) → if held by a live lease, skip and say who holds it
PC-A  a job writes shared state   → append under the lease → release the lease
PC-A  ~/.agents/sync.sh push     → git push → if rejected, pull --rebase and push again
```

`sync.sh` gains `verify`: compares `skill-map.json` and `pc.json` between the two PCs and prints
the divergence (skill present on one side only, differing canonical paths, different map version).

### 6.6 The gate suite

`aswath-improve/scripts/gate.py` runs, on the candidate branch:

1. `manifest.json` parses; every row's `path` exists; every skill directory under `skills/` has
   exactly one row; the README table has one row per skill.
2. Every changed file in the diff is under `skills/**` or `docs/**`. `manifest.json`,
   `install.ps1`, `install.sh` and any deletion of a skill directory are forbidden.
3. Each touched skill's own self-check script, if it has one, exits 0.

All three must pass. The gate is a script in the public repo, so the same gate runs on the second
PC and in CI later.

## 7. Failure modes & error handling

| Failure | Detection | What the user sees | What the system does |
|---|---|---|---|
| Store copy drifts from the published copy | `catalog check` compares content hashes | the skill name, both paths, both hashes | the check exits non-zero; `catalog fix --link <name>` re-points the junction after the human chooses which text wins; the loop refuses to merge a PR that introduced drift |
| Ledger append fails (disk, lock) | the append raises | the failed record on stderr, exit non-zero | the run is **not** silently lost: the caller retries; the failed record is written to `~/.agents/state/ledger-failed.ndjson` and flushed into the ledger on the next successful append |
| Two PCs push at once | git rejects the second push | the rejected push and the branch to rebase onto | `sync.sh push` pulls with `--rebase` and pushes again; a ledger conflict resolves by keeping every line from both sides, sorted by `ts`, dropping duplicate `id`s |
| Two jobs write shared state at once | the lease file exists and is fresh | "lease held by <pc> until <ts>" | the second job skips its write and exits 0 (not an error — the first job is doing the work); an expired lease may be stolen and the steal is logged |
| The gate fails on a proposed PR | `gate.py` exits non-zero | the failing check and its output, on the PR | no merge; the PR stays open with the reason; the branch is not deleted |
| The merge lands and then breaks | the post-merge `catalog check` fails | the failing check, an issue, and the revert commit | a `git revert` commit on `main` (never an amend) and an issue carrying the output |
| A secret is committed | `doctor secrets` greps tracked files | the file path and the line number, the value redacted | exit non-zero; the run is stopped before the push step of `aswath-commit-discipline` |
| The scheduler misses a run (PC asleep) | Task Scheduler's "run as soon as possible" flag | nothing at the time; the job runs late | the job is idempotent by design — every job re-reads state and re-derives, so a late run converges rather than double-applying |
| The router's state directory is missing | the router's builder reports it | the router falls back to its own default | the junction is recreated by `catalog fix`; the plugin never sees the change |
| `gh` is not authenticated on the second PC | `gh auth status` fails at the start of the loop | "gh not authenticated — PR opened manually is required" | the loop writes the diff and the branch, opens the PR when it can, and stops at "PR opened, merge required" instead of failing the job |

## 8. Test plan

Each criterion in section 3 has a check. The checks are cheap, dependency-free and run on Windows.

| # | Check | Runs against | Passes when |
|---|---|---|---|
| 1 | `catalog check` before the fix | this machine | exits non-zero and names `aswath-capability` and the four duplicated copies |
| 2 | `catalog check` after the fix | this machine | exits 0; `skills-active` holds 61 junctions and 0 real directories |
| 3 | ledger round trip | a scratch project dir | one line per action; the JSONL parses; `stats` counts it |
| 4 | delivery stub | a seeded ledger + a stub client | the stub records exactly the superseded ids as deleted |
| 5 | secret redaction | a scratch `.env` with `TOKEN=abc123` | `abc123` appears in neither stdout nor stderr; `TOKEN` appears in stdout |
| 6 | secret tracking check | a scratch git repo | exit 1 when the file is tracked, exit 0 when gitignored |
| 7 | `improve --dry-run` | a seeded failure | a diff file is written; `gh pr list` count is unchanged |
| 8 | gate on `main` | a clean checkout of the public repo | exits 0 today — this must be true **before** auto-merge is enabled |
| 9 | path allow-list | two scratch PR branches | a `SKILL.md` change is mergeable; a `manifest.json` change is refused with the forbidden path named |
| 10 | revert path | a scratch clone with a forced failure | a revert commit exists on `main`; an issue carries the output |
| 11 | scheduler | Windows Task Scheduler | the task appears in `schtasks /query` and is gone after `remove` |
| 12 | lease | two processes | the second is refused, naming the holder and the expiry |
| 13 | stats | a seeded ledger | delivery completion rate = 1/3 |
| 14 | two-PC verify | the store on this PC and a clone | `catalog verify` reports the divergence it is told to look for |
| 15 | harness import | the live MiniMax runtime database, read-only | the import writes run lines for the tasks it finds; the database's modification time is unchanged afterwards; a second import adds no duplicate ids |

Regression suite: a single dependency-free script, `skills/workflow/aswath-record/scripts/selftest.py`
style, that runs checks 3, 5, 6, 12 and 13 in a temp directory and exits non-zero on the first
failure. It is run before any commit in the delivery plan, mirroring the existing
`check_push.py` pattern.

## 9. Implementation ownership — *agent implements* + build order

**The agent implements.** The learner implements *future* skill edits, through the
`aswath-improve` loop, once that loop exists and has a green gate.

Build order, one delivery unit each, each unit one commit and one push (per
`aswath-commit-discipline`), each unit ending with its checks green:

- **U0 — the paperwork.** This spec, its decision-log entry, its prompt record and its change
  inventory, in this repo. The store's own records travel with the units that change the store,
  because unit 0 changes nothing there. Committed and pushed once the spec is approved. Nothing
  else starts before that.
- **U1 — `aswath-catalog`.** The map, the drift detector, the shared-state relocation, the
  junction fixes, the lease, `sync.sh verify`. *First of the code, because every other unit
  writes into the store and the store must be described correctly before anything writes to it.*
- **U2 — `aswath-record`.** The ledger, the delivery integration, the secrets convention, the
  doctor, the metrics. *Second, because it is the substrate the learning loop reads.*
- **U3 — `aswath-improve`.** The learning loop, the gate, the merge policy, the revert path.
  *Third, because it needs the ledger and a green gate.*
- **U4 — `aswath-schedule`.** The Task Scheduler wrappers and the two scheduled jobs
  (`improve --run`, `catalog verify`). *Last, because it schedules work that must exist.*

Edits to `aswath-delivery` and `aswath-capability` ride with U2 and U1 respectively.

## 10. Risks, assumptions, and what would invalidate this spec

### Questions asked, and the answers given

1. **Where does the split live?** Answer: the skill code is public (`aswathas/aswath-skills`), the
   data is private (`aswathas/agent-store`). The spec follows that: skill files in the public
   repo, ledger/state/secrets/map in the store. Secrets are the exception by necessity — they are
   private and *untracked*.
2. **What scope?** Answer: all eight gaps in one spec. This document is that spec.
3. **Where does the ledger live?** Answer: the private store, git-tracked. So
   `~/.agents/ledger/<project>.jsonl`.
4. **What happens to a learning-loop proposal that passes its checks?** Answer: auto-merge. This
   spec implements that with a path allow-list, a local gate, a post-merge verification and an
   automatic revert.

### Assumptions

- `gh` is authenticated on both PCs. *Verified on this PC* (`aswathas`, scopes `repo`,
  `workflow`). *Assumed* on the other.
- The public repo's `main` stays unprotected. *Verified today* ("Branch not protected"). If it
  becomes protected, auto-merge becomes `gh pr merge --auto` and the local gate stays as the
  deciding check.
- The store's private remote accepts pushes from both PCs with the same account.
- Python 3 on both PCs is new enough for `pathlib` and `hashlib` (any 3.8+). The existing scripts
  already assume this.
- The four duplicated `skills-active` copies and the `aswath-capability` store copy are the only
  real-directory cases; `catalog check` will say if that is wrong.
- The MiniMax runtime database keeps its `local_runtime_*` tables. *Observed today* (nine scheduler
  jobs, nine cron definitions, nine cron runs, 3683 background tasks), but it is an internal v2
  schema with no stability promise, so the import is best-effort: a missing table means "no
  records imported", never an error that stops the job.

### Risks

- **A learning-loop edit can degrade a skill that works.** Mitigated by the path allow-list, the
  gate, and the revert. It is not eliminated: a semantically wrong edit that passes the gate will
  merge. Mitigation on top: the loop proposes, the merge is recorded, and the ledger records the
  outcome so a regression shows up as a falling score.
- **Git-tracked ledger grows without bound.** Mitigation: one line per run and per artifact, no
  history rewriting; a yearly prune that keeps delivered artifacts under `history/` is explicitly
  out of scope and named as future work.
- **Two PCs diverging in the skill map.** Mitigation: `catalog verify` and the tracked
  `pc.json`; divergence is visible, not silent.
- **The scheduler adds a machine-level job that writes to git.** Mitigation: every job takes the
  lease, is idempotent, and `sync.sh push` is a separate human-or-scheduled step with rebase.
- **Importing harness records makes the ledger depend on a schema we do not own.** Mitigation: the
  import is read-only, additive and skippable; if the tables change, the ledger keeps the records
  it already has.

### What would invalidate this spec

- Observation: `gh auth status` fails on the second PC **and** no other credential path exists →
  U3 degrades to "open the PR, do not merge", and the auto-merge decision in question 4 no longer
  holds on that machine.
- Observation: `catalog check` reports many more real-directory cases than the five found today →
  U1 is bigger than planned, and the "smallest complete change" assumption behind four skills
  needs re-checking.
- Observation: the router's plugin cannot be pointed at a shared state directory without a code
  change → gap 5 needs a plugin PR upstream, and the shared state must stay per-machine until then.
- Observation: the gate suite does **not** pass on today's `main` → auto-merge is unsafe and
  U3 ships with merge disabled until the gate is green. This is checked before U3 starts (criterion
  8), not discovered during it.
- Observation: the MiniMax runtime database stops exposing `local_runtime_background_tasks` →
  the import step is dropped, and the ledger keeps only the records our own skills write. The
  ledger itself does not depend on it.
