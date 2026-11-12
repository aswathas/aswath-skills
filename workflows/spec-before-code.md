# Workflow: spec-before-code

**Use when** a new build, feature or refactor starts without an approved spec.

| # | Skill | Gate |
|---|---|---|
| 1 | `aswath-forge` | Classify: question, routine (minted skill exists), or creative. Questions stop here — answer, no spec. |
| 2 | `aswath-first-principles` | Research → questions → written spec. **Gate: the user approves the spec.** No scaffolding, manifests, config or stubs before this. |
| 3 | `aswath-forge` (mint) | After approval, mint `aswath-<slug>` for the next similar task. |
| 4 | `aswath-commit` | When the change set is ready: decision log, file-by-file inventory, then commit. |

## Rules

- Step 1 is a lookup, not a formality. Naming a skill that is not in the catalog is a fabrication.
- A spec that the implementer wrote alone still needs the user's yes. Approval is a gate, not a step.
- Minting is optional when the work is genuinely one-off. Say which and why.
- No single mass commit. One decision, one commit, a message that states the why.

## Done when

There is an approved spec, the code matching it, and a commit history a future reader can follow without asking.
