# <Task name> — Spec

Status: Draft for user review
Date: YYYY-MM-DD

## 1. Problem & user

*What problem exists, for whom, and what does the user gain when this is done? Name the person and the job to be done.*

## 2. Scope — in / out

*What this task delivers (in), and what it deliberately does not (out). Be explicit about the boundary.*

## 3. Success criteria (measurable)

*Each criterion observable and testable — a state that is true or false, not a quality. Say how each is verified.*

## 4. Constraints & environment

*Runtime, language, harness, existing code, time and platform limits that the solution must live inside.*

## 5. Approach — chosen, with rejected alternatives and why

*The chosen approach, the alternatives rejected, and the reason each was rejected. A spec with one option considered is a decision, not a decision record.*

## 6. Architecture, components & data flow

*Components and their responsibilities, how data moves between them, and where state lives.*

## 7. Failure modes & error handling

*What goes wrong, how it is detected, what the user sees, and what the system does next.*

## 8. Test plan

*What proves each success criterion, what it runs against, and what counts as passing.*

## 9. Implementation ownership — *agent implements* / *learner implements* + build order

*State who writes the implementation — agent or learner — then the order in which the pieces get built.*

## 10. Risks, assumptions, and what would invalidate this spec

*What could be wrong, what this spec assumes, and what observation would prove the spec itself wrong. Record every assumption here, and record each question with the answer given — or the answer you assumed — here too. A sibling `questions.md` beside this spec may hold the questions and answers instead; no file that looks like implementation may hold them.*

## Exit condition

The spec is complete only when all ten sections above are filled with concrete
content, no section contains `TBD`/`TODO`/an empty placeholder, and the user
has said "approved" in response to seeing this file. An agent may not declare
the spec complete on its own judgement. If a section cannot be filled, write
the assumption explicitly in section 10 and ask the user about it.
