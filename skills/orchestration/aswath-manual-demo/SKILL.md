---
name: aswath-manual-demo
description: Use when you want to see how a hand-written skill is captured into the shared catalog
---

## Procedure

1. This skill was written by hand directly into `~/.agents/skills/`, not minted by the forge.
2. `forge capture` found it, copied it into `skills/catalog/`, and registered it with
   `provenance: "manual"`.
3. `forge sync` committed it, so the next machine that syncs gets it too.

It exists to prove the capture path: a skill you write by hand is not lost, and it is not
stuck on one machine.
