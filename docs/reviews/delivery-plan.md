# Delivery plan

Units in build order. Each unit is one feature or step of the work, and each lands as its own
commit and its own push. The `Commit` column is the subject that unit gets.

| # | Unit | Commit | State |
|---|------|--------|-------|
| 1 | The rule: per-unit commits and pushes | feat(commit-discipline): require work to land in units | done |
| 2 | The machine check: bulk commits and commits that match no unit | feat(commit-discipline): warn on bulk commits and unplanned commits | done |
| 3 | Verification and packaging | test(commit-discipline): cover the new checks and refresh the skill metadata | done |

State is one of `planned`, `doing`, `done`, `dropped`.
