# Build log

What shipped, when, and where. Each entry names the branch, the change and how it was verified.

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
