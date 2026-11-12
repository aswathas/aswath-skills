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
