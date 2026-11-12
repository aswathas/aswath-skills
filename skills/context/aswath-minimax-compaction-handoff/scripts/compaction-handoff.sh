#!/bin/sh
# MiniMax Code compaction handoff hook (POSIX entry point).
# Reads the hook payload on stdin, delegates to the Python worker.
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
fi
if [ -z "$PY" ]; then
  exit 0
fi
exec "$PY" "$HOME/.minimax/compaction-handoff.py"
