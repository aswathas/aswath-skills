---
name: aswath-compact
description: Use when the session's context is filling, before a long task, or when the user says "compact", "free up context", "too much in context", or asks how much context is being used. Measures what the session is actually carrying, distils it into a dense handoff file, persists that handoff so any later session can resume from it, and reports how to actually release the window.
---

# Aswath Compact — distil the session, then release the window

Two separate problems, two separate steps. Most attempts at this fail by doing only the
first and pretending it was the second.

- **Distilling** is yours: turn a long transcript into a small file that carries the
  working state.
- **Releasing the window** is the harness's: the runtime owns the context window, and
  it compacts on its own schedule. You cannot shrink it from inside a turn.

Do both, in that order, and be honest about which one you have done.

## Step 1 — Measure and gather

Run the helper. It is deterministic; it gathers raw material and reports the real
numbers. It does not decide what matters.

```bash
python ~/.agents/skills/aswath-minimax-compaction-handoff/scripts/compaction-handoff.py \
  --session-id <session id> --cwd <your project dir>
```

That script ships with the `aswath-minimax-compaction-handoff` skill. Install it once:

```bash
npx skills add aswathas/aswath-skills@aswath-minimax-compaction-handoff -g
```

It is stdlib-only Python 3.9+, needs no network, and reads the session transcript from
the local runtime database. It writes `HANDOFF.md` into `--cwd` with five sections:
Session Intent, Files Modified, Decisions Made, Current State, Next Steps. Every fact
is extracted verbatim - no model call, nothing guessed.

If the session id is unknown, take it from the session store:
`~/.minimax/v2/sessions/<yyyy>/<mm>/<dd>/*/manifest.json` holds `sessionId`.

Read `HANDOFF.md` before you write anything. If the measured context is small, say so
and stop - do not manufacture a handoff nobody needs.

## Step 2 — Distil it yourself

The script's `HANDOFF.md` is the raw material: verbatim facts, no judgement. Read it,
then write a curated **`handoff.md`** next to it in the same directory. This is the
artifact that replaces the transcript.

Use the official **`handoff-doc`** skill for the document shape (Goal, Decisions
made, Constraints to keep, Ruled out, Current state, Next steps, Watch out for,
Pointers) — it is installed and knows the template. This skill adds only what
`handoff-doc` cannot know: the measured numbers and the release mechanism.

Extra rules on top of `handoff-doc`:

- **Hard ceiling: 150 lines.** If it does not fit, it is not distilled yet.
- **Lead with what is true now**, not with history. State, decisions, exact paths,
  exact commands, exact next actions.
- **Decisions carry their reason.** A decision without a reason forces a re-litigation
  later.
- **Record the "do not re-read" pointers**: the file path of the spec, the plan, the
  last commit sha. These are what the next session opens instead of the transcript.
- **Carry the measured context numbers** from Step 1 into the handoff, so the next
  session knows what it is inheriting.
- **Drop the noise**: failed tool calls that were already fixed, exploratory dead ends,
  my own interim narration, and anything the transcript already settled.

Write the file yourself with the `write` tool. Do not shell out to generate it.

## Step 3 — Persist it outside the session

The handoff must outlive this session. Do both:

1. `save_memory` — one durable note carrying the state, decisions, and next action.
2. `work_state_write` — the open items, on the project list, so they show up at the
   start of every later session.

## Step 4 — Release the window (be precise about this)

This is where most tools over-promise. State plainly what happened:

- **If the runtime compacts on its own**, the window shrinks when it fills. Distilling
  first makes that compaction cheap and lossless, because the summary can point at
  `handoff.md`.
- **A fresh session in lightweight context mode is the reliable way to start small.**
  The user starts it themselves with:
  ```
  mcode --mode lightweight
  ```
  or `mcode --mode lightweight --continue` to carry the session forward in the lean
  mode. You cannot switch the running session's mode.
- **A new session plus `aswath-resume`** is the cleanest way to keep working with a
  small window: start it, ask for "resume", and it loads the handoff instead of the
  transcript.

Say which of these applies and what the user must do. Do not claim the window is
smaller because you wrote a file.

## What this skill is not

It is not a summariser of the transcript's prose. The transcript is the input; the
handoff is the output; the point is that afterwards nobody needs the transcript.

## Verification

Before reporting done:

- `handoff.md` exists, is under 150 lines, and names the current state.
- `save_memory` returned a memory id — quote it.
- The user knows the one command that releases the window.
