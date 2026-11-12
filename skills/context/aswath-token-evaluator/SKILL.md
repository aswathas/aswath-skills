---
name: aswath-token-evaluator
description: Use when the user asks how many tokens a session used, what the context was spent on, how much was saved, whether the token guard is working, or wants a statistics report after a session. Produces a per-session table and a cause breakdown from the usage objects the runtime reports.
---

# Aswath Token Evaluator — measure the sessions, then prove the saving

Run it after a session, or over a batch of them. It answers "how much did that cost,
and how much of it was avoidable".

This skill is a view over the token-guard tool. Install the tool once:

```bash
npx skills add aswathas/aswath-skills@aswath-token-guard -g
```

## Run it

```bash
python ~/.agents/skills/aswath-token-guard/scripts/token_guard.py --view stats --last 10
```

Useful flags:

- `--last N` - the N most recent sessions (default 1).
- `--all` - every session in the store.
- `--session-id <id>` - one session.
- `--json` - machine-readable output.
- `--store claude|minimax|both` - which runtime's store to read (default both).

## What the numbers mean

**Total** - every token the runtime reported for that session: input, output, cache
read and cache write. These come from the usage objects, not an estimate.

**Cache read** - the context the model was served from cache instead of being sent
again. A high ratio means the same context was re-read many times, which is normal
for a long session and is not waste on its own.

**Cause breakdown** - the context split into tool results, your prompts and the
assistant's own output. Tool results dominate most sessions, and the split is
attributed by content weight inside each turn. The script says so; quote the total as
a fact and the split as a method.

**Turns** - how many model turns the session took.

## Avoidable spend, and how to label it

- **Measured** - a saving the guard actually blocked. This only exists if the
  MiniMax Code plugin hooks are installed and running. If they are not, there is no
  measured number, and you do not invent one.
- **Counterfactual** - the cost of the repeat reads the ledger shows: the same file
  or region read more than once in one session. This is avoidable spend you had, not
  a saving you earned.

Quote them separately, and label which is which. Never present a counterfactual as a
saving.

## Reporting to the user

Give: the total, the biggest cause with its share, the cache read ratio, the
counterfactual repeat-read cost labelled as such, and the single next action. Do not
paste the whole table unless asked.

## Related

- `aswath-token-guard` - the habits, and the live view of one session.
- `aswath-token-ledger` - the raw line items.
- `aswath-compact` - distil a session and release the window.
