# Change inventory

One row per changed file. Every changed file in a change set appears exactly once, including this
file and the decision log.

Template: `skills/workflow/aswath-commit-discipline/reference/record-templates.md`.

---

## aswath-skills-wk — `feat/aswath-commit-discipline`

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/SKILL.md` | New skill. The standing rule, the five obligations, where records live, the procedure, the push-time checklist, the checker warning table, repair paths, relation to `aswath-commit` / `aswath-chronicle` / `aswath-publish-github`, red flags | The rule must be a reusable asset, not prose in a settings file, so every harness can load it | Read in full; frontmatter `name`/`description` checked; resolved through the router catalog after the rebuild |
| `skills/workflow/aswath-commit-discipline/scripts/check_push.py` | New read-only checker. Warns on `NO_DECISION_DOC`, `NO_INVENTORY_DOC`, `UNCOVERED_FILE`, `UNDOCUMENTED_COMMIT`, `PLACEHOLDER_SUBJECT`, `PROMPT_NOT_LOGGED`, `UNPUSHED_WORK`, `DIRTY_AT_PUSH`; prints per-commit file/line counts as info; always exits 0 | The rule needs a machine check that holds for every repo and every harness | Ran against this repo, against a bare-remote scratch repo, and against a documented scratch repo; exit code 0 in every case |
| `skills/workflow/aswath-commit-discipline/reference/doc-rules.json` | New config: record paths, prompt-record patterns, doc/skill path prefixes, body-length threshold, placeholder subject list | Thresholds must be tunable without editing code | Loaded by the checker; a bad path in the file changes behaviour, confirmed by a scratch-repo run |
| `skills/workflow/aswath-commit-discipline/reference/record-templates.md` | New templates: decision entry, change-inventory row, new-skill record, prompt record | "Documented in detail" needs a concrete shape, otherwise agents write free-form prose | Read against the entries written in `docs/reviews/decision-log.md`; the templates were used to write them |
| `manifest.json` | Added the `aswath-commit-discipline` entry (category `workflow`, path, description, resources `scripts` + `reference`) | The manifest is the machine index; an unregistered skill is invisible to tooling | `python -c "import json;json.load(open('manifest.json'))"` parsed it; entry verified |
| `README.md` | Added the workflow-table row and updated the `workflow/` layout line | A human must find the skill without reading the manifest | Rendered table row checked against the manifest entry |
| `docs/reviews/decision-log.md` | New. Six decisions with prompt, options, choice, evidence, consequence | The rule requires the reasoning of this work to be written down before it is committed | Read back; each entry carries its source prompt and its evidence |
| `docs/reviews/change-inventory.md` | New. This file. One row per changed file | The rule requires every changed file to be accounted for | `check_push.py` reports no `UNCOVERED_FILE` for this range |
| `skills/workflow/aswath-commit-discipline/scripts/check_push.py` | Changed. The `UNPUSHED_WORK` check now asks the remote for its heads (`git ls-remote --heads`, read-only) instead of trusting local remote-tracking refs; the branch's remote and remote branch come from git config; squash-merge detection runs against the remote head; local tracking refs remain the fallback when the remote is unreachable | The old check produced a false `UNPUSHED_WORK` on repos whose fetch refspec covers one branch only, because no tracking ref existed for the pushed branch | Reproduced the false positive live on `feat/aswath-commit-discipline` before the fix and confirmed it is gone after; the branch is pushed and the checker is silent for it |
| `skills/workflow/aswath-commit-discipline/SKILL.md` | Changed. The checker description no longer claims "no network" and states that the checker lists the remote's heads and why local tracking refs are not enough | The skill text must not contradict what the code does | Read back after the edit |
| `skills/workflow/aswath-commit-discipline/scripts/check_push.py` | Changed again, same file as the row above. Range resolution now skips a candidate base that resolves to HEAD (an empty range hid every finding), falls back to the commits that are on no remote, and diffs against git's empty tree when the range has no lower bound | The scratch proof showed the checker going quiet on an undocumented first push | Reproduced in a scratch repository with a narrow fetch refspec: before the change the undocumented push reported one warning, after it the same push reports `NO_DECISION_DOC` and `NO_INVENTORY_DOC`; the documented case is silent again |

## Machine-local (this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.minimax/commit-discipline-hook.ps1` | New mcode hook. `UserPromptSubmit` prints the contract when the prompt mentions push/commit/GitHub/PR/branch/documentation; `PreToolUse` on `bash` runs the checker on `git push`/`git commit`; any parse error exits 0 silently. Later edit: the header comment no longer claims "No network" | Deliver the contract at the moment it matters, without a per-turn token tax | Fed six sample stdin payloads through a real stdin pipe: matching prompt produced the context block, non-matching prompt produced nothing, `PreToolUse` with a git command ran the checker, `PreToolUse` with a non-git command produced nothing, malformed payload produced nothing, empty payload produced nothing; every run exited 0 |
| `~/.minimax/hooks.json` | Appended one `UserPromptSubmit` handler and added one `PreToolUse` group with `"matcher": "bash"` | mcode reads user hooks from this file; every existing entry was preserved | Parsed as JSON; diffed against the previous content to confirm only additions |
| `~/.githooks/pre-push` | New POSIX sh hook that runs the checker with the repo root and always exits 0. Later edit: the header comment no longer claims "no network" | Harness-independent floor: the rule holds for every repo on this PC, including pushes by a human | Scratch-repo push printed the WARN lines and the push still succeeded; live push of `feat/aswath-commit-discipline` printed the warnings and the branch still reached the remote |
| `~/.gitconfig` | `core.hooksPath = C:/Users/ADMIN/.githooks` | Makes the global hook the active hook for every repo | `git config --global --get core.hooksPath` |
| `~/.agents/skills/aswath-commit-discipline` | New junction to `skills/workflow/aswath-commit-discipline` in the skills repo | The store mirrors the repo, same as `aswath-commit` | `Get-Item` reports the expected target |
| `~/.agents/skills-active/aswath-commit-discipline` | New junction to the store entry | The active set is what MiniMax Code resolves | `Get-Item` reports the expected target |
| `~/.agents/skills-active.list.json` | Added the slug to the `keep` array; bumped `generated` | The keep list is the manual record of the active set; no generator script exists on this machine | Parsed as JSON; `Get-ChildItem` on the active dir shows the new entry |
| `~/.routing/routes.static.json` | Added one pinned rule for the slug | A pinned rule always wins over a learned one, so the skill resolves for push-shaped prompts | Router test suite run after the catalog rebuild |

## ~/.agents store — `main`

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills-active.list.json` | Keep-list entry for `aswath-commit-discipline` | The active set must include the new skill | JSON parsed; active dir listing shows the junction |

## aswath-skills-wk — `feat/phase2-harness-coverage`

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/scripts/hook.py` | New. One cross-harness hook runner: prompt events (`UserPromptSubmit`, `beforeSubmitPrompt`) print the contract; tool events whose command matches `git commit`/`git push` run `check_push.py` and print its warnings to stdout and stderr; Cursor shell events get `{"permission":"allow","userMessage":...}`; every path exits 0 and a parse error exits 0 silently. The contract path was corrected from `scripts/reference/` to the skill root `reference/` | Phase 2 has to deliver the rule to Claude Code, Codex, Cursor and Command Code, and one runner means one copy of the warning logic | 11 payload cases pass (Claude/Codex/Cursor prompt hit and miss, Claude `PreToolUse` git push in a scratch repo, Cursor `beforeShellExecution` JSON verdict, Command Code payload, non-git command, malformed payload, raw malformed JSON, empty stdin); every case exits 0; the Cursor verdict's `permission` is `allow`; the prompt event printed `reference/contract.txt`, not the inline fallback |
| `skills/workflow/aswath-commit-discipline/scripts/install_harness_wiring.py` | New. Idempotent installer: wires the prompt hook and the pre-commit/push hook into the five harness configs, backs each file up once as `<file>.pre-commit-discipline.bak`, creates the plain-dir skill junctions with `cmd /c mklink /J`, and supports `--dry-run` | The wiring must be reproducible and re-runnable after a harness reset, not a one-off hand edit | Dry run listed the changes; the applied run reported `wired` for all five configs and `linked` for the fourteen junctions; all five configs parse as JSON and each backup file exists |
| `skills/workflow/aswath-commit-discipline/reference/contract.txt` | New. The contract text the hook prints on a prompt event, with the four obligations, the push rules and the checker command line | One source for the contract text, shared by the runner and the docs, so the copies cannot drift | A prompt event printed this file's text, including the two lines the runner's inline fallback does not carry |
| `skills/workflow/aswath-commit-discipline/SKILL.md` | Changed. New "Harness coverage" section: the runner, the installer, the contract file, the per-harness table, the warn-only guarantee and the events that were not runtime-verified | The skill is the reusable asset; the way it reaches the other harnesses has to be documented in it | Read back after the edit; every path named in the section exists on disk and the command in it is the one the configs carry |
| `docs/reviews/decision-log.md` | Changed. Six entries added, D9 to D14: one shared runner, warn-only verdicts, one contract file, one idempotent installer, the curated keep-list left intact, and the store path in the configs | The rule requires the reasoning behind this phase to be written down before it is committed | Read back; each entry names the prompt that triggered it, the alternatives, the choice and the evidence |
| `docs/reviews/change-inventory.md` | Changed. This section, one row per file changed in phase 2 | The rule requires every changed file to be accounted for | `check_push.py --repo .` reports no `UNCOVERED_FILE` for the phase-2 range |

## Machine-local (phase 2, this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.claude/settings.json` | Added one `UserPromptSubmit` group and one `PreToolUse` group (matcher `Bash`) that run `python "C:/Users/ADMIN/.agents/skills/aswath-commit-discipline/scripts/hook.py"` | Claude Code is the harness the user drives most; the contract must be stated before a commit and the gaps reported before a push | Parsed as JSON; the hook command appears twice; the backup `settings.json.pre-commit-discipline.bak` exists; the runner was fed a Claude `PreToolUse` git-push payload and produced the checker's warnings on stdout and stderr |
| `~/.agents/config/settings.json` | Same two hook groups as `~/.claude/settings.json` | The store mirrors Claude Code's settings, so the store's own copy must carry the wiring too | Parsed as JSON; two occurrences of the hook command; backup exists; this file is the one tracked in the store repository |
| `~/.codex/hooks.json` | Added one `UserPromptSubmit` group and one `PreToolUse` group (matcher `Bash`) running the same hook command | Codex is in daily use and speaks the same event names as Claude Code | Parsed as JSON; two occurrences of the hook command; backup exists; a Codex-shaped prompt payload produced the contract text and exited 0 |
| `~/.cursor/hooks.json` | Added one `beforeSubmitPrompt` entry and one `beforeShellExecution` entry (matcher `^git\s+(commit\|push)`) running the same hook command | Cursor has its own event names and answers shell hooks with a JSON verdict | Parsed as JSON; two occurrences of the hook command; backup exists; a `beforeSubmitPrompt` payload printed the contract and a `beforeShellExecution` payload returned `{"permission":"allow",...}` |
| `~/.commandcode/settings.json` | Added one `UserPromptSubmit` group and one `PreToolUse` group (matcher `bash\|powershell`) running the same hook command | Command Code names its shell tool `bash` or `powershell`, so the matcher differs from the Claude-style one | Parsed as JSON; two occurrences of the hook command; backup exists; a Command Code payload with `tool_input.command` produced output and exited 0 |
| `~/.minimax/skills/aswath-commit-discipline` | New junction to `~/.agents/skills/aswath-commit-discipline` | The MiniMax app's curated skills dir is where the app looks, and the app recreates that dir on reset | `Get-Item` reports a junction; `SKILL.md`, `scripts/hook.py` and `reference/contract.txt` all resolve through it |
| `~/.{continue,trae,roo,kiro,qoder,codebuddy,augment,iflow,junie,zcode,grok,vibe,openclaw}/skills/aswath-commit-discipline` | Thirteen new junctions to `~/.agents/skills/aswath-commit-discipline` | These harnesses have no hook surface at all, so the skill link plus the global git `pre-push` hook is the whole contract they can get | `Get-Item` reports a junction for each of the thirteen; `SKILL.md`, `scripts/hook.py` and `reference/contract.txt` resolve through every one |

## ~/.agents store — phase 2

| File | What changed | Why | How tested |
|---|---|---|---|
| `config/settings.json` | The two commit-discipline hook groups added by the installer | The store's copy of Claude Code's settings must carry the same wiring as the live one | Parsed as JSON; two occurrences of the hook command; the backup `config/settings.json.pre-commit-discipline.bak` exists |
| `skills/aswath-commit-discipline/scripts/hook.py` | The new shared runner, mirrored into the store's skill entry | The store is what the harness configs point at, so the runner must exist under the store path | Read through the junction; the runner executed from that path and produced the contract and the warnings |
| `skills/aswath-commit-discipline/scripts/install_harness_wiring.py` | The new installer, mirrored into the store's skill entry | The installer is part of the skill, and the store copy has to match the canonical one | Read through the junction; byte-identical to the canonical file |
| `skills/aswath-commit-discipline/reference/contract.txt` | The new contract file, mirrored into the store's skill entry | The runner reads the contract from this path, and the store path is what the configs use | Read through the junction; the prompt-event test printed this file's text from the store path |
| `skills-active/aswath-commit-discipline/scripts/hook.py` | The new shared runner, mirrored into the store's active set | The active set is what MiniMax Code resolves, and it must carry the same runner | Read through the junction; the file resolves and matches the canonical one |
| `skills-active/aswath-commit-discipline/scripts/install_harness_wiring.py` | The new installer, mirrored into the store's active set | The active set mirrors the whole skill, not a subset | Read through the junction; the file resolves and matches the canonical one |
| `skills-active/aswath-commit-discipline/reference/contract.txt` | The new contract file, mirrored into the store's active set | Same reason: the active set carries the whole skill | Read through the junction; the file resolves and matches the canonical one |
## The aswath-delivery skill

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-delivery/SKILL.md` | New skill: delete the superseded messages and files first, send the current build once, remove the staging copies, report the clean-up to the owner | The chat had accumulated four copies of the report and two dead links, and the person had no way to tell which file was current | Read back after install; the skill resolves through the harness link |
| `manifest.json` | The row for the new skill, and the `updated` date | The manifest is the catalogue the installer reads | Parsed as JSON; the skill appears once with its category and path |
| `README.md` | The table row, the category list and the workflow chain description | The README is the catalogue a reader scans | Read back after the change |
| `docs/categories.md` | The judgement note: thevai and delivery are the same conversation at its two ends, so both are workflow | The category rule is "the question the skill answers", and that question needed a stated call | Read back after the change |
| `workflows/thevai-a-request.md` | Step 4 is now the delivery, and the done condition says the chat holds no superseded copy | The chain ends with the work leaving the machine, and leaving it clean is part of that | Read back after the change |
## Publishing the catalogue (2026-11-17)

| File | What changed | Why | How tested |
|---|---|---|---|
| `manifest.json` | Added the missing `aswath-commit-discipline` row, bumped `version` 1.1.0 → 1.2.0 and set `updated` to 2026-11-17 | PR #4 landed the skill as a squash merge that kept the folder and the README row but dropped the manifest row, so the catalogue counted 19 skills while the repo carried 20 | Parsed as JSON; 21 rows; every row's `path` resolves to a `SKILL.md` that exists |
| `docs/reviews/decision-log.md` | D2, the catalogue/manifest drift and how it was closed, and D3, the impeccable hook path | The contract requires every decision to be written down before the push | Read back after the change |
| `docs/reviews/change-inventory.md` | This section | The contract requires one row per changed file | Read back after the change |
| `C:/Users/ADMIN/.claude/settings.json` (outside this repo) | The three impeccable hook commands call `/c/Users/ADMIN/.claude/skills/impeccable/scripts/impeccable` instead of `C:\Users\ADMIN\...` | The launcher parses its own directory out of `$0` with a forward-slash match, so a backslash path left it searching the hook's working directory for the engine and it exited 127 on every prompt | The command was run straight out of the parsed JSON after the change: exit 0, empty stdout and stderr; the old form exited 127 with "no engine binary" |

## aswath-skills-wk — `feat/commit-discipline-unit-delivery` (unit 1: the rule)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/SKILL.md` | Sixth obligation added: work lands in units. Procedure gains "plan the units" first and "push per unit" last. Push-time checklist gains three boxes. Checker table gains `BULK_COMMIT`, `COMMIT_NOT_PLANNED`, `UNIT_NOT_COMMITTED`. Red flags gain two rows. Description mentions the delivery plan | The contract said "one commit per unit is preferred"; a preference left the bulk push the user complained about wide open | Read back after the change; the frontmatter still parses as YAML and the description still begins "Use when" |
| `skills/workflow/aswath-commit-discipline/reference/contract.txt` | The unit rule, and "One commit per unit is the rule whenever the work has units" replacing "preferred, not required" | The file the hook prints is the contract the agent reads; a soft sentence there is a soft rule everywhere | Read back after the change; the hook prints it on a "push" prompt |
| `skills/workflow/aswath-commit-discipline/reference/delivery.txt` | New file: the short delivery rule for build-time prompts | The unit rule has to reach the agent while the work is planned, not only at push time | New file; the hook prints it on a "build" prompt |
| `skills/workflow/aswath-commit-discipline/reference/record-templates.md` | Delivery-plan template added, with the note that a unit is one thing a reviewer could describe in one sentence | The plan shape is part of the contract, and a vague unit is how a bulk commit comes back | Read back after the change |
| `skills/workflow/aswath-commit-discipline/scripts/hook.py` | `BUILD_PATTERNS`, `delivery_text()`, and the branch that prints the short rule on build-time prompts. `FALLBACK_CONTRACT` carries the unit rule | The hook is the only thing that reaches an agent that never asked about commits | `python -m py_compile` clean; replayed `UserPromptSubmit` prompts "build me a login screen" (delivery rule) and "now push it" (full contract) |
| `docs/reviews/delivery-plan.md` | New file: this change's own three-unit plan, with the exact commit subject per unit | The rule applies to this change first, or it does not apply | Read back after the change; unit 1 marked `done` |
| `docs/reviews/decision-log.md` | D4, D5 and D6 — the unit rule, the plan-before-first-commit rule, and the split between the short delivery rule and the full contract | The contract requires every decision to be written down before the push | Read back after the change |
| `docs/reviews/change-inventory.md` | This section | The contract requires one row per changed file | Read back after the change |
| `docs/reviews/prompts.md` | New file: the two prompts that produced this change, verbatim, with the decisions each caused | This repo had no prompt record; obligation 3 needs one | Read back after the change |
| `BUILDLOG.md` | New file: what shipped for unit 1, where and how it was verified | The repo had no build log; the contract names it as a record | Read back after the change |

## aswath-skills-wk — `feat/commit-discipline-unit-delivery` (unit 2: the machine check)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/scripts/check_push.py` | New: `parse_delivery_plan`, `subject_matches`, `normalise_subject`, `fork_point`, `plan_governs_range`, `check_delivery_units`, and the `BULK_COMMIT` warning inside `check_commits`. New rule keys `delivery_plan`, `bulk_commit_file_threshold`, `bulk_commit_line_threshold` | A rule an agent can forget is not a rule; the checker has to see a bulk commit, a commit that matches no unit, and a unit that was marked done but never committed | `python -m py_compile` clean. Scratch repo: 32-file commit -> `BULK_COMMIT`; `feat(y): unplanned work` -> `COMMIT_NOT_PLANNED`; a unit marked `done` with no commit -> `UNIT_NOT_COMMITTED`; `chore: housekeeping` -> no warning; the planned unit's commit -> no warning. Second scratch repo with the plan merged to `main`: a later unrelated branch produced neither new warning |
| `skills/workflow/aswath-commit-discipline/reference/doc-rules.json` | Added `delivery_plan`, `bulk_commit_file_threshold` (30) and `bulk_commit_line_threshold` (2000) | The thresholds are a property of the repository, not of the checker, and a repo that ships a large vendor drop needs to be able to move them | Parsed as JSON; the three keys load into the rules and the thresholds are the ones the scratch run used |
| `skills/workflow/aswath-commit-discipline/SKILL.md` | The two new code rows now say what the checker says: `COMMIT_NOT_PLANNED` matches no unit "in the range", `UNIT_NOT_COMMITTED` has no commit "on the branch" | A table that says "in the range" when the checker looks at the whole branch sends the reader looking in the wrong place | Read back after the change; both rows match the warning text |
| `docs/reviews/decision-log.md` | D7 (the plan governs only the work it was written for), D8 (bulk is measured by size, and the size limits live in the rules file), D9 (housekeeping commits are exempt) | The contract requires every decision to be written down before the push | Read back after the change |
| `docs/reviews/change-inventory.md` | This section | The contract requires one row per changed file | Read back after the change |
| `docs/reviews/delivery-plan.md` | Unit 2 marked `done` | The plan is the record of what landed and what is left | Read back after the change |
| `BUILDLOG.md` | Unit 2 entry: what shipped, and the scratch runs that proved it | The build log is the running narrative of what shipped | Read back after the change |

## aswath-skills-wk — `feat/commit-discipline-unit-delivery` (unit 3: verification and packaging)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/scripts/test_check_push.py` | New file: the checker's self-check. Builds a scratch repository per case in a temp directory, runs the real checker against it and asserts on the warnings | The manual scratch runs proved the checks once; nothing in the repo would run them again, so the next change to the checker could break them silently | `python skills/workflow/aswath-commit-discipline/scripts/test_check_push.py` -> `5/5 case(s) passed`, exit 0. Six assertions: compliant branch quiet, 31-file commit -> `BULK_COMMIT`, commit matching no unit -> `COMMIT_NOT_PLANNED`, `chore:` commit quiet, unit marked done with no commit -> `UNIT_NOT_COMMITTED`, inherited plan quiet |
| `skills/workflow/aswath-commit-discipline/SKILL.md` | The command that runs the self-check, under the checker section | The self-check is useless if nobody knows it exists | Read back after the change; the command matches the file path |
| `manifest.json` | Version 1.2.0 -> 1.3.0, and the description of `aswath-commit-discipline` now states the unit rule and names `docs/reviews/delivery-plan.md` | The catalogue is what a reader scans before loading the skill; it described the old contract | Parsed as JSON; the row's description matches the skill's frontmatter description |
| `README.md` | The catalogue row states the unit rule and names the plan file | The README is the page most people read | Read back after the change; the row names `docs/reviews/delivery-plan.md` |
| `docs/reviews/decision-log.md` | D10 (the checker is verified by a stdlib script, not by a test framework) and D11 (the catalogue states the unit rule and the manifest version moves to 1.3.0) | The contract requires every decision to be written down before the push | Read back after the change |
| `docs/reviews/change-inventory.md` | This section | The contract requires one row per changed file | Read back after the change |
| `docs/reviews/delivery-plan.md` | Unit 3 marked `done` | The plan is the record of what landed and what is left | Read back after the change |
| `BUILDLOG.md` | Unit 3 entry: what shipped, and the self-check that proved it | The build log is the running narrative of what shipped | Read back after the change |

## The runtime spec (2026-11-17)

| File | What changed | Why | How tested |
|---|---|---|---|
| `docs/superpowers/specs/2026-11-17-runtime-design.md` | New. The spec for the eight gaps: skill-location truth, the run/artifact ledger, the secrets home, the learning loop, the shared skill state, scheduling, two-PC coordination and metrics | The work starts from assumptions about what the estate knows about itself; the decisions belong on paper before any code | Read back; all ten sections filled; a placeholder scan for `TBD`, `TODO`, `FIXME`, `XXX` and `...` returns no match |
| `docs/reviews/decision-log.md` | Changed. Entry D12 added: what was chosen, what was rejected, and the evidence for each | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its source prompts, its options and its evidence |
| `docs/reviews/prompts.md` | Changed. A dated section for the runtime work, with the four answers the spec depended on | The rule requires every prompt that shaped the work to be recorded | Read back; the section names each prompt and the decision each one produced |
| `docs/reviews/delivery-plan.md` | Changed. The five units of this work, in build order | The plan is written before the first commit, so the commit count and the push count are known | Read back; the unit table lists each unit with its commit subject |
| `docs/reviews/change-inventory.md` | Changed. This section, one row per changed file | The rule requires every changed file to be accounted for | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |

## aswath-skills-wk — `feat/catalog` (unit 2: the map, the drift detector, the lease)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/utilities/aswath-catalog/SKILL.md` | New. The catalogue skill: the link chain as it really is, the five commands, every code `check` can report, the one thing `fix` refuses, the lease, and the map | The estate had no answer to "where is the real copy of this skill"; the skill is the answer, and its description has to name the situations that should route a request to it | Read back; the frontmatter description starts with "Use when" and names the two-copy case, the catalogue-vs-machine case and the two-PC case |
| `skills/utilities/aswath-catalog/scripts/catalog.py` | New. `build`, `check`, `fix`, `verify`, `lease` | The map and the drift check are the unit's deliverable; they have to be runnable on a machine that is not this one, so the locations are environment-overridable | `catalog check` exits 0 on this machine with 354 skills mapped; `catalog build` writes the map and `pc.json`; `catalog fix aswath-catalog` created the missing store link |
| `skills/utilities/aswath-catalog/scripts/selftest.py` | New. Nine cases against a scratch estate | A checker that has never been wrong is not a checker; every rule it encodes needs a case that fails when the rule is broken | `python skills/utilities/aswath-catalog/scripts/selftest.py` -> `9/9 case(s) passed`, exit 0 |
| `skills/orchestration/aswath-capability/SKILL.md` | Changed. The Files section is now three tables — skill files, state directory, runtime files — and the duplicated `registry/ledger.json` row is gone; the shared state path is `~/.agents/state/` | The published copy described a layout the live skill no longer had, which is the drift this unit exists to remove | Read back; no row names a file twice, and every state path in the table is under `~/.agents/state/` |
| `skills/orchestration/aswath-capability/scripts/build-registry.py` | Changed. Reads the shared state from `~/.agents/state/` instead of the MiniMax runtime directory | The router's state was in a MiniMax-named folder, untracked, so the second PC had a different state and the two ranked skills differently | `learn.py` prints the ledger path it uses; the shared directory is overridable with `SKILL_ROUTER_STATE_DIR` and the old path is a junction to the new one |
| `skills/orchestration/aswath-capability/scripts/invoke.py` | Changed. Same shared-state path | Same reason | Read back after the change |
| `skills/orchestration/aswath-capability/scripts/learn.py` | Changed. Same shared-state path, and it is the script that writes the scores | Same reason | Read back after the change |
| `skills/orchestration/aswath-capability/scripts/query-registry.py` | Changed. Same shared-state path | Same reason | Read back after the change |
| `skills/orchestration/aswath-capability/scripts/record-outcome.py` | Changed. Same shared-state path | Same reason | Read back after the change |
| `skills/orchestration/aswath-capability/scripts/stage-install.py` | Changed. Same shared-state path | Same reason | Read back after the change |
| `skills/orchestration/aswath-capability/scripts/taxonomy-audit.py` | Changed. Same shared-state path | Same reason | Read back after the change |
| `skills/orchestration/aswath-capability/registry/backends.json` | Changed. The registry file the live skill had been writing, ported from the store | The published registry described the pre-port state; porting it makes the published copy the current one | Read back; the file parses as JSON |
| `skills/orchestration/aswath-capability/registry/capabilities.json` | Changed. Same | Same reason | Read back; the file parses as JSON |
| `skills/orchestration/aswath-capability/registry/ledger.json` | Changed. Same | Same reason | Read back; the file parses as JSON |
| `skills/orchestration/aswath-capability/registry/backends.sample.json` | New. The sample copy the live skill carries | The live skill shipped it; leaving it out would make the published copy smaller than the real one | Read back; the file parses as JSON |
| `skills/orchestration/aswath-capability/registry/ledger.sample.json` | New. Same | Same reason | Read back; the file parses as JSON |
| `skills/orchestration/aswath-capability/registry/staged.json` | New. Same | Same reason | Read back; the file parses as JSON |
| `manifest.json` | Version 1.3.0 -> 1.4.0, and the `aswath-catalog` row added under `utilities` | The manifest is the machine index; a skill that is not in it is not installed by `install.ps1` and not routed to | Parsed as JSON; the row's path resolves to the skill directory that holds `SKILL.md` |
| `README.md` | The utilities row now lists `aswath-catalog`, and the layout block names it | The README is the page a person reads before the manifest | Read back; the row appears in both places |
| `docs/reviews/decision-log.md` | Changed. D13: one canonical copy per skill, and the map compares places, not paths | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its options, its rejection and its evidence |
| `docs/reviews/prompts.md` | Changed. The approval prompt and the section it produced | The rule requires every prompt that shaped the work to be recorded | Read back; the section names the prompt and the unit it produced |
| `docs/reviews/delivery-plan.md` | Changed. Units 1 and 2 marked `done` | The plan is the record of what landed and what is left | Read back; the unit table matches the commits |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |
| `BUILDLOG.md` | Changed. The unit 2 entry | The build log is the running narrative of what shipped | Read back after the change |

### Machine-local (this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.agents/.gitignore` | Added: `state/**` with `state/scores/*.json` re-included, and `secrets/` ignored | The spec decided that derived per-skill scores travel and raw events, the router's working files, the lease and the secrets stay on the machine; the ignore file is where that rule lives | `git check-ignore` says `state/observations.ndjson`, `state/lease.json` and `secrets/x.env` are ignored, and `state/scores/a.json` is not |
| `~/.agents/sync.sh` | Added the `verify` command (local check, then the two-PC comparison) and a `catalog check` after `pull` | The spec's data flow says a pull ends in a layout check; without `verify` two PCs could disagree about the estate without either machine knowing | `bash ~/.agents/sync.sh verify` runs both halves; `catalog check` exits 0, `catalog verify` reports against the remote's committed map |
| `~/.agents/skills-active.list.json` | `aswath-catalog` added, and four published skills that `install.ps1` had already linked were added with it — 61 -> 66 | The keep list decides what is installed in the harnesses, and `install.ps1` links every published skill, so the two must agree or the check cries wolf on every install | `catalog check` reports `KEEP_NOT_ACTIVE` and `ACTIVE_NOT_KEPT` for any drift; it reports neither today, and the active set holds 66 junctions and 0 real directories |
| `~/.agents/skills/aswath-catalog/`, `~/.agents/skills-active/aswath-catalog/` | Junctions to the published skill | The store's copy is a link to the published copy, so an edit in the repo is the edit everywhere | `os.lstat` shows the reparse point; `catalog check` reports no `WRONG_TARGET` |
| `~/.agents/config/skill-map.json`, `~/.agents/config/pc.json` | New, tracked | The map and the PC's identity are what the two PCs compare | `catalog build` wrote them; `catalog verify` reads the remote's copy of the map |
| `~/.agents/state/` | The router's state moved here from `~/.minimax/local-runtime/skill-learning/`, which is now a junction to it | The state was in a MiniMax-named folder that git never tracked, so the second PC had a different state | `catalog check` is clean; the router's `learn.py --report` reads the moved ledger |
| `~/.agents/memory/home/aswath-skill-router-install.md` | The router note now records the deleted hand-made marketplace source and the MiniMax copy at 0.1.1 | The note was the record of the router install; it was stale about both | Read back; the note matches the machine |

## aswath-skills-wk — `feat/record` (unit 3: the ledger, the delivery link, the secrets convention, the metrics)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-record/SKILL.md` | New. The ledger's shape and why it is append-only, the seven commands, the metrics, the import, the secrets convention, the doctor, and when to run it | Nothing in the estate recorded what ran or what was produced, so a later session could not tell which artifact was current | Read back; the description starts with "Use when" and names the run, the artifact and the secret case |
| `skills/workflow/aswath-record/scripts/ledger.py` | New. `add`, `superseded`, `deliver`, `import`, `stats`, `doctor secrets` | The ledger, the doctor and the metrics are one mechanism; splitting them would duplicate the state files | `selftest.py` -> `5/5 case(s) passed`; on this machine `import` wrote 3683 run lines, a second `import` wrote 0, `stats` counted 506 failures, `doctor secrets` exits 0 |
| `skills/workflow/aswath-record/scripts/selftest.py` | New. Five cases against a scratch directory: the round trip, the delivery completion rate, the superseded list, the redaction, and the tracked-versus-ignored secret file | The doctor and the ledger decide what is tracked and what is redacted; a rule that has never been wrong is not a rule | `python skills/workflow/aswath-record/scripts/selftest.py` -> `5/5 case(s) passed`, exit 0 |
| `skills/workflow/aswath-delivery/SKILL.md` | Changed. The order now asks the ledger which artifact ids are superseded, deletes exactly those, and records what was sent | The chat holds what was sent, in order, with no marker of which copy is current; the ledger holds that | Read back; step 2 names the command and step 6 records the delivery |
| `manifest.json` | Version 1.4.0 -> 1.5.0, and the `aswath-record` row added under `workflow` | The manifest is the machine index; a skill that is not in it is not installed and not routed to | Parsed as JSON; the row's path resolves to the skill directory that holds `SKILL.md` |
| `README.md` | The workflow table gains an `aswath-record` row, and the layout block names it | The README is the page a person reads before the manifest | Read back; the row appears in both places |
| `docs/reviews/decision-log.md` | Changed. D14: the ledger is append-only JSONL, and the doctor judges a file and a line separately | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its options, its rejection and the evidence, including the 31 false positives the first rule produced |
| `docs/reviews/prompts.md` | Changed. The approval prompt now names both units it produced | The rule requires every prompt that shaped the work to be recorded | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 3 marked `done` | The plan is the record of what landed and what is left | Read back; the unit table matches the commits |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |
| `BUILDLOG.md` | Changed. The unit 3 entry | The build log is the running narrative of what shipped | Read back after the change |

### Machine-local (this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.agents/ledger/minimax.jsonl` | New. 3683 run lines harvested from the MiniMax runtime database | The runtime already knew what ran; the ledger is where that history becomes readable and analysable | `stats --project minimax` -> `runs: 3683`, `failures: 506`; a second `import` added 0 lines |
| `~/.agents/secrets/` | New, empty, gitignored | The secrets convention needs a home that exists before the first project writes to it | `git check-ignore` says `secrets/x.env` is ignored; `doctor secrets` reports the home |
| `~/.agents/skills-active.list.json` | `aswath-record` added, 66 -> 67 | The keep list decides what is installed in the harnesses | `catalog check` is clean |
| `~/.agents/skills/aswath-record/`, `~/.agents/skills-active/aswath-record/` | Junctions to the published skill | The store's copy is a link to the published copy | `catalog check` reports no `WRONG_TARGET` |
| `~/.agents/config/skill-map.json`, `~/.agents/config/pc.json` | Rebuilt: 355 skills | The map is what the two PCs compare | `catalog check` is clean; `catalog build` wrote both files |

## aswath-skills-wk — `feat/improve` (unit 4: the learning loop, the gate, the merge policy, the revert)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-improve/SKILL.md` | New. The flow, the three gate checks, the merge policy, the revert, the commands, and when to run it | The estate recorded what ran but nothing acted on it, so a skill could fail three times with nothing in the repo saying so | Read back; the description starts with "Use when" and names the failing skill and the pull request |
| `skills/workflow/aswath-improve/scripts/gate.py` | New. `check --repo --base --head`: the catalogue agrees with the tree, the diff stays inside `skills/` and `docs/`, and every touched skill's self-check exits 0 | The gate is what stands between a machine-made edit and the published repo | `selftest.py` -> `8/8 case(s) passed`; green on this repo's `main` with the manifest and README rows in place |
| `skills/workflow/aswath-improve/scripts/improve.py` | New. `propose` writes the diff for an open failure; `run` branches, commits, pushes, opens the PR, gates it, merges, checks the merged tree and reverts with a new commit when that check fails | The loop is the machinery; the diff is written by the person or by the ledger | `selftest.py` -> `8/8 case(s) passed`, against a scratch repo with a stub `gh` and a local remote |
| `skills/workflow/aswath-improve/scripts/selftest.py` | New. Eight cases: the gate green, the gate refusing the manifest, the gate refusing a deletion, the gate running a touched skill's self-check, the proposal leaving out a closed failure, the loop merging, the loop refusing to merge, the revert with its issue | A loop that edits the estate's own skills needs its failure paths proven before it is allowed near the real repo | `python skills/workflow/aswath-improve/scripts/selftest.py` -> `8/8 case(s) passed`, exit 0 |
| `skills/workflow/aswath-record/scripts/ledger.py` | Changed. `add` takes `--skill`, so a run can be filed against the skill that owns it | The loop reads the ledger by skill; without the field it cannot tell which skill to change | `selftest.py` for aswath-record -> `5/5 case(s) passed`; the field lands in the record as `skill` |
| `manifest.json` | Version 1.5.0 -> 1.6.0, and the `aswath-improve` row added under `workflow` | The manifest is the machine index; a skill that is not in it is not installed and not routed to | Parsed as JSON; the row's path resolves to the skill directory that holds `SKILL.md`; the gate's first check passes |
| `README.md` | The workflow table gains an `aswath-improve` row, and the layout block names it | The README is the page a person reads before the manifest | Read back; the row appears in both places, and the gate's first check counts one row per skill |
| `docs/reviews/decision-log.md` | Changed. D15: the machine merges only what the gate cleared, and undoes a bad merge with a new commit | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its options, its rejections and the evidence |
| `docs/reviews/prompts.md` | Changed. The runtime build section now names unit 4 | The rule requires every prompt that shaped the work to be recorded | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 4 marked `done` | The plan is the record of what landed and what is left | Read back; the unit table matches the commits |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |
| `BUILDLOG.md` | Changed. The unit 4 entry | The build log is the running narrative of what shipped | Read back after the change |

### Machine-local (this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.agents/ledger/agent-estate.jsonl` | New. The open failures the loop reads: the keep list and the active set drifting apart after a publish, recorded once per publish that drifted | The loop needs a real open failure to work on, and this one is real and recurring | `stats --project agent-estate` counts the failures; `propose` writes the diff from them |
| `~/.agents/skills-active.list.json` | `aswath-improve` added, 67 -> 68 | The keep list decides what is installed in the harnesses | `catalog check` is clean |
| `~/.agents/skills/aswath-improve/`, `~/.agents/skills-active/aswath-improve/` | Junctions to the published skill | The store's copy is a link to the published copy | `catalog check` reports no `WRONG_TARGET` |
| `~/.agents/config/skill-map.json`, `~/.agents/config/pc.json` | Rebuilt: 356 skills | The map is what the two PCs compare | `catalog check` is clean; `catalog build` wrote both files |

## aswath-skills-wk — `fix/improve-commands` (unit 8: the loop's commands wear the spec's names)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-improve/scripts/improve.py` | Changed. `propose` and `run` become the flat flags `--dry-run` and `--run`; the proposal is now a function both paths call; `--run` without `--diff` writes the proposal first | The spec names `aswath-improve --dry-run` and `aswath-improve --run`, and the scheduled job in unit 5 is written as `improve --run` | `selftest.py` -> `8/8 case(s) passed`; the dry-run case asserts the diff file is written and no pull request was opened |
| `skills/workflow/aswath-improve/scripts/selftest.py` | Changed. The cases call the flags; the dry-run case also asserts that no `pr create` reached the stub `gh` | The spec's criterion 7 asks for a diff file and an unchanged pull-request count | `selftest.py` -> `8/8 case(s) passed`, exit 0 |
| `skills/workflow/aswath-improve/SKILL.md` | Changed. The flow, the commands and the last line name the flags | A person reads the skill, not the source | Read back; no `propose` left in the file |
| `docs/reviews/decision-log.md` | Changed. D16: the loop's commands wear the spec's names | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its options, its rejections and the evidence |
| `docs/reviews/delivery-plan.md` | Changed. Units 6 and 7 marked `done` (both had merged), and unit 8 added | The plan is the record of what landed and what is left | Read back; the unit table matches the commits |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |
| `BUILDLOG.md` | Changed. The unit 8 entry | The build log is the running narrative of what shipped | Read back after the change |

## aswath-skills-wk — `feat/schedule` (unit 5: the scheduled jobs and the harness-scheduler report)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/utilities/aswath-schedule/SKILL.md` | New. The jobs, the three schedulers, the commands, the two estate jobs, and when to run it | The estate could learn and could check itself, but nothing ran either | Read back; the description starts with "Use when" and names the missed-start flag |
| `skills/utilities/aswath-schedule/scripts/schedule.py` | New. `add` creates a task from UTF-16 task XML with the missed-start flag; `remove` deletes it; `list` prints the Windows tasks, the Claude Code task list and the MiniMax cron table with the finished one-shots marked dead | A job that must run daily is run by hand otherwise, and a slot missed while the PC slept never runs at all | `selftest.py` -> `7/7 case(s) passed`; on this machine both estate tasks are created and visible in `schtasks /query` |
| `skills/utilities/aswath-schedule/scripts/selftest.py` | New. Seven cases: the task name, the missed-start flag, the escaped command, the trigger boundary, the Claude Code task list, the MiniMax dead one-shots, and a live task that appears and is gone after `remove` | A skill that creates machine-level jobs must prove the task really appears and really goes | `python skills/utilities/aswath-schedule/scripts/selftest.py` -> `7/7 case(s) passed`, exit 0 |
| `manifest.json` | Version 1.6.0 -> 1.7.0, and the `aswath-schedule` row added under `utilities` | The manifest is the machine index; a skill that is not in it is not installed and not routed to | Parsed as JSON; the row's path resolves to the skill directory that holds `SKILL.md` |
| `README.md` | The utilities table gains an `aswath-schedule` row, and the layout block names it | The README is the page a person reads before the manifest | Read back; the row appears in both places |
| `docs/reviews/decision-log.md` | Changed. D17: the estate's clock is Windows Task Scheduler, and the three schedulers are reported in one place | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its options, its rejections and the evidence |
| `docs/reviews/prompts.md` | Changed. The runtime build section now names unit 5 | The rule requires every prompt that shaped the work to be recorded | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 5 marked `done` | The plan is the record of what landed and what is left | Read back; the unit table matches the commits |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |
| `BUILDLOG.md` | Changed. The unit 5 entry | The build log is the running narrative of what shipped | Read back after the change |

### Machine-local (this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `Aswath\catalog-verify`, `Aswath\improve` (Windows Task Scheduler) | New. The two estate jobs: the catalogue check at 09:00, the learning loop at 09:30 | The spec gives this skill two jobs to schedule | `schtasks /query /fo CSV /v` shows both, with their next run times; the verify task was run by hand and returned the real difference it found |
| `~/.agents/skills-active.list.json` | `aswath-schedule` added, 68 -> 69 | The keep list decides what is installed in the harnesses | `catalog check` is clean |
| `~/.agents/skills/aswath-schedule/`, `~/.agents/skills-active/aswath-schedule/`, `~/.claude/skills/aswath-schedule/`, `~/.commandcode/skills/aswath-schedule/` | Junctions to the published skill | The store's copies are links to the published copy | `catalog check` reports no `WRONG_TARGET` |
| `~/.agents/config/skill-map.json`, `~/.agents/config/pc.json` | Rebuilt: 357 skills | The map is what the two PCs compare | `catalog check` is clean; `catalog build` wrote both files |

## aswath-skills-wk — `fix/improve-closing` (unit 9: the merge closes the failure, and nothing to do is not a failure)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-improve/scripts/improve.py` | Changed. A successful merge records a successful run of each job the proposal fixed, under that job's own name; "nothing to do" exits 0 | The loop recorded its success under `improve <skill>`, so the failure it repaired stayed open forever and the daily job reported a failure every day on a healthy estate | `selftest.py` -> `9/9 case(s) passed`; the live `Aswath\improve` job returns 0 |
| `skills/workflow/aswath-improve/scripts/selftest.py` | Changed. A new case seeds a failure, runs the loop with no diff, and shows the ledger holding a successful run of the same job and the next dry run finding nothing to do; the scratch runs set `PYTHONDONTWRITEBYTECODE` so the imported ledger leaves no `__pycache__` in the scratch tree | The closing rule and the exit code are the two things a scheduled job lives on | `python skills/workflow/aswath-improve/scripts/selftest.py` -> `9/9 case(s) passed`, exit 0 |
| `skills/workflow/aswath-improve/SKILL.md` | Changed. The flow says a check that found nothing exits 0, and a new section states that a merge closes what it fixed | A reader must know why the job is quiet on a good day | Read back |
| `docs/reviews/decision-log.md` | Changed. D18: a merge closes the failure it fixed, and a check with nothing to do is not a failure | The rule requires the reasoning behind a change to be written down before it is pushed | Read back; the entry carries its options, its rejections and the evidence |
| `docs/reviews/delivery-plan.md` | Changed. Unit 9 added | The plan is the record of what landed and what is left | Read back; the unit table matches the commits |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | `check_push.py --repo ~/Projects/aswath-skills-wk` reports no `UNCOVERED_FILE` for this range |
| `BUILDLOG.md` | Changed. The unit 9 entry | The build log is the running narrative of what shipped | Read back after the change |

### Machine-local (this PC, outside the skills repo)

| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.agents/ledger/agent-estate.jsonl` | A successful run of "the keep list and the active set stay in step after a publish" for `aswath-catalog` | The job was done — the keep list is 69 and the map is rebuilt — but the ledger held only the failure, so the failure stayed open | `improve.py --dry-run --project agent-estate` -> "nothing to do", exit 0 |
## aswath-skills-wk - `feat/resume-tailor` (unit 10: a job description becomes a tailored resume)
| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/writing/aswath-resume-tailor/SKILL.md` | New. The inputs, the procedure (JD -> evidence -> JSON variant -> build -> render -> verify -> deliver), the commands and the mistakes | The skill has to work for any posting, not for one JD | Built the SuperDream variant through it: `pages 1`, 4,995 characters, no placeholder |
| `skills/writing/aswath-resume-tailor/scripts/build_resume.py` | New. The generic builder, copied from the Myntra PM1 builder with its hardcoded paths removed: argv is source JSON, output dir, basename | One builder for every role; the content is the only thing that changes | `python scripts/build_resume.py ~/.agents/resume/variants/superdream-sde.json <outdir> <name>` -> docx + txt; LibreOffice -> PDF, `pages 1` |
| `skills/writing/aswath-resume-tailor/references/schema.md` | New. The resume JSON: fields, meaning, required shape, base versus variant | The JSON is the source of truth, so its shape has to be written down | Read back |
| `skills/writing/aswath-resume-tailor/references/jd-to-evidence.md` | New. The JD mapping, the honesty rules, the ATS rules and the one-page budget | The rules that keep the resume honest and one page | Read back |
| `manifest.json` | Changed. The `aswath-resume-tailor` row with its three resources; version 1.7.0 -> 1.8.0 | The manifest is the catalogue the harnesses read | `python -c "import json;json.load(open('manifest.json'))"` -> 27 skills |
| `README.md` | Changed. The row in the writing table and the layout line | The README table is the catalogue a human reads | Read back |
| `docs/categories.md` | Changed. `resume-tailor` in the writing row and a judgement note | The rule is that a skill lives in the folder of the question it answers | Read back |
| `docs/reviews/decision-log.md` | Changed. D19 | The rule requires the reasoning behind a change to be written down before it is pushed | Read back |
| `docs/reviews/prompts.md` | Changed. The 2026-11-18 entry | The rule requires every prompt and the decision it produced to be written down | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 10 | The plan is the record of what landed | Read back |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | Read back |
| `BUILDLOG.md` | Changed. The unit 10 entry | The build log is the running narrative of what shipped | Read back after the change |
### Machine-local (this PC, outside the skills repo)
| File | What changed | Why | How tested |
|---|---|---|---|
| `~/.agents/resume/profile.json` | New. The candidate's base profile, copied from the site repo's `src/data/resume.json` | The base profile is the fallback when no JD has arrived; the private store keeps the data out of the public skills repo | File reads as JSON; the private repo `aswathas/agent-store` is the owner |
| `~/.agents/resume/variants/superdream-sde.json` | New. The SuperDream SDE-intern variant | The first role variant, built from the JD | Built to a one-page PDF |
| `~/.routing/routes.static.json` | Changed. A pinned rule for `aswath-resume-tailor` on the words resume, resumes, curriculum, vitae | "Use our router": the router matches a prompt to a skill through pinned rules and the catalogue | `echo '{"prompt":"tailor my resume for this job description"}' \| python router.py` -> "Pinned rule. Load the aswath-resume-tailor skill and follow it." |
| `~/.routing/catalog.json` | Rebuilt: 587 records (396 skills) | The router reads the catalogue at match time; a new skill is invisible until the catalogue is rebuilt | `python build_catalog.py` -> `records 587`, exit 0 |
| `~/.claude/skills/aswath-resume-tailor/` | Junction to the published skill | The harness links skills, it does not copy them | `install.ps1 -Target claude` -> `link aswath-resume-tailor -> claude` |
## aswath-skills-wk - `feat/resume-tailor-public` (unit 11: the skill is public and generic)
| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/writing/aswath-resume-tailor/SKILL.md` | Changed. The profile is found by search order (`$RESUME_PROFILE`, `profile.json`, `~/.resume/`, `~/.agents/`), a first-time-user block, the one dependency named, and a rule that the candidate's data never ships with the skill | A stranger has no `~/.agents` store and must still be able to run the skill | `scripts/selftest.py` -> `6/6 case(s) passed` |
| `skills/writing/aswath-resume-tailor/assets/profile.template.json` | New. An empty but valid profile with the fields filled with clear placeholders | The first run should not need a schema document to be usable | Built by the self-check |
| `skills/writing/aswath-resume-tailor/scripts/selftest.py` | New. Builds the template and checks the docx, the txt, every section, the bullets and the skill labels | The builder is the part that can rot; the check is six cases | `python skills/writing/aswath-resume-tailor/scripts/selftest.py` -> `6/6 case(s) passed` |
| `skills/writing/aswath-resume-tailor/scripts/build_resume.py` | Changed. A missing `python-docx` now fails with the install line instead of a traceback | The one dependency, said plainly | The self-check still passes with the dependency present |
| `skills/writing/aswath-resume-tailor/references/schema.md` | Changed. The profile search order and the template | The schema document is where a new user looks first | Read back |
| `.claude-plugin/plugin.json` | New. The plugin manifest, listing every skill directory | Other people install with one line and never clone | `claude plugin validate .` -> `Validation passed` |
| `.claude-plugin/marketplace.json` | New. The marketplace manifest for `aswathas/aswath-skills` | The publish path | `claude plugin validate .` -> `Validation passed` |
| `.claude-plugin/icon.png` | New. A 512x512 icon | The validator asked for one; the marketplace listing shows it | `claude plugin validate .` -> no icon warning |
| `manifest.json` | Changed. The `aswath-resume-tailor` resources now list the template and the self-check; version 1.8.0 -> 1.9.0 | The catalogue names the files a reader needs | `python -c "import json;json.load(open('manifest.json'))"` |
| `README.md` | Changed. The marketplace install line and a job-application quickstart | The README is the first thing a stranger reads | `claude plugin validate .` no longer advises an install line |
| `docs/reviews/decision-log.md` | Changed. D20 | The rule requires the reasoning written down before the push | Read back |
| `docs/reviews/prompts.md` | Changed. The 2026-11-18 entry | The rule requires every prompt and the decision it produced | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 11 | The plan is the record of what landed | Read back |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | Read back |
| `BUILDLOG.md` | Changed. The unit 11 entry | The build log is the running narrative | Read back after the change |

## aswath-skills-wk - `feat/gform-fill` (unit 12: the reusable Google Form filler)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/utilities/aswath-gform-fill/SKILL.md` | New skill. The procedure (one persistent browser, inspect before filling, dry run before submit), the commands, and the mistakes that cost the most time on the real survey | The method was the deliverable; the survey was only the first run of it | Read in full; frontmatter `name`/`description` checked |
| `skills/utilities/aswath-gform-fill/scripts/gform.mjs` | New. One Node script, no dependencies: `inspect` dumps every page and question; `fill` signs in (email/password, an OTP file, or by hand in the open window), fills by heading text, handles rating grids and branch re-render, walks Back to page 1 then Next to Submit, clicks Submit once, and verifies "Thank you for your response" | The whole method in one file, so a new machine needs no setup beyond Node and Chrome | `inspect` against the live survey form; `fill --no-submit` filled every page and stopped before Submit |
| `skills/utilities/aswath-gform-fill/references/answers.md` | New. The answers JSON schema: `text`, `radio`, `grid.default`, `textDefault` | A caller needs to know the answer file shape without reading the script | Read back; the file it documents is the one the script parses |
| `skills/utilities/aswath-gform-fill/assets/answers.template.json` | New. A valid empty answers file to copy | A first run should not need the schema document to start | Parsed as JSON and used as the shape of the test answers file |
| `manifest.json` | Changed. Added the `aswath-gform-fill` entry (category `utilities`, resources `scripts` + `references`); version 1.9.0 -> 1.10.0 | The catalogue names the files a reader needs | `python -c "import json;json.load(open('manifest.json'))"` |
| `skills/utilities/aswath-gform-fill/scripts/selftest.mjs` | New. Runs the whole engine against `tests/mock-form.html` in a throwaway headless Chrome and asserts ten facts: both pages walked, nothing missing, the response recorded, the radio, both grid rows, the text answer and the free-text default | The script is the part that can rot; the check is a form, not a mock of the form's data | `node skills/utilities/aswath-gform-fill/scripts/selftest.mjs` -> `10 passed, 0 failed` |
| `skills/utilities/aswath-gform-fill/tests/mock-form.html` | New. A two-page form that reproduces the Google Forms DOM shape (listitem blocks, heading, `jsname="YPqjbf"` inputs, `role="radio"` options, grid cells labelled `"<value>, response for <row>"`, Next / Back / Submit buttons, a thank-you panel) | The engine can be proved without a real form, and without risking a second real response | Driven by the self-check |
| `README.md` | Changed. The utilities-table row and the `utilities/` layout line | A human must find the skill without reading the manifest | Row checked against the manifest entry |
| `docs/categories.md` | Changed. The utilities row now names `gform-fill`, and a judgement note says why it is utilities and not workflow | The category rule is stated by the question, and this one needed saying | Read back |
| `.claude-plugin/plugin.json` | Changed. Added the skill directory; version 1.9.0 -> 1.10.0 | The plugin must carry every skill so a stranger can install the library | `claude plugin validate .` |
| `.claude-plugin/marketplace.json` | Changed. Version 1.9.0 -> 1.10.0 | The marketplace publishes the plugin version | `claude plugin validate .` |
| `docs/reviews/decision-log.md` | Changed. D21 | The rule requires the reasoning written down before the push | Read back |
| `docs/reviews/prompts.md` | Changed. The 2026-11-18 entry | The rule requires every prompt and the decision it produced | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 12 | The plan is the record of what landed | Read back |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | Read back |
| `BUILDLOG.md` | Changed. The unit 12 entry | The build log is the running narrative | Read back after the change |

## aswath-skills-wk - `feat/gform-multi-account` (unit 13: any Google account, not one account)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/utilities/aswath-gform-fill/scripts/lib.mjs` | New. The account store (`loadAccounts`, `saveAccounts`, `findAccount`, `upsertAccount`, `slug`, `storePath`) and TOTP (`base32Decode`, `totp`) | The account has to be the unit of isolation, and the shared pieces were about to be duplicated between the CLI and the sign-in path | Three RFC 6238 vectors plus a store round trip in `scripts/selftest.mjs` |
| `skills/utilities/aswath-gform-fill/scripts/gform.mjs` | Changed. The `account list|add|remove` subcommand; `--email` resolves the profile, the port, the password and the TOTP secret; the sign-in path fills the saved password and computes the 2FA code itself | One hard-coded account does not answer "any email" | `account add` -> `list` -> `remove` against a temp store; `fill` against the mock form still exits 0 |
| `skills/utilities/aswath-gform-fill/SKILL.md` | Changed. The procedure picks the account first, the commands block lists the account subcommands, the options document `--email`, `--profile`, `--port`, `--password`, `--totp`, `--otp-file`, and the mistakes gain "one profile for every account" and "committing the account store" | The skill is what a stranger reads first | Read back; the commands match the script's usage block |
| `commands/gform-fill.md` | New. The `/gform-fill` slash command: list the accounts, add one if missing, inspect, dry run, submit only when nothing is missing | The user asked for a plugin that works for any email; the command is the plugin surface | `claude plugin validate .` -> validation passed |
| `.claude-plugin/plugin.json` | Changed. Added `"commands": ["./commands/gform-fill.md"]`; version 1.10.0 -> 1.11.0 | The command has to ship with the plugin | `claude plugin validate .` |
| `skills/utilities/aswath-gform-fill/scripts/selftest.mjs` | Changed. Eight more assertions: three RFC 6238 vectors, the slug, the store round trip, the store path, and the CLI listing | TOTP and the store are the parts that rot silently | `node scripts/selftest.mjs` -> `18 passed, 0 failed` |
| `manifest.json` | Changed. Added `scripts/lib.mjs` to the resources; version 1.10.0 -> 1.11.0 | The catalogue names the files a reader needs | `python -c "import json;json.load(open('manifest.json'))"` |
| `.claude-plugin/marketplace.json` | Changed. Version 1.10.0 -> 1.11.0 | The marketplace publishes the plugin version | `claude plugin validate .` |
| `README.md` | Changed. The utilities row now says any number of accounts and names `/gform-fill` | A human must find the command without reading the manifest | Row checked against the manifest entry |
| `docs/reviews/decision-log.md` | Changed. D22 | The rule requires the reasoning written down before the push | Read back |
| `docs/reviews/prompts.md` | Changed. The 2026-11-18 entry | The rule requires every prompt and the decision it produced | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Unit 13 | The plan is the record of what landed | Read back |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | Read back |
| `BUILDLOG.md` | Changed. The unit 13 entry | The build log is the running narrative | Read back after the change |

## aswath-skills-wk - `chore/push-everything` (units 14-16: the pending work, split and pushed)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-commit-discipline/SKILL.md` | Changed. The unit/plan obligation is gone: five obligations instead of six, commit granularity is a soft preference, the delivery-plan row is out of the records table, and the three unit/bulk findings are out of the warning table | The rule is a documentation gate, and the plan file was enforcement machinery around it | Read back against the diff of `scripts/check_push.py`; the finding names in the SKILL.md match the codes the checker still emits |
| `skills/workflow/aswath-commit-discipline/reference/contract.txt` | Changed. The units block is gone; "one commit per meaningful unit is preferred, not required" replaces "one commit per unit is the rule" | The contract text is printed on every prompt that matches, so it has to say the same thing the skill says | Printed by `hook.py` in the smoke test below |
| `skills/workflow/aswath-commit-discipline/reference/delivery.txt` | Deleted. It carried the build-time delivery rule | Its only reader was the build-pattern branch of the hook, which is gone | `grep -rn "delivery.txt" skills/workflow/aswath-commit-discipline/` returns nothing |
| `skills/workflow/aswath-commit-discipline/reference/doc-rules.json` | Changed. `delivery_plan`, `bulk_commit_file_threshold` and `bulk_commit_line_threshold` removed | The checker reads these; a rule the checker ignores is a rule that lies | `check_push.py` runs against the repo with no unknown-key errors |
| `skills/workflow/aswath-commit-discipline/reference/record-templates.md` | Changed. The delivery-plan template section removed | It documented a file the contract no longer asks for | Read back; the remaining templates match the files the contract names |
| `skills/workflow/aswath-commit-discipline/scripts/check_push.py` | Changed. `check_delivery_units`, `parse_delivery_plan`, `subject_matches`, `normalise_subject`, `fork_point`, `plan_governs_range` and the bulk-commit warning removed; the three delivery findings are gone | The checker has to stop enforcing the rule the contract dropped | `python scripts/check_push.py --repo .` runs clean and reports only `UNPUSHED_WORK` and `DIRTY_AT_PUSH` |
| `skills/workflow/aswath-commit-discipline/scripts/hook.py` | Changed. `DELIVERY`, `FALLBACK_DELIVERY`, `BUILD_PATTERNS`, `delivery_text()` and `build_hits()` removed | The build-time delivery rule no longer has a rule to print | `hook.py` with a `UserPromptSubmit` payload prints the relaxed contract and exits 0 |
| `skills/workflow/aswath-commit-discipline/scripts/test_check_push.py` | Deleted. All five cases covered the removed delivery warnings | A test for a feature that is gone is a test that fails for the wrong reason | `grep -rn "delivery" skills/workflow/aswath-commit-discipline/` returns nothing |
| `manifest.json` | Changed. The `aswath-commit-discipline` description drops the delivery-plan sentence; the `aswath-talk` description is unquoted again | The catalogue description must match the skill's own frontmatter | `python -c "import json;json.load(open('manifest.json'))"` |
| `README.md` | Changed. The `aswath-commit-discipline` row drops the delivery-plan sentence | The README row is the catalogue's face of the skill | Row read against the manifest entry |
| `skills/orchestration/aswath-capability/SKILL.md` | Changed. The default state dir is `~/.minimax/local-runtime/skill-learning/`; the file table keeps the source registry and the generated state in two tables again | The staged edit had duplicated three registry rows into the state table and dropped the per-skill scores row | Read back; the two tables no longer overlap |
| `skills/orchestration/aswath-capability/scripts/build-registry.py` | Changed. The default state dir | All eight scripts have to agree on one dir | `python -m py_compile` on all eight; `query-registry.py stats` reads the registry from the new default |
| `skills/orchestration/aswath-capability/scripts/invoke.py` | Changed. The default state dir | As above | As above |
| `skills/orchestration/aswath-capability/scripts/learn.py` | Changed. The default state dir | As above | As above |
| `skills/orchestration/aswath-capability/scripts/query-registry.py` | Changed. The default state dir | As above | As above |
| `skills/orchestration/aswath-capability/scripts/record-outcome.py` | Changed. The default state dir | As above | As above |
| `skills/orchestration/aswath-capability/scripts/stage-install.py` | Changed. The default state dir | As above | As above |
| `skills/orchestration/aswath-capability/scripts/taxonomy-audit.py` | Changed. The default state dir | As above | As above |
| `skills/workflow/aswath-thevai/SKILL.md` | Changed. English examples with the Tanglish variant beside them, a fast path for a complete brief, verify-once QA, a rule against cold-opening, and a rule against handling money | The user's register was leaking into the contact's, and a complete brief was paying for a sign-off round trip it did not need | Read back in full |
| `docs/reviews/decision-log.md` | Changed. D23, D24, D25 | The rule requires the reasoning written down before the push | Read back |
| `docs/reviews/prompts.md` | Changed. The 2026-11-18 entry for this push | The rule requires every prompt that shaped the work | Read back |
| `docs/reviews/delivery-plan.md` | Changed. Units 14, 15 and 16 | The plan file stays in the repo and the improve loop still writes into it | Read back |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | Read back |
| `BUILDLOG.md` | Changed. The unit 14-16 entry | The build log is the running narrative | Read back after the change |

## aswath-skills-wk - `main` (the design-hook triage)

| File | What changed | Why | How tested |
|---|---|---|---|
| `.impeccable/config.json` | New. The `overused-font` rule ignores the value `arial`, with the reason written down | `tests/mock-form.html` reproduces the Google Forms DOM for the self-check. It is a machine-read fixture with no designed interface, so the font in it is not a design decision | The design hook no longer reports the fixture |
| `.gitignore` | Changed. `.impeccable/hook.cache.json` ignored | The hook's cache is machine state and does not belong in the repository | `git status` shows the cache untracked and ignored |

## aswath-skills-wk - `main` (the token guard marker and its selftest)

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/context/aswath-token-guard/plugin/install.py` | Changed. `is_ours` now looks for `token_guard-hook` instead of `token-guard-hook` | The hook scripts on disk are `token_guard-hook.sh` and `token_guard-hook.ps1`. The hyphenated marker never matched, so the installer duplicated its own groups on every run and uninstall removed nothing | The selftest's install cases: a second install leaves one group per event, and uninstall removes the three token guard groups while keeping the foreign one |
| `skills/context/aswath-token-guard/scripts/selftest.py` | New. Thirteen cases covering the installer and both hook scripts | The plugin shipped with no check. The earlier draft of this file tested a `handle()` API that exists in no branch and no commit; it is rewritten against the shipped plugin - `patch_hooks` called directly, the hook scripts run as subprocesses against a scratch `MINIMAX_DATA_DIR` and a scratch `HOME` | `python skills/context/aswath-token-guard/scripts/selftest.py` reports `13/13 case(s) passed` |
| `docs/reviews/decision-log.md` | Changed. This section | The rule requires every decision to be written down before it is pushed | Read back |
| `docs/reviews/change-inventory.md` | Changed. This section | The rule requires one row per changed file | Read back |

## 2026-11-23 — fetched skill minted into the catalogue

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/utilities/aswath-rust-security/SKILL.md` | New: the Rust security skill fetched from `claude-dev-suite/claude-dev-suite`, renamed, given a `Use when` description and an origin line | The catalogue did not cover Rust security, and a fetched skill must follow this repo's naming, description and category rules | The harness lists the skill with the right description; `router ask "rust security vulnerabilities cargo audit"` answers `aswath-rust-security` |
| `manifest.json` | One skill row for `aswath-rust-security` in category `utilities` | Every skill in this repo is registered | JSON parses; the row count matches the skills on disk |
| `README.md` | One row in the utilities table | The README is the catalogue the human reads | Row present under the utilities heading |
| `skills/orchestration/aswath-capability/scripts/build-registry.py` | `load_ledger()` folds the outcome counts into one number per skill, and the merge keys on the slug and covers plugin skills | The counts were handed over as a dict where a number belonged, so the ledger could not change a ranking | `router learn` prints the weighted map; the benchmark moved from 0.792 to 0.805 top-1 |
| `docs/reviews/decision-log.md` | Added D1 | Contract requires every decision to be written down | Read back; the entry names the prompt, the options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-23 prompt entry | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |

## 2026-11-24 — the semantic layer, shipped inside the capability skill

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/orchestration/aswath-capability/scripts/embed.py` | New: the local embedding index builder (LM Studio, OpenAI-compatible, base64 float32 cache) | The requests that never name a capability were the largest group of routing failures, and this repo's skill is what other harnesses load | `embed.py build` embeds the catalogue in 15 s and writes a 12.6 MB index; `embed.py status` loads it warm in 0.000 s |
| `skills/orchestration/aswath-capability/scripts/semantic.py` | New: the semantic layer, with the conservative profile as default and the keyword fallback | Same reason; the layer is what turns a meaning match into a routed skill | `semantic.py status`; `router ask` shows the semantic line and 0.31 s per query |
| `skills/orchestration/aswath-capability/SKILL.md` | The file table now names the two scripts, and the state table names `<state>/embeddings.json` | A file that is not in the table does not get used | Read back; both scripts and the state path are listed |
| `docs/reviews/decision-log.md` | Added D2 | Contract requires every decision to be written down | Read back; the entry names the prompt, the options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-24 prompt entry | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |

## 2026-11-24 — the precedent store

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/orchestration/aswath-capability/scripts/precedent.py` | New: reads the recorded request/skill pairs and answers which skill was used last time for a request like this one | 27 of 38 strict failures were a sibling of the right skill winning, and no matcher can tell them apart. Only history can | `pytest tests` -> 58 passed; `precedent.py stats` lists the recorded pairs; `precedent.py lookup` finds the skill for a rephrased request |
| `skills/orchestration/aswath-capability/SKILL.md` | The file table names `precedent.py`, and the state table says the `observations.ndjson` `load` rows are the precedent | A file that is not in the table does not get used | Read back; both rows present |
| `docs/reviews/decision-log.md` | Added D3 | Contract requires every decision to be written down, including the ones the measurements ended | Read back; the entry names the decomposition, the three rejected options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-24 prompt entry | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |

## 2026-11-24 — one resolver for the skill and the command

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/orchestration/aswath-capability/scripts/query-registry.py` | `rank_with_router()` uses `semantic.py` and `precedent.py` when they are available, with the old local scorer as the fallback. `need` now prints the semantic and precedent lines | The skill shipped its own scorer, so the agent's routing missed the semantic layer and the precedent, and disagreed with the `router` command | `query-registry.py need "find the failing checks on this pr and fix them"` -> `semantic layer: on (rescued ci-delivery)`, `fix-ci` first; `pytest tests` -> 62 passed, the sync test included |
| `docs/reviews/decision-log.md` | Added D4 | Contract requires every decision to be written down | Read back; the entry names the drift, the options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-24 prompt entry | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |

## 2026-11-24 - autocompact templates for small, medium and hard tasks

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/context/aswath-autocompact/SKILL.md` | New: the skill - the three templates, how to apply one, and the three caveats (next-session window, env var precedence, model cap) | The user asked for reusable autocompact templates; the skill is how they are invoked | `claude plugin validate .` passes; the skill is listed in the installed skill catalogue |
| `skills/context/aswath-autocompact/presets.json` | New: the source of truth - window, allowed range, use-when and the rules for basic (200k), medium (300k) and hard (400k) | The rules are the part that has no native runtime setting, so they need a home of their own | `python scripts/selftest.py` -> the applied template's rules match the preset; the hook prints "MEDIUM task" for medium |
| `skills/context/aswath-autocompact/scripts/autocompact.py` | New: apply / status / uninstall. Writes the window top-level and per model id, writes the state file, registers the rules hook, removes exactly what it owns | The window must be settable without the `/autocompact` slash command, which refuses to write while the env var is set | 24 assertions green, including preservation of `effortLevel`, unrelated keys, another `PreCompact` hook, and the env block |
| `skills/context/aswath-autocompact/scripts/compaction_rules.py` | New: the `PreCompact` hook. Prints the active template's rules; silent and exit 0 when no template is active | Claude Code has no custom-compaction-instruction setting, so the hook stdout is the only channel | Piped a real PreCompact payload: rules printed, exit 0; with no state file: no output, exit 0 |
| `skills/context/aswath-autocompact/scripts/selftest.py` | New: 24 assertions against a throwaway HOME | The script edits the real user settings file; the check must not | `python scripts/selftest.py` -> passed 24, failed 0, run twice |
| `manifest.json` | Added the `aswath-autocompact` row; version 1.11.0 -> 1.12.0; updated 2026-11-24 | A new skill has to be in the machine index or the installer skips it | `install.ps1` -> linked 2, skipped 88; the skill resolves in the installed catalogue |
| `README.md` | Added the context-table row and the layout line | The README lists every invocable skill | Read back; both lines present |
| `docs/reviews/decision-log.md` | Added D5 | Contract requires every decision to be written down | Read back; the entry names the options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` for this work appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-24 prompt entry | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |

## 2026-11-25 - the interview skill, minted by hand

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-questions-ask/SKILL.md` | New: the question ladder, the marking rule, the ledger format and the handoff to the study build | The requested skill - ask the user lots of questions until we both understand the concepts | Read back; the harness lists `aswath-questions-ask` with its `Use when` description |
| `manifest.json` | One skill row for `aswath-questions-ask` in category `workflow`, and the `updated` date moved to 2026-11-25 | Every skill in this repo is registered | JSON parses; the row count matches the skills on disk |
| `README.md` | One row in the workflow table and one in the layout block | The README is the catalogue the human reads | Row present under the workflow heading |
| `docs/categories.md` | One judgement call: questions-ask vs first-principles | A skill lands in one folder only, and the rule needs a stated reason | Read back |
| `docs/reviews/decision-log.md` | Added D19 | Contract requires every decision to be written down | Read back; the entry names the prompt, the rejected options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-25 prompt entry | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |

## 2026-11-25 - the interview skill, rebased and given a short-on-time mode

| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-questions-ask/SKILL.md` | Added the "Short on time" subsection under The Loop: mark-carrying topics only, rungs 1 -> 2 -> 6, budget to shaky and unknown, `not interviewed` recorded for the rest | The 21CSE433T exam is the next morning; the seven-rung ladder needs a budget-aware mode | Read back; the section sits between The Loop and The Question Ladder |
| `manifest.json` | Rebase conflict resolved: kept both the `aswath-study-technique` and the `aswath-questions-ask` rows | `origin/main` moved; both sides added a row | `JSON.parse` succeeds |
| `README.md` | Rebase conflict resolved: workflow table carries both rows, layout line carries both skills | Same reason | Read back; both names appear in the workflow table and in the layout block |
| `docs/reviews/decision-log.md` | Added D20 | Contract requires every decision to be written down | Read back; the entry names the prompt, the rejected options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
## 2026-11-25 - the 21CSE433T course content and the tree that clipped
| File | What changed | Why | How tested |
|---|---|---|---|
| `skills/workflow/aswath-study-technique/content/21cse433t-u1.json` | New unit file: unit 1, 6 topics with definition, problem, mechanism, terminology, exam answer, traps and recall, plus a 10-term glossary | The study skill needs a per-unit content contract before it can build notes for a subject | `JSON.parse` succeeds; 6 topics and 10 glossary entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u2.json` | New unit file: unit 2, 7 topics, 11 glossary entries | Same contract, unit 2 | `JSON.parse` succeeds; 7 topics and 11 glossary entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u3.json` | New unit file: unit 3, 8 topics, 10 glossary entries | Same contract, unit 3 | `JSON.parse` succeeds; 8 topics and 10 glossary entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u4.json` | New unit file: unit 4, 8 topics, 10 glossary entries | Same contract, unit 4 | `JSON.parse` succeeds; 8 topics and 10 glossary entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u5.json` | New unit file: unit 5, 11 topics, 10 glossary entries | Same contract, unit 5 | `JSON.parse` succeeds; 11 topics and 10 glossary entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u1-enrich.json` | New enrichment file: 6 topics with advantages, limitations, memory trick, modern note and exam answer | The enrichment layer deepens a topic beyond the core note | `JSON.parse` succeeds; 6 topics read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u2-enrich.json` | New enrichment file: 7 topics | Same contract, unit 2 | `JSON.parse` succeeds; 7 topics read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u3-enrich.json` | New enrichment file: 8 topics | Same contract, unit 3 | `JSON.parse` succeeds; 8 topics read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u4-enrich.json` | New enrichment file: 8 topics | Same contract, unit 4 | `JSON.parse` succeeds; 8 topics read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u5-enrich.json` | New enrichment file: 11 topics | Same contract, unit 5 | `JSON.parse` succeeds; 11 topics read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u1-revision.json` | New revision file: 6 mental-map entries and 6 top exam questions | The revision layer is what a student opens the night before | `JSON.parse` succeeds; 6 mental-map and 6 exam-question entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u2-revision.json` | New revision file: 10 mental-map entries and 7 top exam questions | Same contract, unit 2 | `JSON.parse` succeeds; 10 mental-map and 7 exam-question entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u3-revision.json` | New revision file: 8 mental-map entries and 8 top exam questions | Same contract, unit 3 | `JSON.parse` succeeds; 8 mental-map and 8 exam-question entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u4-revision.json` | New revision file: 8 mental-map entries and 8 top exam questions | Same contract, unit 4 | `JSON.parse` succeeds; 8 mental-map and 8 exam-question entries read back |
| `skills/workflow/aswath-study-technique/content/21cse433t-u5-revision.json` | New revision file: 11 mental-map entries and 11 top exam questions | Same contract, unit 5 | `JSON.parse` succeeds; 11 mental-map and 11 exam-question entries read back |
| `skills/workflow/aswath-study-technique/scripts/layout.cjs` | One-line fix in `layoutTree`: the fan start x is clamped with `Math.max(..., PAD + w / 2)` so the first child box is never at a negative x, plus a two-line comment saying why | A wide fan centred on the root started off the left edge of the canvas and the first child was drawn where it could not be seen | Old formula puts the first box at x = -240 for five children and x = -400 for six; the clamped formula puts both at x = 40. The rebuilt vault renders the full fan |
| `docs/reviews/decision-log.md` | Added D21, D22, D23 and D24 | Contract requires every decision to be written down | Read back; each entry names the prompt, the rejected options and the evidence |
| `docs/reviews/change-inventory.md` | Added the table above | Contract requires one row per changed file | Every file in `git status -s` appears exactly once above |
| `docs/reviews/prompts.md` | Added the 2026-11-25 entry carrying both verbatim prompts | Contract requires the prompt trail to be recorded | Cross-checked against the session transcript |
