#!/bin/sh
# POSIX wrapper for the token guard hook. The runtime calls this; it forwards
# the event and the payload to the Python hook and passes stdout through,
# because stdout is how the hook injects context.
event="${1:-}"
script="$(dirname "$0")/token_guard_hook.py"
payload="$(mktemp)"
cat > "$payload"

# Pick an interpreter that actually runs. On Windows, `python3` can be the
# Microsoft Store stub, which exits 0 without doing anything - so each
# candidate has to prove it works before it is used.
py=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.stdout.write("ok")' 2>/dev/null | grep -q ok; then
      py="$candidate"
      break
    fi
  fi
done

if [ -n "$py" ]; then
  "$py" "$script" --event "$event" --payload-file "$payload" 2>/dev/null || true
fi
rm -f "$payload"
exit 0
