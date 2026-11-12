# Decision log

One entry per real choice. Oldest first. A decision is a choice with alternatives; facts and
diff restatements are not decisions.

Template: `skills/workflow/aswath-commit-discipline/reference/record-templates.md`.

---

## D1 — One machine-wide rule, delivered as a skill plus warn-only hooks

- Date: 2026-11-13
- Prompt: "i always to told you whenever you push something in github it should nt be mass push
  it should e well documented a commit for evy meaning ful work or decision make its skill and tell
  me how can plug it into all ai agents in our computer"
- Context: the rule the user lives by — nothing reaches GitHub undocumented — was a spoken
  habit. It had to become machine state, and it had to work for every AI harness on this PC.
- Options:
  - Rewrite `~/.claude/CLAUDE.md` only. Only Claude Code sees it, and it is prose, so it drifts.
  - One skill in the shared skills repo, invoked by hand. Machine-independent but never fires
    unless the agent remembers to call it.
  - A skill plus soft hooks in each harness plus a global git hook. Layered, warn-only.
  - A blocking global git hook. Cannot be bypassed, but breaks unrelated work.
- Chosen: a skill in the `aswath-skills` repo plus warn-only hooks. The skill holds the contract
  and is reusable across harnesses; the hooks deliver it at the moment it matters (before a
  commit or a push); the global git hook is the floor that holds even for a human at the
  keyboard. Nothing blocks, because the user's rule is about quality, not about stopping work.
- Evidence: `~/.claude/CLAUDE.md` names the skills repo as the canonical home for `aswath-*`
  skills; the mcode hook contract (`references/hooks.md` in the runtime) documents `UserPromptSubmit`
  context injection on stdout with exit 0, and `PreToolUse` exit 2 for blocking; the user
  questionnaire answered "warn only, never block" for both the agent hooks and the git hook.
- Consequence: enforcement is layered and advisory. A warning that is ignored is the failure
  mode, so the messages name the exact missing record.

## D2 — "Mass push" means undocumented work, not many commits

- Date: 2026-11-13
- Prompt: "it should nt be mass push it should be well documented a commit for evy meaning ful
  work or decision make"
- Context: the first reading of the rule was "fewer commits". The user then stated that 100 or
  1000 commits are fine. What is forbidden is undetailed work reaching GitHub.
- Options:
  - Keep commit count as the gate. Would have flagged legitimate small-commit workflows.
  - Drop all counting and gate on documentation only.
- Chosen: gate on documentation only. The checker reports file and line counts per commit as
  information so a reviewer can judge granularity, and never reports commit count as a finding.
- Evidence: the checker's warning list contains no commit-count code; `PLACEHOLDER_SUBJECT` and
  `UNDOCUMENTED_COMMIT` judge the commit's message, not how many commits there are.
- Consequence: the metric is documentation detail. Splitting a change set per unit stays a soft
  preference stated in the skill text, not a machine gate.

## D3 — Checker in Python 3 stdlib, warn-only, always exit 0

- Date: 2026-11-13
- Prompt: "Implement this plan"
- Context: the check runs from a git `pre-push` hook and from a PowerShell agent hook. It must
  be fast, dependency-free, and must never break a push.
- Options:
  - Python script with stdlib only. `python` is on PATH (3.13.1 verified).
  - A PowerShell implementation, called from the sh hook via `powershell.exe -File`.
  - A compiled binary.
- Chosen: Python 3 stdlib. One implementation serves both hooks; the sh hook calls it directly and
  the PowerShell hook calls it with `& python`. It exits 0 on every path, including its own
  internal exception handler, so no repository can be blocked by it.
- Evidence: `python --version` -> `Python 3.13.1`; the script's `except Exception` branch prints
  a warning and returns 0.
- Consequence: the hook is a floor, not a gate. Repair is the response to every warning.

## D4 — Phase 1 covers MiniMax Code only; other harnesses come after review

- Date: 2026-11-13
- Prompt: questionnaire answer — "start with mcode, then expand"
- Context: the user asked how to plug the rule into all AI agents on the computer. The other
  harnesses each have their own hook schema (Claude Code `PreToolUse` on `Bash`, Codex
  `hooks.json`, Cursor `beforeShellExecution`, Command Code `journal-commit.py`), and the plain-dir
  harnesses have no hook surface at all.
- Options:
  - Wire every harness now in one change.
  - Wire MiniMax Code plus the harness-independent global git hook first, verify, then extend.
- Chosen: phase 1 covers MiniMax Code and the global git hook, which already applies to every
  repo regardless of harness. The remaining harnesses are phase 2, after the user confirms phase
  1 works.
- Evidence: the approved plan snapshot lists the phase 2 harness surfaces one by one.
- Consequence: the rule already holds for any repo on this PC via the git hook; the phase 2 work
  adds earlier, in-session reminders for the other harnesses.

## D5 — The skill lives in `aswath-skills` and is mirrored by junctions, not copies

- Date: 2026-11-13
- Prompt: "Implement this plan"
- Context: `~/.claude/CLAUDE.md` names the skills repo as the canonical home for `aswath-*` skills.
  The store `~/.agents/skills` already mirrors `aswath-commit` by junction to the repo path, and
  `~/.agents/skills-active` mirrors the store by a second junction.
- Options:
  - Copy the skill into each harness directory.
  - Junction the repo path into the store, then the store into the active set.
- Chosen: the same two-junction chain that `aswath-commit` already uses. Edits in the repo are
  seen by every harness; the active-set junction is what makes `/aswath-commit-discipline`
  resolve in MiniMax Code.
- Evidence: `Get-Item` on the existing `aswath-commit` junctions shows the identical target
  pattern; `~/.minimax-code/skills` is itself a junction to `~/.agents/skills-active`.
- Consequence: the skills repo is the single edit point. `install.ps1` already links every
  skill directory, so it needs no change.

## D6 — The task's own commits obey the rule it installs

- Date: 2026-11-13
- Prompt: "Implement this plan"
- Context: shipping a documentation-discipline skill without documenting that skill would be the
  exact failure the skill exists to prevent.
- Options:
  - Ship the skill and document it later.
  - Write the decision log and the change inventory before the first commit.
- Chosen: write `docs/reviews/decision-log.md` and `docs/reviews/change-inventory.md` in the
  skills repo before committing. That repo had no `docs/reviews/` tree, so this work creates it.
- Evidence: the decision log above and the change inventory beside it; both are committed with
  the work they describe.
- Consequence: the rule ships with a worked example in the repo that enforces it.

## D7 — The checker asks the remote, not the local remote-tracking refs

- Date: 2026-11-13
- Prompt: "Implement this plan" (verification phase of the same task)
- Context: after the first real push of `feat/aswath-commit-discipline`, the checker still warned
  `UNPUSHED_WORK` on that branch: "has no upstream and holds commits no remote has". The push had
  succeeded and the remote head was exactly the local tip. The cause was the repo's fetch
  refspec, which covers one branch only (`+refs/heads/main:refs/remotes/origin/main`), so git kept
  no remote-tracking ref for the feature branch. `git rev-list <branch> --not --remotes` therefore
  counted the pushed commits as unpushed. A false positive on the very first push is the worst
  place for it: it teaches the user to ignore the warning.
- Options:
  - Keep the local-only check and accept the false positive on narrow-refspec repos.
  - Ask the remote for its heads (`git ls-remote --heads`, read-only) and treat the remote as the
    authority, falling back to the local tracking refs when the remote is unreachable.
  - Fetch the missing tracking refs, which writes to the repo and contradicts the read-only
    contract of the checker.
- Chosen: option 2. The checker now resolves the branch's configured remote and remote branch from
  git config (independent of the tracking ref), lists the remote heads once, and compares the local
  tip against the remote head. Squash-merged branches are still recognised through `git cherry`,
  now run against the remote head rather than against the tracking ref.
- Evidence: the false positive was reproduced live (`git rev-parse --abbrev-ref @{u}` failed with
  "upstream branch not stored as a remote-tracking branch", `git ls-remote --heads origin` showed
  the pushed head, and the checker warned anyway) and disappeared after the fix. The checker now
  reports no `UNPUSHED_WORK` for the pushed branch.
- Consequence: the checker makes one read-only network call per branch. It stays warn-only and
  still exits 0. When the remote cannot be reached it falls back to the local tracking refs, which
  is the old behaviour.
