#!/usr/bin/env python3
"""Self-check for aswath-improve. Runs against a scratch repo and a stub gh.

Nothing real is touched: the repo, the remote and the ledger are all in a
temporary directory, and `gh` is a stub that records what it was asked to do.
"""
from __future__ import annotations

import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPROVE = HERE / "improve.py"
GATE = HERE / "gate.py"
REPO_OF_THIS_SKILL = HERE.parents[3]  # the repo that holds aswath-improve

results = []

GH_STUB = '''\
import os, subprocess, sys
args = sys.argv[1:]
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as fh:
    fh.write(" ".join(args) + "\\n")
    if "--body-file" in args:
        name = args[args.index("--body-file") + 1]
        fh.write(open(name, encoding="utf-8").read() + "\\n")
if args[:2] == ["pr", "create"]:
    print(os.environ.get("GH_PR_URL", "https://github.com/scratch/scratch/pull/7"))
elif args[:2] == ["pr", "merge"]:
    repo = os.environ["GH_REPO"]
    out = subprocess.run(["git", "-C", repo, "branch", "--format=%(refname:short)"],
                         capture_output=True, text=True).stdout.split()
    other = [b for b in out if b not in ("main", "master")]
    if other:
        subprocess.run(["git", "-C", repo, "checkout", "-q", "main"], check=True)
        subprocess.run(["git", "-C", repo, "merge", "-q", "--squash", other[0]], check=True)
        subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "squashed merge"], check=True)
        subprocess.run(["git", "-C", repo, "push", "-q", "origin", "main"], check=True)
'''

CATALOG_STUB = '''\
import os, sys
marker = os.environ.get("CATALOG_FAIL")
if marker and os.path.exists(marker):
    print("catalog: FAIL the merged tree is broken")
    sys.exit(1)
print("catalog: clean. Every skill resolves to one canonical copy.")
'''

DEMO_SELFTEST = '''\
import os, sys
marker = os.environ.get("DEMO_SELFTEST_FAIL")
if marker and os.path.exists(marker):
    print("selftest: the demo skill is broken")
    sys.exit(1)
print("selftest: ok")
'''

MANIFEST = {
    "name": "scratch",
    "version": "0.0.1",
    "skills": [
        {"name": "demo", "category": "workflow",
         "path": "skills/workflow/demo/SKILL.md",
         "description": "Use when testing the loop.", "resources": ["scripts"]},
        {"name": "aswath-catalog", "category": "utilities",
         "path": "skills/utilities/aswath-catalog/SKILL.md",
         "description": "Use when checking the layout.", "resources": ["scripts"]},
        {"name": "aswath-record", "category": "workflow",
         "path": "skills/workflow/aswath-record/SKILL.md",
         "description": "Use when keeping the ledger.", "resources": ["scripts"]},
    ],
}

README = """# scratch

| Skill | What | Use |
|---|---|---|
| `demo` | a demo skill | `/demo` |
| `aswath-catalog` | a fake catalogue | `/aswath-catalog` |
| `aswath-record` | the real ledger | `/aswath-record` |
"""

PLAN = """# Delivery plan

| # | Unit | Commit | State |
|---|------|--------|-------|
| 1 | the scratch unit | fix(demo): scratch | done |
"""


def case(name):
    def wrap(fn):
        results.append((name, fn))
        return fn
    return wrap


def git(repo: Path, *args, check=True):
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {args} failed")
    return out


def build_repo(root: Path) -> Path:
    repo = root / "repo"
    for d in ("skills/workflow/demo/scripts", "skills/utilities/aswath-catalog/scripts",
              "skills/workflow/aswath-record/scripts", "docs/reviews"):
        (repo / d).mkdir(parents=True, exist_ok=True)
    (repo / "skills/workflow/demo/SKILL.md").write_text(
        "# demo\n\nUse when testing the loop.\n", encoding="utf-8")
    (repo / "skills/workflow/demo/scripts/selftest.py").write_text(DEMO_SELFTEST, encoding="utf-8")
    (repo / "skills/utilities/aswath-catalog/SKILL.md").write_text(
        "# aswath-catalog\n", encoding="utf-8")
    (repo / "skills/utilities/aswath-catalog/scripts/catalog.py").write_text(
        CATALOG_STUB, encoding="utf-8")
    source = REPO_OF_THIS_SKILL / "skills/workflow/aswath-record/scripts"
    if source.is_dir():
        for f in source.glob("*.py"):
            shutil.copy(f, repo / "skills/workflow/aswath-record/scripts" / f.name)
    (repo / "skills/workflow/aswath-record/SKILL.md").write_text(
        "# aswath-record\n", encoding="utf-8")
    (repo / "manifest.json").write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")
    (repo / "README.md").write_text(README, encoding="utf-8")
    (repo / "docs/reviews/delivery-plan.md").write_text(PLAN, encoding="utf-8")

    git(repo.parent, "init", "-b", "main", str(repo))
    git(repo, "config", "user.email", "scratch@example.com")
    git(repo, "config", "user.name", "scratch")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "the scratch repo")
    remote = root / "remote.git"
    git(repo.parent, "init", "-b", "main", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "--quiet", "-u", "origin", "main")
    return repo


def write_gh(root: Path) -> Path:
    bindir = root / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    stub = root / "gh_stub.py"
    stub.write_text(GH_STUB, encoding="utf-8")
    # Windows runs a .cmd through PATHEXT; a bare "gh" would not be found.
    (bindir / "gh.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{stub}" %*\r\n',
                                   encoding="utf-8")
    return bindir


def env_for(root: Path, repo: Path) -> dict:
    env = dict(os.environ)
    env["PATH"] = str(root / "bin") + os.pathsep + env.get("PATH", "")
    env["GH_LOG"] = str(root / "gh.log")
    env["GH_REPO"] = str(repo)
    env["ASWATH_LEDGER"] = str(root / "ledger")
    env["ASWATH_STATE"] = str(root / "state")
    env["ASWATH_SKILLS_REPO"] = str(repo)
    # Without this the imported ledger module leaves a __pycache__ in the
    # scratch repo and the run refuses to start on a dirty tree.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run(argv, env):
    return subprocess.run(argv, capture_output=True, text=True, env=env)


def make_diff(repo: Path, rel: str, old: str, new: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}"))


# ---------------------------------------------------------------- cases


@case("the gate is green on a change that only touches a skill")
def t_gate_green(root: Path) -> None:
    repo = build_repo(root / "a")
    bindir = write_gh(root / "a")
    env = env_for(root / "a", repo)
    rel = "skills/workflow/demo/SKILL.md"
    diff = make_diff(repo, rel, "# demo\n\nUse when testing the loop.\n",
                     "# demo\n\nUse when testing the loop. And the gate.\n")
    (root / "a" / "change.diff").write_text(diff, encoding="utf-8")
    git(repo, "checkout", "-b", "work")
    (repo / rel).write_text("# demo\n\nUse when testing the loop. And the gate.\n",
                             encoding="utf-8")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "fix(demo): test the gate")
    out = run([sys.executable, str(GATE), "check", "--repo", str(repo),
               "--base", "main", "--head", "work"], env)
    assert out.returncode == 0, (out.stdout, out.stderr)
    assert "green" in out.stdout, out.stdout


@case("the gate refuses a change that touches the manifest")
def t_gate_manifest(root: Path) -> None:
    repo = build_repo(root / "b")
    env = env_for(root / "b", repo)
    old = (repo / "manifest.json").read_text(encoding="utf-8")
    new = old.replace('"version": "0.0.1"', '"version": "0.0.2"')
    diff = make_diff(repo, "manifest.json", old, new)
    git(repo, "checkout", "-b", "work")
    (repo / "manifest.json").write_text(new, encoding="utf-8")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "chore(demo): move the manifest")
    out = run([sys.executable, str(GATE), "check", "--repo", str(repo),
               "--base", "main", "--head", "work"], env)
    assert out.returncode == 1, out.stdout
    assert "manifest.json is a forbidden path" in out.stdout, out.stdout


@case("the gate refuses a deletion inside skills")
def t_gate_delete(root: Path) -> None:
    repo = build_repo(root / "c")
    env = env_for(root / "c", repo)
    git(repo, "checkout", "-b", "work")
    (repo / "skills/workflow/demo/SKILL.md").unlink()
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "chore(demo): drop the skill")
    out = run([sys.executable, str(GATE), "check", "--repo", str(repo),
               "--base", "main", "--head", "work"], env)
    assert out.returncode == 1, out.stdout
    assert "deletion inside skills/ is forbidden" in out.stdout, out.stdout


@case("the gate runs a touched skill's own self-check")
def t_gate_selfcheck(root: Path) -> None:
    repo = build_repo(root / "d")
    env = env_for(root / "d", repo)
    rel = "skills/workflow/demo/SKILL.md"
    git(repo, "checkout", "-b", "work")
    (repo / rel).write_text("# demo\n\nchanged\n", encoding="utf-8")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "fix(demo): change the skill")
    broken = root / "d" / "broken"
    broken.write_text("x", encoding="utf-8")
    env["DEMO_SELFTEST_FAIL"] = str(broken)
    out = run([sys.executable, str(GATE), "check", "--repo", str(repo),
               "--base", "main", "--head", "work"], env)
    assert out.returncode == 1, out.stdout
    assert "its self-check failed" in out.stdout, out.stdout


@case("the dry run writes a diff for the open failure and leaves out the closed one")
def t_propose(root: Path) -> None:
    repo = build_repo(root / "e")
    write_gh(root / "e")
    env = env_for(root / "e", repo)
    ledger = root / "e" / "ledger"
    ledger.mkdir(parents=True, exist_ok=True)
    lines = [
        {"id": "1", "ts": "2026-11-10T10:00:00Z", "project": "scratch", "kind": "run",
         "job": "build the thing", "outcome": "failed", "skill": "demo"},
        {"id": "2", "ts": "2026-11-11T10:00:00Z", "project": "scratch", "kind": "run",
         "job": "the other thing", "outcome": "failed", "skill": "demo"},
        {"id": "3", "ts": "2026-11-12T10:00:00Z", "project": "scratch", "kind": "run",
         "job": "the other thing", "outcome": "ok", "skill": "demo"},
        {"id": "4", "ts": "2026-11-12T11:00:00Z", "project": "scratch", "kind": "run",
         "job": "a failure with no skill", "outcome": "failed"},
    ]
    (ledger / "scratch.jsonl").write_text(
        "\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    out_file = root / "e" / "proposal.diff"
    out = run([sys.executable, str(IMPROVE), "--dry-run", "--project", "scratch",
               "--repo", str(repo), "--out", str(out_file)], env)
    assert out.returncode == 0, (out.stdout, out.stderr)
    diff = out_file.read_text(encoding="utf-8")
    assert "build the thing" in diff, diff
    assert "the other thing" not in diff, diff
    assert "a failure with no skill" not in diff, diff
    assert "skills/workflow/demo/SKILL.md" in diff, diff
    # the dry run opens no pull request
    log_path = root / "e" / "gh.log"
    log = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
    assert "pr create" not in log, log


@case("run merges a change that only touches a skill")
def t_run_merge(root: Path) -> None:
    repo = build_repo(root / "f")
    write_gh(root / "f")
    env = env_for(root / "f", repo)
    rel = "skills/workflow/demo/SKILL.md"
    diff = make_diff(repo, rel, "# demo\n\nUse when testing the loop.\n",
                     "# demo\n\nUse when testing the loop. And the gate.\n")
    diff_file = root / "f" / "change.diff"
    diff_file.write_text(diff, encoding="utf-8")
    out = run([sys.executable, str(IMPROVE), "--run", "--repo", str(repo),
               "--diff", str(diff_file), "--skill", "demo", "--project", "scratch",
               "--subject", "fix(demo): record the open failure"], env)
    assert out.returncode == 0, (out.stdout, out.stderr)
    assert "merged and verified" in out.stdout, out.stdout
    log = (root / "f" / "gh.log").read_text(encoding="utf-8")
    assert "pr merge" in log, log
    assert "pr create" in log, log
    assert "And the gate." in (repo / rel).read_text(encoding="utf-8")


@case("a merged proposal closes the failure it fixed")
def t_run_closes(root: Path) -> None:
    repo = build_repo(root / "i")
    write_gh(root / "i")
    env = env_for(root / "i", repo)
    ledger = root / "i" / "ledger"
    ledger.mkdir(parents=True, exist_ok=True)
    (ledger / "scratch.jsonl").write_text(json.dumps({
        "id": "1", "ts": "2026-11-10T10:00:00Z", "project": "scratch", "kind": "run",
        "job": "build the thing", "outcome": "failed", "skill": "demo"}) + "\n",
        encoding="utf-8")
    out = run([sys.executable, str(IMPROVE), "--run", "--project", "scratch",
               "--repo", str(repo), "--skill", "demo"], env)
    assert out.returncode == 0, (out.stdout, out.stderr)
    records = [json.loads(line) for line
               in (ledger / "scratch.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    closed = [r for r in records
              if r.get("job") == "build the thing" and r.get("outcome") == "ok"]
    assert closed, records
    # and the next pass has nothing to do, which is not a failure
    out = run([sys.executable, str(IMPROVE), "--dry-run", "--project", "scratch",
               "--repo", str(repo)], env)
    assert out.returncode == 0, (out.stdout, out.stderr)
    assert "nothing to do" in (out.stdout + out.stderr).lower(), out.stdout


@case("run refuses to merge a change that touches the manifest")
def t_run_refuses(root: Path) -> None:
    repo = build_repo(root / "g")
    write_gh(root / "g")
    env = env_for(root / "g", repo)
    old = (repo / "manifest.json").read_text(encoding="utf-8")
    new = old.replace('"version": "0.0.1"', '"version": "0.0.2"')
    diff_file = root / "g" / "change.diff"
    diff_file.write_text(make_diff(repo, "manifest.json", old, new), encoding="utf-8")
    out = run([sys.executable, str(IMPROVE), "--run", "--repo", str(repo),
               "--diff", str(diff_file), "--skill", "demo", "--project", "scratch",
               "--subject", "fix(demo): move the manifest"], env)
    assert out.returncode == 1, (out.stdout, out.stderr)
    log = (root / "g" / "gh.log").read_text(encoding="utf-8")
    assert "pr merge" not in log, log
    assert "pr comment" in log, log
    assert "manifest.json is a forbidden path" in (out.stdout + out.stderr), out.stdout


@case("a failed check after the merge leaves a revert commit and an issue")
def t_run_revert(root: Path) -> None:
    repo = build_repo(root / "h")
    write_gh(root / "h")
    env = env_for(root / "h", repo)
    fatal = root / "h" / "fatal"
    fatal.write_text("x", encoding="utf-8")
    env["CATALOG_FAIL"] = str(fatal)
    rel = "skills/workflow/demo/SKILL.md"
    diff = make_diff(repo, rel, "# demo\n\nUse when testing the loop.\n",
                     "# demo\n\nUse when testing the loop. And the gate.\n")
    diff_file = root / "h" / "change.diff"
    diff_file.write_text(diff, encoding="utf-8")
    out = run([sys.executable, str(IMPROVE), "--run", "--repo", str(repo),
               "--diff", str(diff_file), "--skill", "demo", "--project", "scratch",
               "--subject", "fix(demo): record the open failure"], env)
    assert out.returncode == 1, (out.stdout, out.stderr)
    assert "reverted" in (out.stdout + out.stderr), (out.stdout, out.stderr)
    log = (root / "h" / "gh.log").read_text(encoding="utf-8")
    assert "issue create" in log, log
    subjects = git(repo, "log", "--format=%s", "main").stdout
    assert "Revert" in subjects, subjects
    assert "squashed merge" in subjects, subjects


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="improve-selftest-"))
    failed = 0
    try:
        for index, (name, fn) in enumerate(results):
            case_root = root / f"case{index}"
            case_root.mkdir(parents=True, exist_ok=True)
            try:
                fn(case_root)
                print(f"ok   {name}")
            except AssertionError as exc:
                failed += 1
                print(f"FAIL {name}: {exc}")
        print(f"{len(results) - failed}/{len(results)} case(s) passed")
        return 1 if failed else 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
