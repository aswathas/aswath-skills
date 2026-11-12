---
name: aswath-commit
description: Use when a change set is ready to commit and the reasoning must be written down. Produces a decision log and a file-by-file change inventory, then commits. No mass dumps.
---

# ASWATH commit

Documentation is the deliverable, not a by-product. In the AI era a diff is cheap and unreviewable; the reasoning is what a future reader needs. One entry per decision, one row per changed file, each with why and how it was verified.

## When to use

- A change set is ready to commit and the reasoning is not already written down.
- A bug fix, feature or refactor where someone will later ask "why this way?".

## Procedure

1. **Inventory.** `git status -s`, `git diff --stat`, `git diff`. Read every changed file, not just the diff.
2. **Verify.** Run the suite that covers the change. Record the exact command and result.
3. **Decision log.** Append to `docs/reviews/decision-log.md`, oldest first.
   One entry per real choice:

   ```
   ## D<n> — <decision>
   - Date:
   - Context: what forced a choice
   - Options: the real alternatives
   - Chosen: what and why
   - Evidence: test or live proof, with the command or event
   - Consequence: what this locks in or blocks
   ```

   A decision is a choice with alternatives. Do not log facts, and do not restate the diff.
4. **Change inventory.** Write `docs/reviews/change-inventory.md`, one row per file:
   `| file | what changed | why | how tested |`
   Every changed file appears exactly once.
5. **Truth docs.** Update the capability checklist and the build log when reality
   changed. Never leave them stale.
6. **Commit.** `git add -A`, then a message via heredoc:

   ```
   <one-line summary>

   <2-5 lines: what changed and why>

   Co-authored-by: CommandCodeBot <noreply@commandcode.ai>
   ```

   Never amend a published commit.

## Rules

- No mass dump. If a line could be a diff line, delete it.
- Every decision names the alternatives it beat.
- Every claim carries its evidence: a command, a result, an event id.
- One docs tree: `docs/reviews/`, beside the build log. Do not invent another.
- A failed test goes in the log with its failure, not hidden.
- Document why, never what the code already shows.

## Red flags

| Thought | Reality |
|---|---|
| "I'll explain the change" | Explain the choice; the diff explains the change. |
| "I'll summarise the session" | A summary is a mass dump. Log decisions. |
| "Tests pass, no need to record" | The exact command and result is the evidence. |
| "Docs after merging" | Unwritten reasoning is lost reasoning. |
