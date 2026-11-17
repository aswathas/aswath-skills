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
| 3 | `aswath-record`: the ledger, the delivery link, the secrets convention, the metrics | feat(record): keep a ledger of runs and artifacts | planned |
| 4 | `aswath-improve`: the learning loop, the gate, the merge policy, the revert | feat(improve): let the estate learn from its own runs | planned |
| 5 | `aswath-schedule`: the scheduled jobs and the harness-scheduler report | feat(schedule): run the loop and the check on a clock | planned |

Unit 1 landed on approval. Units 3 to 5 stay `planned` until then.
