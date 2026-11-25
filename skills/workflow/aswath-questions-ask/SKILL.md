---
name: aswath-questions-ask
description: Use when the user wants to be questioned until a shared understanding exists - "ask me lots of questions", "quiz me", "test my understanding", "make sure we both understand X", "ask me questions until I'm clear" - before or while study material, a build or an explanation is written
---

## Overview

A shared understanding is a thing two people hold. The interview is how you find
out whether you do. Asking questions is not politeness before the work — it *is*
the work, for as long as it takes to make the user's mental model and yours the
same shape.

The output of this skill is a written **understanding ledger**: every concept,
marked understood / shaky / unknown, with the user's own words kept. That
ledger is what a later build consumes, and what the user revises from.

## When to Use

Use when the user asks to be asked, questioned, quizzed, interviewed, or tested.
Use it when a study topic, a build, or an explanation depends on concepts the
user may not hold yet and the gap is invisible from the outside. Skip it when
the user wants the answer, not the questions.

## The Loop

1. **Scope** — name the subject and the depth in one sentence, and agree it.
   *Gate:* the subject is bounded.
2. **Map** — list the concepts the subject decomposes into, ranked by how much
   the rest depends on them. *Gate:* a spine, not a topic dump.
3. **Probe** — ask, per The Question Ladder. *Gate:* an answer per question.
4. **Mark** — for each concept: `understood` (explains it unprompted, with
   example and consequence), `shaky` (correct only when prompted or by rote),
   `unknown` (cannot answer). *Gate:* every map entry is marked.
5. **Re-aim** — next questions target `shaky` and `unknown` only, hardest
   dependency first. *Gate:* the loop repeats until no `unknown` remains.
6. **Lock** — print the ledger in chat: the user's words per concept, the one
   analogy that worked, the trap they fell into, the remaining doubt in their
   own words. *Gate:* the user says the ledger is right.
7. **Write** — only now, and only to the ledger path, write the ledger file.
   Every row quotes the user's answer verbatim. *Gate:* the file exists and
   holds nothing the user did not say.
8. **Hand off** — the ledger is the input to whatever comes next: notes, a
   build, a plan. Name that consumer explicitly.

Never stop at step 4. "Correct answer" is not understanding; a rehearsed
definition is `shaky` until the user applies it to a new case.

### Short on time

When the deadline is hours, not days, the loop shrinks instead of the depth
dropping:

- Interview **only the topics that carry marks** — never the ones marked
  skip. Ask which those are, or take them from the exam weight.
- Run rungs **1 → 2 → 6** only. Recall, explain, apply. Rungs 3–5 and 7
  are dropped: they cost turns and do not change what the notes must contain.
- Spend the remaining budget on `shaky` and `unknown` only, hardest
  dependency first.
- Record `not interviewed` for every topic left out, so the gap is visible
  in the ledger instead of silent.

## Read-only until locked

While this skill runs, **you do not write any file**. Read, search and think
are free. The interview happens in chat, and the ledger is printed in chat
before anything touches disk.

A hook enforces this — not your discipline. `hooks/write_guard.py` blocks
every write while the interview is open, and blocks everything except the
ledger path after the user says `LOCK`. The rules it applies, the state
machine and the known holes are in
[references/write-guard.md](references/write-guard.md). Read that file only if
a write is blocked and you need the escape hatch.

The user's words are the ledger's raw material, so the file can only be
written once they have been said. Writing earlier means writing from your own
head — the exact failure the skill exists to prevent.

## The Question Ladder

Climb one rung per concept. Do not skip down.

| Rung | Ask | What it proves |
|---|---|---|
| 1 Recall | "What is X?" | vocabulary |
| 2 Explain | "Explain X to me as if I know nothing about it." | structure exists |
| 3 Why | "Why does X exist? What broke without it?" | the problem it solves |
| 4 How | "Walk me through X step by step." | mechanism, in order |
| 5 Contrast | "How is X different from Y?" | boundaries |
| 6 Apply | "Here is a new case. What happens?" | transfer |
| 7 Trap | "What is the most common mistake here?" | self-monitoring |

Rung 6 is the decisive one. A concept is only `understood` when the user
applies it to a case they have not seen. Use a case from the syllabus, a real
company, or a hypothetical you construct — never the example the user was
taught.

## How to Ask

- **Batch independent questions.** Up to four per `AskUserQuestion` batch.
  Questions that depend on each other's answers go one at a time.
- **Choices get options; open questions get prose.** Use the questionnaire tool
  for anything with a small set of plausible answers (with a recommended option
  and a reason). Write open questions out as plain text in the reply.
- **Ask for the user's own words.** "Say it how you'd say it" gets a model you
  can build on. A polished definition gets a rehearsed model.
- **Ask one thing.** Two questions in one sentence get one answer.
- **Never lead.** Do not embed the answer in the question. If the user has not
  named a term, describe the situation and ask what it is called.
- **Praise nothing.** "Correct" adds no information. Move to the next rung or
  the next concept.
- **Do not lecture mid-loop.** If an answer is wrong, ask a narrower question
  that exposes the gap. Explanations belong in the notes, not in the interview.

## Question quality bar

A good question for this loop:

- tests one concept at one rung,
- has an answer that is checkable,
- cannot be answered "yes" or "it depends",
- is not already answered in the source material the user will read,
- is not a fact the tool can look up — the user must own it.

Bad: "Do you understand hashes?" / "What are the five types of blockchain?"
(as a bare list the user recites).

## The Understanding Ledger

Written to a file so the next step and the next session can use it. Path:
`docs/understanding/<subject-slug>.md` in the repo that holds the work, or
`Understanding/<subject> understanding ledger.md` beside the vault when the
subject is a study topic. Both paths are on the hook's ledger allowlist.

Print the ledger in chat first. Write the file only after the user says
`LOCK`.

```markdown
# Understanding — <subject>

Scope: <one sentence agreed in step 1>
Depth: <rung the user is being held to>

## Concepts

| Concept | Mark | User's words | Trap hit |
|---|---|---|---|
| Merkle tree | understood | "a receipt for the receipts" | — |

## Open doubts (the user's own words)
- <verbatim>

## Analogy that landed
- <concept> → <the analogy the user used>

## Handoff
Consumed by: <notes build / plan / answer>
```

Keep the user's words. A paraphrased ledger is a summary; the paraphrasing is
where understanding quietly goes wrong.

## Handoff

- **Study material** — the ledger decides emphasis: `shaky` and `unknown`
  concepts get the deep note, the worked example and the most recall cards;
  `understood` concepts get the crisp treatment. The user's own analogies
  become the note's analogies, because they are the ones that will be
  recalled under exam pressure.
- **A build** — the ledger is the concept list the build must satisfy, and the
  `unknown` list is the acceptance criteria.
- **An explanation** — the ledger says how far to go before stopping.

## Relationship to other skills

- `aswath-first-principles` decides *what to build* before any code exists.
  This skill decides *whether the person understands it*. Run this one first
  when the build's correctness depends on the user holding the concepts.
- `aswath-study-technique` builds the vault. This skill decides what the vault
  must hammer, and the ledger's analogies and traps go into it.
- `aswath-thevai` asks a person outside the session over WhatsApp and ends at
  an approved brief. This one asks the user in the session and ends at a shared
  model.

## Rationalisation Table

| Rationalisation | Reality |
| --- | --- |
| "I asked twenty questions and got twenty right answers, so they understand it." | A question answered from memory proves recall, not understanding. Rung 6 is the test. |
| "The ledger says every concept is understood, so I can skip the notes." | The ledger is a map of the user's head, not a substitute for the notes. It steers them. |
| "I'll paraphrase the user's words into standard terminology." | Paraphrasing is where the gap hides. Their phrasing is the thing that survived. |
| "The user got one wrong, so they need the whole subject re-taught." | One wrong answer is one concept at one rung. Re-aim at it. |
| "I asked the questions in the order the syllabus lists them." | The syllabus lists for the examiner. Teach along the dependency spine. |
| "I'll make the interview short because the notes are the real work." | The notes teach a concept the user does not hold. That is the note's failure, not the interview's cost. |

## Red Flags

STOP when you think:

- "They answered correctly, so they're done."
- "I've asked enough questions."
- "I'll explain it to them instead — that builds understanding too."
- "The ledger can be written from my understanding of the subject."
- "This question is probably too hard for them."
- "Let me confirm the definition before we start."
- "I'll write the ledger now and tidy it later." — before `LOCK`, no file.
- "I'll write it in my own words, it reads better." — the ledger quotes.
- "I'll save a note to remember where we got to." — the hook will block it.

## Common Mistakes

- Quizzing trivia instead of testing structure.
- Asking only rung-1 questions because they are fast.
- Moving on when an answer is recited rather than reasoned.
- Interrogating without a map, so the questions wander.
- Asking the same concept at the same rung twice because the answer sounded good.
- Writing the ledger from your own head instead of their answers.
