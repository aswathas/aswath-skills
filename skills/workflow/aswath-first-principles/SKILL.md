---
name: aswath-first-principles
description: Use when a new project, feature, or build task has no approved spec yet, and the work would otherwise start from assumptions
---

## Overview

Decide before you build; a later spec only describes what was built.

## When to Use

Use when work starts from assumptions — new project, feature, unfixed scope, unmade decision. Skip only when the task changes no files and needs no decision.

## The Loop

1. **Context** — read repo, docs, commits, specs. *Gate:* context known.
2. **Research** — dispatch `task` (`agent_name: "explore"`) for the facts the questions need; with no such tool, research them yourself, read-only. *Gate:* facts in hand.
3. **Questions** — ask per the Question Loop; no questionnaire tool? write them out with options and recommendation. *Gate:* the user owns the choices.
4. **Spec** — write it per The Spec, from `reference/spec-template.md`. *Gate:* file written.
5. **Self-review** — placeholder scan, consistency, scope, ambiguity; fix inline. *Gate:* no `TBD`.
6. **Approve** — show the spec path, wait for explicit approval. **Hard gate.** Unapproved is parked, not abandoned: on resume, restate the spec path and what is awaited; do not proceed.
7. **Mint** — mint the skill per Minting below. *Gate:* skill written.
8. **Execute** — follow the minted skill. *Gate:* build to the approved spec.

## The Question Loop

Batch independent questions (≤4 per `ask_user` questionnaire); ask singly when an answer changes the rest. Multiple choice, always with a recommended option and rationale. Each must be a **choice the user owns**, not a tool-answerable fact. Recommend; never decide. A second batch is legitimate when independent of the first batch's answers; drop any question it invalidates. With no questionnaire tool, write each question out with options and recommendation, record the answer assumed — an assumption is a placeholder for an answer, never a substitute; if the user answers differently, their answer wins, so revise the spec and re-show it — and still stop at the approval gate. Record questions and answers in section 10 or a sibling `questions.md` beside the spec, never in a file that looks like implementation.

## The Spec

Path: `docs/superpowers/specs/YYYY-MM-DD-<slug>-design.md` in the repo that will hold the implementation; if none, "where does this live?" is the user's choice. Slug: lowercase, hyphenated, no dates, shared with `aswath-<slug>`. Template: `reference/spec-template.md`.

```markdown
## Exit condition

The spec is complete only when all ten sections above are filled with concrete
content, no section contains `TBD`/`TODO`/an empty placeholder, and the user
has said "approved" in response to seeing this file. An agent may not declare
the spec complete on its own judgement. If a section cannot be filled, write
the assumption explicitly in section 10 and ask the user about it.
```

## Approval Gate

**No implementation file for this task may be created until the user has
approved the written spec.** This includes scaffolding, package manifests,
config files, and "just a quick stub". Approval is the user's word, on a spec
they have been shown. If the spec changes after approval, approval lapses.

If you catch yourself about to write code: stop, and ask. Being told "just
build it" is not approval of a spec that does not exist yet — say that plainly
and offer to write the spec first.

Approval is the user's word on a spec they saw; a changed spec needs fresh approval. Pushback: revise, re-show, wait.

## Minting

After approval, mint `skills/catalog/aswath-<slug>/SKILL.md` recording what this task learned, so the next similar task starts from a decision, not zero. The procedure belongs to `aswath-forge`.

## Rationalisation Table

| Rationalisation | Reality |
| --- | --- |
| "The request was a single small utility with one flag, so a spec would have been restating the prompt." | Smallness is when a spec is cheapest and decisions go silent; it records decisions, not tasks. |
| "I implemented it directly against an explicit, self-checked contract ... and encoded that contract as the 17-test suite rather than in prose." | Tests lock in implementation decisions; they cannot catch a decision the user never made. |
| "None of these blocked the work; each was resolved with a documented default." | Not blocking is not decided; behaviour-changing defaults are the user's. |
| Added `--delimiter`, `--no-header`, `--no-coerce`, `--indent`, stdin input and file output. | Six unrequested features, each a promise nobody agreed to. |
| Asked zero questions and reported four decisions it had already made. | Those questions were all choices — what this loop collects. |

## Red Flags

STOP when you think:

- "The request is small" — decisions go silent.
- "The tests are the spec" — unseen decisions.
- "It doesn't block" — not decided.
- "I can add this flag later" — unagreed promise.
- "I asked no questions" — they were choices.
- "The user said just build it" — not approval.

## Common Mistakes

- Asking for facts, not choices.
- Batching dependent questions.
- Spec outside the repo that will hold the implementation.
- Minting before approval.
- "Sounds good" treated as approval.
- Leaving `TBD` for a hard section.
