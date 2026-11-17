#!/usr/bin/env python3
"""The estate's own layout, made checkable.

One map says where every skill lives and which copy is canonical. One check
says whether the machine still matches that map. One lease says which machine
is writing shared state right now.

    catalog.py build            write ~/.agents/config/skill-map.json
    catalog.py check            verify the machine against the map; exit 1 on a violation
    catalog.py fix <name>       re-point one skill at its canonical copy
    catalog.py verify           compare this machine's map with the remote's
    catalog.py lease take <task> [--minutes N]
    catalog.py lease release

No dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}
SKIP_SUFFIX = (".pyc", ".pyo")


# ---------------------------------------------------------------- locations


def repo_root() -> Path:
    """The skills repo this script lives in."""
    env = os.environ.get("ASWATH_SKILLS_REPO")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[4]


def store_root() -> Path:
    return Path(os.environ.get("ASWATH_STORE", Path.home() / ".agents"))


def active_root() -> Path:
    return Path(os.environ.get("ASWATH_ACTIVE", store_root() / "skills-active"))


def claude_root() -> Path:
    return Path(os.environ.get("ASWATH_CLAUDE", Path.home() / ".claude" / "skills"))


def state_root() -> Path:
    return Path(os.environ.get("ASWATH_STATE", store_root() / "state"))


def map_path() -> Path:
    return store_root() / "config" / "skill-map.json"


def pc_path() -> Path:
    return store_root() / "config" / "pc.json"


def lease_path() -> Path:
    return state_root() / "lease.json"


def manifest_path() -> Path:
    return repo_root() / "manifest.json"


# ---------------------------------------------------------------- links


def is_link(path: Path) -> bool:
    """True for a symlink or a Windows junction.

    os.path.islink() is False for a junction, so the reparse-point attribute
    is what actually answers the question on Windows.
    """
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def link_target(path: Path) -> Path:
    """Where a link points, resolved."""
    return Path(os.path.realpath(path))


def path_present(path: Path) -> bool:
    """True when the path exists, including a junction whose target is gone."""
    return path.exists() or is_link(path) or path.is_symlink()


def remove_path(path: Path) -> None:
    """Remove the path itself. A junction is removed, not its target."""
    if is_link(path) or path.is_symlink():
        try:
            os.unlink(path)
        except OSError:
            os.rmdir(path)
        return
    if path.is_dir():
        import shutil

        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def make_junction(link: Path, target: Path) -> None:
    """Create a Windows junction. Falls back to a symlink elsewhere."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if path_present(link):
        raise FileExistsError(f"{link} already exists")
    if os.name == "nt":
        r = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"mklink failed: {r.stdout.strip()} {r.stderr.strip()}")
    else:
        link.symlink_to(target, target_is_directory=True)


def replace_with_junction(link: Path, target: Path) -> None:
    if path_present(link):
        remove_path(link)
    make_junction(link, target)


# ---------------------------------------------------------------- content


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(root: Path) -> dict:
    """{relative path: sha256} for every file under root, or {} if missing."""
    out = {}
    if not root.is_dir():
        return out
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix in SKIP_SUFFIX:
            continue
        out[p.relative_to(root).as_posix()] = file_hash(p)
    return out


def tree_diff(a: Path, b: Path) -> dict:
    """Files that differ between two trees."""
    ta, tb = tree_hash(a), tree_hash(b)
    only_a = sorted(set(ta) - set(tb))
    only_b = sorted(set(tb) - set(ta))
    changed = sorted(k for k in set(ta) & set(tb) if ta[k] != tb[k])
    return {"only_in_first": only_a, "only_in_second": only_b, "changed": changed}


# ---------------------------------------------------------------- map


def load_manifest() -> dict:
    p = manifest_path()
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {row["name"]: row for row in data.get("skills", [])}


def place(entry: dict) -> str:
    """Where the skill lives, in a form two PCs can compare."""
    return entry.get("rel") or entry.get("canonical", "")


def describe(name: str, canonical: Path, origin: str) -> dict:
    store = store_root() / "skills" / name
    active = active_root() / name
    claude = claude_root() / name
    entry = {
        "origin": origin,
        "canonical": str(canonical),
        "store": str(store),
        "active": str(active),
        "claude": str(claude),
        "store_is_link": is_link(store),
        "active_is_link": is_link(active),
        "claude_is_link": is_link(claude),
    }
    for key, path in (("store_target", store), ("active_target", active), ("claude_target", claude)):
        if is_link(path):
            entry[key] = str(link_target(path))
    # The absolute path is this PC's. The relative one is the skill's place in
    # its origin, and it is what two PCs can compare.
    repo = repo_root()
    try:
        entry["rel"] = str(canonical.resolve().relative_to(repo.resolve()))
    except ValueError:
        try:
            entry["rel"] = "store/" + str(canonical.resolve().relative_to(store_root().resolve()))
        except ValueError:
            entry["rel"] = str(canonical)
    return entry


def build_map() -> dict:
    repo = repo_root()
    manifest = load_manifest()
    skills = {}
    for name, row in sorted(manifest.items()):
        canonical = (repo / row["path"]).resolve().parent
        skills[name] = describe(name, canonical, "public-repo")

    # Skills that live in the store and are not published: vendored and
    # third-party ones. They are canonical where they are.
    store_dir = store_root() / "skills"
    if store_dir.is_dir():
        for child in sorted(store_dir.iterdir()):
            if not child.is_dir() or child.name in skills:
                continue
            canonical = link_target(child) if is_link(child) else child
            origin = "public-repo" if str(canonical).startswith(str(repo)) else "store"
            skills[child.name] = describe(child.name, canonical, origin)

    return {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo": str(repo),
        "skills": skills,
    }


def cmd_build(_args) -> int:
    data = build_map()
    target = map_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    pc = {
        "host": socket.gethostname(),
        "last_map_build": data["generated"],
        "skill_count": len(data["skills"]),
    }
    pc_path().parent.mkdir(parents=True, exist_ok=True)
    pc_path().write_text(json.dumps(pc, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {target} ({len(data['skills'])} skills)")
    print(f"wrote {pc_path()}")
    return 0


# ---------------------------------------------------------------- check


def keep_list() -> set:
    """The curated set of active skills."""
    keep_file = store_root() / "skills-active.list.json"
    if not keep_file.is_file():
        return set()
    try:
        return set(json.loads(keep_file.read_text(encoding="utf-8")).get("keep", []))
    except json.JSONDecodeError:
        return set()


def check() -> list:
    """Every way the machine can disagree with the map."""
    problems = []
    manifest = load_manifest()
    repo = repo_root()
    store_dir = store_root() / "skills"
    active_dir = active_root()
    keep = keep_list()

    for name, row in sorted(manifest.items()):
        canonical = (repo / row["path"]).resolve().parent
        store = store_dir / name
        active = active_dir / name
        claude = claude_root() / name
        wanted = name in keep

        if not canonical.is_dir():
            problems.append(("MISSING_CANONICAL", name, f"{canonical} does not exist"))
            continue

        if not store.exists():
            problems.append(("MISSING_STORE", name, f"{store} does not exist"))
        elif not is_link(store):
            diff = tree_diff(canonical, store)
            if diff["only_in_first"] or diff["only_in_second"] or diff["changed"]:
                detail = (
                    f"{len(diff['only_in_first'])} only in the repo, "
                    f"{len(diff['only_in_second'])} only in the store, "
                    f"{len(diff['changed'])} changed"
                )
            else:
                detail = "identical content, but a copy where a link belongs"
            problems.append(("SHADOWED_COPY", name, f"{store} is a real directory ({detail})"))
        elif link_target(store) != canonical:
            problems.append(("WRONG_TARGET", name, f"{store} points at {link_target(store)}, expected {canonical}"))

        # A skill only has to be active when the keep list says so.
        if not wanted:
            continue

        if not active.exists():
            problems.append(("MISSING_ACTIVE", name, f"{active} does not exist"))
        elif not is_link(active):
            problems.append(("COPY_IN_ACTIVE", name, f"{active} is a real directory, expected a link"))
        elif link_target(active) != canonical:
            problems.append(("ACTIVE_WRONG_TARGET", name, f"{active} points at {link_target(active)}, expected {canonical}"))

        # Some harnesses read the active set through a directory junction, so
        # the two paths are one place and the check would say it twice.
        if os.path.realpath(claude_root()) == os.path.realpath(active_dir):
            continue

        if not claude.exists():
            problems.append(("MISSING_CLAUDE", name, f"{claude} does not exist"))
        elif not is_link(claude):
            problems.append(("COPY_IN_CLAUDE", name, f"{claude} is a real directory, expected a link"))
        elif link_target(claude) != active.resolve() and link_target(claude) != active:
            problems.append(("CLAUDE_WRONG_TARGET", name, f"{claude} points at {link_target(claude)}, expected {active}"))

    # Every active entry is a link. A copy there is a copy nobody updates.
    for root, label in ((active_dir, "skills-active"), (claude_root(), ".claude/skills")):
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and not is_link(child):
                problems.append(("COPY_IN_ACTIVE", child.name, f"{child} is a real directory in {label}, expected a link"))

    # The keep list and the active directory must be the same set.
    keep_file = store_root() / "skills-active.list.json"
    if keep_file.is_file():
        try:
            keep = set(json.loads(keep_file.read_text(encoding="utf-8")).get("keep", []))
        except json.JSONDecodeError as exc:
            keep = set()
            problems.append(("BAD_KEEP_LIST", "-", f"{keep_file} is not valid JSON: {exc}"))
        if active_dir.is_dir():
            actual = {p.name for p in active_dir.iterdir() if p.is_dir()}
            for missing in sorted(keep - actual):
                problems.append(("KEEP_NOT_ACTIVE", missing, "in the keep list, absent from skills-active"))
            for extra in sorted(actual - keep):
                problems.append(("ACTIVE_NOT_KEPT", extra, "in skills-active, absent from the keep list"))
    else:
        problems.append(("NO_KEEP_LIST", "-", f"{keep_file} does not exist"))

    return problems


def cmd_check(_args) -> int:
    problems = check()
    if not problems:
        print("catalog: clean. Every skill resolves to one canonical copy.")
        return 0
    for code, name, detail in problems:
        print(f"catalog: {code} {name}: {detail}")
    print(f"catalog: {len(problems)} problem(s).")
    return 1


def cmd_fix(args) -> int:
    manifest = load_manifest()
    row = manifest.get(args.name)
    store = store_root() / "skills" / args.name

    if row:
        canonical = (repo_root() / row["path"]).resolve().parent
        if not canonical.is_dir():
            print(f"catalog: {canonical} does not exist.", file=sys.stderr)
            return 1
        if path_present(store) and not is_link(store):
            diff = tree_diff(canonical, store)
            only_store = diff["only_in_second"]
            if only_store:
                print(
                    f"catalog: the store copy of {args.name} holds {len(only_store)} file(s) the "
                    "published copy does not. Port them into the repo first - nothing was changed.",
                    file=sys.stderr,
                )
                for name in only_store[:10]:
                    print(f"  only in store: {name}", file=sys.stderr)
                return 1
            if diff["changed"]:
                print(
                    f"catalog: replacing the store copy of {args.name} "
                    f"({len(diff['changed'])} file(s) differed; the published copy wins)."
                )
        replace_with_junction(store, canonical)
        print(f"linked store  {store} -> {canonical}")
    elif store.is_dir():
        # A skill that lives in the store: the store copy is the canonical one.
        canonical = link_target(store) if is_link(store) else store
        print(f"catalog: {args.name} is a store skill; the store copy is canonical.")
    else:
        print(f"catalog: {args.name} is in neither the manifest nor the store.", file=sys.stderr)
        return 1

    if args.name not in keep_list():
        print(f"catalog: {args.name} is not in the keep list, so it stays inactive.")
        return 0

    replace_with_junction(active_root() / args.name, canonical)
    print(f"linked active {active_root() / args.name} -> {canonical}")
    # Some harnesses read the active set through a directory junction, so the
    # two paths are the same place. Linking twice would make a self-link.
    if os.path.realpath(claude_root()) != os.path.realpath(active_root()):
        claude = claude_root() / args.name
        replace_with_junction(claude, active_root() / args.name)
        print(f"linked claude {claude} -> {active_root() / args.name}")
    return 0


# ---------------------------------------------------------------- verify


def remote_map() -> dict:
    store = store_root()
    if not (store / ".git").exists():
        return {}
    fetch = subprocess.run(
        ["git", "-C", str(store), "fetch", "-q", "origin", "main"],
        capture_output=True,
        text=True,
    )
    if fetch.returncode != 0:
        return {}
    show = subprocess.run(
        ["git", "-C", str(store), "show", "FETCH_HEAD:config/skill-map.json"],
        capture_output=True,
        text=True,
    )
    if show.returncode != 0:
        return {}
    try:
        return json.loads(show.stdout)
    except json.JSONDecodeError:
        return {}


def cmd_verify(_args) -> int:
    local = build_map()
    remote = remote_map()
    if not remote:
        print("catalog: no map on the remote. Run this on both PCs after the first sync.")
        return 1
    ls, rs = local["skills"], remote.get("skills", {})
    only_local = sorted(set(ls) - set(rs))
    only_remote = sorted(set(rs) - set(ls))
    moved = sorted(n for n in set(ls) & set(rs) if place(ls[n]) != place(rs[n]))
    if not (only_local or only_remote or moved):
        print(f"catalog: both machines agree on {len(ls)} skills.")
        return 0
    for n in only_local:
        print(f"catalog: only on this PC: {n} -> {ls[n]['canonical']}")
    for n in only_remote:
        print(f"catalog: only on the remote: {n} -> {rs[n]['canonical']}")
    for n in moved:
        print(f"catalog: different canonical path: {n}")
        print(f"  this PC: {ls[n]['canonical']}")
        print(f"  remote:  {rs[n]['canonical']}")
    print(f"catalog: {len(only_local) + len(only_remote) + len(moved)} difference(s).")
    return 1


# ---------------------------------------------------------------- lease


def read_lease() -> dict:
    p = lease_path()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def cmd_lease(args) -> int:
    if args.action == "take":
        minutes = args.minutes
        held = read_lease()
        now = time.time()
        if held and held.get("until", 0) > now and held.get("host") != socket.gethostname():
            print(
                f"catalog: the lease is held by {held.get('host')} "
                f"({held.get('task')}) until {time.strftime('%H:%M:%S', time.localtime(held['until']))}.",
                file=sys.stderr,
            )
            return 1
        if held and held.get("until", 0) > now:
            print(f"catalog: renewed the lease this machine already held ({held.get('task')}).")
        else:
            if held:
                print(f"catalog: took over an expired lease from {held.get('host')}.")
            else:
                print(f"catalog: took the lease for {args.task}.")
        payload = {
            "host": socket.gethostname(),
            "task": args.task,
            "pid": os.getpid(),
            "until": now + minutes * 60,
        }
        lease_path().parent.mkdir(parents=True, exist_ok=True)
        lease_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return 0

    if args.action == "release":
        held = read_lease()
        if not held:
            print("catalog: no lease is held.")
            return 0
        if held.get("host") != socket.gethostname():
            print(
                f"catalog: the lease is held by {held.get('host')}, not this machine.",
                file=sys.stderr,
            )
            return 1
        lease_path().unlink(missing_ok=True)
        print(f"catalog: released the lease ({held.get('task')}).")
        return 0

    if args.action == "show":
        held = read_lease()
        if not held:
            print("catalog: no lease is held.")
            return 0
        print(json.dumps(held, indent=2))
        return 0

    return 2


# ---------------------------------------------------------------- cli


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="write the skill map")
    sub.add_parser("check", help="verify the machine against the map")
    p_fix = sub.add_parser("fix", help="re-point one skill at its canonical copy")
    p_fix.add_argument("name")
    sub.add_parser("verify", help="compare this machine's map with the remote's")
    p_lease = sub.add_parser("lease", help="take, release or show the write lease")
    p_lease.add_argument("action", choices=["take", "release", "show"])
    p_lease.add_argument("task", nargs="?", default="unknown")
    p_lease.add_argument("--minutes", type=int, default=30)

    args = ap.parse_args(argv)
    return {
        "build": cmd_build,
        "check": cmd_check,
        "fix": cmd_fix,
        "verify": cmd_verify,
        "lease": cmd_lease,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
