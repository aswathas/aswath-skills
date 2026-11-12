---
name: aswath-minimax-compaction-handoff
description: Use when asked to set up, install, verify, or debug automatic context compaction for the MiniMax Code runtime, the 100k compaction trigger, HANDOFF.md generation before compaction using the context-compression structure (Session Intent, Files Modified, Decisions Made, Current State, Next Steps), or the PreCompact/PostCompact/SessionStart hook wiring in MiniMax Code.
---

# MiniMax Code compaction handoff

Wires the MiniMax Code runtime so that:

1. The conversation compacts automatically every 100000 tokens.
2. `HANDOFF.md` is written **before** compaction happens, so the summary of the
   work survives the compaction.
3. After compaction, `HANDOFF.md` is re-injected into the agent context.

## Why a hook instead of a skill

A skill only runs when an agent decides to run it. Compaction is decided by the
runtime, so the summary must be produced by a runtime hook, not by a prompt.
The hook is deterministic: it reads the session transcript straight out of the
local runtime SQLite database and extracts facts verbatim. No model call, no
network, no extra tokens spent on summarizing.

## Runtime facts

| Fact | Value |
|---|---|
| Trigger config | `contextManagement.compactionTriggerAt` in `<dataDir>/config.yaml` |
| Trigger value | `100000` (integer token count, or a ratio in `(0,1]`) |
| Hook events | `PreCompact`, `PostCompact`, `SessionStart` |
| Hook file | `<dataDir>/hooks.json` (user scope) or `<project>/.minimax/hooks.json` (project scope) |
| Hook payload | JSON on stdin: `hook_event_name`, `session_id`, `cwd`, `trigger` |
| `PreCompact` payload | `trigger` is `"auto"` or `"manual"` |
| `SessionStart` matcher value | `source` is `"startup"`, `"resume"` or `"compact"` |
| Local hooks loader | events live under the top-level `"hooks"` object |
| Handler fields | `type`, `name`, `command`, `commandWindows`, `command_windows`, `timeout` (1-10 s) |
| Source of truth for the transcript | `<dataDir>/v2/sqlite/runtime-state.sqlite`, table `local_runtime_message_rows` (columns `role`, `data_json`) |

Trigger math in the runtime: the effective automatic trigger is
`min(ratio-derived cap, compactionTriggerAt)`. An integer value therefore acts as
an upper bound and never raises the trigger above the runtime's own safety cap.
With `compactionTriggerAt: 100000` the runtime compacts once input tokens pass
100000.

`PreCompact` handlers must exit 0. Returning `decision: "deny"` or `defer: true`
skips the compaction for that turn, which would silently defeat the feature.

## Install

```bash
python scripts/install.py                 # patches <dataDir>/config.yaml + <dataDir>/hooks.json
python scripts/install.py --dry-run       # show what would change
python scripts/install.py --data-dir <path>
```

The installer is idempotent and preserves everything it does not own: unknown
YAML keys stay, unknown JSON keys stay, other hook groups stay.

On Windows the hooks call `scripts/compaction-handoff.ps1`, on POSIX they call
`scripts/compaction-handoff.sh`. Both delegate to `scripts/compaction-handoff.py`,
which is also the file `<dataDir>/compaction-handoff.py` forwards to.

## Files

| File | Role |
|---|---|
| `scripts/compaction-handoff.py` | The worker. Stdlib only, Python 3.8+. |
| `scripts/compaction-handoff.sh` | POSIX entry point. |
| `scripts/compaction-handoff.ps1` | Windows entry point. |
| `scripts/install.py` | Idempotent config and hooks patcher. |
| `reference/hooks.json.example` | The hook groups this skill registers. |
| `reference/config.yaml.example` | The `contextManagement` block this skill registers. |

## Output

`HANDOFF.md` is written to the session working directory (`cwd` from the hook
payload) and copied to
`<dataDir>/v2/session-handoff/records/<session_id>/HANDOFF.md`.

It carries the `context-compression` skill structure:

```
# HANDOFF.md

## Session Intent
## Files Modified
## Decisions Made
## Current State
## Next Steps
```

Merging is anchored and iterative: an existing `HANDOFF.md` is merged into, not
replaced, so repeated compactions never lose earlier facts.

`HANDOFF.md` is a scratch file. Do not commit it.

Per-session logs live beside it: `events.log` (every hook event) and
`compactions.log` (one line per compaction with its trigger).

## Verify

Manual event tests, from the data dir's parent:

```bash
printf '{"hook_event_name":"PreCompact","session_id":"mvs_manual","cwd":"'"$PWD"'","trigger":"auto"}' \
  | python scripts/compaction-handoff.py
```

Expect exit 0 and a `HANDOFF.md` in the current directory. `PostCompact` appends to
`compactions.log`. `SessionStart` with `"source":"compact"` prints the file to
stdout so the runtime injects it as agent context.

End-to-end proof needs a real compaction. Lower the trigger in a scratch config
(`compactionTriggerAt: 3000`), run the CLI against that config, then read
`<dataDir>/v2/session-handoff/records/<session_id>/events.log`. The three events
must appear in order: `PreCompact`, `PostCompact`, `SessionStart`.
