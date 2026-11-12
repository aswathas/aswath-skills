---
name: aswath-token-ledger
description: Use when the user wants the raw context ledger of a session - every token attributed to a cause, the costliest tool outputs, files read more than once - or wants to compare token spend across sessions. Reads the Claude Code and MiniMax Code transcript stores directly, including sessions that predate any hook.
---

# Aswath Token Ledger — the raw books

The token-guard skill answers "what is this session costing me". This one answers
"show me the ledger", across sessions, including old ones and sessions from another
machine that has the store.

This skill is a view over the token-guard tool. Install the tool once:

```bash
npx skills add aswathas/aswath-skills@aswath-token-guard -g
```

## The stores

Claude Code:

```
~/.claude/projects/<project-slug>/<session-id>.jsonl
```

One JSON record per line. The assistant records carry a `usage` object with
`input_tokens`, `output_tokens`, `cache_read_input_tokens` and
`cache_creation_input_tokens`.

MiniMax Code:

```
~/.minimax/v2/sessions/<yyyy>/<mm>/<dd>/<time>-session_<id>/
    manifest.json      session id, model, cwd
    messages.jsonl     one JSON message per line
    llm-call.json      the request envelope of the last model call
```

The usage objects for MiniMax Code live in the runtime database, not in the session
folder:

```
~/.minimax/v2/sqlite/runtime-state.sqlite
    local_runtime_token_usage   session_id, turn_id, model, ts, input_tokens,
                                 output_tokens, reasoning_tokens,
                                 cache_read_tokens, cache_write_tokens
```

## Measuring

```bash
python ~/.agents/skills/aswath-token-guard/scripts/token_guard.py --view ledger --session-id <id> --json
```

Without `--session-id` it picks the newest session with a transcript. `--view ledger`
prints one block per session: the totals, the costliest tool outputs, and the files
that were read more than once. `--json` gives the same thing machine-readable.

## How the tokens are attributed

| cause | what it is |
| --- | --- |
| `tool result` | output returned by tools - usually the biggest line |
| `user prompt` | what you asked for |
| `assistant output` | the model's own prose |

A turn's window (input plus cache read) is split across the context that produced it
by content weight. The totals are exact; the split is a stated method.

## Comparing sessions

Compare `total`, `cache_read` and the tool-result share. A session that grows fast on
tool results is one that is re-reading or dumping large outputs. A session with a very
high cache read ratio is re-serving the same context turn after turn. A session with a
high prompt share is one where the user is doing the talking.

## Related

- `aswath-token-guard` - the habits, and the live view of one session.
- `aswath-token-evaluator` - the table and the cause breakdown.
- `aswath-compact` - distil a session and release the window.
