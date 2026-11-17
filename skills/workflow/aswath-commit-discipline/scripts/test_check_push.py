#!/usr/bin/env python3
"""Self-check for the commit-discipline checker.

Runs the real `check_push.py` against scratch repositories in a temp directory
and asserts what it warns about. No test framework and no dependency: run it
with `python scripts/test_check_push.py`. Exit 0 when every case holds, 1
otherwise.

The cases cover the three delivery warnings - BULK_COMMIT, COMMIT_NOT_PLANNED
and UNIT_NOT_COMMITTED - and the two ways the checker must stay quiet: a
compliant branch, and a branch that inherits a plan it did not write.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_push.py"

DELIVERY_CODES = ("BULK_COMMIT", "COMMIT_NOT_PLANNED", "UNIT_NOT_COMMITTED")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def check(repo: Path, rng: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--repo", str(repo), "--range", rng],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.stdout


def new_repo(root: Path, name: str) -> Path:
    """A repository with a `main` branch and one commit on it."""
    repo = root / name
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main", ".")
    git(repo, "config", "user.email", "t@t.t")
    git(repo, "config", "user.name", "t")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: base", "-m", "The base commit of the scratch repository.")
    return repo


def write_plan(repo: Path, rows: list[tuple[str, str, str, str]]) -> None:
    """rows: (number, unit, commit subject, state)."""
    path = repo / "docs" / "reviews" / "delivery-plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Delivery plan",
        "",
        "| # | Unit | Commit | State |",
        "|---|------|--------|-------|",
    ]
    for number, unit, subject, state in rows:
        lines.append(f"| {number} | {unit} | {subject} | {state} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_records(repo: Path) -> None:
    reviews = repo / "docs" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / "decision-log.md").write_text("# Decision log\n", encoding="utf-8")
    (reviews / "change-inventory.md").write_text(
        "# Change inventory\n\n| File | What changed | Why | How tested |\n|---|---|---|---|\n",
        encoding="utf-8",
    )


def commit(repo: Path, subject: str, files: dict[str, str]) -> None:
    for name, content in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject, "-m", f"{subject}: the reasoning of this commit, in a body.")


def report(label: str, ok: bool, detail: str = "") -> bool:
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f" -- {detail}"))
    return ok


def delivery_warnings(output: str) -> list[str]:
    return [code for code in DELIVERY_CODES if code in output]


def case_compliant_branch(root: Path) -> bool:
    """A branch whose commits match its plan: no delivery warnings."""
    repo = new_repo(root, "compliant")
    git(repo, "checkout", "-q", "-b", "feat/test")
    write_records(repo)
    write_plan(
        repo,
        [
            ("1", "The first unit", "feat(x): the first unit", "done"),
            ("2", "The second unit", "feat(x): the second unit", "done"),
        ],
    )
    commit(repo, "feat(x): the first unit", {"a.txt": "one\n"})
    commit(repo, "feat(x): the second unit", {"b.txt": "two\n"})
    output = check(repo, "main..HEAD")
    found = delivery_warnings(output)
    return report("compliant branch raises no delivery warning", not found, ", ".join(found))


def case_bulk_commit(root: Path) -> bool:
    """A commit that carries more files than the threshold."""
    repo = new_repo(root, "bulk")
    git(repo, "checkout", "-q", "-b", "feat/test")
    write_records(repo)
    write_plan(repo, [("1", "The bulk unit", "feat(x): the bulk unit", "done")])
    files = {f"f{i}.txt": "x\n" for i in range(31)}
    commit(repo, "feat(x): the bulk unit", files)
    output = check(repo, "main..HEAD")
    ok = report("a 31-file commit raises BULK_COMMIT", "BULK_COMMIT" in output, output)
    return ok


def case_unplanned_and_housekeeping(root: Path) -> bool:
    """A commit that matches no unit is reported; a chore commit is not."""
    repo = new_repo(root, "unplanned")
    git(repo, "checkout", "-q", "-b", "feat/test")
    write_records(repo)
    write_plan(repo, [("1", "The first unit", "feat(x): the first unit", "done")])
    commit(repo, "feat(x): the first unit", {"a.txt": "one\n"})
    write_plan(repo, [("1", "The first unit", "feat(x): the first unit", "done")])
    commit(repo, "feat(y): unplanned work", {"b.txt": "two\n"})
    write_plan(repo, [("1", "The first unit", "feat(x): the first unit", "done")])
    commit(repo, "chore: housekeeping", {"c.txt": "three\n"})
    output = check(repo, "main..HEAD")
    ok = report("a commit matching no unit raises COMMIT_NOT_PLANNED", "COMMIT_NOT_PLANNED" in output, output)
    chore_line = [ln for ln in output.splitlines() if "chore: housekeeping" in ln and "COMMIT_NOT_PLANNED" in ln]
    ok = report("a chore commit is exempt from the plan match", not chore_line, " | ".join(chore_line)) and ok
    return ok


def case_unit_not_committed(root: Path) -> bool:
    """A unit marked done with no commit on the branch."""
    repo = new_repo(root, "missing-unit")
    git(repo, "checkout", "-q", "-b", "feat/test")
    write_records(repo)
    write_plan(
        repo,
        [
            ("1", "The first unit", "feat(x): the first unit", "done"),
            ("2", "The second unit", "feat(x): the second unit", "done"),
        ],
    )
    commit(repo, "feat(x): the first unit", {"a.txt": "one\n"})
    output = check(repo, "main..HEAD")
    return report("a unit marked done with no commit raises UNIT_NOT_COMMITTED", "UNIT_NOT_COMMITTED" in output, output)


def case_inherited_plan(root: Path) -> bool:
    """A plan that arrived with an earlier merge does not govern later work."""
    repo = new_repo(root, "inherited")
    write_records(repo)
    write_plan(repo, [("1", "An older unit", "feat(x): an older unit", "done")])
    commit(repo, "feat(x): an older unit", {"old.txt": "old\n"})
    git(repo, "checkout", "-q", "-b", "feat/later")
    commit(repo, "feat(z): unrelated later work", {"new.txt": "new\n"})
    output = check(repo, "main..HEAD")
    found = delivery_warnings(output)
    return report("an inherited plan raises no delivery warning", not found, ", ".join(found))


def main() -> int:
    if not CHECKER.is_file():
        print("FAIL the checker is missing: " + str(CHECKER))
        return 1
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        results.append(case_compliant_branch(root))
        results.append(case_bulk_commit(root))
        results.append(case_unplanned_and_housekeeping(root))
        results.append(case_unit_not_committed(root))
        results.append(case_inherited_plan(root))
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} case(s) passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
