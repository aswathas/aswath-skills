#!/usr/bin/env python3
"""Self-check for aswath-record. Runs against a scratch directory; touches nothing real."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ledger", HERE / "ledger.py")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

results = []


def case(name):
    def wrap(fn):
        results.append((name, fn))
        return fn

    return wrap


def build_scratch(root: Path) -> Path:
    store = root / "store"
    if store.is_dir():
        shutil.rmtree(store)
    (store / "ledger").mkdir(parents=True)
    (store / "secrets").mkdir(parents=True)
    (store / "state").mkdir(parents=True)
    os.environ["ASWATH_STORE"] = str(store)
    os.environ["ASWATH_LEDGER"] = str(store / "ledger")
    os.environ["ASWATH_SECRETS"] = str(store / "secrets")
    os.environ["ASWATH_STATE"] = str(store / "state")
    os.environ["ASWATH_ENV_ROOTS"] = str(root / "no-such-root")
    return store


def run(argv) -> tuple:
    """Run a command, capture stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ledger.main(argv)
    return code, out.getvalue(), err.getvalue()


@case("a run is appended and counted")
def t_roundtrip(root: Path) -> None:
    build_scratch(root)
    code, _out, _err = run([
        "add", "--project", "demo", "--kind", "run", "--job", "build", "--outcome", "failed",
    ])
    assert code == 0
    lines = (root / "store" / "ledger" / "demo.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    record = json.loads(lines[0])
    assert record["kind"] == "run" and record["outcome"] == "failed", record
    _code, out, _err = run(["stats", "--project", "demo"])
    assert "runs: 1" in out, out
    assert "failures: 1" in out, out


@case("the delivery completion rate counts delivered over produced")
def t_rate(root: Path) -> None:
    build_scratch(root)
    for name in ("a1", "a2", "a3"):
        run(["add", "--project", "demo", "--kind", "artifact", "--id", name, "--path", f"/{name}"])
    run(["deliver", "--project", "demo", "--id", "a1", "--channel", "whatsapp", "--message-id", "M1"])
    _code, out, _err = run(["stats", "--project", "demo"])
    assert "artifacts: 3" in out, out
    assert "delivered: 1" in out, out
    assert "delivery completion rate: 1/3" in out, out


@case("a superseded artifact is listed as superseded, not current")
def t_superseded(root: Path) -> None:
    build_scratch(root)
    run(["add", "--project", "demo", "--kind", "artifact", "--id", "old"])
    run(["add", "--project", "demo", "--kind", "artifact", "--id", "new", "--supersedes", "old"])
    _code, out, _err = run(["superseded", "--project", "demo"])
    assert "superseded old" in out, out
    assert "current new" in out, out
    assert "current old" not in out, out


@case("the doctor prints the name and never the value")
def t_redaction(root: Path) -> None:
    store = build_scratch(root)
    (store / "secrets" / "demo.env").write_text("TOKEN=abc123\n", encoding="utf-8")
    code, out, err = run(["doctor", "secrets"])
    assert "abc123" not in out and "abc123" not in err, (out, err)
    assert "TOKEN" in out, out
    assert code == 0, (code, out, err)


@case("a tracked secret file fails the doctor, an ignored one does not")
def t_tracking(root: Path) -> None:
    store = build_scratch(root)
    subprocess.run(["git", "init", "-q", str(store)], check=True)
    secret = store / ".env"
    secret.write_text("TOKEN=abc123\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(store), "add", ".env"], check=True)
    code, out, err = run(["doctor", "secrets"])
    assert code == 1, (code, out, err)
    assert "abc123" not in out and "abc123" not in err, (out, err)

    subprocess.run(["git", "-C", str(store), "rm", "-q", "--cached", ".env"], check=True)
    (store / ".gitignore").write_text(".env\n", encoding="utf-8")
    code, out, err = run(["doctor", "secrets"])
    assert code == 0, (code, out, err)


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="record-selftest-"))
    failed = 0
    try:
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
