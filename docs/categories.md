# Categories

Six folders. One rule: **a skill lives in the folder of the question it answers.**

| Folder | The question | Skills |
|---|---|---|
| `context/` | "What is this session carrying, and what do I cut?" | token-guard, token-ledger, token-evaluator, compact |
| `publishing/` | "How does this leave the machine?" | publish-github, publish-linkedin, publish-instagram |
| `workflow/` | "What do I decide before I write code, and what do I record after?" | first-principles, forge, commit, chronicle, throw |
| `orchestration/` | "Which units should this job be made of?" | capability, manual-demo |
| `writing/` | "How should this be said?" | talk |
| `utilities/` | "One narrow transformation, done properly." | csvjson |

## Judgement calls

- **Token tools vs. compact.** `compact` produces an artefact (a handoff file). The three token skills produce measurements. Measurement belongs in `context/`; the artefact also belongs in `context/` because the question is the same.
- **commit vs. chronicle.** Both write records. `commit` writes the record *at commit time*; `chronicle` keeps the record running across a build. Both are `workflow/` because both answer "what do I record, and when".
- **throw vs. capability.** `throw` accepts a raw request and runs the harness end to end. `capability` assembles what the harness should consist of. Both are orchestration; neither is a workflow step of the other, though `delegate-a-request` chains them.
- **publish-github is publishing, not workflow.** It creates and pushes, but the question it answers is "how does this get out", which is the same question LinkedIn and Instagram answer.

## What does not go here

- Vendor automation packs (the hundreds of `*-automation` skills). Those are installed, not authored; this repo tracks only the `aswath-*` set.
- Anything without a `description` that begins "Use when". That is a document, not a skill.
