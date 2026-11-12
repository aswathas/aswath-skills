---
name: aswath-token-guard
description: Use when the user asks why a session is expensive, how much context is being used, what is wasting tokens, where the context window went, or before a long task that would grow the window. Measures the live session, attributes every token to a cause, names the largest waste, and applies the four habits that cut it. Also the entry point when a PreToolUse hook blocks a repeat read.
---

# Aswath Token Guard — measure, then stop wasting

Four habits, one measurement, no ceremony. The measurement tells you what the habits
would have saved.

## Step 1 — Measure

```bash
python ~/.agents/skills/aswath-token-guard/scripts/token_guard.py --view guard
```

The script ships with this skill. Stdlib-only Python 3.9+, no network.

Three views of the same numbers:

- `--view guard` (default) - the newest session: what it cost, what the context is
  mostly made of, the files that were read more than once.
- `--view stats` - a table of sessions, then where the context went.
- `--view ledger` - every session as a line item, the costliest tool outputs, the
  repeat reads.

Other flags: `--last N` (the N newest sessions, default 1), `--all` (every session in
the store), `--session-id <id>` (one session), `--json` (machine-readable),
`--store claude|minimax|both`.

What the report gives you:

- **Where it went** - the context split into tool results, your prompts and the
  assistant's own output, with the share each one takes.
- **Costliest results** - the single tool outputs that cost the most.
- **Repeat reads** - files read more than once in the same session.
- **The cache read ratio** - how much of the spend is the same context read again.

Token counts come from the usage objects the runtime reports, not from an estimate:
Claude Code records them per assistant message, the MiniMax Code runtime per turn in
its local database. The totals are exact. The split by cause is attributed by content
weight inside each turn, and the script says so - quote the total as a fact and the
split as a method.

## Step 2 — The four habits

1. **Read once.** Do not re-read a region you already read; cite it instead. The
   PreToolUse hook blocks an exact repeat read of an unchanged file.
2. **Reference, do not re-send.** Point at a path, an identifier, a line number.
3. **Summarise, do not re-quote.** Large tool output becomes one line, not a paste.
4. **Read narrow.** grep or glob with a pattern before opening a whole file; prefer
   an explicit `offset`/`limit` over a full read.

## Step 3 — The hooks, where they exist

The repeat-read blocker and the live orientation are MiniMax Code plugin hooks. They
run only in a MiniMax Code runtime that has the plugin installed.

The measurement above works in any runtime, on any session, with no plugin at all. So
measure first, and never assume a hook is running just because a habit was mentioned.

## Reporting to the user

Give the three numbers that matter and the one action that pays: total context,
the largest single cause, the biggest repeat waste, and the next change you are
making. Do not paste the whole ledger. If the user asks for the ledger itself,
give the path to the report or the JSON.

## Do not

- Do not run the measurement when the user did not ask for it.
- Do not use compaction as a substitute for not re-reading.
- Do not claim a saving you have not measured.

## Related

- `aswath-token-ledger` — read the transcript ledger directly, across sessions.
- `aswath-compact` — distil the session and release the window.
- `save-token` — the dedupe and summarise-don't-resend habits.