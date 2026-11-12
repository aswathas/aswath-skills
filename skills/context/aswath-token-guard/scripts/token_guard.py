#!/usr/bin/env python3
"""
Token guard - what a session costs, what wasted it, and the raw ledger.

Three views over the same numbers:

    --view stats    per-session table, cause breakdown, totals
    --view ledger   every turn as a line item, the costliest tool outputs,
                    the files that were read more than once
    --view guard    what to stop doing now: repeat reads, oversized outputs,
                    the cache-read ratio

Token counts come from the API usage objects the runtime reports, never from
a character estimate. Claude Code records them per assistant message; the
MiniMax runtime records them per turn in its local runtime database.

A turn's window (input + cache read) is attributed to causes by content
weight inside that turn. The totals are exact; the split is a stated method.

Usage:
    token_guard.py                       # the newest session, guard view
    token_guard.py --view stats --last 10
    token_guard.py --view ledger --session-id <id>
    token_guard.py --view stats --all --json

Stdlib only. Python 3.9+.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

CHARS_PER_TOKEN = 4


# --------------------------------------------------------------------------
# stores
# --------------------------------------------------------------------------

def claude_sessions():
    """Every Claude Code transcript, with its session id."""
    out = []
    for path in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        out.append(path)
    return out


def minimax_sessions():
    """Every MiniMax Code session directory that has a transcript."""
    return sorted(
        os.path.dirname(p)
        for p in glob.glob(os.path.expanduser("~/.minimax/v2/sessions/**/messages.jsonl"), recursive=True)
    )


def approx_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


def block_text(block) -> str:
    if isinstance(block, str):
        return block
    if isinstance(block, dict):
        for key in ("text", "content", "output", "input"):
            value = block.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, list):
                return " ".join(block_text(b) for b in value)
    return ""


# --------------------------------------------------------------------------
# Claude Code
# --------------------------------------------------------------------------

def read_claude(path: str) -> dict:
    """One Claude Code transcript -> usage totals and content causes."""
    sid = os.path.splitext(os.path.basename(path))[0]
    turns = 0
    usage = Counter()
    causes = Counter()
    tool_outputs = []          # (tool, approx tokens, text)
    file_reads = Counter()     # path -> times
    pending_context = []       # blocks since the last assistant message
    model = ""
    cwd = ""
    window_now = 0             # the window the last turn actually carried

    with open(path, encoding="utf8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rtype = rec.get("type")
            cwd = rec.get("cwd") or cwd
            message = rec.get("message") or {}

            if rtype == "user":
                content = message.get("content")
                if isinstance(content, str):
                    pending_context.append(("user prompt", content))
                    causes["user prompt"] += approx_tokens(content)
                elif isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_result":
                            text = block_text(block.get("content"))
                            pending_context.append(("tool result", text))
                            causes["tool result"] += approx_tokens(text)
                            tool_outputs.append((str(block.get("tool_use_id", "")), approx_tokens(text), text[:200]))
                        else:
                            text = block_text(block)
                            pending_context.append(("user prompt", text))
                            causes["user prompt"] += approx_tokens(text)

            elif rtype == "assistant":
                turns += 1
                u = message.get("usage") or {}
                model = message.get("model") or model
                inp = int(u.get("input_tokens") or 0)
                out = int(u.get("output_tokens") or 0)
                cr = int(u.get("cache_read_input_tokens") or 0)
                cw = int(u.get("cache_creation_input_tokens") or 0)
                usage["input"] += inp
                usage["output"] += out
                usage["cache_read"] += cr
                usage["cache_write"] += cw
                usage["total"] += inp + out + cr + cw
                causes["assistant output"] += out
                window_now = inp + cr + cw

                # attribute the window across the context that produced it
                window = inp + cr
                if window and pending_context:
                    weight = sum(approx_tokens(t) for _, t in pending_context) or 1
                    for cause, text in pending_context:
                        causes[cause] += int(window * approx_tokens(text) / weight)
                pending_context = []

            # tool calls: note which files were read
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = str(block.get("name", ""))
                        inp_block = block.get("input") or {}
                        path_arg = inp_block.get("file_path") or inp_block.get("path")
                        if name in ("Read", "read", "view") and path_arg:
                            file_reads[str(path_arg)] += 1

    return {
        "store": "claude-code",
        "id": sid,
        "title": os.path.basename(os.path.dirname(path)),
        "cwd": cwd,
        "model": model,
        "turns": turns,
        "usage": dict(usage),
        "causes": dict(causes),
        "tool_outputs": tool_outputs,
        "file_reads": dict(file_reads),
        "window_now": window_now,
    }


# --------------------------------------------------------------------------
# MiniMax Code
# --------------------------------------------------------------------------

def minimax_usage_rows() -> dict:
    """session_id -> usage totals, straight from the runtime database."""
    db = os.path.expanduser("~/.minimax/v2/sqlite/runtime-state.sqlite")
    if not os.path.exists(db):
        return {}
    out = defaultdict(Counter)
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        for row in con.execute(
            "select session_id, turn_id, model, input_tokens, output_tokens, "
            "reasoning_tokens, cache_read_tokens, cache_write_tokens "
            "from local_runtime_token_usage"
        ):
            sid = row[0]
            out[sid]["input"] += int(row[3] or 0)
            out[sid]["output"] += int(row[4] or 0)
            out[sid]["reasoning"] += int(row[5] or 0)
            out[sid]["cache_read"] += int(row[6] or 0)
            out[sid]["cache_write"] += int(row[7] or 0)
            out[sid]["turns"] += 1
            turn_window = (int(row[3] or 0) + int(row[6] or 0) + int(row[7] or 0))
            if turn_window > out[sid].get("window_now", 0):
                out[sid]["window_now"] = turn_window
            if row[2]:
                out[sid]["model"] = row[2]
        con.close()
    except sqlite3.Error:
        return {}
    return {k: dict(v) for k, v in out.items()}


def read_minimax(session_dir: str, usage: dict) -> dict:
    """One MiniMax session directory -> totals plus content causes."""
    manifest_path = os.path.join(session_dir, "manifest.json")
    sid = os.path.basename(session_dir)
    title = ""
    created = 0
    if os.path.exists(manifest_path):
        try:
            manifest = json.load(open(manifest_path, encoding="utf8"))
            sid = manifest.get("sessionId") or sid
            created = int(manifest.get("createdAtMs") or 0)
        except (json.JSONDecodeError, OSError):
            pass

    causes = Counter()
    tool_outputs = []
    file_reads = Counter()
    messages_path = os.path.join(session_dir, "messages.jsonl")
    if os.path.exists(messages_path):
        with open(messages_path, encoding="utf8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = rec.get("message") or {}
                role = message.get("role")
                content = message.get("content")
                if isinstance(content, str):
                    causes["assistant output" if role == "assistant" else "user prompt"] += approx_tokens(content)
                    continue
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    text = block_text(block.get("text") or block.get("content") or block.get("output"))
                    if btype == "tool_result":
                        causes["tool result"] += approx_tokens(text)
                        tool_outputs.append((str(block.get("tool_use_id", "")), approx_tokens(text), text[:200]))
                    elif btype == "text":
                        causes["assistant output" if role == "assistant" else "user prompt"] += approx_tokens(text)
                    elif btype == "tool_use":
                        name = str(block.get("name", ""))
                        arg = block.get("input") or {}
                        p = arg.get("file_path") or arg.get("path")
                        if name.lower() in ("read", "view", "read_file") and p:
                            file_reads[str(p)] += 1

    u = usage.get(sid, {})
    total = (u.get("input", 0) + u.get("output", 0) + u.get("cache_read", 0) + u.get("cache_write", 0))
    return {
        "store": "minimax-code",
        "id": sid,
        "title": title or os.path.basename(session_dir),
        "cwd": "",
        "model": u.get("model", ""),
        "turns": u.get("turns", 0),
        "usage": {
            "input": u.get("input", 0),
            "output": u.get("output", 0),
            "reasoning": u.get("reasoning", 0),
            "cache_read": u.get("cache_read", 0),
            "cache_write": u.get("cache_write", 0),
            "total": total,
        },
        "causes": dict(causes),
        "tool_outputs": tool_outputs,
        "file_reads": dict(file_reads),
        "created": created,
        "window_now": u.get("window_now", 0),
    }


def collect(store: str, limit: int | None = None) -> list:
    """Read the sessions. With a limit, only the newest files are parsed -
    transcripts run to megabytes and reading all of them to show the newest
    one is the thing this tool exists to avoid."""
    sessions = []
    if store in ("both", "claude"):
        paths = claude_sessions()
        if limit:
            paths = sorted(paths, key=os.path.getmtime, reverse=True)[:limit]
        for path in paths:
            try:
                sessions.append(read_claude(path))
            except OSError:
                continue
    if store in ("both", "minimax"):
        dirs = minimax_sessions()
        if limit:
            dirs = sorted(dirs, key=lambda d: os.path.getmtime(os.path.join(d, "messages.jsonl"))
                          if os.path.exists(os.path.join(d, "messages.jsonl")) else 0,
                          reverse=True)[:limit]
        usage = minimax_usage_rows()
        for d in dirs:
            try:
                sessions.append(read_minimax(d, usage))
            except OSError:
                continue
    return sessions


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def fmt(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "-"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def view_stats(sessions: list) -> None:
    if not sessions:
        print("no sessions found")
        return
    sessions = sorted(sessions, key=lambda s: s["usage"].get("total", 0), reverse=True)
    print(f"{'session':38s} {'turns':>5s} {'input':>9s} {'out':>8s} {'cache':>9s} {'total':>9s}")
    print("-" * 84)
    totals = Counter()
    causes = Counter()
    for s in sessions:
        u = s["usage"]
        print(f"{s['id'][:38]:38s} {s['turns']:5d} {fmt(u.get('input')):>9s} "
              f"{fmt(u.get('output')):>8s} {fmt(u.get('cache_read')):>9s} {fmt(u.get('total')):>9s}")
        for key, value in u.items():
            if isinstance(value, (int, float)):
                totals[key] += value
        for cause, value in s["causes"].items():
            causes[cause] += value
    print("-" * 84)
    print(f"{'TOTAL':38s} {'':5s} {fmt(totals['input']):>9s} {fmt(totals['output']):>8s} "
          f"{fmt(totals['cache_read']):>9s} {fmt(totals['total']):>9s}")
    print()
    print("where the context went (attributed by content weight inside each turn):")
    for cause, value in causes.most_common():
        share = (value / sum(causes.values()) * 100) if causes else 0
        print(f"  {cause:22s} {fmt(value):>9s}  {share:5.1f}%")


def view_ledger(sessions: list) -> None:
    if not sessions:
        print("no sessions found")
        return
    sessions = sorted(sessions, key=lambda s: s["usage"].get("total", 0), reverse=True)
    for s in sessions:
        u = s["usage"]
        print(f"### {s['id']}  ({s['store']})  model={s['model'] or '-'}")
        print(f"    turns={s['turns']}  input={fmt(u.get('input'))}  output={fmt(u.get('output'))}  "
              f"cache_read={fmt(u.get('cache_read'))}  cache_write={fmt(u.get('cache_write'))}  "
              f"total={fmt(u.get('total'))}")
        big = sorted(s["tool_outputs"], key=lambda t: t[1], reverse=True)[:5]
        if big:
            print("    costliest tool outputs:")
            for _, tokens, snippet in big:
                print(f"      {fmt(tokens):>8s}  {snippet[:90].replace(chr(10), ' ')}")
        repeats = [(p, n) for p, n in s["file_reads"].items() if n > 1]
        if repeats:
            print("    files read more than once:")
            for path, n in sorted(repeats, key=lambda x: -x[1])[:8]:
                print(f"      {n:3d}x  {path}")
        print()


def view_guard(sessions: list) -> None:
    if not sessions:
        print("no sessions found")
        return
    s = sorted(sessions, key=lambda x: x["usage"].get("total", 0), reverse=True)[0]
    u = s["usage"]
    total = u.get("total", 0) or 1
    print(f"session {s['id']}  ({s['store']})")
    print(f"  context carried   {fmt(s.get('window_now', 0))} tokens on the last turn")
    print(f"  billed so far     {fmt(u.get('total'))} tokens over {s['turns']} turns")
    print(f"  cache read ratio  {(u.get('cache_read', 0) / total * 100):.1f}%")
    causes = s.get("causes") or {}
    if causes:
        top = sorted(causes.items(), key=lambda kv: -kv[1])[:3]
        print("  context is mostly:")
        for cause, value in top:
            print(f"    {cause:22s} {fmt(value)}")
    print()
    big = sorted(s["tool_outputs"], key=lambda t: t[1], reverse=True)[:3]
    if big:
        print("  biggest tool outputs in this session:")
        for _, tokens, snippet in big:
            print(f"    {fmt(tokens):>8s}  {snippet[:80].replace(chr(10), ' ')}")
    repeats = [(p, n) for p, n in s["file_reads"].items() if n > 1]
    if repeats:
        print("  read more than once:")
        for path, n in sorted(repeats, key=lambda x: -x[1])[:8]:
            print(f"    {n:3d}x  {path}")
    else:
        print("  no file was read twice")


def main() -> int:
    ap = argparse.ArgumentParser(description="what a session costs, and what wasted it")
    ap.add_argument("--view", choices=("stats", "ledger", "guard"), default="guard")
    ap.add_argument("--session-id")
    ap.add_argument("--last", type=int, default=1, help="the N newest sessions")
    ap.add_argument("--all", action="store_true", help="every session in the store")
    ap.add_argument("--store", choices=("both", "claude", "minimax"), default="both")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if args.session_id:
        sessions = collect(args.store)
        sessions = [s for s in sessions if args.session_id in s["id"]]
        if not sessions:
            print(f"no session matching {args.session_id!r}", file=sys.stderr)
            return 1
    elif args.all:
        sessions = collect(args.store)
    else:
        sessions = collect(args.store, limit=args.last)
    if not sessions:
        print("no sessions found in either store", file=sys.stderr)
        return 1
    if not args.all and not args.session_id:
        sessions = sorted(sessions, key=lambda s: s["usage"].get("total", 0), reverse=True)[: args.last]

    if args.json:
        for s in sessions:
            s.pop("tool_outputs", None)
        print(json.dumps(sessions, indent=2))
        return 0

    if args.view == "stats":
        view_stats(sessions)
    elif args.view == "ledger":
        view_ledger(sessions)
    else:
        view_guard(sessions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
