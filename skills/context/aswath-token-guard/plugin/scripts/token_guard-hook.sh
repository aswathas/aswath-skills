#!/bin/sh
# POSIX wrapper for the token guard hook. The runtime calls this; it forwards
# the event and the payload to the Python hook and passes stdout through,
# because stdout is how the hook injects context.
event="${1:-}"
script="$(dirname "$0")/token_guard_hook.py"
payload="$(mktemp)"
cat > "$payload"

if command -v python3 >/dev/null 2>&1; then
  py=python3
elif command -v python >/dev/null 2>&1; then
  py=python
else
  py=""
fi

if [ -n "$py" ]; then
  "$py" "$script" --event "$event" --payload-file "$payload" 2>/dev/null || true
fi
rm -f "$payload"
exit 0
