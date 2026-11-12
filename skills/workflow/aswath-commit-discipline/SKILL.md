---
name: aswath-commit-discipline
description: Use when work is about to be committed or pushed to GitHub, when the user says "push to GitHub", "mass push", "commit per meaningful work", "well documented commit", or when a change set needs its decisions, edits, prompts and new skills written down before it leaves the machine. Enforces the standing rule that every decision spoken with an AI, every edit, every prompt and every skill added is documented in detail and then committed and pushed. The commit count is free; the detail is not.
---

# ASWATH commit discipline

The rule, in one line: **every decision spoken with an AI, every edit, every prompt and every
skill added is documented in detail, then committed and pushed.**

"Mass push" does not mean *many commits*. It means *undocumented* work reaching GitHub. A hundred
commits, each documented, is compliant. One undocumented dump of forty files is not. Commit
granularity is a soft preference; documentation completeness is the gate.

Nothing here blocks. The skill, the agent hooks and the global git hook all warn. Repair is
always the response to a warning, never a refusal to push.

## When to use

- A change set is about to be committed, pushed, or opened as a pull request.
- The user says "push to GitHub", "commit this", "open a PR", "ship it", "mass push".
- A skill was added, changed or removed in this repo.
- You are reviewing your own diff before handing it over.

## The contract

Five obligations. All five, every time.

1. **Every decision is documented.** A decision is a choice with real alternatives. Each one gets
   an entry in `docs/reviews/decision-log.md` — including a decision that came out of a
   conversation with an AI. The prompt that produced the decision is part of the entry.
2. **Every edit is documented.** Every file that changed gets exactly one row in
   `docs/reviews/change-inventory.md`: what changed, why, how it was verified.
3. **Every prompt is recorded.** The prompts that shaped the work are logged. `aswath-chronicle`
   already keeps that record — name it, do not duplicate it.
4. **Every new skill is documented.** A new skill answers a question, has triggers, may ship
   scripts, and needs a note on how it was verified.
5. **Then it is pushed.** Documented but unpushed is unfinished. Push on explicit instruction,
   branch first, never amend a published commit, never force-push a shared branch.

Commit granularity is free. One commit per meaningful unit is preferred; many small commits are
fine; one commit is fine when the unit is one. The measure is documentation detail, never commit
count.

## Where the records live

| Record | Path |
|---|---|
| Decisions | `docs/reviews/decision-log.md` |
| Changed files | `docs/reviews/change-inventory.md` |
| Prompts and choices | `docs/reviews/prompts.md` (or the `aswath-chronicle` record) |
| Build log | `BUILDLOG.md` beside the docs tree |

One docs tree: `docs/reviews/`. Do not invent another.

Templates for every record shape are in
[`reference/record-templates.md`](reference/record-templates.md).

## Procedure

1. **Inventory.** `git status -s`, `git diff --stat`. Read every changed file, not only the diff.
2. **Verify.** Run the suite that covers the change. Record the exact command and its result.
3. **Decision log.** Append entries to `docs/reviews/decision-log.md`, oldest first. One entry per
   real choice, with the prompt that produced it.
4. **Change inventory.** Write or extend `docs/reviews/change-inventory.md`, one row per changed
   file. Every changed file appears exactly once — including the doc files themselves.
5. **Split the change set.** One meaningful unit per commit where the units are separable. Use
   `git reset --soft HEAD~<n>` and recommit per unit when a commit mixes units. Never amend a
   commit that is already published.
6. **Commit.** Conventional subject, a body that says what and why, and the repo's co-author
   trailer.
7. **Push.** Branch first, then push, then open the PR if one was asked for.

## Push-time checklist

Before `git push`, every box is ticked:

- [ ] Every decision in this change has a `decision-log.md` entry, with its prompt.
- [ ] Every changed file has a `change-inventory.md` row, with how it was verified.
- [ ] Every prompt that shaped the work is logged.
- [ ] A new skill records its question, triggers, scripts and verification.
- [ ] Each commit has a real subject and a body that carries the reasoning.
- [ ] The branch is up to date with its remote and has no local commits left behind.
- [ ] Nothing is pushed that the docs do not cover.

## What the checker warns about

`scripts/check_push.py` inspects the range a push would carry. Read-only git commands only, always exits 0.
One read-only network call (`git ls-remote --heads`) per branch, to learn what the remote really has; local
remote-tracking refs alone are not enough, because a repo whose fetch refspec covers one branch only keeps
no tracking ref for the others and looks unpushed right after a successful push.

| Code | Meaning |
|---|---|
| `NO_DECISION_DOC` | Non-doc files changed, but the decision log was not updated in the range. |
| `NO_INVENTORY_DOC` | Files changed, but the change inventory was not updated in the range. |
| `UNCOVERED_FILE` | A changed file has no row in the current change inventory. |
| `UNDOCUMENTED_COMMIT` | A commit has no body, or a body under 20 characters. |
| `PLACEHOLDER_SUBJECT` | Subject is `wip`, `fixup`, `squash`, `tmp`, `asdf`, `test commit`. |
| `PROMPT_NOT_LOGGED` | The range changes skills or docs but carries no prompt/decision record. |
| `UNPUSHED_WORK` | Local commits sit on a branch with no upstream, or ahead of its upstream. |
| `DIRTY_AT_PUSH` | The working tree has uncommitted changes while a push runs. |

File and line counts per commit are printed as information only, to help judge granularity.
Commit count is never a finding.

Run it by hand:

```
python <skill>/scripts/check_push.py --repo <repo path>
```

## Harness coverage

The rule reaches every AI harness on this PC in three layers. Nothing in any layer blocks.

| Layer | Where | What it does |
|---|---|---|
| Skill | this file | The contract, the procedure, the records. Loaded on demand by any harness that can read skills. |
| Agent hooks | `scripts/hook.py`, wired into each harness config | States the contract when a prompt looks like commit/push work, and reports the checker's gaps before a `git commit` or `git push` runs. |
| Git hook | `~/.githooks/pre-push` (`core.hooksPath`) | The floor: the checker runs on every push in every repo on this PC, including pushes by a human. |

### The shared runner

`scripts/hook.py` is one script for every harness that speaks a stdin/JSON hook protocol.

- **Prompt events** (`UserPromptSubmit`, `beforeSubmitPrompt`): when the prompt matches commit,
  push, GitHub, PR, branch, merge, publish, ship or documentation words, the contract from
  `reference/contract.txt` is printed to stdout as context.
- **Tool events** (`PreToolUse`, `beforeShellExecution`): when the command matches `git commit` or
  `git push`, `scripts/check_push.py` runs and its output is printed to stdout and to stderr.
- **Cursor** shell events answer with `{"permission": "allow", "userMessage": "..."}`, so a
  documentation gap never refuses a command.
- Every path exits 0. A malformed payload, a missing file or an unexpected exception exits 0
  silently — a hook must never break a session.

| Harness | Config | Events used |
|---|---|---|
| MiniMax Code | `~/.minimax/hooks.json` | `UserPromptSubmit`, `PreToolUse` (PowerShell hook) |
| Claude Code | `~/.claude/settings.json` | `UserPromptSubmit`, `PreToolUse` (`Bash`) |
| Codex | `~/.codex/hooks.json` | `UserPromptSubmit`, `PreToolUse` (`Bash`) |
| Cursor | `~/.cursor/hooks.json` | `beforeSubmitPrompt`, `beforeShellExecution` (`^git\s+(commit\|push)`) |
| Command Code | `~/.commandcode/settings.json` | `UserPromptSubmit`, `PreToolUse` (`bash\|powershell`) |
| Continue, Trae, Roo, Kiro, Qoder, CodeBuddy, Augment, iFlow, Junie, Zcode, Grok, Vibe, OpenClaw | `~/.<harness>/skills/` | no hook surface — skill link plus the global git hook |
| MiniMax app | `~/.minimax/skills/` | curated skills dir — skill link |

### Installing the wiring

```
python <skill>/scripts/install_harness_wiring.py --dry-run   # report only
python <skill>/scripts/install_harness_wiring.py             # apply
```

The installer is idempotent: it adds the hook groups only when they are absent, backs each config
up once as `<file>.pre-commit-discipline.bak`, and creates the skill junctions for the harnesses
that have no hook surface.

## Repairing a bad push

Work that was already pushed badly is not lost; document it forward.

- **Unpushed, mixed commit.** `git reset --soft HEAD~1`, write the decision entry and inventory
  rows, recommit per unit.
- **Already pushed.** Never amend a published commit. Add a follow-up commit that writes the
  missing decision entry and inventory rows, and say in the body that it repairs the record for
  commit `<sha>`.
- **Unpushed work on another branch.** Push that branch, or merge it first. Documented but
  unpushed is unfinished.

## Relation to the other skills

Named, never path-imported:

- `aswath-commit` writes the decision log and the change inventory at commit time. This skill is
  the push-time gate over the same records, and adds the prompt record and the new-skill record.
- `aswath-chronicle` keeps the persistent prompt/choice trail. Use it; do not re-log prompts here.
- `aswath-publish-github` owns the branch, secret scan, push and PR mechanics.

## Red flags

| Thought | Reality |
|---|---|
| "It is 40 commits, that is fine" | Commit count is not the metric; documentation is. |
| "I will explain it in the chat" | Chat is not the record. Write it to `docs/reviews/`. |
| "The diff already shows what changed" | The diff shows what. The record shows why. |
| "The hook warned, so I cannot push" | Nothing blocks. Write the missing records, then push. |
| "One commit for the whole branch" | One commit per meaningful unit where units are separable. |
| "This skill is obvious, no record needed" | A new skill needs its question, triggers and verification. |
| "It is already pushed, never mind" | Never amend a published commit; add the record in a follow-up. |
