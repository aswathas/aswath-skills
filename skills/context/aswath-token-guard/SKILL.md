---
name: aswath-token-guard
description: Use when the user asks why a session is expensive, how much context is being used, what is wasting tokens, where the context window went, or before a long task that would grow the window. Measures the live session, attributes every token to a cause, names the largest waste, and applies the four habits that cut it. Also the entry point when a PreToolUse hook blocks a repeat read.
---

# Aswath Token Guard — measure, then stop wasting

Four habits, one measurement, no ceremony. The hooks enforce three of the four
automatically; this skill is how you see the ledger and how you talk about it.

## Step 1 — Measure

```bash
python "$env:USERPROFILE\.minimax\plugins\aswath-token-guard\scripts\token_guard.py" --session-id <session id>
```

Add `--json` for machine-readable output. Omit `--session-id` to pick the newest
session with a transcript. The script is stdlib-only Python 3.9+ and needs no
network.

What the report gives you:

- **Where it went** — tokens split into tool results, thinking, tool-call
  arguments, assistant text, your prompts, and injected harness context.
- **Costliest results** — the single tool outputs that cost the most.
- **Repeat reads** — files read more than once in the same session.
- **Injected context** — reminders and plumbing that are not the user's intent.

The estimate is a relative measure (about 3.6 characters per token plus framing),
not a billing number. Quote it as an order of magnitude, never as an invoice.

## Step 2 — The four habits

1. **Read once.** Do not re-read a region you already read; cite it instead. The
   PreToolUse hook blocks an exact repeat read of an unchanged file.
2. **Reference, do not re-send.** Point at a path, an identifier, a line number.
3. **Summarise, do not re-quote.** Large tool output becomes one line, not a paste.
4. **Read narrow.** grep or glob with a pattern before opening a whole file; prefer
   an explicit `offset`/`limit` over a full read.

## Step 3 — What the hooks already did

- **SessionStart** injects a short orientation with the live numbers and these
  four habits.
- **UserPromptSubmit** stays silent until the session passes 200k tokens, and then
  only fires again after another 25k of growth. A silent hook is the point.
- **PreToolUse (read)** denies an exact repeat read of a file that has not changed.
  If it blocks you, the file changed or you want a different range — read that
  instead of retrying the same call.

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