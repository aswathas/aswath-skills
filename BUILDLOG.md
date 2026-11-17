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
