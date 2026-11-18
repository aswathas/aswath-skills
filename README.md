# aswath-skills

A skill library built like a framework: **atomic skills**, grouped into **categories**, chained into **workflows** — and every skill still invocable on its own.

```
skills/<category>/<skill>/SKILL.md     one unit, one job, self-contained
workflows/<name>.md                    a named chain of units with gates
manifest.json                          machine index: name, category, path, triggers
install.ps1 / install.sh               link every skill into your harnesses
```

No runtime, no build step, no dependencies. Skills are markdown; a harness reads them, a human can read them too.

---

## Install

```powershell
# Windows
.\install.ps1                 # links into ~/.claude/skills, ~/.commandcode/skills, ~/.agents/skills
.\install.ps1 -Target claude  # or one harness only
```

```bash
# WSL / macOS
chmod +x install.sh && ./install.sh
```

Links, not copies. Edit the repo, every harness sees the change. Re-run with `-Force` / `--force` to repair a broken link.

**As a Claude Code plugin** — for anyone who does not want to clone the repo:

```
/plugin install aswath-skills --marketplace aswathas/aswath-skills
```

The marketplace serves every skill in this repo as one plugin. `claude plugin validate .` in this
repo is the check that keeps the manifests honest.

## Use it for a job application

`aswath-resume-tailor` turns a job description into a tailored, one-page, ATS-safe resume:

```
python -m pip install python-docx
cp skills/writing/aswath-resume-tailor/assets/profile.template.json ~/resume/profile.json
# fill in the template once
/aswath-resume-tailor "here is the job description ..."
```

It maps the JD onto evidence you already have, writes a role-specific JSON variant, builds the
DOCX and PDF, and reports the gaps it refused to invent. Nothing about the skill is specific to one
person: the profile belongs to whoever runs it.

## Use

Two ways in, and they are the same units.

**One skill, manually.** Type the slash command or name it in the prompt:

```
/aswath-token-guard
/aswath-publish-linkedin
/aswath-first-principles
```

**A workflow, when the job spans several.** Each workflow names the order and the gate between steps:

| Workflow | Chain | Use when |
|---|---|---|
| [`context-discipline`](workflows/context-discipline.md) | token-guard → token-ledger → token-evaluator → compact | the session feels expensive or is filling |
| [`spec-before-code`](workflows/spec-before-code.md) | first-principles → forge → commit | new build, no approved spec |
| [`ship-and-publish`](workflows/ship-and-publish.md) | commit → chronicle → publish-github | work is done, needs to leave the machine |
| [`publish-everywhere`](workflows/publish-everywhere.md) | publish-github + publish-linkedin + publish-instagram | one artefact, several destinations |
| [`delegate-a-request`](workflows/delegate-a-request.md) | throw → capability | raw request in, proven artefact out |
| [`thevai-a-request`](workflows/thevai-a-request.md) | thevai → publish-github → delivery | a real person is the source of the brief |

---

## The skills

### context — measure and shrink what a session carries

| Skill | What it does | Invoke |
|---|---|---|
| `aswath-token-guard` | Attributes every token to a cause, names the largest waste, applies the four habits that cut it. Also the entry point when a hook blocks a repeat read. | `/aswath-token-guard` |
| `aswath-token-ledger` | Raw per-session ledger: costliest tool outputs, files read twice, spend across sessions. Reads the transcript store directly. | `/aswath-token-ledger` |
| `aswath-token-evaluator` | Per-session stats table, cause breakdown, measured vs counterfactual savings, before/after around the guard. | `/aswath-token-evaluator` |
| `aswath-compact` | Measures what the session carries, distils it into a dense handoff, persists it so a later session resumes, and says how to actually release the window. | `/aswath-compact` |
| `aswath-minimax-compaction-handoff` | Automatic context compaction at 100k tokens in MiniMax Code; writes HANDOFF.md via PreCompact hook before compaction and re-injects on resume. | `/aswath-minimax-compaction-handoff` |

### publishing — get the work out

| Skill | What it does | Invoke |
|---|---|---|
| `aswath-publish-github` | Create a repo, branch, commit, push, open a PR, cut a release, publish a gist — with a secret scan before anything leaves. | `/aswath-publish-github` |
| `aswath-publish-linkedin` | Publish, schedule, delete, check LinkedIn posts from an agent. | `/aswath-publish-linkedin` |
| `aswath-publish-instagram` | Posts, reels, carousels, stories; refuses to post into a logged-out session. | `/aswath-publish-instagram` |

### workflow — decide, spec, record, commit, delegate

| Skill | What it does | Invoke |
|---|---|---|
| `aswath-first-principles` | Research → questions → spec → approval, before any implementation. The template other tasks route into. | `/aswath-first-principles` |
| `aswath-forge` | Routes a task to a minted skill if one exists, otherwise into first-principles, then mints the asset afterwards. | `/aswath-forge` |
| `aswath-commit` | Decision log and file-by-file change inventory, then commits. No mass dumps. | `/aswath-commit` |
| `aswath-commit-discipline` | Push-time gate: every decision spoken with an AI, every edit, every prompt and every new skill documented in detail, then committed and pushed. Work with separable parts lands as one commit and one push per unit, planned in `docs/reviews/delivery-plan.md`. Commit count is free; detail is not. Ships a warn-only checker. | `/aswath-commit-discipline` |
| `aswath-chronicle` | Persistent audit trail of prompts, choices and git history without re-printing docs into context. | `/aswath-chronicle` |
| `aswath-throw` | Raw request → harness work item → leader-authored test → agent pool → two independent verifiers → report. | `/aswath-throw` |
| `aswath-delivery` | The other end of `aswath-thevai`: finished work back to a person on a chat channel, with only the final version in the chat. Deletes the superseded messages and files, sends the current build once. | `/aswath-delivery` |
| `aswath-record` | The run and artifact ledger in the private store: what ran, what it produced, what was delivered, and the delivery rate. Also the secrets convention and the doctor that checks no secret file is tracked by git. | `/aswath-record` |
| `aswath-improve` | The learning loop. Reads the ledger's open failures, writes the diff, opens the pull request, and merges only what the gate cleared — reverting the merge with a new commit when the check after it fails. | `/aswath-improve` |
| `aswath-thevai` | A real person is the source of the brief. Warm, one-question-at-a-time conversation over WhatsApp → an approved brief → build, QA, deliver. Ships with the `thevai-agent`. | `/aswath-thevai` |
| `aswath-thinking` | Deconstruct ungrounded assumptions via first principles, inversion, and adversarial verification before executing code. | `/aswath-thinking` |

### orchestration — assemble the thing

| Skill | What it does | Invoke |
|---|---|---|
| `aswath-capability` | Takes a one-line brief to shipped work: brainstorm, feasibility, plan, then resolve skills, subagents, hooks, MCPs and plugins from a registry — authoring gaps mid-build. | `/aswath-capability` |
| `aswath-manual-demo` | Shows how a hand-written skill is captured into the shared catalog (`provenance: manual`). | `/aswath-manual-demo` |

### writing

| Skill | What it does | Invoke |
|---|---|---|
| `aswath-talk` | Plain words, short shape, smallest honest answer. The compression/minimalism register for every reply. | `/aswath-talk` |
| `aswath-resume-tailor` | A job description becomes a tailored, one-page, ATS-safe resume. Maps the JD onto evidence the candidate already has, writes a role-specific JSON variant, builds the DOCX and PDF, and reports the gaps it refused to invent. | `/aswath-resume-tailor` |

### utilities

| Skill | What it does | Invoke |
|---|---|---|
| `aswath-csvjson` | CSV → JSON done properly: header-keyed rows, type sniffing, quoting, embedded newlines, leading-zero IDs kept as strings. | `/aswath-csvjson` |
| `aswath-catalog` | The estate's own layout, made checkable. One map says where every skill lives and which copy is canonical; one check says whether the machine still matches it. Also the lease that keeps two PCs from writing the same shared state. | `/aswath-catalog` |
| `aswath-schedule` | Work that runs without a human. Windows Task Scheduler jobs named `Aswath\<name>`, created so a missed slot runs late instead of never — and one report for the Windows, Claude Code and MiniMax schedulers together. | `/aswath-schedule` |
| `aswath-gform-fill` | A Google Form filled and submitted, end to end. One persistent browser so the Google sign-in happens once; answers matched to the real question headings; rating grids and branch questions handled; dry run before the one irreversible click. Any number of accounts: each email gets its own browser profile and its own saved credentials. | `/aswath-gform-fill`, `/gform-fill` |

---

## Layout in full

```
skills/
  context/          aswath-compact, aswath-token-guard, aswath-token-ledger, aswath-token-evaluator, aswath-minimax-compaction-handoff
  publishing/       aswath-publish-github, aswath-publish-instagram, aswath-publish-linkedin
  workflow/         aswath-first-principles, aswath-forge, aswath-commit, aswath-commit-discipline, aswath-chronicle, aswath-delivery, aswath-record, aswath-improve, aswath-throw, aswath-thevai, aswath-thinking
  orchestration/    aswath-capability, aswath-manual-demo
  writing/          aswath-talk, aswath-resume-tailor
  utilities/        aswath-csvjson, aswath-catalog, aswath-schedule, aswath-gform-fill
```

`skills/orchestration/aswath-capability` carries its own `registry/`, `skillsets/`, `workflows/`, `agents/` and `scripts/` — it is the only skill with runtime support files, and they travel with it.

See [`docs/framework.md`](docs/framework.md) for how the three layers fit, and [`docs/categories.md`](docs/categories.md) for the rule that puts a skill in one folder only.

MIT. Built and maintained by Aswath S.
