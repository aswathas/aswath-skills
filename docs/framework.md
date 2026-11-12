# The framework

Three layers. Each one only knows about the layer below it.

| Layer | Unit | Lives in | Changes |
|---|---|---|---|
| **Skill** | One markdown file with a `description` that states its triggers | `skills/<category>/<skill>/` | rarely; a skill that keeps changing is two skills |
| **Workflow** | An ordered chain of skills with gates | `workflows/<name>.md` | when the process changes |
| **Harness** | Whatever reads the skills — Claude Code, Command Code, anything | outside this repo | never |

## Rules

1. **A skill does one job.** If the description needs an "and" to be accurate, split it.
2. **The description states triggers, not procedure.** "Use when the session is filling" — not a summary of the steps. A summary in the description lets an agent skip the body.
3. **A workflow never contains procedure.** It names skill, order, gate, and what to do when a gate fails. The steps live in the skills.
4. **No skill depends on another skill's file layout.** Dependencies are named ("invoke `aswath-first-principles`"), never path-imported.
5. **Every skill is invocable alone.** A workflow is a convenience, not a requirement. If a skill only works inside its chain, it is a step pretending to be a skill.

## Invocation

| Surface | How |
|---|---|
| Slash command | `/aswath-token-guard` |
| Natural language | "check what's eating my context" → the skill's description matches |
| Explicit | "run aswath-commit" |
| From a workflow | the workflow names the skill and the gate |

All four hit the same `SKILL.md`. There is no second copy and no generated variant.

## Adding a skill

1. Pick the category — the one whose question the skill answers. See `categories.md`.
2. Create `skills/<category>/aswath-<slug>/SKILL.md`.
3. Frontmatter: `name: aswath-<slug>` and a `description` beginning "Use when …".
4. Add the row to `manifest.json` and the README table.
5. Re-run `install.ps1` so the harnesses see the new link.

## Removing a skill

Delete the folder, the manifest row, the README row, then re-run the installer. Never leave a symlink pointing at a deleted directory; `install.ps1 -Force` repairs dangling links.
