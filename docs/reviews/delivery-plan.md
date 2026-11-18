# Delivery plan

Units in build order. Each unit is one feature or step of the work, and each lands as its own
commit and its own push. The `Commit` column is the subject that unit gets.

| # | Unit | Commit | State |
|---|------|--------|-------|
| 1 | The rule: per-unit commits and pushes | feat(commit-discipline): require work to land in units | done |
| 2 | The machine check: bulk commits and commits that match no unit | feat(commit-discipline): warn on bulk commits and unplanned commits | done |
| 3 | Verification and packaging | test(commit-discipline): cover the new checks and refresh the skill metadata | done |

State is one of `planned`, `doing`, `done`, `dropped`.

---

## The runtime work — `docs/superpowers/specs/2026-11-17-runtime-design.md`

Approved before unit 1 lands. Unit 1 is the paperwork; unit 5 is the last code unit. Each code
unit also pushes to the private store, where its data half lives.

| # | Unit | Commit | State |
|---|------|--------|-------|
| 1 | The spec, its decisions and its records | docs(runtime): spec the eight gaps of the agent estate | done |
| 2 | `aswath-catalog`: the skill map, the drift detector, the shared state, the lease | feat(catalog): make the estate's own layout checkable | done |
| 3 | `aswath-record`: the ledger, the delivery link, the secrets convention, the metrics | feat(record): keep a ledger of runs and artifacts | done |
| 4 | `aswath-improve`: the learning loop, the gate, the merge policy, the revert | feat(improve): let the estate learn from its own runs | done |
| 5 | `aswath-schedule`: the scheduled jobs and the harness-scheduler report | feat(schedule): run the loop and the check on a clock | done |
| 6 | the loop's own fix: a blank line before the section it writes | fix(improve): keep a blank line before the new heading | done |
| 7 | the loop's own fixes: the patch and the plan row are written in bytes | fix(improve): write the patch and the plan row in bytes | done |
| 8 | the loop's commands wear the spec's names | fix(improve): name the loop's commands the way the spec does | done |
| 9 | the loop closes the failures it fixed, and a check with nothing to do is not a failure | fix(improve): close the failure the merge fixed | done |

Unit 1 landed on approval. Every unit of the runtime build is now done.

## The loop's own units

Rows the learning loop added. Each row is a commit the loop pushed.

| # | Unit | Commit | State |
|---|------|--------|-------|
| 1 | aswath-catalog learns from the ledger | fix(aswath-catalog): record 2 open failures | done |
## The resume units
| # | Unit | Commit | State |
|---|------|--------|-------|
| 10 | `aswath-resume-tailor`: a JD becomes a tailored, one-page, ATS-safe resume | feat(resume-tailor): turn a job description into a tailored resume | done |
## The public library units
| # | Unit | Commit | State |
|---|------|--------|-------|
| 11 | the skill as a public, generic tool: template profile, self-check, plugin and marketplace manifests | feat(resume-tailor): publish the skill as a plugin anyone can install | done |

## The form units
| # | Unit | Commit | State |
|---|------|--------|-------|
| 12 | `aswath-gform-fill`: a reusable Google Form filler - persistent browser, heading-matched fill, dry run before submit | feat(gform-fill): fill and submit a Google Form from one script | done |
| 13 | `aswath-gform-fill`: any account, not one account - a saved account store, a profile and a port per email, self-computed 2FA, and a `/gform-fill` command | feat(gform-fill): fill a Google Form with any saved Google account | done |
