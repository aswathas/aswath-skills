# The write guard for `aswath-questions-ask`

Date: 2026-11-25
Status: approved and built

## Intent

The rule the user gave, in their words:

> ai should not touch or edit any file it can read

The scope they fixed:

> only for the skill

and the exception they allowed:

> git is accepted

## The problem this solves

`aswath-questions-ask` writes an understanding ledger. The ledger is built from
the user's answers, so the file can only be correct after the user has said
them. Two failures follow from writing earlier:

1. **Premature write.** The agent writes the ledger from its own understanding
   of the subject. That is the exact failure the skill exists to prevent — the
   paraphrase is where understanding quietly goes wrong.
2. **Collateral writes.** Nothing stopped the agent from touching other files
   in passing while the interview ran.

A prohibition in prose is a request. The rule has to live in the harness.

## Goals

- The agent writes **no file** while the interview is open.
- After the user says `LOCK`, the agent writes **exactly one file**: the ledger.
- Every ledger row quotes the user's answer verbatim.
- Git stays accepted.
- The rule applies to this skill alone.

## Non-goals

- Not a global rule. Other skills, and the agent outside this skill, are
  untouched.
- Not a sandbox. The guard is a phase gate, not a jail: after `LOCK` the
  ledger is writable, and after the interview ends everything is writable
  again.
- Not a security boundary against the user. The user is the principal.

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

The state file is `~/.claude/state/questions-ask.json`. The hook owns it; the
agent never writes it, or the guard would be advisory.

State lives in a file, not in the prompt, because the harness is the only
party that can hold it across turns without being asked to remember it.

## The mechanism

Two hooks, registered by `install-hooks.ps1` into `~/.claude/settings.json`:

| Hook | Event | What it does |
|---|---|---|
| `write_guard.py` | `UserPromptSubmit` | moves the state machine: the skill marker opens the interview, `LOCK` locks, "enough" or "I understand completely" closes |
| `write_guard.py` | `PreToolUse` | denies the writes the current state forbids |

Denial is **exit 2 with the reason on stderr**, so the agent sees why the call
was refused instead of the call simply failing.

### The deny matrix

| Tool | `INACTIVE` | `INTERVIEW` | `LOCKED` | `CLOSED` |
|---|---|---|---|---|
| `Write` / `Edit` / `MultiEdit` / `NotebookEdit` | allow | **deny** | ledger path only | allow |
| `Bash` (write-ish) | allow | **deny** | **deny** | allow |
| `Bash` (read-only) | allow | allow | allow | allow |
| everything else | allow | allow | allow | allow |

The write-ish `Bash` set: `>` and `>>` redirection, `tee`, `sed -i`, `cp`,
`mv`, `rm`, `mkdir`, `rmdir`, `touch`, `install`, `chmod`, `chown`,
`python -c`, `node -e`, `curl -o`, `wget`, `tar -x`, `unzip`, and the
working-tree-rewriting Git subcommands (`checkout`, `restore`, `reset`,
`apply`, `clean`, `stash`). `git commit`, `git add` and `git push` pass.

### The ledger allowlist

Pattern-based, because the agent cannot declare a path during an interview it
may not write in. A path is a ledger path when it matches:

- `*/docs/understanding/*.md`
- `*/Understanding/*ledger*.md`
- `understanding ledger.md`

### The escape hatch

`QA_OVERRIDE` anywhere in a command line lets a blocked `Bash` command
through. It does not unlock `Write` or `Edit` — those are denied by path, not
by command.

## The skill's side

`SKILL.md` changes so the prose matches the hook:

- A new section, **Read-only until locked**, between The Loop and The Question
  Ladder, with one pointer to `references/write-guard.md`.
- Step 6 becomes **Lock — print the ledger in chat**; a new step 7 becomes
  **Write — only now, and only to the ledger path**.
- The ledger section states that every row quotes the user's answer.
- Three red flags: writing the ledger before `LOCK`, paraphrasing it, and
  saving a progress note.

The rule is stated once in prose and enforced once in code. The reference file
holds the detail — patterns, matrix, known holes — behind a pointer, so it
costs nothing until the agent needs it.

## Known holes

Stated, not hidden:

1. **Other tools.** `WebFetch`, MCP write tools and anything outside the
   matcher are not covered.
2. **A shell that hides the write.** `python - <<EOF` heredocs, `bash -c`,
   `sh script.sh` and `make` change files without matching the pattern list.
3. **Git.** Accepted by design, apart from the working-tree subcommands.
4. **The state file.** A user who knows the path can edit it and unlock the
   interview. The user is the principal.
5. **`LOCK` in ordinary speech.** "Lock the door" unlocks the ledger. The
   state is cheap to reset by re-invoking the skill.

## Verification

- `python tests/test_write_guard.py` — 12 cases over the deny matrix and the
  state transitions.
- Live through the PowerShell wrapper: exit 2 for a non-ledger path, exit 0
  for the ledger path, and the three prompt transitions writing the expected
  state file.
- `install-hooks.ps1` run twice — one entry, not two. Then `-Remove`, then
  again, with the rest of `settings.json` parsing each time.

## Rejected approaches

| Approach | Why not |
|---|---|
| A prose rule in `SKILL.md` alone | A request, not a fact |
| A blanket ban including the ledger | The user wants the ledger file |
| The agent declares the ledger path at lock time | The agent would choose what the rule covers |
| Blocking every Git command | Git was accepted |
| A plugin directory per skill | The skill is not a plugin; the hook registers into the user settings file |
