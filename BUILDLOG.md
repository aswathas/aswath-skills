# Build log

What shipped, when, and where. Each entry names the branch, the change and how it was verified.

## 2026-11-17 — the runtime build, unit 2: `aswath-catalog`
- Branch: `feat/catalog`
- Shipped:
  - `skills/utilities/aswath-catalog/` — the catalogue skill. `catalog.py` writes the skill map
    (`~/.agents/config/skill-map.json`), checks this machine against it, re-points one skill at
    its canonical copy, compares the map with the other PC's, and holds the write lease.
    `selftest.py` runs nine cases against a scratch estate.
  - `skills/orchestration/aswath-capability/` — the live skill ported into the repo, so the
    published copy is the current one, and its seven scripts now read the shared state from
    `~/.agents/state/` instead of the MiniMax runtime directory.
  - `manifest.json` (1.4.0) and `README.md` — the new skill is in the catalogue.
  - Store side: the state moved to `~/.agents/state/` with the old path left as a junction, the
    `.gitignore` states what travels (derived per-skill scores) and what stays (raw events, the
    router's working files, the lease, the secrets), `sync.sh` gained `verify`, and the new
    skill is in the keep list.
- Verified: `catalog check` exits 0 — 354 skills mapped, 66 active entries, every one a
  junction, the keep list and the active set the same set. `selftest.py` -> `9/9 case(s)
  passed`. The ten real violations the estate had before the change (four real directories in
  `skills-active`, each duplicated into `~/.claude/skills`, plus the self-referential junctions
  a first `fix` created) are gone.
- Records: `docs/reviews/decision-log.md` (D13), `docs/reviews/change-inventory.md`.

## 2026-11-17 — the runtime build, unit 3: `aswath-record`
- Branch: `feat/record`
- Shipped:
  - `skills/workflow/aswath-record/` — the run and artifact ledger. `ledger.py` appends records,
    lists what is superseded and what is current, records a delivery, harvests the runs MiniMax
    Code already recorded, reports the metrics and runs the secrets doctor. `selftest.py` runs
    five cases against a scratch directory.
  - `skills/workflow/aswath-delivery/SKILL.md` — it now asks the ledger which artifact ids are
    superseded and deletes exactly those, and records what it sent, instead of guessing from the
    chat.
  - `manifest.json` (1.5.0) and `README.md` — the new skill is in the catalogue.
  - Store side: `~/.agents/ledger/minimax.jsonl` holds the harvested history, `~/.agents/secrets/`
    is the new home for project secrets (gitignored), and the keep list grew to 67.
- Verified: `selftest.py` -> `5/5 case(s) passed`. The import wrote 3683 run lines and reported
  506 failures; a second import added 0 lines. `doctor secrets` exits 0 on this machine and
  prints no value — the two old `.env` files are reported as outside the convention. The first
  version of the doctor's line rule produced 31 false positives on this machine and was narrowed
  until it produced none.
- Records: `docs/reviews/decision-log.md` (D14), `docs/reviews/change-inventory.md`.

## 2026-11-17 — commit discipline, unit delivery (unit 1 of 3)
- Branch: `feat/commit-discipline-unit-delivery`
- Shipped:
  - `skills/workflow/aswath-commit-discipline/SKILL.md` — a sixth obligation: work lands in
    units. The procedure gains "plan the units" before "inventory" and "push per unit"
    after "commit per unit". The push-time checklist gains three boxes.
  - `skills/workflow/aswath-commit-discipline/reference/contract.txt` — the contract text
    the hook prints now carries the unit rule.
  - `skills/workflow/aswath-commit-discipline/reference/delivery.txt` — the short rule the
    hook prints on build-time prompts, before the first commit exists.
  - `skills/workflow/aswath-commit-discipline/reference/record-templates.md` — the delivery
    plan template.
  - `skills/workflow/aswath-commit-discipline/scripts/hook.py` — build-time prompt patterns
    and `delivery_text()`.
  - `docs/reviews/delivery-plan.md` — this change's own three-unit plan.
  - `docs/reviews/prompts.md`, `BUILDLOG.md` — the records this repo did not have yet.
- Verified: `python -m py_compile` on the hook; a replayed `UserPromptSubmit` prompt
  "build me a login screen" printed the delivery rule, and "now push it" printed the full
  contract.
- Records: `docs/reviews/decision-log.md` (D4-D6), `docs/reviews/change-inventory.md`.

## 2026-11-17 — commit discipline, unit delivery (unit 2 of 3)
- Branch: `feat/commit-discipline-unit-delivery`
- Shipped:
  - `skills/workflow/aswath-commit-discipline/scripts/check_push.py` — three new
    warnings. `BULK_COMMIT` when one commit carries more files or lines than the rules
    file allows. `COMMIT_NOT_PLANNED` when a commit in the range matches no unit of the
    plan. `UNIT_NOT_COMMITTED` when a unit is marked `done` and no commit on the branch
    carries it.
  - The plan governs only the work it was written for: it applies when it changed in the
    range, or when it does not exist at the point the branch forked from. A plan merged
    earlier governs that merge, not later work.
  - `skills/workflow/aswath-commit-discipline/reference/doc-rules.json` — the plan path
    and the two bulk thresholds.
  - `skills/workflow/aswath-commit-discipline/SKILL.md` — the wording of the two new
    codes now matches what the checker says.
- Verified: a scratch repository with a `main` branch and a feature branch produced
  `BULK_COMMIT` for a 32-file commit, `COMMIT_NOT_PLANNED` for a commit matching no
  unit, `UNIT_NOT_COMMITTED` for a unit marked done with no commit, and nothing for the
  `chore:` commit. A second scratch repository with the plan merged to `main` reported
  neither new warning for a later unrelated branch.
- Records: `docs/reviews/decision-log.md` (D7-D9), `docs/reviews/change-inventory.md`.

## 2026-11-17 — commit discipline, unit delivery (unit 3 of 3)
- Branch: `feat/commit-discipline-unit-delivery`
- Shipped:
  - `skills/workflow/aswath-commit-discipline/scripts/test_check_push.py` — the
    checker's self-check. Six assertions over five scratch repositories: a compliant
    branch stays quiet, a 31-file commit raises `BULK_COMMIT`, a commit matching no unit
    raises `COMMIT_NOT_PLANNED`, a `chore:` commit does not, a unit marked done with no
    commit raises `UNIT_NOT_COMMITTED`, and a plan inherited from `main` stays quiet.
  - `skills/workflow/aswath-commit-discipline/SKILL.md` — the command that runs the
    self-check.
  - `manifest.json` — version 1.3.0, and the description states the unit rule.
  - `README.md` — the catalogue row states the unit rule and names the plan file.
- Verified: `python skills/workflow/aswath-commit-discipline/scripts/test_check_push.py`
  -> `5/5 case(s) passed`, exit 0.
- Records: `docs/reviews/decision-log.md` (D10-D11), `docs/reviews/change-inventory.md`.

## 2026-11-17 — the learning loop (unit 4 of the runtime build)
- Branch: `feat/improve`
- Shipped:
  - `skills/workflow/aswath-improve/scripts/gate.py` — the gate suite. The catalogue agrees with
    the tree; the diff stays under `skills/` or `docs/`; every touched skill's own self-check
    exits 0. `manifest.json`, `install.ps1`, `install.sh` and any deletion inside `skills/` are
    refused by name.
  - `skills/workflow/aswath-improve/scripts/improve.py` — the loop. `propose` turns the ledger's
    open failures into a diff on the skill that owns them. `run` branches, commits, pushes, opens
    the pull request, runs the gate, merges on green, checks the merged tree, and reverts the merge
    with a new commit when that check fails.
  - `skills/workflow/aswath-improve/scripts/selftest.py` — eight cases against a scratch repo with
    a stub `gh` and a local remote.
  - `skills/workflow/aswath-improve/SKILL.md` — the flow, the gate, the merge policy, the revert.
  - `skills/workflow/aswath-record/scripts/ledger.py` — `add` takes `--skill`, so a run can be
    filed against the skill that owns it.
  - `manifest.json` — version 1.6.0, and the `aswath-improve` row. `README.md` — the workflow row
    and the layout block.
- Verified: `python skills/workflow/aswath-improve/scripts/selftest.py` -> `8/8 case(s) passed`,
  exit 0. `gate.py check --repo . --base main --head main` -> green on this repo.
- Records: `docs/reviews/decision-log.md` (D15), `docs/reviews/change-inventory.md`.

## 2026-11-17 — the loop's commands wear the spec's names (unit 8 of the runtime build)
- Branch: `fix/improve-commands`
- Shipped:
  - `skills/workflow/aswath-improve/scripts/improve.py` — the subcommands `propose` and `run`
    become the flat flags `--dry-run` and `--run`. The proposal is a function both paths call,
    and `--run` with no `--diff` writes the proposal first and runs that.
  - `skills/workflow/aswath-improve/scripts/selftest.py` — the cases call the flags, and the
    dry-run case now asserts that no pull request was opened.
  - `skills/workflow/aswath-improve/SKILL.md` — the flow, the commands and the closing line name
    the flags.
- Verified: `python skills/workflow/aswath-improve/scripts/selftest.py` -> `8/8 case(s) passed`,
  exit 0.
- Records: `docs/reviews/decision-log.md` (D16), `docs/reviews/change-inventory.md`.

## 2026-11-17 — the estate's clock (unit 5 of the runtime build)
- Branch: `feat/schedule`
- Shipped:
  - `skills/utilities/aswath-schedule/scripts/schedule.py` — `add` creates a Windows Task Scheduler
    task named `Aswath\<name>` from UTF-16 task XML with the "run as soon as possible after a missed
    start" flag; `remove` deletes it; `list` prints the Windows tasks, the Claude Code task list
    and the MiniMax cron table in one place, marking the finished one-shots dead.
  - `skills/utilities/aswath-schedule/scripts/selftest.py` — seven cases, including a live task that
    appears in `schtasks /query` and is gone after `remove`.
  - `skills/utilities/aswath-schedule/SKILL.md` — the jobs, the commands, the two estate jobs.
  - `manifest.json` — version 1.7.0, and the `aswath-schedule` row. `README.md` — the utilities row
    and the layout block.
- Machine-local: the two estate tasks — `Aswath\catalog-verify` at 09:00 and `Aswath\improve` at
  09:30 — are created and visible; the keep list is 69; the map is rebuilt at 357 skills.
- Verified: `python skills/utilities/aswath-schedule/scripts/selftest.py` -> `7/7 case(s) passed`,
  exit 0. `catalog.py check` -> clean.
- Records: `docs/reviews/decision-log.md` (D17), `docs/reviews/change-inventory.md`.

## 2026-11-17 — the loop closes what it fixed (unit 9 of the runtime build)
- Branch: `fix/improve-closing`
- Shipped:
  - `skills/workflow/aswath-improve/scripts/improve.py` — a successful merge records a successful run
    of each job the proposal fixed, under that job's own name, so the failure it repaired stops
    being open. "Nothing to do" exits 0; a real error still exits 1.
  - `skills/workflow/aswath-improve/scripts/selftest.py` — a ninth case: a seeded failure, a run
    with no diff, the ledger holding the success, and the next dry run finding nothing.
  - `skills/workflow/aswath-improve/SKILL.md` — the two rules.
- Machine-local: the ledger records the successful run of "the keep list and the active set stay in
  step after a publish", which closes the estate's one open failure.
- Verified: `python skills/workflow/aswath-improve/scripts/selftest.py` -> `9/9 case(s) passed`,
  exit 0.
- Records: `docs/reviews/decision-log.md` (D18), `docs/reviews/change-inventory.md`.

## 2026-11-18 - a job description becomes a tailored resume (unit 10)
- Branch: `feat/resume-tailor`
- Shipped:
  - `skills/writing/aswath-resume-tailor/` - the skill, the generic builder (`scripts/build_resume.py`),
    and two references: the resume JSON schema and the JD-to-evidence rules.
  - `manifest.json`, `README.md`, `docs/categories.md` - the catalogue rows and the category note.
- Machine-local: the private profile and the SuperDream variant in `~/.agents/state/resume/`, a
  pinned router rule in `~/.routing/routes.static.json`, and a rebuilt catalogue (587 records).
- Verified: the builder turned the SuperDream variant into a one-page PDF (4,995 characters, no
  placeholder), and the router fires the pinned rule on "tailor my resume for this job description".
- Records: `docs/reviews/decision-log.md` (D19), `docs/reviews/change-inventory.md`.

## 2026-11-18 - the skill goes public and generic (unit 11)
- Branch: `feat/resume-tailor-public`
- Shipped:
  - `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.claude-plugin/icon.png` - the
    repo is now a Claude Code plugin and a marketplace, so anyone installs with one line:
    `/plugin install aswath-skills --marketplace aswathas/aswath-skills`.
  - `skills/writing/aswath-resume-tailor/assets/profile.template.json` - an empty profile to copy.
  - `skills/writing/aswath-resume-tailor/scripts/selftest.py` - six cases over the builder.
  - `SKILL.md` and `references/schema.md` - the profile is found by search order, so the author's
    private store is an option, not a requirement.
- Verified: `claude plugin validate .` -> `Validation passed`;
  `python skills/writing/aswath-resume-tailor/scripts/selftest.py` -> `6/6 case(s) passed`.
- Records: `docs/reviews/decision-log.md` (D20), `docs/reviews/change-inventory.md`.

## 2026-11-18 - a Google Form, filled and submitted, by one script (unit 12)
- Branch: `feat/gform-fill`
- Shipped:
  - `skills/utilities/aswath-gform-fill/` - the skill, the driver script (`scripts/gform.mjs`) and the
    answers schema (`references/answers.md`). One persistent Chrome profile, one sign-in, an
    `inspect` that dumps every page and question, a `fill` that matches answers to the real
    question headings, handles rating grids and branch re-render, and a dry run that stops before
    the one irreversible Submit click.
  - `manifest.json`, `README.md`, `docs/categories.md`, `.claude-plugin/*.json` - the catalogue rows
    and the plugin listing, version 1.9.0 -> 1.10.0.
- Verified: the ECE end-of-course survey was submitted once through this method and the page read
  "Thank you for your response"; `inspect` and `fill --no-submit` were run against the live form.
- Records: `docs/reviews/decision-log.md` (D21), `docs/reviews/change-inventory.md`.

## 2026-11-18 - any email, not one email (unit 13)
- Branch: `feat/gform-multi-account`
- Shipped:
  - `skills/utilities/aswath-gform-fill/scripts/lib.mjs` - the account store and the TOTP code.
    `~/.gform-accounts.json` (or `$GFORM_ACCOUNTS`) holds the email, the port, the profile path,
    the password and the TOTP secret. It stays on the machine and is never committed.
  - `scripts/gform.mjs` - `account list|add|remove`, and `--email` now picks the profile, the
    DevTools port and the saved credentials. Each email gets its own profile and its own port, so
    several accounts stay signed in side by side. The 2FA code is computed in-process; the human
    typing it into the visible window is still the fallback.
  - `commands/gform-fill.md` - the `/gform-fill` plugin command: list the accounts, add one if
    missing, inspect, dry run, submit only when nothing is missing.
  - `SKILL.md` rewritten around the account workflow; `manifest.json`, `README.md` and
    `.claude-plugin/*.json` at version 1.10.0 -> 1.11.0.
- Verified: `node scripts/selftest.mjs` -> `18 passed, 0 failed`, including three RFC 6238 vectors
  and the account store round trip. `account add` -> `list` -> `remove` run against a temp store.
- Records: `docs/reviews/decision-log.md` (D22), `docs/reviews/change-inventory.md`.
