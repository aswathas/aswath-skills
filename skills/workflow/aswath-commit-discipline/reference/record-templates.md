# Record templates

Exact shapes for the records this skill requires. Copy the block, fill every field, delete
nothing. A field you cannot fill is a decision you have not made yet.

## Decision entry — `docs/reviews/decision-log.md`

One entry per real choice. Oldest first. A decision is a choice with alternatives; facts and
diff restatements are not decisions.

```markdown
## D<n> — <the choice, in one line>
- Date: <YYYY-MM-DD>
- Prompt: "<the user prompt or instruction that triggered this decision, verbatim>"
- Context: <what forced a choice>
- Options: <the real alternatives, one per line, with the consequence of each>
- Chosen: <what, and why it beat the others>
- Evidence: <the command run and its result, or the event that proves it>
- Consequence: <what this locks in, or what it blocks>
```

Example:

```markdown
## D7 — Warn-only global pre-push hook instead of a blocking hook
- Date: 2026-11-13
- Prompt: "it should nt be mass push it should be well documented"
- Context: the rule needs to apply to every repo on this PC, including pushes made by a human
  at the keyboard and by harnesses other than MiniMax Code.
- Options:
  - Blocking global hook — a push fails until the docs are written. Breaks unrelated work.
  - Warn-only global hook — the push proceeds and prints the gaps. Can be ignored.
  - No global hook, agent-only. Misses pushes made outside an agent.
- Chosen: warn-only global hook. The user asked for enforcement that never blocks, and a
  blocking hook would break every repo on the machine for a documentation gap.
- Evidence: `git config --global --get core.hooksPath` -> `C:/Users/ADMIN/.githooks`;
  scratch-repo push printed WARN lines and still exited 0.
- Consequence: the rule is visible everywhere but never stops a push; repair is the response.
```

## Change inventory row — `docs/reviews/change-inventory.md`

One row per changed file. Every changed file appears exactly once — including this file and the
decision log.

```markdown
| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/SKILL.md` | New skill: the push-time documentation contract | The rule must be installable on any harness, not remembered | Read frontmatter + ran `/aswath-commit-discipline` through the router |
```

Keep it one row per file. A row that describes a directory is a mass dump; split it.

## New skill record — `docs/reviews/new-skill.md`

For every skill added, changed or removed, write one block:

```markdown
## <skill-name>
- Question it answers: <the question a user brings to it>
- Triggers: <the phrases and situations that should load it>
- Scripts and resources: <what ships beside SKILL.md>
- Depends on: <other skills it names>
- Verified by: <the exact command or session that proved it works>
```

## Prompt record — `docs/reviews/prompts.md`

The `aswath-chronicle` skill writes this record. If it is not running, write it by hand:

```markdown
## <YYYY-MM-DD> — <session label>
- Prompt: "<verbatim>"
- Decision it produced: <D<n> reference or short summary>
- Work it caused: <files changed, commits made>
```

## Build log — `BUILDLOG.md`

The running narrative of what shipped, when, and where. Keep it beside `docs/reviews/`, never
instead of it.
