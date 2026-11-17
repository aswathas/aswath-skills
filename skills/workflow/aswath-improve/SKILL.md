---
name: aswath-improve
description: Use when a skill keeps failing and should change itself — the run ledger holds a failure with no later success, and the change has to reach the published repo without a human in the middle. Writes the diff, opens the pull request, runs the gate, merges when the gate is green, and reverts the merge when the check after it fails.
---

# aswath-improve

The loop that lets the estate learn from its own runs.

The failure this exists to prevent: a skill fails the same way three times, and nothing in the
repo says so — so the next session repeats the failure and the estate never gets better. The
other failure is worse: a machine editing its own skills lands a broken change in the published
repo and nobody notices for a week.

Both are closed the same way. The change goes out as a pull request, a gate decides, and the
machine may merge only what the gate cleared.

## The flow

```
ledger failures -> a diff on one skill -> a pull request -> the gate -> merge, or stop
                                                                    |
                                                       after the merge: the check again
                                                                    |
                                              red -> a revert commit, and an issue
```

1. **Find the open failures.** A failure is open when the ledger holds a failed run of a skill
   and no later successful run of the same job. A later success closes it; a failure that names
   no skill has no skill to change and is left alone.
2. **Write the diff.** `--dry-run` records the open failures in the skill that owns them, as a
   `## Known failures` section. It touches no git state: the output is a diff file. When there is
   nothing to change it says so and exits 0 — a check that found nothing is not a failure.
3. **Take it to a pull request.** `--run` branches from the base, applies the diff, adds the unit
   to the delivery plan, commits, pushes and opens the PR. With no `--diff` it writes the
   proposal first and runs that.
4. **The gate decides.** Green means merge. Red means the PR gets the reason and stays open.
5. **After the merge, the check runs again** on the merged tree. Red means the merge is reverted
   with a new commit and the failing output goes into an issue.

## The gate

`scripts/gate.py` runs three checks, and all three must pass.

1. **The catalogue agrees with the tree.** `manifest.json` parses, every row's path exists, every
   skill directory has exactly one row, and the README has one table row per skill.
2. **The diff stays inside.** Every changed file is under `skills/` or `docs/`. `manifest.json`,
   `install.ps1`, `install.sh` and any deletion inside `skills/` are forbidden.
3. **Every touched skill's own self-check exits 0.** A skill with `scripts/selftest.py` must
   pass it.

The gate never edits anything. It reports, and the loop acts on the report.

## The merge policy

The machine merges only what the gate cleared. It never merges the manifest, the installers, or
a deletion, because the gate says no first. It never rewrites a published commit — a bad merge
is undone by a new revert commit, not by an amend.

A human is still the author of the change. The loop writes the diff from what the ledger
recorded; a person who wants a different change writes the diff by hand and gives it to `--run`.

## The revert

After the merge, the check runs again on the merged tree — by default the catalogue check. If it
fails, the loop:

- reverts the merge with `git revert` and pushes the revert;
- opens an issue carrying the failing output;
- stops with a non-zero exit.

The revert is a new commit. The merged commit stays in the history, because the history is what
tells the next session what happened.

## The closing

A merge closes the failures it fixed. After it, the ledger holds a successful run of each job the
proposal fixed, so those failures stop being open and the next pass does not propose them again.
Without this the loop would propose the same fix every day and the scheduled job would report a
failure every day.

A failure is closed by a success of the *same job*. A merge that fixed another job does not close
it.

## Commands

```bash
I=skills/workflow/aswath-improve/scripts/improve.py
G=skills/workflow/aswath-improve/scripts/gate.py

python $I --dry-run --project agent-estate            # write the diff, change nothing
python $I --run --diff <file> --skill <skill>        # branch, PR, gate, merge, check, revert
python $I --run --project agent-estate                # the whole cycle: propose, then run
python $G check --repo . --base main --head <branch> # the gate on its own
```

`--run` takes `--repo`, `--remote`, `--base`, `--branch`, `--subject` and `--post-check`. The
last one replaces the post-merge check with another command; the default is the catalogue check
on the merged tree.

A failure is recorded against the skill that owns it, so the loop has something to read:

```bash
python ~/.agents/skills/aswath-record/scripts/ledger.py add \
  --project agent-estate --kind run --job "catalog fix" --outcome failed --skill aswath-catalog
```

## When to run it

- when the same job failed more than once and nothing in the skill says so
- after a skill ships and the ledger shows it is not working
- when the estate's own check finds drift the loop could fix

Not for a change a person wants to make by hand. Write that diff yourself and hand it to `--run`.

## Self-check

```bash
python skills/workflow/aswath-improve/scripts/selftest.py
```

Runs against a scratch repo with a stub `gh`: the gate green, the gate refusing the manifest, the
gate refusing a deletion, the gate running a touched skill's self-check, the proposal leaving out
a closed failure, the loop merging, the loop refusing to merge, and the revert with its issue.
It touches nothing real.
