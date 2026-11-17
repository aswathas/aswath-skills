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

## D8 — The range must be the commits the push would actually carry

- Date: 2026-11-13
- Prompt: "Implement this plan" (verification phase of the same task)
- Context: the scratch-repository proof showed the checker going quiet on a push it should have
  reported. A brand-new branch in a repo whose fetch refspec covers one branch only has no upstream
  and no remote-tracking ref, so the range fell back to the local branch itself. The base then
  pointed at HEAD, the range was empty, and every documentation finding was skipped. The second
  defect sat in the same place: with no base, the file list came from a diff of HEAD against the
  working tree, and a clean working tree produced no files at all.
- Options:
  - Leave the range as it was and rely on the agent to write the records anyway.
  - Make the range resolution mirror what the push carries: skip a candidate base that resolves to
    HEAD, and fall back to the commits that are on no remote.
- Chosen: option 2. A candidate base whose sha equals HEAD's sha is skipped, because it makes the
  range empty. When no remote reference can be used, the range is the newest commit that no remote
  has, and with no lower bound the file list is a diff against git's empty tree.
- Evidence: in the scratch repository, before the change the checker reported one warning (the
  unpushed work) for a push that changed a file with no records at all; after the change it reports
  `NO_DECISION_DOC` and `NO_INVENTORY_DOC` for the same push. The documented case is silent again
  once the records exist, and a range of forty documented commits produces no finding.
- Consequence: the checker is quiet only when the records are actually there. The cost is that a
  first push of a new branch now reports what it is missing, which is the point of the rule.

## D9 — One shared hook runner for every harness, not one script per harness

- Date: 2026-11-13
- Prompt: "finish all" (phase 2 of the same task: "plug it into all ai agents in our computer")
- Context: phase 1 covered MiniMax Code and the global git hook. Phase 2 had to reach Claude Code,
  Codex, Cursor and Command Code. Four harnesses, four dialects on top of one shared stdin/JSON
  envelope: Claude-style hook groups keyed by event name, Cursor's flat per-event list that answers
  with a JSON verdict, Command Code's `bash|powershell` shell-tool matcher, and Codex's
  `UserPromptSubmit` / `PreToolUse` pair.
- Options:
  - One hook script per harness, written in that harness's dialect. Four copies of the same warning
    logic; the texts and the codes drift apart.
  - One shared runner that reads the payload and branches on the event name, wired into every
    config. One copy of the logic; the harness-specific part is the config entry.
  - Wire only the harnesses that share one dialect and leave Cursor and Command Code on the global
    git hook alone. Half the coverage.
- Chosen: option 2. `scripts/hook.py` is the single runner. It reads `hook_event_name` and looks for
  a command in `tool_input` or at the top level, so one code path serves all four payload shapes.
- Evidence: 11 payload cases pass against the shared runner — Claude, Codex and Cursor prompt hits,
  a Claude prompt miss, a Claude `PreToolUse` git push in a scratch repo, a Cursor
  `beforeShellExecution` JSON verdict, a Command Code payload, a non-git command, a malformed
  payload, raw malformed JSON and empty stdin. Every case exits 0.
- Consequence: one fix to the warning text reaches every harness at once. The cost is a known blind
  spot: the Codex, Cursor and Command Code event names were verified against the local payload
  shapes, not against those products' runtimes, so an event name that differs would fall through to
  the silent path.

## D10 — The hook warns and never denies

- Date: 2026-11-13
- Prompt: "finish all" (phase 2 of the same task)
- Context: the phase-1 rule is warn-only everywhere, but the new surfaces invite the stronger
  behaviour. Cursor's `beforeShellExecution` expects a permission verdict, and Claude Code's
  `PreToolUse` treats exit code 2 as a refusal.
- Options:
  - Return `permission: "deny"` on a documentation gap, or exit 2, so an undocumented push cannot
    run. Enforces the rule hard, but blocks work over a missing paragraph.
  - Warn only: plain text everywhere, exit 0 everywhere, and let the missing record be the
    response.
- Chosen: option 2. Cursor shell events get `{"permission": "allow", "userMessage": "<warning>"}`.
  The runner always exits 0, and every exception path exits 0 silently. For tool events the warning
  goes to stdout (the context channel) and to stderr (the channel Claude Code shows the user for a
  `PreToolUse` hook).
- Evidence: the payload test asserts exit 0 on every case and asserts the Cursor verdict's
  `permission` field is `allow`; the scratch-repo `PreToolUse` push case produced the checker output
  on both stdout and stderr.
- Consequence: the rule stays advisory end to end. A harness that shows only stdout sees the
  contract, one that shows only stderr sees the gap, and none of them can refuse a push.

## D11 — The contract text lives in one file

- Date: 2026-11-13
- Prompt: "finish all" (phase 2 of the same task)
- Context: the contract text is needed by the shared runner on a prompt event, by the mcode
  PowerShell hook and by the skill's own documentation. Three hand-maintained copies drift, and the
  skill's contract is the thing the whole system exists to enforce.
- Options:
  - Keep the text inside the runner script only. The mcode hook then has its own copy anyway.
  - Keep the text in the docs only. The runner would have to parse Markdown to find it.
  - One file, `reference/contract.txt`, read by the runner, with an inline fallback for the case
    where the file cannot be read.
- Chosen: option 3. The runner reads `reference/contract.txt` and falls back to a short inline
  copy if the read fails, so a missing file degrades to a weaker contract instead of to silence.
- Evidence: a prompt event printed the file's text, including the two lines the inline fallback does
  not carry ("One commit per meaningful unit is preferred, not required." and the checker command
  line). The first run of the runner looked for the file under `scripts/reference/` and silently used
  the fallback; the path was corrected to the skill root and the file's text then appeared.
- Consequence: editing the contract updates every harness that reads the file. The inline copy is a
  safety net, not a second source, and it is allowed to be shorter.

## D12 — One installer owns the wiring, and it is idempotent

- Date: 2026-11-13
- Prompt: "finish all" (phase 2 of the same task)
- Context: five config files and fourteen skill links had to be created on this PC. Hand-editing them
  is not reproducible on another machine, and a second hand-edit can duplicate a hook entry.
- Options:
  - Hand-edit the five config files and create the junctions by hand. Fast once, unreproducible.
  - One script per harness. Five scripts for one job.
  - One idempotent installer that wires every config and creates every link, with a dry-run mode and
    one-time backups.
- Chosen: option 3. `scripts/install_harness_wiring.py` adds the prompt hook and the pre-commit/push
  hook to each config, backs each file up once as `<file>.pre-commit-discipline.bak`, and creates the
  plain-dir junctions with `cmd /c mklink /J`. A second run finds the hook command already present
  and changes nothing.
- Evidence: the dry run listed every change; the applied run reported `wired` for all five configs
  and `linked` for the fourteen junctions; all five configs still parse as JSON and each backup file
  exists next to its config.
- Consequence: re-running the script after a harness reset or on a new machine is one command, and
  the backup files make a bad edit recoverable without a version-control history.

## D13 — The curated keep-list stays authoritative; `skillhub repair` is not run

- Date: 2026-11-13
- Prompt: "finish all" (phase 2 of the same task)
- Context: `skillhub status` reports five BROKEN Windows targets — `~/.claude/skills`,
  `~/.config/opencode/skills`, `~/.commandcode/skills`, `~/.hermes/skills` and
  `~/.minimax-code/skills` — each pointing at `~/.agents/skills-active` instead of the canonical
  store. The tool's own advice is to run `skillhub repair`, which would repoint all five at the full
  337-skill store and drop the user's curated 54-skill set.
- Options:
  - Run `skillhub repair`. The status report goes green, but the curated set is replaced by
    everything, and the user's choice of 54 skills is lost.
  - Leave the mismatch and accept five BROKEN lines in the status output.
  - Repoint by hand, link by link, keeping the curated set.
- Chosen: option 2 for now. The mismatch is deliberate: the 54-skill set in
  `~/.agents/skills-active.list.json` is the curated set the user chose, and `skills-active` is where
  those five harnesses read from. `skillhub repair` is not run.
- Evidence: `skillhub status` shows `9/14 windows targets OK` with the five BROKEN lines naming the
  `skills-active` target; the skill itself resolves under each of them, because the link points at a
  directory that contains it.
- Consequence: `skillhub status` stays noisy on this machine and its exit code stays non-zero. If
  the full store is ever wanted for those harnesses, the repair has to be a manual repoint that keeps
  the keep list, not `skillhub repair`.

## D14 — Harness configs point at the store path, not the repo path

- Date: 2026-11-13
- Prompt: "finish all" (phase 2 of the same task)
- Context: the canonical source of the skill is the skills repo, but a config entry must name a path
  that exists on this PC and survives the repo being moved, renamed or not checked out. The global
  `pre-push` hook already used `C:/Users/ADMIN/.agents/skills/aswath-commit-discipline/scripts/check_push.py`.
- Options:
  - Point at the repo path, `C:/Users/ADMIN/Projects/aswath-skills-wk/...`. One hop fewer, but the
    config breaks when the repo moves and forces the repo to be present on every machine.
  - Point at the store path, `C:/Users/ADMIN/.agents/skills/...`. The store entry is a junction into
    the repo, so the content is still canonical and the config outlives a repo move.
  - Put the hook on PATH and call it by name. Breaks if the PATH entry is missing.
- Chosen: option 2. Every harness config uses
  `python "C:/Users/ADMIN/.agents/skills/aswath-commit-discipline/scripts/hook.py"`, the same
  convention the global git hook uses.
- Evidence: all five configs contain that command twice (prompt hook and pre-commit/push hook); the
  store entry `~/.agents/skills/aswath-commit-discipline` resolves to the repo path; the runner
  executed from that path printed the contract and the checker's warnings.
- Consequence: the wiring survives a repo rename and works on a machine that has the store but not a
  checkout of the skills repo.
## D1 — A chat is a shelf, not a ledger: the delivery skill

- Date: 2026-11-14
- Prompt: "just delte unwanted messages in wahtsapp and give only perfectly final needed whenever
  you update or improve things remove unwated from whatsapp add this to our /aswath-delivery
  skill linked with /aswath-thevai create a enw skill"
- Context: work handed to a person on WhatsApp had accumulated four copies of the report, two
  dead links and a run of "sent, sorry, here it is again". The person had no way to tell which
  file was current, and the stale one was the one they opened. `aswath-thevai` already owns the
  first half of that conversation; nothing owned the last half.
- Options:
  - Add a rule to the global instructions. Applies everywhere but lives nowhere; it drifts and is
    not discoverable as a skill.
  - Fold the cleanup into `aswath-thevai`. One file, but a skill that does two jobs, and the
    description would need an "and" to be accurate.
  - A separate skill in the same category, joined to the thevai chain. One job each, the pair
    reads as the two ends of one conversation.
  - Put it in `publishing/` beside publish-github. That folder answers "how does this leave the
    machine" for public channels; this is one person on one private channel.
- Chosen: a separate `aswath-delivery` skill in `workflow/`, beside `aswath-thevai`, with the
  delete-first order, the rules about what stays and what goes, and a step at the end of the
  `thevai-a-request` workflow. Delete before sending, send once, remove the staging copies.
  The judgement note in `docs/categories.md` records why it sits with thevai and not with the
  publishing skills.
- Evidence: the skill is linked into `~/.claude/skills` and `~/.agents/skills` by `install.ps1`
  and resolves to the repo; the chain in `workflows/thevai-a-request.md` names it as step 4 with
  its gate; the chat it was written for now holds the current report and deck exactly once each,
  with the earlier copies and the stale status messages removed.
- Consequence: every delivery on a chat channel ends with one final state rather than a
  sequence, and the person never has to work out which file is the real one.
