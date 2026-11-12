---
name: aswath-token-ledger
description: Use when the user wants the raw context ledger of a session - every token attributed to a cause, the costliest tool outputs, files read more than once - or wants to compare token spend across sessions. Reads the MiniMax Code transcript store directly, including sessions that predate the token-guard hooks.
---

# Aswath Token Ledger — the raw books

The token-guard skill answers "what is this session costing me". This skill
answers "show me the ledger" and works on any session, including old ones and
sessions from another machine that has the store.

## The store

```
~/.minimax/v2/sessions/<yyyy>/<mm>/<dd>/<time>-session_<id>/
    manifest.json      session id, model, cwd
    messages.jsonl     one JSON message per line
    llm-call.json      last model call
```

`messages.jsonl` roles: `user`, `assistant`, `toolResult`, `custom`,
`compactionSummary`. Content is a list of blocks: `text`, `thinking`, `toolCall`.
A `toolResult` is a whole message carrying `toolName`, `content`, `isError`.

## Measuring

```bash
python "$env:USERPROFILE\.minimax\plugins\aswath-token-guard\scripts\token_guard.py" --session-id <session id> --json
```

Without `--session-id` it picks the newest session with a transcript. Use
`--transcript <path>` for a transcript outside the store, and `--session-dir` when
you already know the folder.

## How tokens are attributed

Every block is charged to one of six causes:

| cause | what it is |
| --- | --- |
| `tool_results` | output returned by tools — usually the biggest line |
| `assistant_thinking` | reasoning blocks |
| `tool_calls` | the arguments sent to a tool |
| `assistant_text` | your prose |
| `user_text` | the user's actual prompts |
| `injected_context` | reminders, plugin context, task notices |

Per-message framing overhead (about 8 tokens) is added on top.

## Comparing sessions

Run the measurement per session and compare `estimated_total`, `tool_results` and
`repeat_reads`. A session that grows fast on `tool_results` is a session that is
re-reading or dumping large outputs; one that grows on `injected_context` is
being fed the same reminders over and over; one that grows on `tool_calls` is
passing large arguments around.

## Related

- `aswath-token-guard` — the habits and the hooks.
- `aswath-compact` — distil a session and release the window.
- `token-dashboard` — cross-harness session collection (Claude Code store).