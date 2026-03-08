#!/bin/bash
# ─────────────────────────────────────────────
# update-image-counts.sh
# Updates image counts in _SESSION-INFO.md files.
#
# Usage:
#   Run with --all to update every session in this Folder templates directory:
#     bash update-image-counts.sh --all
#
#   Pass a specific session folder path:
#     bash update-image-counts.sh "/path/to/0001_CLIENT-NAME_Wedding_2026-06-14"
#
#   Run from inside a session folder:
#     bash /path/to/update-image-counts.sh
# ─────────────────────────────────────────────

IMAGE_EXTS=( jpg jpeg png tif tiff raw cr2 cr3 nef arw dng heic )

count_images() {
  local dir="$1"
  if [ ! -d "$dir" ]; then
    echo "0"
    return
  fi
  local total=0
  for ext in "${IMAGE_EXTS[@]}"; do
    local n
    n=$(find "$dir" -maxdepth 1 -type f -iname "*.${ext}" 2>/dev/null | wc -l | tr -d ' ')
    total=$((total + n))
  done
  echo "$total"
}

update_session() {
  local session_dir="$1"
  local info_file="${session_dir}/_SESSION-INFO.md"

  if [ ! -f "$info_file" ]; then
    echo "  ⚠️  No _SESSION-INFO.md in: $(basename "$session_dir")"
    return
  fi

  local best_dir raw_dir
  best_dir=$(find "$session_dir" -type d -name "Best Images" 2>/dev/null | head -1)
  raw_dir=$(find "$session_dir" -type d -name "Unedited RAWs*" 2>/dev/null | head -1)

  local best_count raw_count timestamp
  best_count=$(count_images "$best_dir")
  raw_count=$(count_images "$raw_dir")
  timestamp=$(date "+%Y-%m-%d %H:%M")

  # Write a temp file to avoid in-place sed path issues
  local tmp
  tmp=$(mktemp)
  sed \
    -e "s/- \*\*Best Images:\*\* .*/- **Best Images:** ${best_count}/" \
    -e "s/- \*\*Unedited RAWs:\*\* .*/- **Unedited RAWs:** ${raw_count}/" \
    -e "s/\*Last updated: .*\*/*Last updated: ${timestamp}*/" \
    "$info_file" > "$tmp" && mv "$tmp" "$info_file"

  echo "  ✓ $(basename "$session_dir") — Best Images: ${best_count} | RAWs: ${raw_count}"
}

# ── Main ────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" == "--all" ]; then
  echo "Updating all sessions in: $SCRIPT_DIR"
  echo ""
  while IFS= read -r -d '' info_file; do
    update_session "$(dirname "$info_file")"
  done < <(find "$SCRIPT_DIR" -name "_SESSION-INFO.md" -print0)
  echo ""
  echo "Done."

elif [ -n "$1" ]; then
  echo "Updating: $1"
  update_session "$1"

else
  echo "Updating current directory: $(pwd)"
  update_session "$(pwd)"
fi
