---
name: aswath-token-evaluator
description: Use when the user asks how many tokens a session used, what the context was spent on, how much was saved, whether the token guard is working, or wants a statistics report after a session. Produces a per-session table, a cause breakdown, measured savings from blocked reads, counterfactual savings from repeat reads, and a before/after comparison around the guard.
---

# Aswath Token Evaluator — measure the sessions, then prove the saving

Run it after a session (or a batch of them). It is the tool that answers
"how much did that cost, and how much of it was avoidable".

## Run it

```bash
python "$env:USERPROFILE\.minimax\plugins\aswath-token-guard\scripts\evaluate.py" --last 10
```

Useful flags:

- `--last N` - the N most recent sessions (default 10).
- `--all` - every session in the store.
- `--session-id mvs_xxx` - one session.
- `--json` - machine-readable output.
- `--report <path>` - also write a markdown report (default: a timestamped file
  in `~/.minimax/audits/`).

## What the numbers mean

**Context window** - the tokens actually in the window right now, measured from
`messages.jsonl` (the current generation). This is the number that matters for
context pressure.

**History** - the whole session, measured from the newest snapshot in
`snapshots/`. Use it to judge the session as a whole.

**Cause breakdown** - every token is charged to one of: `tool_results`,
`assistant_thinking`, `tool_calls`, `assistant_text`, `user_text`,
`injected_context`.

## The two savings numbers - never mix them

- **Measured** - reads the guard actually blocked, read from its denial log.
  This is a fact about what happened.
- **Counterfactual** - the cost of repeat reads of the same region in the
  recorded history. This is what the guard *would* have stopped.

Quote them separately. A counterfactual is not a saving you earned; it is
avoidable spend you had.

## Reporting to the user

Give: the context total, the biggest cause with its percentage, the two savings
numbers labelled correctly, and the single next action. Do not paste the whole
table unless asked; the report path is enough.

## Pair it with the switch

```bash
python "$env:USERPROFILE\.minimax\plugins\aswath-token-guard\scripts\control.py" status
python "$env:USERPROFILE\.minimax\plugins\aswath-token-guard\scripts\control.py" on
python "$env:USERPROFILE\.minimax\plugins\aswath-token-guard\scripts\control.py" off
```

`status` shows whether the hooks are live, whether the global token-control
directive is present in every agent, and which skills are missing where.

## Related

- `aswath-token-guard` - the hooks and the live ledger.
- `aswath-token-ledger` - raw transcript reading.
- `aswath-compact` - distil and release the window.
- `context-tax-audit` - audit one session for context tax in detail.