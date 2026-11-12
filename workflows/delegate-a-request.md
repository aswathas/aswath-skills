# Workflow: delegate-a-request

**Use when** the owner hands over a raw request and wants it executed end to end.

| # | Skill | Gate |
|---|---|---|
| 1 | `aswath-throw` | Request turned into a harness work item: brief, leader-authored test, agent pool, two independent verifiers (one adversarial). |
| 2 | `aswath-capability` | Only if the work item needs units that do not exist yet — a missing skill, subagent, hook or MCP. Resolves from the registry, authors the gap. |
| 3 | `aswath-throw` (report) | Proven artefact plus the verification output, not a summary of effort. |

## Rules

- The owner does not write briefs. Writing the brief is step 1's job, and the brief is shown before the pool runs.
- The test is authored by the leader before the agents run, not after. A test written to match the output proves nothing.
- Two verifiers, independent. Same-model self-check is not verification.
- A gap is information, not failure. Name it, author it, continue — do not silently work around it.

## Done when

The artefact passes a test that was written before it existed, and both verifiers' output is attached.
