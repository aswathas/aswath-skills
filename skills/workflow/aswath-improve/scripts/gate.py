#!/usr/bin/env python3
"""The gate suite. Three checks; all three must pass before a merge.

    python gate.py check --repo <path> [--base main] [--head HEAD]

1. The catalogue agrees with the tree: manifest.json parses, every row's path
   exists, every skill directory has exactly one row, and the README has one
   table row per skill.
2. The diff is allowed: every changed file is under skills/ or docs/. The
   manifest, the installers and any deletion inside skills/ are forbidden.
3. Every touched skill's own self-check exits 0.

Exit 0 when all three pass, 1 otherwise, with one line per failure.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_PREFIXES = ("skills/", "docs/")
FORBIDDEN_FILES = ("manifest.json", "install.ps1", "install.sh")
# A row in the README's skill tables.
TABLE_ROW = re.compile(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|")


def git(repo: Path, *args) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout


def manifest_rows(repo: Path) -> tuple:
    """(rows by skill name, problems)."""
    path = repo / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"manifest.json does not parse: {exc}"]
    rows = {}
    problems = []
    for row in data.get("skills", []):
        name = row.get("name")
        if not name:
            problems.append("a manifest row has no name")
            continue
        if name in rows:
            problems.append(f"{name} has more than one manifest row")
        rows[name] = row
        target = repo / row.get("path", "")
        if not target.is_file():
            problems.append(f"{name}: manifest path does not exist: {row.get('path')}")
    return rows, problems


def check_catalogue(repo: Path) -> list:
    """Check 1: the manifest, the tree and the README agree."""
    problems = []
    rows, found = manifest_rows(repo)
    problems += found

    skills_dir = repo / "skills"
    if skills_dir.is_dir():
        for category in sorted(skills_dir.iterdir()):
            if not category.is_dir():
                continue
            for skill_dir in sorted(category.iterdir()):
                if not skill_dir.is_dir():
                    continue
                owners = [
                    name for name, row in rows.items()
                    if (repo / row.get("path", "x")).resolve().parent == skill_dir.resolve()
                ]
                if not owners:
                    problems.append(f"{skill_dir.relative_to(repo)} has no manifest row")
                elif len(owners) > 1:
                    problems.append(f"{skill_dir.relative_to(repo)} has {len(owners)} manifest rows")

    readme = repo / "README.md"
    if readme.is_file():
        seen = {}
        for line in readme.read_text(encoding="utf-8").splitlines():
            m = TABLE_ROW.match(line)
            if m:
                seen[m.group(1)] = seen.get(m.group(1), 0) + 1
        for name in sorted(rows):
            if seen.get(name, 0) == 0:
                problems.append(f"README has no row for {name}")
            elif seen[name] > 1:
                problems.append(f"README has {seen[name]} rows for {name}")
        for name in sorted(seen):
            if name not in rows:
                problems.append(f"README has a row for {name}, which is not in the manifest")
    else:
        problems.append("README.md does not exist")
    return problems


def changed_files(repo: Path, base: str, head: str) -> list:
    """(status, path) for everything the branch changed."""
    out = git(repo, "diff", "--name-status", f"{base}...{head}")
    changes = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        for path in parts[1:]:
            changes.append((status[0], path))
    return changes


def check_paths(repo: Path, base: str, head: str) -> list:
    """Check 2: the diff only touches what it is allowed to touch."""
    problems = []
    for status, path in changed_files(repo, base, head):
        name = path.replace("\\", "/")
        if status == "D" and name.startswith("skills/"):
            problems.append(f"deletion inside skills/ is forbidden: {name}")
            continue
        if name in FORBIDDEN_FILES:
            problems.append(f"{name} is a forbidden path")
            continue
        if not name.startswith(ALLOWED_PREFIXES):
            problems.append(f"outside skills/ and docs/: {name}")
    return problems


def touched_skills(repo: Path, base: str, head: str) -> list:
    skills = set()
    for _status, path in changed_files(repo, base, head):
        parts = path.replace("\\", "/").split("/")
        if len(parts) >= 3 and parts[0] == "skills":
            skills.add((parts[1], parts[2]))
    return sorted(skills)


def check_self_checks(repo: Path, base: str, head: str) -> list:
    """Check 3: every touched skill's own self-check exits 0."""
    problems = []
    for category, name in touched_skills(repo, base, head):
        script = repo / "skills" / category / name / "scripts" / "selftest.py"
        if not script.is_file():
            continue
        out = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, cwd=str(repo)
        )
        if out.returncode != 0:
            tail = (out.stdout + out.stderr).strip().splitlines()[-5:]
            problems.append(f"{name}: its self-check failed -> " + " | ".join(tail))
    return problems


def cmd_check(args) -> int:
    repo = Path(args.repo).resolve()
    problems = []
    problems += check_catalogue(repo)
    problems += check_paths(repo, args.base, args.head)
    problems += check_self_checks(repo, args.base, args.head)
    if problems:
        print(f"gate: {len(problems)} problem(s) on {args.base}...{args.head}")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"gate: green on {args.base}...{args.head}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gate.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="run the three checks")
    p.add_argument("--repo", required=True)
    p.add_argument("--base", default="main")
    p.add_argument("--head", default="HEAD")
    p.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
