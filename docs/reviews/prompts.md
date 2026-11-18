# Prompt record

The prompts that shaped the work, verbatim. `aswath-chronicle` keeps the same trail; this file
is the copy that travels with the commit.

Template: `skills/workflow/aswath-commit-discipline/reference/record-templates.md`.

---

## 2026-11-17 — commit-discipline unit delivery

- Prompt: "i want to updte aswath documentaion skill"
- Prompt: "aswath-commit-discipline" / "Extend the contract"
- Decision it produced: D4, D5, D6 in `decision-log.md` — the contract grows a sixth
  obligation, the unit plan is written before the first commit, and the build-time hook
  prints the short delivery rule.
- Work it caused: `skills/workflow/aswath-commit-discipline/` gained the per-unit rule, the
  delivery plan template and the build-time prompt path.

## 2026-11-17 — per-unit commits and pushes

- Prompt: "if am doing a project or any work the push should have lot / multiple commits
  meaning ful commits every step needs to docuemnated or commited not bulk single push if
  design an app with 4 feature each feature and its builds shodl be commited in a way that
  we planned"
- Decision it produced: D4 — one commit and one push per unit, planned in
  `docs/reviews/delivery-plan.md`.
- Work it caused: the delivery plan for this change itself
  (`docs/reviews/delivery-plan.md`, three units), and the checker work that follows in the
  second unit.

## 2026-11-17 — the runtime spec

- Prompt: "https://github.com/swamp-club/swamp/ , analyse this"
- Prompt: "do /leanrea on this github repo"
- Prompt: "use simple caveman termsn adn explain me what is swamp"
- Prompt: "swamps owns the half we fake , whats the meaning?"
- Prompt: "so how can we solve this in our system"
- Prompt: "i want to create a engine like swamp which can learn and update this ( will this owrk) /ponytail"
- Prompt: "tell us our gaps in simple words"
- Prompt: "how to solve thiss"
- Decision it produced: D12 in `decision-log.md` — the eight gaps, the four skills, the gate and
  the revert. The spec is `docs/superpowers/specs/2026-11-17-runtime-design.md`.
- Answers given to the four questions the spec depended on:
  1. "Split: skill public, data private" — the skill code lands in `aswathas/aswath-skills`, the
     ledger, the state, the map and the secrets land in `aswathas/agent-store`.
  2. "All 8 gaps in one spec" — one document covers all eight.
  3. "Private store, git-tracked" — the ledger is `~/.agents/ledger/<project>.jsonl`, tracked.
  4. "Auto-merge when checks pass" — the loop merges its own pull request when the gate is green,
     and reverts the merge if the post-merge check fails.
- Work it caused: the spec, and the decision log entry that records why `swamp` is not adopted.

## 2026-11-17 — the runtime build

- Prompt: "approved  solve all the gaps"
- Decision it produced: the approval gate in `aswath-first-principles` is lifted. The spec at
  `docs/superpowers/specs/2026-11-17-runtime-design.md` is approved as written, and units U1 to
  U4 build it — `aswath-catalog`, `aswath-record`, `aswath-improve`, `aswath-schedule` — one
  commit and one push per unit.
- Work it caused: unit 2, `aswath-catalog` (`feat/catalog`), unit 3, `aswath-record`
  (`feat/record`), unit 4, `aswath-improve` (`feat/improve`) and unit 5, `aswath-schedule`
  (`feat/schedule`), with the store-side work that describes where the estate's own files live and
  what it ran.
## 2026-11-18 - the reusable resume skill
- Prompt: "i want too yuo to create this skills as resuable tool or skill which can used again for
  upcoming or any job jd /obra/superppowers use our router"
- Decisions it produced:
  1. D19 in `decision-log.md` - the skill is a JSON variant per role; the base profile is never
     edited for a posting; the gap list is part of the answer.
  2. The skill lands in `writing/`, because it answers "how should this be said" for one reader.
  3. "Use our router" means the pinned rule in `~/.routing/routes.static.json` and a rebuilt
     catalogue: the router reads the skill's frontmatter, so a skill with a good description is
     routable by construction.
  4. Public code, private data: the skill ships in `aswathas/aswath-skills`, the profile JSON and
     the variants live in the private `aswathas/agent-store`.
- Work it caused: `skills/writing/aswath-resume-tailor/` (skill, builder, two references), the
  manifest row, the README row, the category note, the pinned router rule, and the private profile
  and SuperDream variant.
