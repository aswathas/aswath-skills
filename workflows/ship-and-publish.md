# Workflow: ship-and-publish

**Use when** the work is done on the machine and needs to leave it.

| # | Skill | Gate |
|---|---|---|
| 1 | `aswath-commit` | Reasoning written down before the commit: decisions, files, how each was verified. |
| 2 | `aswath-chronicle` | Session ledger entry with the commit range. Docs referenced, never re-printed into context. |
| 3 | `aswath-publish-github` | Secret scan, then branch → commit → push → PR or release. **Gate: clean scan.** One credential string found stops the publish. |

## Rules

- The scan in step 3 is not advisory. `token|secret|password|api[_-]?key` across `git log --all -p` before anything is pushed.
- If a skill in this chain fails, stop the chain. Do not push a partial state to "finish the workflow".
- The publish records the returned URL. A push with no recorded URL is an unverifiable claim.

## Done when

There is a URL, and the commit history explains what changed and why.
