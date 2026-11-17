#!/usr/bin/env python3
"""aswath-record: the run and artifact ledger, the secrets doctor, the metrics.

The ledger is append-only JSONL in the private store:

    ~/.agents/ledger/<project>.jsonl

One JSON object per line. A mistake is corrected by appending a new record,
never by editing a line, so git holds the history of what was believed when.

    python ledger.py add --project X --kind run --job Y --outcome ok
    python ledger.py add --project X --kind artifact --path P --sha256 H --supersedes ID
    python ledger.py superseded --project X
    python ledger.py deliver --project X --id ARTIFACT --channel whatsapp --message-id M
    python ledger.py import --since 2026-01-01
    python ledger.py stats --project X
    python ledger.py doctor secrets

Standard library only. Locations are environment-overridable so the
self-check can run against a scratch directory.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()

# A name that smells like a credential.
SECRET_NAME = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE_?KEY|CREDENTIAL|ACCESS_?KEY|"
    r"CLIENT_?SECRET|AUTH)", re.I
)
# A file that holds credentials by name.
SECRET_FILE = re.compile(r"^\.env$|\.env$|\.(pem|p12|pfx|key)$", re.I)
# A template is not a secret.
TEMPLATE = re.compile(r"(example|sample|template|dist|placeholder)", re.I)
ASSIGN = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
# A literal that could be a filled credential: long, mixed case, no code in it.
LITERAL = re.compile(r"^[A-Za-z0-9_\-\+/]{16,}$")
# Words that mean "put your own here".
PLACEHOLDER = re.compile(
    r"(your|paste|here|example|placeholder|changeme|dummy|fake|sample|xxx|insert|replace)",
    re.I,
)
# The old per-tool .env files: reported, never read for values.
ENV_ROOTS = [HOME / ".claude-mem", HOME / ".minimax", HOME / ".claude", HOME / ".commandcode"]
SKIP_DIRS = {
    "node_modules", "plugins", "projects", "sessions", "logs", "background-tasks",
    "skills", "history", "todos", "cache", "dist", "build", ".git", "v2", "skills-active",
}


# ---------------------------------------------------------------- locations


def store_root() -> Path:
    return Path(os.environ.get("ASWATH_STORE", HOME / ".agents"))


def ledger_root() -> Path:
    return Path(os.environ.get("ASWATH_LEDGER", store_root() / "ledger"))


def secrets_root() -> Path:
    return Path(os.environ.get("ASWATH_SECRETS", store_root() / "secrets"))


def state_root() -> Path:
    return Path(os.environ.get("ASWATH_STATE", store_root() / "state"))


def project_file(project: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", project)
    return ledger_root() / f"{safe}.jsonl"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_id() -> str:
    return uuid.uuid4().hex[:16]


# ---------------------------------------------------------------- the ledger


def read_records(project: str) -> list:
    path = project_file(project)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def append_record(record: dict) -> None:
    """Append one line. A failed append is kept, not lost."""
    path = project_file(record["project"])
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True)
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        failed = state_root() / "ledger-failed.ndjson"
        failed.parent.mkdir(parents=True, exist_ok=True)
        with failed.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        print(f"ledger: append to {path} failed: {exc}", file=sys.stderr)
        print(f"ledger: the record is kept in {failed}", file=sys.stderr)
        raise SystemExit(1)
    flush_failed(record["project"])


def flush_failed(project: str) -> None:
    """Move records that failed to append earlier into the ledger."""
    failed = state_root() / "ledger-failed.ndjson"
    if not failed.is_file():
        return
    path = project_file(project)
    known = {r.get("id") for r in read_records(project)}
    kept = []
    for line in failed.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            kept.append(line)
            continue
        if rec.get("project") != project or rec.get("id") in known:
            continue
        known.add(rec.get("id"))
        try:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            kept.append(line)
    if kept:
        failed.write_text("\n".join(kept) + "\n", encoding="utf-8")
    else:
        failed.unlink()


# ---------------------------------------------------------------- commands


def cmd_add(args) -> int:
    record = {
        "id": args.id or new_id(),
        "ts": now(),
        "project": args.project,
        "kind": args.kind,
    }
    for key, value in (
        ("job", args.job),
        ("outcome", args.outcome),
        ("path", args.path),
        ("sha256", args.sha256),
        ("channel", args.channel),
        ("message_id", args.message_id),
        ("artifact", args.artifact),
        ("skill", args.skill),
    ):
        if value:
            record[key] = value
    if args.supersedes:
        record["supersedes"] = list(args.supersedes)
    append_record(record)
    print(f"ledger: {record['kind']} {record['id']} -> {project_file(args.project)}")
    return 0


def cmd_superseded(args) -> int:
    """The ids the ledger marks superseded, and the ones that are current."""
    records = read_records(args.project)
    superseded = set()
    artifacts = {}
    messages = {}
    for r in records:
        for old in r.get("supersedes") or []:
            superseded.add(old)
        if r.get("kind") == "artifact":
            artifacts[r["id"]] = r
        if r.get("kind") == "delivery":
            messages[r.get("artifact")] = r.get("message_id")
    for aid in sorted(superseded):
        msg = messages.get(aid)
        print(f"superseded {aid}" + (f" message={msg}" if msg else ""))
    for aid in sorted(set(artifacts) - superseded):
        print(f"current {aid}")
    return 0


def cmd_deliver(args) -> int:
    record = {
        "id": new_id(),
        "ts": now(),
        "project": args.project,
        "kind": "delivery",
        "artifact": args.id,
        "channel": args.channel,
        "message_id": args.message_id,
    }
    append_record(record)
    print(f"ledger: delivered {args.id} to {args.channel} as {args.message_id}")
    return 0


def cmd_stats(args) -> int:
    records = read_records(args.project)
    runs = [r for r in records if r.get("kind") == "run"]
    failures = [r for r in runs if r.get("outcome") == "failed"]
    artifacts = [r for r in records if r.get("kind") == "artifact"]
    superseded = {old for r in records for old in (r.get("supersedes") or [])}
    produced = {a["id"] for a in artifacts}
    delivered = {r.get("artifact") for r in records if r.get("kind") == "delivery"} & produced
    print(f"project: {args.project}")
    print(f"runs: {len(runs)}")
    print(f"failures: {len(failures)}")
    print(f"artifacts: {len(produced)}")
    print(f"superseded: {len(superseded)}")
    print(f"delivered: {len(delivered)}")
    print(f"delivery completion rate: {len(delivered)}/{len(produced)}")
    return 0


# ---------------------------------------------------------------- import


def outcome_of(status: str) -> str:
    s = (status or "").lower()
    if s in ("succeeded", "success", "ok", "completed"):
        return "ok"
    if s in ("failed", "error"):
        return "failed"
    if s in ("canceled", "cancelled"):
        return "canceled"
    return "unknown"


def ms_to_iso(ms) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except (TypeError, ValueError, OSError):
        return now()


def parse_since(value: str) -> int:
    """Epoch seconds or YYYY-MM-DD, as milliseconds."""
    if not value:
        return 0
    if value.isdigit():
        return int(value) * 1000
    try:
        day = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return 0
    return int(day.timestamp() * 1000)


def cmd_import(args) -> int:
    """Harvest the runs the MiniMax runtime already knows about. Read-only."""
    db = Path(args.db) if args.db else HOME / ".minimax/v2/sqlite/runtime-state.sqlite"
    if not db.is_file():
        print(f"ledger: {db} does not exist. Nothing to import.", file=sys.stderr)
        return 1
    before = db.stat().st_mtime_ns
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select task_id, kind, status, created_at_ms, record_json "
            "from local_runtime_background_tasks where created_at_ms >= ?",
            (parse_since(args.since),),
        ).fetchall()
    finally:
        con.close()
    known = {r.get("id") for r in read_records(args.project)}
    added = 0
    for task_id, kind, status, created_ms, record_json in rows:
        rid = f"minimax:{task_id}"
        if rid in known:
            continue
        job = ""
        try:
            job = json.loads(record_json or "{}").get("description", "")
        except json.JSONDecodeError:
            job = ""
        append_record({
            "id": rid,
            "ts": ms_to_iso(created_ms),
            "project": args.project,
            "kind": "run",
            "job": job or kind,
            "outcome": outcome_of(status),
            "source": "minimax",
        })
        known.add(rid)
        added += 1
    after = db.stat().st_mtime_ns
    if before != after:
        print("ledger: the runtime database changed. It must be read-only.", file=sys.stderr)
        return 1
    print(f"ledger: imported {added} run record(s) from {db}")
    return 0


# ---------------------------------------------------------------- the doctor


def env_names(path: Path) -> list:
    """Variable names in a file. Never a value."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    names = []
    for line in text.splitlines():
        m = ASSIGN.match(line)
        if m:
            names.append(m.group(1))
    return names


def is_tracked(store: Path, rel: str) -> bool:
    out = subprocess.run(
        ["git", "-C", str(store), "ls-files", "--error-unmatch", "--", rel],
        capture_output=True,
        text=True,
    )
    return out.returncode == 0 and bool(out.stdout.strip())


def tracked_files(store: Path) -> list:
    out = subprocess.run(
        ["git", "-C", str(store), "ls-files", "-z"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return []
    return [p for p in out.stdout.split("\0") if p]


def scan_content(path: Path) -> list:
    """(line number, name) for every credential-looking literal in a file."""
    try:
        if path.stat().st_size > 2_000_000:
            return []
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if "\0" in text[:4096]:
        return []
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        m = ASSIGN.match(line)
        if not m:
            continue
        name, value = m.group(1), m.group(2).strip().strip("'\"")
        if not SECRET_NAME.search(name):
            continue
        if not LITERAL.match(value):
            continue
        if not any(c.isdigit() for c in value) or not any(c.islower() for c in value):
            continue  # a name in capitals, or a word, is not a credential
        if PLACEHOLDER.search(value):
            continue
        found.append((number, name))
    return found


def env_roots() -> list:
    """Where the old per-tool .env files live. Overridable for the self-check."""
    raw = os.environ.get("ASWATH_ENV_ROOTS")
    if raw is not None:
        return [Path(p) for p in raw.split(os.pathsep) if p]
    return ENV_ROOTS


def outside_convention() -> list:
    """The old per-tool .env files. Reported by path only."""
    hits = []
    for root in env_roots():
        if not root.is_dir():
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                if name == ".env" or name.endswith(".env"):
                    hits.append(Path(dirpath) / name)
    return sorted(hits)


def cmd_doctor(args) -> int:
    """Report secret names, never secret values. Fail on a tracked secret."""
    store = store_root()
    problems = 0

    secrets = secrets_root()
    if secrets.is_dir():
        for f in sorted(secrets.glob("*.env")):
            names = env_names(f)
            print(f"secret file: {f} -> {', '.join(names) if names else '(no variables)'}")
    else:
        print(f"secret home: {secrets} does not exist yet.")

    for rel in tracked_files(store):
        path = store / rel
        name = path.name
        if SECRET_FILE.search(name) and not TEMPLATE.search(name):
            names = env_names(path) if path.is_file() else []
            print(f"TRACKED SECRET FILE: {rel}"
                  + (f" ({', '.join(names)})" if names else ""))
            problems += 1
            continue
        for number, hit in scan_content(path):
            print(f"TRACKED SECRET: {rel}:{number}: {hit}=<redacted>")
            problems += 1

    for f in outside_convention():
        print(f"outside the convention: {f}")

    if problems:
        print(f"doctor: {problems} tracked secret file(s) or value(s).", file=sys.stderr)
        return 1
    print("doctor: no tracked secret found.")
    return 0


# ---------------------------------------------------------------- main


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ledger.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="append one record")
    p_add.add_argument("--project", required=True)
    p_add.add_argument("--kind", default="run", choices=["run", "artifact", "delivery", "note"])
    p_add.add_argument("--id")
    p_add.add_argument("--job")
    p_add.add_argument("--outcome")
    p_add.add_argument("--path")
    p_add.add_argument("--sha256")
    p_add.add_argument("--supersedes", action="append")
    p_add.add_argument("--channel")
    p_add.add_argument("--message-id")
    p_add.add_argument("--artifact")
    p_add.add_argument("--skill", help="the skill this run belongs to")
    p_add.set_defaults(func=cmd_add)

    p_sup = sub.add_parser("superseded", help="list superseded and current artifacts")
    p_sup.add_argument("--project", required=True)
    p_sup.set_defaults(func=cmd_superseded)

    p_del = sub.add_parser("deliver", help="record that an artifact was delivered")
    p_del.add_argument("--project", required=True)
    p_del.add_argument("--id", required=True, help="the artifact id")
    p_del.add_argument("--channel", default="whatsapp")
    p_del.add_argument("--message-id", required=True)
    p_del.set_defaults(func=cmd_deliver)

    p_imp = sub.add_parser("import", help="harvest MiniMax runtime runs")
    p_imp.add_argument("--project", default="minimax")
    p_imp.add_argument("--since", default="")
    p_imp.add_argument("--db")
    p_imp.set_defaults(func=cmd_import)

    p_stats = sub.add_parser("stats", help="count the ledger")
    p_stats.add_argument("--project", required=True)
    p_stats.set_defaults(func=cmd_stats)

    p_doc = sub.add_parser("doctor", help="check the secrets")
    p_doc.add_argument("check", choices=["secrets"])
    p_doc.set_defaults(func=cmd_doctor)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
