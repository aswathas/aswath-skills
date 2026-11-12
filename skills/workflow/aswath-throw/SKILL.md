---
name: aswath-throw
description: Use when the owner hands over a raw request, idea, or build-this and wants it executed end to end without hand-holding - the request is turned into a harness work item, gated by a leader-authored test, run by the agent pool, checked by two independent verifiers (one adversarial), projected for time, and reported back when it closes.
---

# Aswath Throw - raw request in, proven artefact out

The owner does not write briefs. You do. The harness does the rest.

## The pipeline

    think -> research (only if the request needs facts) -> brief + leader gate ->
    register -> loop (agents build) -> test -> verify (standard) -> verify (grill) ->
    ETA -> alert -> report

Never skip a stage. A request that has not passed the grill has not finished.

## 1. Think

Write down, in three lines: what the request actually wants, what done means, and
what could make you build the wrong thing. If the request is ambiguous in a way that
changes the deliverable, ask ONE question (the harness exists to execute, not to
guess). If it is ambiguous in a way that costs nothing, decide, and write the decision
into the brief.

## 2. Research, only if the request needs facts

Check the machine first (files, installed skills, existing projects). Only reach for the
web when the facts are not local. For model or forecasting design questions, use the
ponytail discipline: the smallest complete solution, no speculative flexibility, and
state what you skipped. The ponytail rules live at
C:/Users/aswat/.claude/plugins/cache/ponytail/ponytail/5.0.0/AGENTS.md.

## 3. Brief and leader gate (you write both, the agent writes neither)

The brief is tasks/<slug>/BRIEF.md: the request verbatim, the standing rules, the
deliverable, and the verify commands.

The gate is a script that can go RED. Write it against behaviour, not against the
agent's own claims: spawn the thing, call it, check the answer. Never let the agent
author the gate for the work it is being judged on - that is the one shortcut that
makes the whole loop theatre.

For a request with a specific, checkable shape, write a specific gate (like
tasks/wa-mcp/gate.py). For a request with no obvious shape, use the generic gate and
lean on the two verifiers.

## 4. Register

    python C:/Users/aswat/overnight/intake/build_item.py "<request>" --workdir <dir> --slug <slug>

The orchestrator reads tasks/registry.json every cycle, so the item starts on its own.
No restart, no edit to the orchestrator.

## 5. The loop does the rest

The orchestrator dispatches to the agent pool (agy, agy-wsl, mcode), runs the verify
commands, then runs two verifiers in parallel: a standard verifier that proves each
brief requirement, and a grill that tries to break the work. Only when BOTH pass is
the item done. A failed grill sends its findings back into the next dispatch.

## 6. Time

The ETA comes from the standalone projector, not from the orchestrator:

    python C:/Users/aswat/Projects/time-projector/projector.py observe --name <slug> --value <seconds>
    python C:/Users/aswat/Projects/time-projector/projector.py predict --name <slug>

The projector picks its estimator by backtesting against a naive baseline, and it
refuses a time-series foundation model until there is enough history to justify one.
When an item closes, the harness records predicted vs actual and retunes the model.
Report the ETA to the owner with the caveat that early predictions are weak.

## 7. Report

Read C:/Users/aswat/overnight/state/ALERT.md and
C:/Users/aswat/overnight/state/eta.json. Tell the owner: what was built, what the
verifiers found, the ETA for anything still open, and what you deliberately did not do.

## Standing rules

- One agent per workdir, ever.
- A quota failure is not a work attempt; do not count it as one.
- Never mark something done because a command exited 0. Exit 0 is not evidence.
- Write findings into the harness memory (C:/Users/aswat/overnight/memory/) so the next
  leader starts from a decision, not from zero.
