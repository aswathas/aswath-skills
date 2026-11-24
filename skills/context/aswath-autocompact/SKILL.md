---
name: aswath-autocompact
description: Use when the user wants to change the auto-compact window for a task, says "autocompact template", "compact window", "set compaction to 200k/300k/400k", "basic/medium/hard task compaction", or asks what compaction rules apply to the current task. Also use when compaction is landing at the wrong size, or when the summary that came back dropped the parts that mattered.
---

# Aswath Autocompact — a window and a rule set per task class

Three templates. Each one sets two things: how big the auto-compact window is, and
what the compaction summary is told to keep.

| Template | Window | Use when |
|---|---|---|
| `basic` | 200k (150k–200k allowed) | One focused job: a single file, a question, a fix, an answer. |
| `medium` | 300k (250k–300k allowed) | A multi-step feature or investigation: several files, a plan, tests, open questions. |
| `hard` | 400k | A long build, a hard debugging hunt, a migration, a multi-repo change. |

The window is the runtime's `autoCompactWindow`. The rules ride along in a
`PreCompact` hook, whose stdout the runtime feeds into the compaction summary as
instructions. That is the only way to change what a summary keeps — Claude Code
has no setting for custom compaction instructions.

## Apply a template

```bash
python ~/.agents/skills/aswath-autocompact/scripts/autocompact.py apply medium
```

`basic`, `medium`, `hard`. The script writes the window into the user settings
file, writes the active template to `~/.claude/autocompact-template.json`, and
registers the rules hook. It preserves everything it does not own.

```bash
python ~/.agents/skills/aswath-autocompact/scripts/autocompact.py status
python ~/.agents/skills/aswath-autocompact/scripts/autocompact.py uninstall
```

## What the user has to know

1. **The window applies to the next session.** A running session keeps the window
   it started with. Say so when applying.
2. **`CLAUDE_CODE_AUTO_COMPACT_WINDOW` outranks the settings file.** While that
   environment variable is set, `/autocompact` refuses to write and the window
   does not change. The script warns when it sees it. On this machine it was
   removed from `~/.claude/settings.json`; if it reappears, unset it.
3. **The window is capped by the model's own context window.** The runtime
   reports this as "capped to model limit of N".

## Rules per template

The rules are what the summary keeps. Full text lives in `presets.json`; the
shape of it:

- **basic** — one line of goal, files touched with exact paths, decisions made,
  the next step, and any error text still blocking. Everything else goes.
- **medium** — the goal, the plan split into done and remaining, each decision
  with a one-line reason, files changed with exact paths, test results including
  failures, open questions and who owns them.
- **hard** — the goal and success criteria, every constraint and invariant
  learned, each decision with its reason *and the alternatives rejected*, exact
  file paths and symbol names, error text and stack fragments verbatim, the
  current state, next steps in order, and everything tried that failed.

Pick by what a lost summary would cost. Losing a failed attempt in a debugging
hunt is expensive. Losing it in a one-line answer is not.

## Files

| File | Role |
|---|---|
| `presets.json` | The three templates: window, use-when, rules. The source of truth. |
| `scripts/autocompact.py` | apply / status / uninstall. Stdlib only, Python 3.8+. |
| `scripts/compaction_rules.py` | The `PreCompact` hook. Prints the active template's rules; silent when no template is active. |
| `scripts/selftest.py` | 24 assertions against a throwaway HOME. Never touches the real settings file. |

## Verify

```bash
python scripts/selftest.py
```

Expect `passed 24, failed 0`.
