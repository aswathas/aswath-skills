#!/usr/bin/env python3
"""Self-check for aswath-catalog. Runs against a scratch estate; touches nothing real."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("catalog", HERE / "catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

results = []


def case(name):
    def wrap(fn):
        results.append((name, fn))
        return fn

    return wrap


def build_estate(root: Path) -> None:
    """A machine where every skill resolves to one canonical copy."""
    repo = root / "repo"
    skill = repo / "skills" / "workflow" / "aswath-demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: aswath-demo\n---\n", encoding="utf-8")
    (repo / "manifest.json").write_text(
        json.dumps(
            {
                "name": "test",
                "skills": [
                    {
                        "name": "aswath-demo",
                        "category": "workflow",
                        "path": "skills/workflow/aswath-demo/SKILL.md",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    store = root / "store"
    (store / "skills").mkdir(parents=True)
    (store / "skills-active").mkdir(parents=True)
    (store / "config").mkdir(parents=True)
    (store / "state").mkdir(parents=True)
    (root / "claude" / "skills").mkdir(parents=True)

    (store / "skills-active.list.json").write_text(
        json.dumps({"keep": ["aswath-demo"]}), encoding="utf-8"
    )

    catalog.make_junction(store / "skills" / "aswath-demo", skill)
    catalog.make_junction(store / "skills-active" / "aswath-demo", skill)
    catalog.make_junction(root / "claude" / "skills" / "aswath-demo", store / "skills-active" / "aswath-demo")


def point_env(root: Path) -> None:
    os.environ["ASWATH_SKILLS_REPO"] = str(root / "repo")
    os.environ["ASWATH_STORE"] = str(root / "store")
    os.environ["ASWATH_ACTIVE"] = str(root / "store" / "skills-active")
    os.environ["ASWATH_CLAUDE"] = str(root / "claude" / "skills")
    os.environ["ASWATH_STATE"] = str(root / "store" / "state")


def codes(root: Path):
    return {code for code, _name, _detail in catalog.check()}


@case("a clean estate reports no problem")
def t_clean(root: Path) -> None:
    assert codes(root) == set(), f"expected no problems, got {codes(root)}"


@case("a shadowed copy in the store is reported")
def t_shadowed(root: Path) -> None:
    link = root / "store" / "skills" / "aswath-demo"
    catalog.remove_path(link)
    copy = link
    copy.mkdir()
    (copy / "SKILL.md").write_text("---\nname: aswath-demo\n---\nOLD\n", encoding="utf-8")
    assert "SHADOWED_COPY" in codes(root), codes(root)
    catalog.remove_path(link)
    catalog.make_junction(link, root / "repo" / "skills" / "workflow" / "aswath-demo")


@case("a real directory in the active set is reported")
def t_copy_active(root: Path) -> None:
    link = root / "store" / "skills-active" / "aswath-demo"
    catalog.remove_path(link)
    link.mkdir()
    (link / "SKILL.md").write_text("copy\n", encoding="utf-8")
    assert "COPY_IN_ACTIVE" in codes(root), codes(root)
    catalog.remove_path(link)
    catalog.make_junction(link, root / "repo" / "skills" / "workflow" / "aswath-demo")


@case("a keep list that disagrees with the active set is reported")
def t_keep_drift(root: Path) -> None:
    keep = root / "store" / "skills-active.list.json"
    keep.write_text(json.dumps({"keep": ["aswath-demo", "aswath-ghost"]}), encoding="utf-8")
    found = codes(root)
    assert "KEEP_NOT_ACTIVE" in found, found
    keep.write_text(json.dumps({"keep": ["aswath-demo"]}), encoding="utf-8")
    assert "KEEP_NOT_ACTIVE" not in codes(root)


@case("fix rebuilds a broken link and check passes after")
def t_fix(root: Path) -> None:
    link = root / "store" / "skills-active" / "aswath-demo"
    catalog.remove_path(link)
    link.mkdir()
    (link / "SKILL.md").write_text("copy\n", encoding="utf-8")
    assert catalog.main(["fix", "aswath-demo"]) == 0
    assert codes(root) == set(), codes(root)


@case("the map is written and holds the canonical path")
def t_build(root: Path) -> None:
    assert catalog.main(["build"]) == 0
    data = json.loads((root / "store" / "config" / "skill-map.json").read_text(encoding="utf-8"))
    entry = data["skills"]["aswath-demo"]
    assert entry["origin"] == "public-repo", entry
    assert entry["canonical"].replace("\\", "/").endswith("skills/workflow/aswath-demo"), entry
    assert entry["active_is_link"] is True, entry
    assert entry["rel"].replace("\\", "/") == "skills/workflow/aswath-demo", entry


@case("two PCs agree when only the absolute root differs")
def t_place(_root: Path) -> None:
    here = {"rel": "skills/workflow/aswath-demo", "canonical": r"C:\one\repo\skills\workflow\aswath-demo"}
    there = {"rel": "skills/workflow/aswath-demo", "canonical": r"D:\two\repo\skills\workflow\aswath-demo"}
    assert catalog.place(here) == catalog.place(there)
    other = {"rel": "store/aswath-other", "canonical": r"C:\one\.agents\skills\aswath-other"}
    assert catalog.place(other) != catalog.place(here)


@case("the lease is taken, refused by another host, and released")
def t_lease(root: Path) -> None:
    lease = root / "store" / "state" / "lease.json"
    assert catalog.main(["lease", "take", "demo", "--minutes", "30"]) == 0
    assert lease.is_file()
    held = json.loads(lease.read_text(encoding="utf-8"))
    held["host"] = "some-other-pc"
    lease.write_text(json.dumps(held), encoding="utf-8")
    assert catalog.main(["lease", "take", "demo"]) == 1, "a live lease on another host must be refused"
    lease.unlink()
    assert catalog.main(["lease", "release"]) == 0


@case("fix creates a store link that is missing")
def t_fix_missing_store(root: Path) -> None:
    link = root / "store" / "skills" / "aswath-demo"
    catalog.remove_path(link)
    assert not catalog.path_present(link), "the store link should be gone"
    assert catalog.main(["fix", "aswath-demo"]) == 0
    assert catalog.is_link(link), "fix must create the missing store link"
    assert codes(root) == set(), codes(root)


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="catalog-selftest-"))
    try:
        build_estate(root)
        point_env(root)
        failed = 0
        for name, fn in results:
            try:
                fn(root)
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
