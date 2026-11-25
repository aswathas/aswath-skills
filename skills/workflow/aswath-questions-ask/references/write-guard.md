# The write guard

The rule this skill runs on: **the AI does not touch or edit any file it can
read.** Git is accepted — commits and pushes are not file writes to the
harness's eye.

Enforcement is a hook, not prose. Prose in `SKILL.md` is a request; a
`PreToolUse` hook with exit code 2 is a fact.

## Files

| File | Role |
|---|---|
| `hooks/write_guard.py` | the state machine and the deny logic |
| `hooks/write-guard.ps1` | Windows wrapper — pipes stdin to the Python, keeps the exit code |
| `hooks/install_hooks.py` | the settings.json surgery |
| `tests/test_write_guard.py` | twelve cases over the matrix below |
| `install-hooks.ps1` | registers both hooks into `~/.claude/settings.json` |

## The state machine

```
INACTIVE ──skill invoked──▶ INTERVIEW ──LOCK──▶ LOCKED ──"enough"──▶ CLOSED
                              │                     │
                              └─────"enough"────────▶ CLOSED
```

| State | Files may be written |
|---|---|
| `INACTIVE` | anything — the skill is not running |
| `INTERVIEW` | **nothing** |
| `LOCKED` | the ledger path only |
| `CLOSED` | anything — the interview is over |

The state file is `~/.claude/state/questions-ask.json`. The hook owns it.
The agent never writes it — that would make the guard advisory.

`LOCK` again from `LOCKED` is an amend: the ledger can be rewritten, still
only to the ledger path.

## What is denied

**During the interview** (`INTERVIEW`):

- `Write`, `Edit`, `MultiEdit`, `NotebookEdit` — all denied.
- `Bash` commands that change files: `>` and `>>` redirection, `tee`,
  `sed -i`, `cp`, `mv`, `rm`, `mkdir`, `rmdir`, `touch`, `install`, `chmod`,
  `chown`, `python -c`, `node -e`, `curl -o`, `wget`, `tar -x`, `unzip`.

**After `LOCK`** (`LOCKED`):

- Writes to any path that is not a ledger path — denied.
- The same write-ish `Bash` set — denied, because a shell can write any file.

## The ledger allowlist

Pattern-based, because the agent cannot declare a path during the interview —
it cannot write, so it cannot announce where the ledger lives.

| Pattern | Matches |
|---|---|
| `*/docs/understanding/*.md` | `docs/understanding/blockchain ledger.md` |
| `*/Understanding/*ledger*.md` | `Understanding/21CSE433T understanding ledger.md` |
| `understanding ledger.md` | a bare `understanding ledger.md` |

## The escape hatch

`QA_OVERRIDE` anywhere in the command line lets a blocked `Bash` command
through:

```
QA_OVERRIDE=1 node scripts/fix.js
```

Use it only when the command is genuinely read-only-in-spirit (a formatter
dry run, a generator the user asked for) and only when the user asked for it.
It does not unlock `Write` or `Edit` — those are denied by path, not by
command.

## Known holes

Stated, not hidden:

1. **Other tools.** `WebFetch`, `NotebookEdit` variants and MCP write tools
   are outside the matcher. The matcher is `Bash|Edit|Write|MultiEdit|NotebookEdit`.
2. **A shell that hides the write.** `python - <<'EOF'` heredocs, `bash -c`,
   `sh script.sh` and `make` all change files without matching the pattern
   list. `python -c` and `node -e` are matched; heredocs are not.
3. **Git.** Accepted by design — commits, pushes and `git add` pass. The
   subcommands that rewrite working-tree files (`checkout`, `restore`,
   `reset`, `apply`, `clean`, `stash`) are blocked: they edit files.
4. **The state file.** A user who knows the path can edit
   `~/.claude/state/questions-ask.json` and unlock the interview. The user is
   the principal; this is a guard against the agent's drift, not an adversary.
5. **`LOCK` in ordinary speech.** The word `lock` in a prompt flips the
   state. "Lock the door" unlocks the ledger. The state is cheap to reset by
   re-invoking the skill.

## Registering the hooks

```powershell
powershell -NoProfile -File install-hooks.ps1
```

Idempotent — running it twice does not double the entries. `-Remove` takes
them back out.

The hooks are registered in `~/.claude/settings.json` under `hooks`:

```json
{
  "matcher": "Bash|Edit|Write|MultiEdit|NotebookEdit",
  "hooks": [{ "type": "command", "command": "powershell -NoProfile -File <skill>\\hooks\\write-guard.ps1 PreToolUse" }]
}
```

and

```json
{
  "hooks": [{ "type": "command", "command": "powershell -NoProfile -File <skill>\\hooks\\write-guard.ps1 UserPromptSubmit" }]
}
```

`UserPromptSubmit` has no matcher — it fires on every prompt, cheaply,
because it only reads a small JSON file.

## Testing

```bash
python tests/test_write_guard.py
```

Twelve cases. Each writes the state file, calls the hook with a payload, and
checks the exit code: 0 means allowed, 2 means blocked.
