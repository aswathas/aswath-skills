---
name: aswath-forge
description: Use when starting any task that may already have a minted skill for it, or when a task needs a spec before any code is written
---

## Overview

Every task ends with a decided spec and a reusable asset. This routes a task to a minted skill
if one answers it, or to `aswath-first-principles` — the template it routes into — otherwise.

## When to Use

A new task arrives, or a task resembles earlier work. Not for a question or a mechanical edit.

## Step 1 — Classify

- **Question** — the user wants an answer, not a change. Answer it. No spec, no skill.
- **Routine** — a matching minted skill exists. Go to Step 2 and use it. The user still
  approves what changes before any file is written; a minted skill is a procedure, not a
  licence to change files unasked.
- **Creative** — new work with unmade decisions. Go to Step 3.

## Step 2 — Catalog Lookup

Use the harness's own skill discovery first: the `skill` tool and the catalog it advertises.
With no discovery tool in this session, scan the directories — that is a first-class path, not a
shortcut: `~/.agents/skills/` (cross-runtime), `~/.minimax/skills/` (MiniMax Code),
`~/.claude/skills/` (Claude Code), and this repo's `skills/catalog/`.

Match on triggers, not names: each `SKILL.md` frontmatter `description` states the trigger
conditions. If `catalog/registry.json` exists it is authoritative **for `aswath-*` capabilities
only** — it lists the forge catalog with their triggers and install state. For every other
skill, use the harness's advertised catalog; the registry does not list the hundreds of skills
installed on this machine and is not a substitute for it. Scan the directories only when
discovery is unavailable.

More than one match: pick the most specific, and say which and why.

This lookup is a **guarantee**, not a novelty: a behaviour test
(tests/evidence/t6-minted-skill-reuse.md) found a competent agent already searches the
catalog on its own. It must still happen when the agent is in a hurry, and "no match" needs a
next step (Step 3). Never present it as a discovery.

## Step 3 — Reuse or Discover

Matched: load the skill and follow it. None: run `aswath-first-principles`
(research→questions→spec→approval→mint→execute).

**No implementation before an approved spec.** Scaffolding, manifests, config and stubs count.

## Step 4 — Mint

After the user approves the spec, mint a task-specific skill so the next
similar task starts from what was learned here.

1. Name it `aswath-<slug>` (lowercase, hyphens, no dates).
2. Write `skills/catalog/aswath-<slug>/SKILL.md`. Its frontmatter `description`
   states only the triggering conditions ("Use when ..."), never a summary of
   the procedure — a workflow summary in the description makes agents shortcut
   the body.
3. The body is the procedure that worked: the steps, the decisions, the
   commands that work, and the mistakes to avoid. Write it for an agent that
   knows nothing about this project.
4. Test it before shipping: dispatch a subagent with only this skill and a
   realistic request. If the subagent improvises instead of following the
   skill, the skill is not ready — fix it and retest.
5. Install it with `scripts/mint-skill.ps1` and commit it to this repo.

## The Minted Skill

Its description triggers on the right tasks; its body is a procedure, not a story; written for
an agent who knows nothing of the project; tested against a realistic request; it lives in the
repo so it travels to the other machines.

## Delegation

Research and test subagents: the `task` tool (`agent_name: "explore"` read-only, `"worker"`
for changes), or the restored `aswath-capability` orchestrator, delegating to the `agy` and
`cmdc` backends: `python scripts/delegate.py --backend agy --model fast --prompt "..."` run
from the installed skill directory `~/.agents/skills/aswath-capability`. With no `task` tool,
do the work directly.

The orchestrator also carries three agent briefs worth using: `aswath-researcher` (gather
facts before asking), `aswath-planner` (turn a settled decision into a build order), and
`aswath-critic` (argue against the plan before it is approved).

## Red Flags

- Minting before the spec is approved.
- A minted skill whose description summarises the procedure.
- A minted skill with no test.
- Ignoring a catalog match and running discovery again.
- Treating a question as a project.

## Common Mistakes

- Scanning the catalog by directory name instead of by trigger.
- Running discovery when a skill already matches.
- Answering a question with a spec.
- Minting a skill that only makes sense in this conversation.
- Leaving the minted skill out of the repo, so it never reaches other machines.
- Installing a minted skill without registering it.
