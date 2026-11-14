# Categories

Six folders. One rule: **a skill lives in the folder of the question it answers.**

| Folder | The question | Skills |
|---|---|---|
| `context/` | "What is this session carrying, and what do I cut?" | token-guard, token-ledger, token-evaluator, compact |
| `publishing/` | "How does this leave the machine?" | publish-github, publish-linkedin, publish-instagram |
| `workflow/` | "What do I decide before I write code, and what do I record after?" | first-principles, forge, commit, chronicle, throw, thevai |
| `orchestration/` | "Which units should this job be made of?" | capability, manual-demo |
| `writing/` | "How should this be said?" | talk |
| `utilities/` | "One narrow transformation, done properly." | csvjson |

## Judgement calls

- **Token tools vs. compact.** `compact` produces an artefact (a handoff file). The three token skills produce measurements. Measurement belongs in `context/`; the artefact also belongs in `context/` because the question is the same.
- **commit vs. chronicle.** Both write records. `commit` writes the record *at commit time*; `chronicle` keeps the record running across a build. Both are `workflow/` because both answer "what do I record, and when".
- **throw vs. capability.** `throw` accepts a raw request and runs the harness end to end. `capability` assembles what the harness should consist of. Both are orchestration; neither is a workflow step of the other, though `delegate-a-request` chains them.
- **thevai vs. first-principles.** Both answer "what exactly are we building?" before any code. `first-principles` asks the user in the session; `thevai` asks a person outside it, over WhatsApp, one question at a time, and ends with that person approving the brief. The source of the requirement decides which one runs. Both are `workflow/`.
- **thevai vs. delivery.** Both are the same conversation with the same person on the same channel, at its two ends: `thevai` collects the requirement and ends with that person approving the brief; `delivery` hands the finished work back and leaves only the final version in the chat. The source of the requirement decides the first; the state of the chat decides the second. Both are `workflow/`.
- **publish-github is publishing, not workflow.** It creates and pushes, but the question it answers is "how does this get out", which is the same question LinkedIn and Instagram answer.

## What does not go here

- Vendor automation packs (the hundreds of `*-automation` skills). Those are installed, not authored; this repo tracks only the `aswath-*` set.
- Anything without a `description` that begins "Use when". That is a document, not a skill.
