# Workflow: context-discipline

**Use when** a session feels expensive, is filling, or the user asks where the context went.

| # | Skill | Gate |
|---|---|---|
| 1 | `aswath-token-guard` | A named cause and a named largest waste, with a number attached. No number → the measurement failed, say so; do not guess. |
| 2 | `aswath-token-ledger` | Only if step 1's cause is "repeat reads" or the user wants the raw ledger. Per-session rows: costliest outputs, files read twice. |
| 3 | `aswath-token-evaluator` | Only if the user asks whether it worked, or a guard change needs a before/after. Measured savings separated from counterfactual savings. |
| 4 | `aswath-compact` | When the window must actually be released. Writes the handoff file and states that compaction cannot be triggered from inside a turn. |

## Rules

- Steps 1 and 4 are the common path. 2 and 3 are evidence steps; skip them unless their question was asked.
- Every number comes from a transcript, a ledger row, or a measurement. No estimates dressed as measurements.
- If the guard already blocked a read this session, that block is step 1's starting evidence, not a new investigation.

## Done when

The user can name what is wasting tokens, what it cost, and the single change that removes it.
