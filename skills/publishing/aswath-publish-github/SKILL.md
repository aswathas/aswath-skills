---
name: aswath-publish-github
description: Use when creating a GitHub repository, pushing a project, opening a pull request, cutting a release, or publishing a gist — including phrases like "push to GitHub", "create a repo", "open a PR", "make a release", or "publish this to GitHub".
---

# Publish to GitHub

`gh` CLI, already authenticated on this machine as **aswathas**
(scopes: `repo`, `workflow`, `gist`, `read:org`).

## Before anything

1. `gh auth status` — confirm the account and scopes.
2. **Never commit to the default branch.** Branch first:
   `git switch -c feature/<name>`, commit, push, open a PR.
3. Check the tree for secrets before making a repo public:
   `.env`, `config.toml`, `credentials`, `*.pem`, `*.key`, tokens in code.
   `git log --all -p | grep -iE "token|secret|password|api[_-]?key"` catches
   what a `.gitignore` missed. A deleted secret in history is still a secret.

## Commit identity

```
git config user.name "aswathas"
git config user.email "aswathas20@gmail.com"
```

`aswathas13@gmail.com` resolves to a different account — never use it.
End commit messages with:

```
Co-Authored-By: Claude Code <noreply@anthropic.com>
```

## Common commands

| Task | Command |
|---|---|
| Create + push a repo | `gh repo create <owner>/<name> --public --source=. --remote=origin --push --description "..."` |
| Private repo | same with `--private` |
| Set visibility later | `gh repo edit <name> --visibility public\|private` |
| Push a branch | `git push -u origin <branch>` |
| Open a PR | `gh pr create --title "..." --body "..." --base main` |
| Read a PR | `gh pr view <n>` / `gh pr diff <n>` |
| Checks | `gh pr checks <n>` |
| Merge | `gh pr merge <n> --squash --delete-branch` |
| Release | `gh release create v1.2.0 --notes-file NOTES.md --title "v1.2.0"` |
| Upload a release asset | `gh release upload v1.2.0 ./file.zip` |
| List releases | `gh release list` |
| Gist | `gh gist create file.md --public` |
| Download a gist | `gh gist view <id>` |

## Claude Code plugin publishing

A repo becomes an installable plugin when it carries:

```
.claude-plugin/plugin.json     # the plugin manifest
.claude-plugin/marketplace.json # only when the repo IS the marketplace
skills/<skill>/SKILL.md        # skills the plugin installs
commands/*.md                  # slash commands the plugin installs
```

Then, on any machine:

```
claude plugin marketplace add <owner>/<repo>
claude plugin install <plugin-name>@<repo>
```

`plugin.json` keys that matter: `name`, `description`, `version`, `author`,
`skills` (array of paths to skill dirs), `mcpServers` (command/args/env per
server), `hooks`, `commands`, `agents`.

## Rules

- Do not push, create a repo, open a PR, or cut a release without an explicit
  instruction — pushing to a public remote is not reversible.
- Confirm the target repo and visibility before `gh repo create`. Public means
  the whole history is world-readable.
- Do not delete tags, releases, or branches that were already pushed without
  being asked.
- If the maintainer is expected to edit the branch and squash-merge, expect a
  changed PR: re-read the PR after any push instead of assuming your diff is
  what landed.
- A failing CI check is reported as failing. Do not describe a run as green
  because the command exited zero locally.
