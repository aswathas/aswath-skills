# Workflow: thevai-a-request

**Use when** a real person is the source of the brief — someone asks Aswath for something and the requirement is not yet known.

| # | Skill | Gate |
|---|---|---|
| 1 | `aswath-thevai` | The conversation ends with a brief the person approved. **Gate: they say yes.** No building before this. |
| 2 | `aswath-thevai` (build phase) | Deliverables built to the approved brief, each one rendered and looked at before it is sent. |
| 3 | `aswath-publish-github` | When the work is done and needs to leave the machine. |
| 4 | `aswath-delivery` | The person's chat holds only the final version: the superseded files and status messages are deleted, the current build is sent once, and the staging copies are removed. |

## Rules

- The brief is written in the person's own words. A brief the agent paraphrased into its own vocabulary is not the brief.
- Approval is a gate, not a step. One unanswered question about scope is a reason to keep talking, not a reason to start building.
- If the person cannot answer a hole, the hole is stated as an assumption in the deliverable and in the message — never silently filled.
- Never batch questions. One message, one idea, one question.
- Facts are the agent's job, not the person's. Anything findable in their messages, their files or the workspace is looked up, never asked.

## Done when

Both deliverables are with the person exactly once, the chat holds no superseded copy of either, they have confirmed the result, and the work is committed.
