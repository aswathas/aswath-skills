#!/usr/bin/env python3
"""Push-time documentation checker for aswath-commit-discipline.

Warn only. Never blocks a push, never changes repo state. The metric is
documentation detail, not commit count: the number of commits in a range is
never a finding.

Network: one read-only "git ls-remote --heads" per branch, to learn what the
remote really has. It reads refs and nothing else. When the remote cannot be
reached, the checker falls back to the local remote-tracking refs.

Usage:
    python check_push.py --repo <path> [--range <base>..<head>] [--strict]

Exit codes:
    0  always (warn only). --strict is reserved for a future blocking variant
       and is not wired to any hook.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent.parent / "reference" / "doc-rules.json"

DEFAULT_RULES = {
    "decision_log": "docs/reviews/decision-log.md",
    "change_inventory": "docs/reviews/change-inventory.md",
    "prompt_record_patterns": [
        "docs/reviews/decision-log.md",
        "docs/reviews/prompts.md",
        "docs/reviews/change-inventory.md",
        "docs/chronicle/",
    ],
    "doc_path_prefixes": ["docs/", ".github/", "notes/"],
    "doc_file_names": ["README.md", "CHANGELOG.md", "LICENSE", "LICENSE.md"],
    "skill_path_prefixes": ["skills/"],
    "min_commit_body_chars": 20,
    "placeholder_subject_patterns": [
        "wip",
        "fixup",
        "squash",
        "tmp",
        "asdf",
        "test commit",
    ],
}


# --------------------------------------------------------------------------- git


def git(repo: str, *args: str) -> tuple[int, str, str]:
    """Run a read-only git command. Returns (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return 1, "", "git unavailable"
    return proc.returncode, proc.stdout, proc.stderr


def git_lines(repo: str, *args: str) -> list[str]:
    code, out, _ = git(repo, *args)
    if code != 0:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def is_doc_path(path: str, rules: dict) -> bool:
    norm = path.replace("\\", "/")
    if any(norm.startswith(p) for p in rules["doc_path_prefixes"]):
        return True
    return os.path.basename(norm) in rules["doc_file_names"]


def is_skill_path(path: str, rules: dict) -> bool:
    norm = path.replace("\\", "/")
    return any(norm.startswith(p) for p in rules["skill_path_prefixes"])


# ---------------------------------------------------------------------- ranges


def resolve_range(repo: str, explicit: str | None) -> tuple[str, str, str]:
    """Return (base, head, description) for the range a push would carry."""
    head = "HEAD"
    if explicit:
        return explicit.split("..")[0], explicit.split("..")[-1], explicit

    code, out, _ = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = out.strip() if code == 0 else ""
    if upstream:
        base = upstream
        desc = f"{upstream}..HEAD"
        return base, head, desc

    # No upstream on this branch: fall back to the remote's default branch.
    for candidate in ("origin/main", "origin/master", "main", "master"):
        code, _, _ = git(repo, "rev-parse", "--verify", "--quiet", candidate)
        if code == 0:
            return candidate, head, f"{candidate}..HEAD"

    # No reference at all: fall back to the last commit only.
    code, _, _ = git(repo, "rev-parse", "--verify", "--quiet", "HEAD")
    if code != 0:
        return "", "", "(no commits)"
    code, out, _ = git(repo, "rev-parse", "--verify", "--quiet", "HEAD~1")
    if code != 0:
        return "", head, "(initial commit)"
    return out.strip(), head, "HEAD~1..HEAD"


def commits_in_range(repo: str, base: str, head: str) -> list[dict]:
    """Ordered list of commits in the range, oldest first."""
    if base:
        rev = f"{base}..{head}"
    else:
        rev = head
    out = git_lines(repo, "log", "--reverse", "--no-merges", "--format=%H%x1f%h%x1f%s%x1f%b%x1e", rev)
    commits = []
    for chunk in out:
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 4:
            continue
        commits.append(
            {
                "sha": parts[0],
                "short": parts[1],
                "subject": parts[2],
                "body": parts[3].replace("\x1e", "").strip(),
            }
        )
    return commits


def files_in_range(repo: str, base: str, head: str) -> list[str]:
    if base:
        rev = f"{base}..{head}"
    else:
        rev = head
    out = git_lines(repo, "diff", "--name-only", rev)
    return [p.replace("\\", "/") for p in out]


# -------------------------------------------------------------------- findings


class Report:
    def __init__(self) -> None:
        self.warnings: list[tuple[str, str]] = []
        self.info: list[str] = []

    def warn(self, code: str, message: str) -> None:
        self.warnings.append((code, message))

    def note(self, message: str) -> None:
        self.info.append(message)


def load_rules() -> dict:
    rules = dict(DEFAULT_RULES)
    try:
        loaded = json.loads(RULES_FILE.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            rules.update(loaded)
    except (OSError, ValueError):
        pass
    return rules


def rev_parse(repo: str, rev: str) -> str:
    code, out, _ = git(repo, "rev-parse", "--verify", "--quiet", rev)
    return out.strip() if code == 0 else ""


def object_exists(repo: str, sha: str) -> bool:
    if not sha:
        return False
    code, _, _ = git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
    return code == 0


def remote_head_shas(repo: str, remote: str) -> dict[str, str] | None:
    """Heads the remote actually has, as {branch name: sha}.

    None when the remote cannot be reached. This is the only network call the
    checker makes, and it only reads refs. Local remote-tracking refs are not
    enough on their own: a repo whose fetch refspec covers one branch only
    (a common setup) keeps no tracking ref for the others, and those branches
    look unpushed even right after a successful push.
    """
    code, out, _ = git(repo, "ls-remote", "--heads", remote)
    if code != 0:
        return None
    heads: dict[str, str] = {}
    for line in out.splitlines():
        if "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        ref = ref.strip()
        if ref.startswith("refs/heads/"):
            heads[ref[len("refs/heads/") :]] = sha.strip()
    return heads


def local_tracking_shas(repo: str, remote: str) -> list[str]:
    return [
        ln.strip()
        for ln in git_lines(repo, "for-each-ref", "--format=%(objectname)", f"refs/remotes/{remote}/")
        if ln.strip()
    ]


def configured_remote(repo: str, branch: str) -> str:
    """Remote this branch tracks, from config, so a missing tracking ref does
    not hide it."""
    code, out, _ = git(repo, "config", "--get", f"branch.{branch}.remote")
    remote = out.strip() if code == 0 else ""
    if remote and remote != ".":
        return remote
    remotes = git_lines(repo, "remote")
    return remotes[0] if remotes else ""


def configured_remote_branch(repo: str, branch: str) -> str:
    code, out, _ = git(repo, "config", "--get", f"branch.{branch}.merge")
    merge = out.strip() if code == 0 else ""
    if merge.startswith("refs/heads/"):
        return merge[len("refs/heads/") :]
    return branch


def all_remote_tips(repo: str, remote: str, heads: dict[str, str] | None) -> list[str]:
    """Remote tips whose objects exist locally, so ancestry can be tested."""
    if heads is None:
        return local_tracking_shas(repo, remote)
    return [sha for sha in heads.values() if object_exists(repo, sha)]


def merged_by_patch(repo: str, tips: list[str], branch: str) -> bool:
    """True when every commit of the branch has an equivalent patch upstream
    (git cherry marks those '-'), which is what a squash-merged branch looks
    like."""
    for tip in tips:
        code, out, _ = git(repo, "cherry", tip, branch)
        if code != 0 or not out.strip():
            continue
        if all(line.startswith("-") for line in out.splitlines() if line.strip()):
            return True
    return False


def commits_reachable_remotely(repo: str, branch: str) -> bool:
    """True when the branch is already merged into a remote branch, or carries
    no commit that no remote has (a squashed merge counts as merged)."""
    remote = configured_remote(repo, branch)
    if not remote:
        return False
    heads = remote_head_shas(repo, remote)
    tips = all_remote_tips(repo, remote, heads)
    if not tips:
        return False
    code, out, _ = git(repo, "rev-list", branch, "--not", *tips)
    if code != 0:
        return True
    if not out.strip():
        return True
    return merged_by_patch(repo, tips, branch)


def check_unpushed_work(repo: str, report: Report) -> None:
    """Documented work must reach the remote: local commits left behind."""
    branches = git_lines(repo, "for-each-ref", "--format=%(refname:short)%09%(upstream:short)%09%(upstream:track)", "refs/heads/")
    for line in branches:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name, upstream = parts[0], parts[1]
        track = parts[2] if len(parts) > 2 else ""
        if "ahead" in track:
            report.warn(
                "UNPUSHED_WORK",
                f"local branch '{name}' is ahead of '{upstream}'; those commits are not pushed",
            )
            continue
        if "behind" in track:
            report.warn(
                "UNPUSHED_WORK",
                f"local branch '{name}' is behind '{upstream}'; push it before pushing again",
            )
            continue
        if upstream:
            # Tracking ref exists and the branch is level with it.
            continue

        # No local tracking ref. The branch may still be pushed, and the remote
        # is the only authority on that.
        remote = configured_remote(repo, name)
        if not remote:
            if commits_reachable_remotely(repo, name):
                continue
            report.warn(
                "UNPUSHED_WORK",
                f"local branch '{name}' has no remote and holds commits no remote has",
            )
            continue

        remote_branch = configured_remote_branch(repo, name)
        heads = remote_head_shas(repo, remote)
        local_tip = rev_parse(repo, name)
        remote_tip = heads.get(remote_branch) if heads else None

        if remote_tip and remote_tip == local_tip:
            # Pushed: the remote head is exactly this branch.
            continue

        tips = all_remote_tips(repo, remote, heads)
        code, out, _ = git(repo, "rev-list", name, "--not", *tips) if tips else (1, "", "")
        if code == 0 and not out.strip():
            # Every commit is already contained in some remote branch.
            continue
        if tips and merged_by_patch(repo, tips, name):
            # Squash-merged upstream.
            continue
        if remote_tip and object_exists(repo, remote_tip):
            code, _, _ = git(repo, "merge-base", "--is-ancestor", name, remote_tip)
            if code == 0:
                report.warn(
                    "UNPUSHED_WORK",
                    f"local branch '{name}' is behind '{remote}/{remote_branch}'; pull before pushing again",
                )
                continue
        report.warn(
            "UNPUSHED_WORK",
            f"local branch '{name}' holds commits that '{remote}/{remote_branch}' does not have",
        )


def check_dirty(repo: str, report: Report) -> None:
    status = git_lines(repo, "status", "--porcelain")
    if status:
        shown = status[:10]
        more = "" if len(status) <= 10 else f" (+{len(status) - 10} more)"
        report.warn(
            "DIRTY_AT_PUSH",
            f"working tree has {len(status)} uncommitted change(s) while pushing:{chr(10)}    "
            + chr(10).join("    " + s for s in shown)
            + more,
        )


def check_docs(repo: str, base: str, head: str, rules: dict, report: Report) -> None:
    changed = files_in_range(repo, base, head)
    if not changed:
        return

    touched = set(changed)
    decision_log = rules["decision_log"]
    inventory = rules["change_inventory"]

    non_doc = [p for p in changed if not is_doc_path(p, rules)]
    if non_doc and decision_log not in touched:
        report.warn(
            "NO_DECISION_DOC",
            f"{len(non_doc)} non-documentation file(s) changed but '{decision_log}' was not updated in this range",
        )
    if changed and inventory not in touched:
        report.warn(
            "NO_INVENTORY_DOC",
            f"{len(changed)} file(s) changed but '{inventory}' was not updated in this range",
        )

    # Every changed file needs a row in the current change inventory.
    inv_path = Path(repo) / inventory
    inv_text = ""
    if inv_path.is_file():
        try:
            inv_text = inv_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            inv_text = ""
    if inv_text:
        uncovered = [
            p for p in changed if p not in inv_text and os.path.basename(p) not in inv_text
        ]
        if uncovered:
            report.warn(
                "UNCOVERED_FILE",
                "file(s) changed in this range have no row in "
                f"'{inventory}': " + ", ".join(uncovered[:20]) + (" ..." if len(uncovered) > 20 else ""),
            )

    # Prompt / decision record of the AI session that produced the work.
    patterns = rules["prompt_record_patterns"]
    has_record = any(any(p in path for p in patterns) for path in changed)
    touches_skills_or_docs = any(
        is_skill_path(p, rules) or is_doc_path(p, rules) for p in changed
    )
    if touches_skills_or_docs and not has_record:
        report.warn(
            "PROMPT_NOT_LOGGED",
            "this range changes skills/ or documentation but contains no prompt/decision record "
            "of the session that produced it",
        )


def check_commits(repo: str, base: str, head: str, rules: dict, report: Report) -> None:
    commits = commits_in_range(repo, base, head)
    words = rules.get("placeholder_subject_patterns") or []
    placeholder = re.compile(
        r"^(" + "|".join(re.escape(w) for w in words) + r")[\s!:-]*$", re.IGNORECASE
    )
    min_body = int(rules.get("min_commit_body_chars", 20))

    for c in commits:
        if placeholder.match(c["subject"].strip()):
            report.warn(
                "PLACEHOLDER_SUBJECT",
                f"commit {c['short']} has a placeholder subject: '{c['subject']}'",
            )
        if len(c["body"]) < min_body:
            report.warn(
                "UNDOCUMENTED_COMMIT",
                f"commit {c['short']} has no written reasoning (body under {min_body} characters): "
                f"'{c['subject']}'",
            )

    # Informational only: size per commit, so a reviewer can judge granularity.
    for c in commits:
        numstat = git_lines(repo, "show", "--numstat", "--format=", c["sha"])
        files = 0
        lines = 0
        for row in numstat:
            parts = row.split("\t")
            if len(parts) < 3:
                continue
            files += 1
            for cell in parts[:2]:
                if cell.isdigit():
                    lines += int(cell)
        report.note(f"{c['short']}  {files} file(s), {lines} line(s)  {c['subject']}")


# -------------------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description="Warn about undocumented work before a push.")
    ap.add_argument("--repo", default=os.getcwd(), help="path inside the git repository")
    ap.add_argument("--range", dest="range_", default=None, help="explicit base..head range")
    ap.add_argument("--strict", action="store_true", help="reserved; always exits 0 today")
    args = ap.parse_args()

    rules = load_rules()
    report = Report()

    code, out, err = git(args.repo, "rev-parse", "--show-toplevel")
    if code != 0:
        print("[commit-discipline] WARN: not a git repository; nothing checked.")
        return 0
    repo = out.strip()

    base, head, desc = resolve_range(repo, args.range_)
    check_unpushed_work(repo, report)
    check_dirty(repo, report)
    if base or head:
        check_docs(repo, base, head, rules, report)
        check_commits(repo, base, head, rules, report)

    if report.warnings:
        print(f"[commit-discipline] range: {desc}")
        for code_, msg in report.warnings:
            print(f"[commit-discipline] WARN {code_}: {msg}")
        print(
            f"[commit-discipline] {len(report.warnings)} warning(s). The push continues; "
            "write the missing records, or split the commit and push again."
        )
    else:
        print(f"[commit-discipline] range: {desc}")
        print("[commit-discipline] OK: documentation looks complete for this range.")

    if report.info:
        print("[commit-discipline] info (per-commit size, not a finding):")
        for line in report.info:
            print(f"[commit-discipline]   {line}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break a push
        print(f"[commit-discipline] WARN: checker error: {exc}")
        sys.exit(0)
