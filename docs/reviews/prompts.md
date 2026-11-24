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
## 2026-11-18 - the skill goes public and generic
- Prompt: "put this in pulick also make sure a version of this goes to generic users so taht other
  people can use this skill" and "update this in my skill library / in githhub"
- Decision it produced: D20 in `decision-log.md` - the profile is found by search order, the
  skill ships a template profile, the repo doubles as a Claude Code plugin and a marketplace, and
  the candidate's data stays in the private store.
- Work it caused: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `.claude-plugin/icon.png`, `skills/writing/aswath-resume-tailor/assets/profile.template.json`,
  `skills/writing/aswath-resume-tailor/scripts/selftest.py`, the genericised `SKILL.md` and
  `references/schema.md`, the README install line, and version 1.9.0.

## 2026-11-18 - the reusable Google Form filler

- Prompt: "learn how did you fille this build resuable system whcih can do this when id , password ,
  (2fa if needed) or login by manual opeingin gthen finish gform fasest way"
- Prompt: "JUST WAIT ILL LOGIN DONTR CLOSE OPEN EVEHIME I CAN LOGIN EVEYTHIME YOU OPEN PROECESS
  FIRST DO GOOD PLAN"
- Decision it produced: D21 - one persistent browser and one sign-in, the fill driven by heading
  text, a dry run before the single Submit click, and credentials kept out of the repository.
- Work it caused: `skills/utilities/aswath-gform-fill/` with the script, the skill text and the
  answers schema; the catalogue rows, the plugin manifest and the build log entry.

## 2026-11-18 - any email, not one email

- Prompt: "i want to create this as reusable tool to plugin any emails for filling these forms"
- Decision it produced: D22 - one machine-local account store, one Chrome profile and one
  DevTools port per email, the 2FA computed in-process from the saved secret, and a
  `/gform-fill` plugin command that drives list -> add -> inspect -> dry run -> submit.
- Work it caused: `skills/utilities/aswath-gform-fill/scripts/lib.mjs`, the `account`
  subcommand and the `--email` resolution in `scripts/gform.mjs`, `commands/gform-fill.md`,
  the rewritten `SKILL.md`, the eight new self-test assertions, the catalogue rows and
  version 1.11.0.

## 2026-11-18 - commit and push everything that is pending

- Prompt: "COMITT AND PUSH EVERTHTHING", after "push this dithub"
- Decision it produced: D23 (the commit rule asks for documentation, not for a plan), D24 (the
  capability router's shared state moves under the minimax runtime dir), D25 (the Thevai skill
  speaks plain English by default).
- Work it caused: the three pending units split into three commits (the commit-discipline
  contract, the capability state dir, the Thevai skill text), the delivery-plan rows 14-16, the
  manifest and README descriptions brought back in line, the capability file table de-duplicated,
  and the whole branch pushed and merged.

## 2026-11-18 - the design hook flagged the form test fixture

- Prompt: the design hook's stop-hook finding on `tests/mock-form.html` (overused-font).
- Decision it produced: the fixture is triaged as a false positive - it is a machine-read file
  that reproduces the form DOM for the self-check, with no designed interface - so the value
  `arial` is ignored for the `overused-font` rule and the reason is written into
  `.impeccable/config.json`. The hook's cache file is gitignored.
- Work it caused: `.impeccable/config.json`, one line in `.gitignore`, the inventory rows above.

## 2026-11-21 - the token guard installer and its missing selftest

- Prompt: the agent-infra repair session ("ok lets repair all the things", then "ok lets install
  dejavu"). While committing the store's pending work the token guard selftest was run, and it
  failed against the shipped plugin.
- Decision it produced: the installer's ownership marker is corrected to the string the hook
  scripts actually carry (`token_guard-hook`), the live `~/.minimax/hooks.json` is repaired by
  re-running the corrected installer, and the selftest is rewritten against the real plugin
  instead of being deleted.
- Work it caused: `plugin/install.py`, `scripts/selftest.py`, the decision-log entry, the
  inventory rows above, and the repair of the live hooks file.

## 2026-11-23 — a skill fetched from the internet, judged and minted
- Prompt: "everything also one more feature find the best skill in the internet and
  update automaticallyu or if new task is given get new skills(tested with some evals
  download and load that skill automaticcly for the task and use it then copy that skill
  and store it under aswath skills(forging) ( not use this lets try this additonaly
  copying best skills and building something bettert than them for our own custom
  skills)"
- Decision it produced: D1 in this repo, and D8-D11 in `aswathas/skill-router`.
- Work it caused: `skills/utilities/aswath-rust-security/`, its manifest row, its
  README row, the ledger fix in `aswath-capability/scripts/build-registry.py`, and
  the records above.

## 2026-11-24 — the semantic layer, shipped inside the capability skill
- Prompt: "lets solve the limit"
- Decision it produced: D2 in this repo, and D12-D13 in `aswathas/skill-router`.
- Work it caused: `scripts/embed.py`, `scripts/semantic.py` and the SKILL.md rows
  for both, inside `skills/orchestration/aswath-capability/`.

## 2026-11-24 — precedent routing for interchangeable skills
- Prompt: "solv eit fully >?"
- Decision it produced: D3 in this repo, and D14 in `aswathas/skill-router`.
- Work it caused: `scripts/precedent.py`, the SKILL.md rows for it, and the
  records above. The learning hook change that fills the store lives in
  `aswathas/skill-router`.

## 2026-11-24 — one resolver
- Prompt: "do we need to do more or how to use the router"
- Decision it produced: D4 (the skill's resolver uses the same ranking as the
  command) and D15 in the skill-router repo.
- Work it caused: `rank_with_router()` in `query-registry.py`, mirrored into
  both copies of the file, and the records above.
