#!/usr/bin/env python3
"""aswath-improve: the learning loop. A failure in, a skill change out, gated.

    python improve.py propose --project X [--repo PATH] [--out FILE]
    python improve.py run --repo PATH --diff FILE [--remote origin] [--base main]

propose reads the run ledger, finds the failures that were never followed by a
success, and writes a diff that records them in the skill that owns them. It
touches no git state.

run takes that diff to a pull request: branch, commit, push, open the PR, run
the gate. A green gate means merge; a red gate means the PR carries the reason
and stays open. After the merge the check runs again; if it fails, the merge is
reverted with a new commit and the failing output goes into an issue.

Standard library only. The git and gh commands come from PATH, so the
self-check can stand a stub in for them.
"""
from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path.home()
GATE = Path(__file__).resolve().parent / "gate.py"
PLAN = "docs/reviews/delivery-plan.md"
PLAN_SECTION = "## The loop's own units"
KNOWN = "## Known failures"


# ---------------------------------------------------------------- locations


def repo_default() -> Path:
    env = os.environ.get("ASWATH_SKILLS_REPO")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[4]


def state_root() -> Path:
    return Path(os.environ.get("ASWATH_STATE", HOME / ".agents" / "state"))


def load_ledger(repo: Path):
    """The aswath-record module, so the loop reads the ledger the same way."""
    for candidate in (
        repo / "skills/workflow/aswath-record/scripts/ledger.py",
        HOME / ".agents/skills/aswath-record/scripts/ledger.py",
    ):
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location("aswath_ledger", candidate)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def manifest_paths(repo: Path) -> dict:
    data = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    return {row["name"]: row["path"] for row in data.get("skills", [])}


# ---------------------------------------------------------------- the failures


def open_failures(records: list) -> dict:
    """(skill, job) -> failures that no later success closed."""
    closed = {}
    for r in records:
        if r.get("kind") != "run" or r.get("outcome") != "ok":
            continue
        key = (r.get("skill"), r.get("job"))
        closed[key] = max(closed.get(key, ""), r.get("ts", ""))
    out = {}
    for r in records:
        if r.get("kind") != "run" or r.get("outcome") != "failed":
            continue
        if not r.get("skill"):
            continue  # a failure that names no skill has no skill to change
        key = (r.get("skill"), r.get("job"))
        if closed.get(key, "") > r.get("ts", ""):
            continue  # a later success closed it
        out.setdefault(key, []).append(r)
    return out


# ---------------------------------------------------------------- the proposal


def known_block(skill: str, jobs: list) -> str:
    lines = [
        KNOWN,
        "",
        "Recorded from the run ledger. A job listed here failed and was never",
        "followed by a success.",
        "",
    ]
    for job, recs in jobs:
        last = max(r.get("ts", "") for r in recs)[:10]
        plural = "failure" if len(recs) == 1 else "failures"
        lines.append(f"- `{job}`: {len(recs)} {plural}, last on {last}")
    return "\n".join(lines)


def replace_section(text: str, block: str) -> str:
    """Put the block in, replacing an earlier copy of the same section."""
    lines = text.splitlines()
    out = []
    i = 0
    placed = False
    while i < len(lines):
        if lines[i].strip() == KNOWN:
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                i += 1
            while out and out[-1] == "":
                out.pop()
            out.append("")
            out.extend(block.splitlines())
            out.append("")
            placed = True
            continue
        out.append(lines[i])
        i += 1
    if not placed:
        while out and out[-1] == "":
            out.pop()
        out.append("")
        out.extend(block.splitlines())
        out.append("")
    return "\n".join(out) + "\n"


def cmd_propose(args) -> int:
    repo = Path(args.repo).resolve()
    ledger = load_ledger(repo)
    if ledger is None:
        print("improve: aswath-record is not installed, so the ledger cannot be read.", file=sys.stderr)
        return 1
    failures = open_failures(ledger.read_records(args.project))
    if not failures:
        print(f"improve: no open failure names a skill for project '{args.project}'.")
        return 1

    counts = {}
    for (skill, job), recs in failures.items():
        counts.setdefault(skill, []).extend(recs)
    skill = max(
        counts,
        key=lambda s: (len(counts[s]), max(r.get("ts", "") for r in counts[s])),
    )
    jobs = sorted(
        [(job, recs) for (sk, job), recs in failures.items() if sk == skill],
        key=lambda pair: pair[0],
    )

    paths = manifest_paths(repo)
    if skill not in paths:
        print(f"improve: {skill} is not in the manifest, so it cannot be changed.", file=sys.stderr)
        return 1
    rel = paths[skill]
    target = repo / rel
    original = target.read_text(encoding="utf-8")
    updated = replace_section(original, known_block(skill, jobs))

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
    )
    if not diff:
        print(f"improve: {skill} already records these failures. Nothing to propose.")
        return 1

    out = Path(args.out) if args.out else state_root() / "improve" / f"{skill}.diff"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(diff, encoding="utf-8")
    print(f"improve: {skill} has {len(counts[skill])} open failure(s) -> {out}")
    for job, recs in jobs:
        print(f"  - {job}: {len(recs)}")
    return 0


# ---------------------------------------------------------------- git and gh


def git(repo: Path, *args, check=True) -> subprocess.CompletedProcess:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return out


def gh(*args) -> subprocess.CompletedProcess:
    cmd = shutil.which("gh")
    if not cmd:
        raise RuntimeError("gh is not on PATH")
    return subprocess.run([cmd, *args], capture_output=True, text=True)


def body_file(body: str) -> Path:
    """gh takes the body from a file, so no shell ever sees the text."""
    handle, name = tempfile.mkstemp(prefix="aswath-improve-", suffix=".md")
    with os.fdopen(handle, "w", encoding="utf-8") as fh:
        fh.write(body)
    return Path(name)


def add_plan_row(repo: Path, unit: str, subject: str) -> None:
    """The loop's commits are units too, so the plan has to name them."""
    path = repo / PLAN
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["# Delivery plan", "", "| # | Unit | Commit | State |", "|---|------|--------|-------|"]
    if PLAN_SECTION not in lines:
        lines += [
            "",
            PLAN_SECTION,
            "",
            "Rows the learning loop added. Each row is a commit the loop pushed.",
            "",
            "| # | Unit | Commit | State |",
            "|---|------|--------|-------|",
        ]
        lines.append(f"| 1 | {unit} | {subject} | done |")
    else:
        index = lines.index(PLAN_SECTION)
        last = None
        number = 0
        for i in range(index, len(lines)):
            if lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if len(cells) >= 4 and cells[0].isdigit():
                    number = max(number, int(cells[0]))
                    last = i
        lines.insert((last if last is not None else index) + 1,
                     f"| {number + 1} | {unit} | {subject} | done |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def post_check_command(repo: Path, override: str) -> str:
    if override:
        return override
    script = repo / "skills/utilities/aswath-catalog/scripts/catalog.py"
    return f'"{sys.executable}" "{script}" check'


# ---------------------------------------------------------------- the run


def default_subject(repo: Path, project: str, skill: str) -> str:
    """The commit subject the plan has to name, so the two agree."""
    ledger = load_ledger(repo)
    count = 0
    if ledger is not None:
        for (sk, _job), recs in open_failures(ledger.read_records(project)).items():
            if sk == skill:
                count += len(recs)
    plural = "failure" if count == 1 else "failures"
    return f"fix({skill}): record {count} open {plural}"


def cmd_run(args) -> int:
    repo = Path(args.repo).resolve()
    diff_path = Path(args.diff).resolve()
    if not diff_path.is_file():
        print(f"improve: {diff_path} does not exist.", file=sys.stderr)
        return 1
    if not (repo / "manifest.json").is_file():
        print(f"improve: {repo} is not a skills repo.", file=sys.stderr)
        return 1

    dirty = git(repo, "status", "--porcelain").stdout.strip()
    if dirty:
        print("improve: the tree is dirty. Commit or stash first; nothing was changed.", file=sys.stderr)
        for line in dirty.splitlines()[:10]:
            print(f"  {line}", file=sys.stderr)
        return 1

    stamp = time.strftime("%Y%m%d-%H%M%S")
    branch = args.branch or f"improve/{stamp}"
    subject = args.subject or default_subject(repo, args.project, args.skill)

    try:
        git(repo, "fetch", "--quiet", args.remote, args.base)
        base_ref = f"{args.remote}/{args.base}"
        git(repo, "checkout", "-b", branch, base_ref)
        applied = subprocess.run(
            ["git", "-C", str(repo), "apply", str(diff_path)], capture_output=True, text=True
        )
        if applied.returncode != 0:
            git(repo, "checkout", "--force", args.base, check=False)
            git(repo, "branch", "--delete", "--force", branch, check=False)
            print(f"improve: the diff did not apply: {applied.stderr.strip()}", file=sys.stderr)
            return 1

        add_plan_row(repo, f"{args.skill} learns from the ledger", subject)
        body = args.body or "The run ledger holds a failure that no later success closed.\n"
        note = body_file(body)
        git(repo, "add", "--all")
        git(repo, "commit", "--quiet", "--message", subject, "--message", body)
        git(repo, "push", "--quiet", args.remote, branch)

        pr = gh("pr", "create", "--base", args.base, "--head", branch,
                "--title", subject, "--body-file", str(note))
        if pr.returncode != 0:
            print(f"improve: the pull request was not opened: {pr.stderr.strip()}", file=sys.stderr)
            return 1
        pr_id = pr.stdout.strip().splitlines()[-1] if pr.stdout.strip() else ""
        print(f"improve: pull request {pr_id}")

        gate = subprocess.run(
            [sys.executable, str(GATE), "check", "--repo", str(repo),
             "--base", base_ref, "--head", branch],
            capture_output=True, text=True,
        )
        if gate.returncode != 0:
            reason = gate.stdout + gate.stderr
            note = body_file(reason)
            gh("pr", "comment", pr_id, "--body-file", str(note))
            print(reason)
            print("improve: the gate is red. The pull request stays open.", file=sys.stderr)
            return 1
        print(gate.stdout.strip())

        merge = gh("pr", "merge", pr_id, "--squash")
        if merge.returncode != 0:
            print(f"improve: the merge failed: {merge.stderr.strip()}", file=sys.stderr)
            return 1

        git(repo, "checkout", args.base)
        pull = git(repo, "pull", "--ff-only", args.remote, args.base, check=False)
        if pull.returncode != 0:
            print(f"improve: the merged base could not be pulled: {pull.stderr.strip()}", file=sys.stderr)
            return 1
        sha = git(repo, "rev-parse", "HEAD").stdout.strip()

        post = subprocess.run(
            post_check_command(repo, args.post_check),
            shell=True, cwd=str(repo),
            env={**os.environ, "ASWATH_SKILLS_REPO": str(repo)},
            capture_output=True, text=True,
        )
        if post.returncode != 0:
            output = post.stdout + post.stderr
            revert = git(repo, "revert", "--no-edit", sha, check=False)
            if revert.returncode != 0:
                print(f"improve: the merge could not be reverted: {revert.stderr.strip()}", file=sys.stderr)
                return 1
            git(repo, "push", args.remote, args.base)
            note = body_file(output)
            gh("issue", "create",
               "--title", f"the merge of {branch} failed its check and was reverted",
               "--body-file", str(note))
            print(output)
            print(f"improve: the merge {sha[:7]} was reverted and the output went into an issue.",
                  file=sys.stderr)
            return 1

        print(f"improve: merged and verified. {sha[:7]} on {args.base}.")
        ledger = load_ledger(repo)
        if ledger is not None:
            ledger.append_record({
                "id": f"improve:{sha[:12]}",
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "project": args.project,
                "kind": "run",
                "job": f"improve {args.skill}",
                "outcome": "ok",
                "skill": args.skill,
            })
        return 0
    except RuntimeError as exc:
        print(f"improve: {exc}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="improve.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_prop = sub.add_parser("propose", help="write the diff for an open failure")
    p_prop.add_argument("--project", required=True)
    p_prop.add_argument("--repo", default=str(repo_default()))
    p_prop.add_argument("--out")
    p_prop.set_defaults(func=cmd_propose)

    p_run = sub.add_parser("run", help="take a diff to a pull request and merge it")
    p_run.add_argument("--repo", default=str(repo_default()))
    p_run.add_argument("--diff", required=True)
    p_run.add_argument("--project", default="agent-estate")
    p_run.add_argument("--skill", default="aswath-improve")
    p_run.add_argument("--remote", default="origin")
    p_run.add_argument("--base", default="main")
    p_run.add_argument("--branch")
    p_run.add_argument("--subject")
    p_run.add_argument("--body")
    p_run.add_argument("--post-check", default="", help="the command that decides whether the merge stays")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
