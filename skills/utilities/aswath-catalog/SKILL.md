---
name: aswath-catalog
description: Use when a skill is in the wrong place, when two copies of a skill exist, when the published catalogue and the machine disagree, when a skill was edited in one place and did not change in another, or when the two PCs need to agree on what is installed. Also the entry point for "where is this skill actually", "which copy is the real one", and "check the skill layout".
---

# aswath-catalog

The estate's own layout, made checkable.

Every harness resolves its skills through one chain:

```
~/.claude/skills/<name>           a junction to ~/.agents/skills-active
~/.commandcode/skills/<name>      a junction to ~/.agents/skills-active
~/.agents/skills-active/<name>    a junction to the canonical copy
~/.agents/skills/<name>           a junction to the canonical copy
<repo>/skills/<category>/<name>/  the canonical copy - published skills
~/.agents/skills/<name>/          the canonical copy - vendored and third-party skills
```

One copy per skill. The canonical copy is where the edit goes; everything else is a link to it.
The failure this exists to prevent: a real directory sitting in the chain, so an edit lands in
the copy and the published catalogue keeps describing the old skill.

## Commands

```bash
C=skills/utilities/aswath-catalog/scripts/catalog.py

python $C build          # write ~/.agents/config/skill-map.json and pc.json
python $C check          # verify this machine against the map; exit 1 on any violation
python $C fix <name>     # re-point one skill at its canonical copy
python $C verify         # compare this machine's map with the one on the remote
python $C lease take <task> [--minutes 30]
python $C lease release
```

## What `check` reports

| Code | Meaning |
|---|---|
| `MISSING_CANONICAL` | the manifest points at a skill that is not on disk |
| `MISSING_STORE` | a published skill is not mirrored into the store |
| `SHADOWED_COPY` | the store holds a real directory where a link belongs — the drift |
| `WRONG_TARGET` | the store link points somewhere else |
| `COPY_IN_ACTIVE` | `skills-active` holds a real directory — edits to one copy never reach the other |
| `ACTIVE_WRONG_TARGET` | the active link points somewhere else |
| `MISSING_ACTIVE` | a kept skill is not installed |
| `KEEP_NOT_ACTIVE` | in the keep list, absent from the active set |
| `ACTIVE_NOT_KEPT` | in the active set, absent from the keep list |
| `NO_KEEP_LIST` / `BAD_KEEP_LIST` | the keep list is missing or unreadable |

A skill that is published but deliberately not kept is not a problem. The keep list is the
curated set, and it decides who has to be installed.

## What `fix` will not do

It refuses to delete a store copy that holds files the published copy does not. That copy may be
newer than the repo — port the difference into the repo first, then run `fix` again. This is the
only place the tool refuses, because everywhere else it can rebuild a link from the map.

## The lease

Two PCs write the same shared state. The lease says who is writing:

```
python $C lease take improve-loop --minutes 30   # refuses if a live lease is held elsewhere
python $C lease release
```

It lives at `~/.agents/state/lease.json` and is not tracked in git — a lock, not data. An expired
lease may be taken over, and the takeover is printed.

## The map

`~/.agents/config/skill-map.json` is tracked in the private store, so both PCs carry it. It says
for every skill: the origin (`public-repo` or `store`), the canonical path, and whether each
link in the chain is a link. `verify` compares it with the remote's copy and prints what differs.

The comparison is by each skill's *place* — `skills/utilities/aswath-catalog` on both PCs — not by
its absolute path, because the two machines have different home directories. A skill that sits
somewhere else, or that only one side has, is reported.

`~/.agents/sync.sh verify` runs both halves: the local layout, then the two-PC comparison.

## When to run it

- after installing or removing a skill
- before pushing, when a skill was edited
- on the second PC after a pull, to prove the layout matches
- when a skill behaves differently in two harnesses — that is a copy, not a bug

## Self-check

```bash
python skills/utilities/aswath-catalog/scripts/selftest.py
```

Runs against a scratch directory. It never touches the real estate.

## Known failures

Recorded from the run ledger. A job listed here failed and was never
followed by a success.

- `the keep list and the active set stay in step after a publish`: 2 failures, last on 2026-11-17

