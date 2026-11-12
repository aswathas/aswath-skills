# Workflow: publish-everywhere

**Use when** one artefact has more than one destination.

| Order | Skill | Gate |
|---|---|---|
| 1 | `aswath-publish-github` | Repo or gist exists and the URL is recorded. |
| 2 | `aswath-publish-linkedin` | Body has one link at most, at the end or in the first comment. |
| 3 | `aswath-publish-instagram` | Session is logged in. A logged-out session is a stop, never a retry loop. |

## Rules

- Same artefact, not the same text. Each destination gets the shape it reads best in; the claim stays identical.
- Publish once per destination. A failed publish is reported, never retried.
- Record every returned URL in one place. Three posts and no links is an unverifiable claim.
- No mention/tag unless the account has a real URN for it.

## Done when

Each destination has one post and one recorded permalink.
