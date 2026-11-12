#!/usr/bin/env bash
# Link every aswath-* skill in this repo into the harness skill directories.
# Links, not copies: edit the repo, every harness sees it.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="$REPO/skills"
TARGET="all"
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --force|-f) FORCE=1 ;;
    claude|commandcode|agents|all) TARGET="$arg" ;;
    *) echo "usage: $0 [all|claude|commandcode|agents] [--force]" >&2; exit 2 ;;
  esac
done

[ -d "$SKILLS" ] || { echo "No skills/ directory beside install.sh ($REPO)" >&2; exit 1; }

declare -A TARGETS=(
  [claude]="$HOME/.claude/skills"
  [commandcode]="$HOME/.commandcode/skills"
  [agents]="$HOME/.agents/skills"
)

if [ "$TARGET" = "all" ]; then
  SELECTED=("${!TARGETS[@]}")
else
  SELECTED=("$TARGET")
fi

linked=0
skipped=0

for t in "${SELECTED[@]}"; do
  dest_root="${TARGETS[$t]}"
  mkdir -p "$dest_root"

  for s in "$SKILLS"/*/*/; do
    [ -d "$s" ] || continue
    name="$(basename "$s")"
    dest="$dest_root/$name"

    if [ -e "$dest" ] || [ -L "$dest" ]; then
      if [ -L "$dest" ] && [ "$FORCE" -eq 0 ]; then
        skipped=$((skipped + 1))
        continue
      fi
      if [ ! -L "$dest" ] && [ "$FORCE" -eq 0 ]; then
        echo "skip  $name  ($t exists, not a link)"
        skipped=$((skipped + 1))
        continue
      fi
      rm -rf "$dest"
    fi

    ln -s "$s" "$dest"
    echo "link  $name  ->  $t"
    linked=$((linked + 1))
  done
done

echo
echo "linked $linked, skipped $skipped"
echo "Invoke any skill directly: /aswath-token-guard"
