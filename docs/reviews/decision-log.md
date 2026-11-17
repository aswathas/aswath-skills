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

## D2 — The catalogue and the manifest had drifted apart: publish both

- Date: 2026-11-17
- Prompt: "publissh all our skills in github ? actively do this"
- Context: the skills repo on `main` carried 20 skill folders but the manifest listed 19. The
  gap was `aswath-commit-discipline`: it landed through PR #4 as a squash merge, and the squash
  kept the skill folder and the README row but dropped the manifest row. The manifest is what
  `install.ps1` reads and what the catalogue counts, so the skill was installed by link but
  invisible to the catalogue. Two further branches were also unpublished: `aswath-delivery`
  (PR #9, open since 2026-11-14) and the closed duplicate PR #6, whose change had already
  merged as PR #7 with an identical tree.
- Options:
  - Add every skill folder that exists. Wrong: the folders include the ones the maintainer
    keeps for reference, and the manifest is a catalogue with a rule per entry, not a dump.
  - Leave the manifest as it is and treat the folder list as truth. Leaves the installer and the
    catalogue disagreeing, which is the state that caused the drift.
  - Add the one missing row, land the open delivery PR, close the duplicate, and say plainly in
    the catalogue what each entry promises.
- Chosen: option 3. One row for `aswath-commit-discipline` in `workflow`, version bumped to
  1.2.0, `updated` set to today; PR #9 merged (squash, the house style); PR #6 closed as the
  duplicate of the already-merged PR #7; local `main` reset to `origin/main` because its extra
  commit `ecb0fe6` had an identical tree to the merged `ef5ec17`.
- Evidence: `git show origin/main:manifest.json` listed 19 rows against 20 skill folders before
  the change and 21 after; every row's `path` resolves to a `SKILL.md` that exists; `gh pr view
  9` reported `MERGEABLE`/`CLEAN` before the merge and the branch head `f20123e` is on
  `origin/main` after it; `git diff ecb0fe6 ef5ec17` is empty.
- Consequence: the catalogue, the installer and the folder tree now agree, and the repo's own
  publishing rule ("a skill that is not in the manifest is not published") can be checked by
  reading one file.

## D3 — The impeccable hook failed because the launcher could not find itself

- Date: 2026-11-17
- Prompt: "why is this impeccbale hook error coming?"
- Context: every Claude Code session printed `impeccable: no engine binary for windows-x64
  found ... exit 127`. The skill ships its own engine at
  `scripts/bin/windows-x64/impeccable.exe`, so the engine was never missing. The launcher
  derives its own directory from `$0` with a forward-slash match (`case $0 in */*) dir=${0%/*}
  ;; *) dir=. ;;`), and the hook passed `C:\Users\ADMIN\...\impeccable` — a path with no forward
  slash. The launcher therefore fell back to `dir="."`, kept the hook's working directory, and
  never found its own `VERSION` file or the engine beside it.
- Options:
  - Download the engine again. Treats the symptom; the engine was already there.
  - Point the hook at `impeccable.cmd`. Works, but the Windows launcher is a second code path
    for the same job.
  - Give the launcher a path it can parse: forward slashes.
- Chosen: option 3. The three hook commands in `~/.claude/settings.json` now call
  `/c/Users/ADMIN/.claude/skills/impeccable/scripts/impeccable`.
- Evidence: the old command run by hand printed the "no engine binary" message and exited 127;
  the same command with forward slashes printed nothing and exited 0; running the command
  straight out of the parsed `settings.json` after the change also exits 0 with empty stderr.
- Consequence: the UI-check hook stops failing on every prompt, and no engine is downloaded for
  a binary that was on disk all along.

## D4 — Work lands in units: one commit and one push per unit

- Date: 2026-11-17
- Prompt: "if am doing a project or any work the push should have lot / multiple commits
  meaning ful commits every step needs to docuemnated or commited not bulk single push if
  design an app with 4 feature each feature and its builds shodl be commited in a way that
  we planned"
- Context: the contract said "commit granularity is free, one commit per meaningful unit is
  preferred". A preference does not change behaviour: the same forty-file branch still
  arrives as one commit and one push, because nothing in the contract or the checker objects.
  The user asked for a rule, not a preference — "if design an app with 4 feature each
  feature and its builds should be committed in a way that we planned".
- Options:
  - Keep granularity as a soft preference and rely on the agent's judgement. Cheap, but the
    failure mode the user described stays open: a bulk single push is still possible.
  - Make per-unit commits and per-unit pushes mandatory whenever the brief has separable
    parts, and plan the units in writing before the first commit.
  - Make the commit count a fixed number. Wrong measure: it would reward 20 empty commits
    over 4 real ones, and the existing decision D2 already ruled the count out as the metric.
- Chosen: option 2. The contract now has six obligations; the sixth says a brief with
  separable parts gets a written unit plan, each unit is committed when it is done, and each
  unit is pushed as it lands.
- Evidence: the change itself is built under the new rule —
  `docs/reviews/delivery-plan.md` lists three units, each unit is its own commit with its own
  subject from the plan, and each commit carries its own records.
- Consequence: "bulk single push" stops being a style preference and becomes a documented
  violation of the contract, which the checker can see.

## D5 — The unit plan is written before the first commit

- Date: 2026-11-17
- Prompt: "each feature and its builds shodl be commited in a way that we planned"
- Context: "in a way that we planned" means the units are decided up front, not split out of
  the finished diff afterwards. A plan reconstructed from a finished branch is a description,
  not a plan: it cannot show that the work was sequenced, and it cannot be checked.
- Options:
  - Write the plan before the first commit, in `docs/reviews/delivery-plan.md`, with the
    exact commit subject per unit. Checkable: a subject in the range can be matched against
    the plan.
  - Keep the plan in the chat. Not a record, and it dies with the session.
  - Keep the plan only in the commit history. The subject is there, but the mapping from
    unit to subject is not, and a dropped unit leaves no trace.
- Chosen: option 1, one file, one row per unit, with the `Commit` column holding the exact
  subject. The file is written before the first commit of the work.
- Evidence: `docs/reviews/delivery-plan.md` in this change names three units and the exact
  subject of each unit's commit; the checker reads the same column.
- Consequence: the plan is a reviewable artefact. A unit that was dropped says so; a unit
  that was never committed is visible as a gap.

## D6 — Build-time prompts get the short delivery rule, not the full contract

- Date: 2026-11-17
- Prompt: "if am doing a project or any work the push should have lot / multiple commits
  meaning ful commits every step needs to docuemnated or commited not bulk single push"
- Context: the unit rule only matters if it reaches the agent while the work is being
  planned. The hook already prints the full contract on shipping prompts (commit, push,
  PR, branch). At the moment a build starts, those words are absent, so the contract was
  silent exactly when the units should have been decided.
- Options:
  - Print the full contract on build-time prompts. Correct content, but the full contract
    is push-time text; it pushes the agent toward writing records at the wrong moment.
  - Print a short delivery rule from a separate file on build-time prompts, and keep the
    full contract for shipping prompts. Two files, each with one job.
  - Leave the hook alone and rely on the skill being loaded. The skill is loaded on demand;
    a build that never asks about commits never loads it.
- Chosen: option 2. `reference/delivery.txt` holds the short rule, `reference/contract.txt`
  keeps the full one, and `hook.py` picks between them by prompt shape.
- Evidence: a replayed `UserPromptSubmit` with the prompt "build me a login screen" printed
  the delivery rule; "now push it" printed the full contract. Both replays ran the hook
  from the repo copy with `python -m py_compile` clean first.
- Consequence: the rule reaches the agent at planning time, and the long contract is only
  spent when it is relevant.

## D7 — The plan governs the work it was written for, and nothing older

- Date: 2026-11-17
- Prompt: "if am doing a project or any work the push should have lot / multiple commits
  meaning ful commits every step needs to docuemnated or commited not bulk single push if
  design an app with 4 feature each feature and its builds shodl be commited in a way that
  we planned"
- Context: the plan names the commits the work is made of, so the checker can compare the
  range against it. But a plan is a file in the repository: once this change merges, the
  plan is on `main` forever. If every later branch is checked against it, every later
  commit on every later branch is "unplanned" — the checker cries wolf on work it has
  nothing to do with, and a warning nobody reads is worth nothing.
- Options:
  - Always apply the plan on every push. Simple, but every branch after this one warns
    about every commit it makes.
  - Apply the plan only when the plan file changed in the range. Precise, but a unit
    commit that forgot to update the plan escapes the check entirely — the non-compliant
    case is the one that would go unchecked.
  - Apply the plan when it changed in the range, or when the plan does not exist at the
    point the branch forked from. The second half covers the branch that wrote the plan
    and never touched it again.
- Chosen: option 3. `plan_governs_range()` asks two questions: did the plan change in
  this range, and does the plan exist at the fork point? A plan that arrived with an
  earlier merge governs that merge only.
- Evidence: in a scratch repository the plan was merged to `main` and a later branch made
  an unrelated commit — the checker reported no `COMMIT_NOT_PLANNED` and no
  `UNIT_NOT_COMMITTED` for it. In the same scratch repository, on the branch that wrote
  the plan, all three new warnings fired.
- Consequence: the check is silent on unrelated work and loud on the work that wrote the
  plan.

## D8 — A bulk commit is measured by size, and the size limits live in the rules file

- Date: 2026-11-17
- Prompt: "not bulk single push"
- Context: "bulk" has to become something the machine can see. The obvious candidate is
  the commit count, and that is the wrong measure: decision D2 already ruled it out,
  because a fixed count rewards twenty empty commits over four real ones.
- Options:
  - A fixed number of commits per push. Wrong measure, already rejected.
  - A size limit on a single commit: files touched and lines changed. A commit that
    touches thirty files or changes two thousand lines is carrying more than one unit.
  - A size limit on the whole range. Same failure as a commit-count limit, only slower.
  - No size limit at all. The rule stays a sentence an agent may forget.
- Chosen: option 2, with the thresholds in `reference/doc-rules.json` — 30 files and 2000
  lines — so a repository can move them without editing the checker. The size of every
  commit is already computed for the informational line; the warning reuses it.
- Evidence: a scratch commit touching 32 files produced
  `WARN BULK_COMMIT: commit 19af649 carries 32 file(s) and 33 line(s), over the bulk
  thresholds (30 files / 2000 lines); split it into units`. This change's own commits
  carry 10 files and 5 files, under the thresholds.
- Consequence: the warning points at the split, not at the count, and the numbers that
  decide it are visible in one file.

## D9 — Housekeeping commits are exempt from the plan match

- Date: 2026-11-17
- Prompt: "if am doing a project or any work the push should have lot / multiple commits
  meaning ful commits every step needs to docuemnated or commited not bulk single push"
- Context: a branch carries more than its units. A commit that fixes a typo in the README,
  bumps a dependency, or renames a CI workflow is not a unit of the work, and it will
  match no row in the plan. Without an exemption the checker reports it as unplanned
  work, and a warning that fires on the ordinary commits of every branch is a warning
  that gets ignored.
- Options:
  - No exemption. Every commit must be a unit. Simple, and noisy on honest housekeeping.
  - Exempt commits whose subject starts with `docs`, `chore` or `ci`. Housekeeping by
    convention, and the three prefixes are the ones the repo's own history already uses.
  - Exempt any commit whose subject does not look like a feature. Judging by wording
    instead of by convention: too fuzzy to check.
- Chosen: option 2. The prefixes are `docs`, `chore` and `ci`. Anything else that matches
  no unit is reported.
- Evidence: in the scratch repository the commit `chore: housekeeping` produced no
  `COMMIT_NOT_PLANNED`, while `feat(y): unplanned work` in the same range produced one.
- Consequence: the check reports the commits that carry work, and stays quiet on the ones
  that do not.

## D10 — The checker is verified by a stdlib script, not by a test framework

- Date: 2026-11-17
- Prompt: "if am doing a project or any work the push should have lot / multiple commits
  meaning ful commits every step needs to docuemnated or commited not bulk single push"
- Context: the three new warnings were verified by hand, in scratch repositories written
  into a temp directory and thrown away. That proves they work once. Nothing in the repo
  would run them again, so the next change to the checker could break them silently.
- Options:
  - pytest. The usual choice, and it needs a dependency the repo does not have, plus a
    config file for one file of tests.
  - `unittest` from the standard library. No dependency, but the scratch repository and
    its git history have to be built inside test-case boilerplate.
  - A plain script that builds scratch repositories, runs the real checker against them
    and asserts on the output. Standard library only, one file, readable top to bottom.
  - Leave the manual runs as the verification. Not repeatable, and the manual run is not
    in the repo for the next person to run.
- Chosen: option 3. `scripts/test_check_push.py` builds a scratch repository per case in a
  temp directory, runs the real `check_push.py` against it, and asserts on the warnings.
  Exit 0 when every case holds.
- Evidence: `python skills/workflow/aswath-commit-discipline/scripts/test_check_push.py`
  printed `5/5 case(s) passed` and exited 0. The cases cover a compliant branch, a 31-file
  commit, a commit matching no unit, a `chore:` commit, a unit marked done with no commit,
  and a branch that inherited a plan from `main`.
- Consequence: the checker's behaviour is reproducible by anyone with Python, and the
  scratch repositories never touch the working tree.

## D11 — The catalogue states the unit rule, and the manifest version moves to 1.3.0

- Date: 2026-11-17
- Prompt: "i want to updte aswath documentaion skill"
- Context: the catalogue is what a reader scans before loading a skill. The manifest
  description and the README row still described the old contract — documentation
  completeness, and a free commit count. They were not wrong, but they no longer said
  what the skill does, and the README is the page most people read.
- Options:
  - Leave the catalogue alone. The descriptions stay true, but they no longer mention the
    plan, the units or the push-per-unit rule.
  - Update the manifest description and the README row to state the unit rule, and leave
    the version alone. The catalogue changes without a version to point at it.
  - Update both and bump the manifest version from 1.2.0 to 1.3.0.
- Chosen: option 3. The manifest description now mirrors the skill's frontmatter
  description, the README row states the unit rule, and the version is 1.3.0 with
  `updated` at today's date.
- Evidence: `manifest.json` parses as JSON and carries `"version": "1.3.0"`; the row for
  `aswath-commit-discipline` names `docs/reviews/delivery-plan.md`; the README row names
  the same path.
- Consequence: the catalogue and the skill describe the same contract, and the version
  records that the contract changed.

## D12 — The runtime spec: eight gaps, four skills, and one gate the loop cannot skip

- Date: 2026-11-17
- Prompt: "so how can we solve this in our system", "i want to create a engine like swamp which
  can learn and update this", "tell us our gaps in simple words", "how to solve thiss", and four
  answers: the skill code is public and the data is private; all eight gaps in one spec; the
  ledger lives in the private store and is git-tracked; a learning-loop change that passes its
  checks merges on its own.
- Context: the estate runs several harnesses on two Windows PCs, and nothing in it knew the
  truth about itself. The live `aswath-capability` skill was ahead of its published copy (265
  lines against 252), so the catalogue described a skill that was not the one running; four
  skills in `skills-active` were real directories instead of junctions; no ledger recorded what
  a run produced or what was delivered; the router's scores lived in a MiniMax-named, untracked
  folder so the second PC had a different state; the MiniMax runtime database already held nine
  scheduler jobs (all one-shot, all deleted) and 3683 background-task records; and no recurring
  job had ever run on this machine.
- Options:
  - Fix the gaps one at a time, each with its own design. Slowest to a working system, and each
    fix would land on a moving base.
  - One spec covering all eight gaps, built as eight skills. One document, but eight descriptions
    added to the per-turn token bill, and four of the eight gaps are the same mechanism wearing
    different names.
  - One spec covering all eight gaps, built as four skills, one question each, with the learning
    loop gated by a suite that must pass before a merge and a revert if the merge breaks something.
  - Adopt `swamp` and inherit its scheduler, ledger and learning loop. It is AGPLv3 and is a
    Deno-compiled automation runtime, not an agent host; linking it into this MIT estate is a
    licence decision the user did not make.
- Chosen: option 3. The spec is `docs/superpowers/specs/2026-11-17-runtime-design.md` and it
  mints `aswath-catalog` (what exists where, and do both PCs agree), `aswath-record` (what ran,
  what it produced, where the secrets are), `aswath-improve` (what failed, what should change) and
  `aswath-schedule` (when it runs). Auto-merge is kept, as the user asked, and made safe by
  construction: a path allow-list, a local gate suite, a post-merge verification and an automatic
  revert commit — never an amend, because the commit is public. `swamp` is not vendored, wrapped
  or executed.
- Evidence: the drift is measured, not assumed — `diff` shows the live `aswath-capability`
  `SKILL.md` at 265 lines against the published 252, and `readlink` shows `skills-active` holding
  57 junctions and 4 real directories; `~/.claude/scheduled_tasks.json` holds `{"tasks": []}`;
  `schtasks` lists no task of ours; the MiniMax runtime database holds 9 scheduler jobs, 9 cron
  definitions, 9 cron runs and 3683 background-task rows (3118 succeeded, 505 failed, 30 canceled,
  3 lost); `gh auth status` is green as `aswathas` and the public repo's `main` reports "Branch
  not protected".
- Consequence: the spec is written and waits for approval; no implementation file exists yet.
  The auto-merge decision is bounded by the gate — if the gate does not pass on today's `main`,
  the loop ships with merge disabled. The learn half of the loop is the part that is new: the
  router already recorded skill outcomes, and now something reads them back into a skill diff.

## D13 — One canonical copy per skill, and the map compares places, not paths

- Date: 2026-11-17
- Prompt: "approved  solve all the gaps" — the approval that lifted the gate on the runtime spec.
- Context: unit 2 of the runtime build, `aswath-catalog`. The estate resolves its skills through
  four directories (`~/.claude/skills`, `~/.commandcode/skills`, `~/.agents/skills-active`,
  `~/.agents/skills`) and nothing said which copy was real. Measured before the change: the live
  `aswath-capability` `SKILL.md` was 265 lines against 252 published; `skills-active` held 57
  junctions and 4 real directories, each of those 4 duplicated into `~/.claude/skills` as well.
  Windows makes this worse than it looks: `Path.exists()` is False for a broken junction, so the
  usual "does it exist" test says a dead link is missing, and `mklink /J` then refuses to
  overwrite it.
- Options:
  - Publish the map and call the drift solved. The map would describe a layout that the machine
    did not have, and the next `install.ps1` would put the drift back.
  - Compare copies by content hash and report every difference. Every store copy is a link, so
    the hash of a link is the hash of its target: the check would find nothing and prove nothing.
  - One canonical copy per skill, every other location a junction, and a checker that reads the
    link chain rather than the files.
- Chosen: option 3. The canonical copy is the repo path for published skills and the store path
  for vendored ones; every other location is a junction to it. The checker reports the shape of
  the chain (`MISSING_STORE`, `SHADOWED_COPY`, `WRONG_TARGET`, `COPY_IN_ACTIVE`, `ACTIVE_WRONG_TARGET`,
  `MISSING_ACTIVE`, `KEEP_NOT_ACTIVE`, `ACTIVE_NOT_KEPT`) rather than comparing content. `fix`
  re-points a link, and refuses in exactly one case: a store copy holding files the published
  copy does not, because that copy may be the newer one.
- The map is compared by *place*, not by absolute path. Both PCs carry `skill-map.json` in the
  private store, but the two machines have different home directories, so an absolute-path
  comparison would report every skill as moved. Each entry therefore carries `rel`
  (`skills/utilities/aswath-catalog`) next to its absolute `canonical`, and `verify` compares the
  relative place.
- Evidence: `catalog check` exits 0 on this machine with 354 skills mapped and 66 entries in the
  active set, all junctions, all matching the keep list. `selftest.py` runs 9 cases against a
  scratch estate — a clean estate, a shadowed copy, a copy in the active set, keep-list drift, a
  broken link rebuilt, a missing store link created, the map written with the relative place, the
  two-PC comparison agreeing on a different absolute root, and the lease taken, refused and
  released — and reports `9/9 case(s) passed`.
- Consequence: the store's `.gitignore` now states in words what travels and what stays: only the
  derived per-skill scores under `state/scores/` are tracked, the raw event stream, the router's
  working files and the write lease stay on the machine, and `secrets/` never leaves it. The
  router's state moved to `~/.agents/state/`, with the old MiniMax path left as a junction so the
  plugin needed no change. The catalogue skill itself is published here, and its store copy is a
  junction to this repo.

## D14 — The ledger is append-only JSONL, and the doctor judges a file and a line separately

- Date: 2026-11-17
- Prompt: "approved  solve all the gaps" — unit 3 of the runtime build, `aswath-record`.
- Context: the estate had no record of what ran. The MiniMax runtime database held 3683 background
  tasks (3140 succeeded, 506 failed, 33 canceled, 4 lost) and nothing read them. The chat held what
  was delivered, in the order it was delivered, with no marker of which copy was current. Two
  `.env` files held credentials outside any convention, and nothing checked whether a secret had
  reached a commit.
- Options:
  - SQLite for the ledger. Binary, merges badly, unreadable with `cat` when something goes wrong.
  - A GitHub issue per artifact. The record of the artefact would live away from the work.
  - The chat as the ledger. That is the gap.
  - Append-only JSONL in the private store, one file per project, plus a doctor that reads the
    store's tracked files.
- Chosen: the fourth. `~/.agents/ledger/<project>.jsonl`, one JSON object per line, tracked in
  the private store. Append-only: a mistake is corrected by appending a record, never by editing a
  line, so git holds the history of what was believed when. A record whose append fails is written
  to `~/.agents/state/ledger-failed.ndjson` and flushed on the next successful append, so a failed
  write is never silently lost.
- The doctor judges two different things. A **file** that holds credentials by name — `.env`,
  `*.env`, `*.pem`, `*.p12`, `*.pfx`, `*.key` — and is tracked by git is a failure, whatever its
  contents. A **line** in any tracked file that assigns a credential-named variable a filled
  literal is a failure, reported with the value redacted. The first rule catches a short secret in
  a `.env`; the second catches a secret pasted into a script or a README.
- The first version of the line rule was noise: 31 findings on this machine, every one a false
  positive — `ENV_ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"` (a name, not a value),
  `total_tokens = event.usage.output_tokens` (code), `PUBLORA_API_KEY=sk_paste_your_key_here` (a
  placeholder), and files whose *names* contained "credential" or "secret" while holding schemas
  and secret-scanning scripts. The rule now requires a value that is long, mixed case, free of
  dots and code punctuation, and free of placeholder words; and the file rule looks at the file's
  name, not at words in the path. Templates — `.env.example`, `env.sample` — are not secrets.
  The same scan now reports nothing on this machine.
- The import reads the MiniMax runtime database read-only, appends one run line per task with a
  deterministic id (`minimax:<task_id>`), and skips ids already in the ledger. The command fails
  if the database's modification time changed.
- The delivery skill now asks the ledger what is superseded instead of guessing from the chat,
  and records what it sent. The chat keeps its own rule — delete only what you are replacing —
  but the list of ids comes from the ledger.
- Evidence: the first import wrote 3683 run lines (779 KB) into `~/.agents/ledger/minimax.jsonl`
  and reported 506 failures; the second import added 0 lines, so no duplicate ids. `doctor
  secrets` exits 0 with the two old `.env` files reported as outside the convention. The
  self-check runs 5 cases against a scratch directory — the round trip, the delivery completion
  rate, the superseded list, the redaction, and the tracked-versus-ignored secret file — and
  reports `5/5 case(s) passed`.
- Consequence: the secrets convention is `~/.agents/secrets/<project>.env`, gitignored, one file
  per project. The old per-tool `.env` files are not moved; the doctor reports them. The ledger
  is tracked in the private store, so both PCs carry it, and a simultaneous append on both PCs is
  resolved by keeping every line from both sides, sorted by `ts`, dropping duplicate ids.
