#!/bin/bash
# ─────────────────────────────────────────────────────────
# organise-existing-event.sh — File Sorting App Event Restructurer
#
# Takes an existing event folder that has RAWs dumped in it
# and builds the proper internal structure around the files.
#
# BEFORE:
#   Events/2025/2025_Mia-Tom_Engagement-Party/
#     DSC_001.NEF
#     DSC_001.xmp
#     DSC_002.NEF
#     ...
#
# AFTER:
#   Events/2025/2025_Mia-Tom_Engagement-Party/
#     Completed/
#       Best Images/
#     Unedited RAWs/
#       DSC_001.NEF
#       DSC_001.xmp
#       DSC_002.NEF
#       ...
#     _SESSION-INFO.md
#
# SETUP: Put this file at /Volumes/Photography/organise-existing-event.sh
#
# USAGE:
#   bash /Volumes/Photography/organise-existing-event.sh
#   bash /Volumes/Photography/organise-existing-event.sh "/Volumes/Photography/Events/2025/2025_Mia-Tom_Engagement-Party"
#
# ─────────────────────────────────────────────────────────

RAW_EXTENSIONS="raf cr2 cr3 nef arw dng rw2 orf pef RAF CR2 CR3 NEF ARW DNG RW2 ORF PEF"
IMAGE_EXTENSIONS="jpg jpeg png tif tiff heic heif JPG JPEG PNG TIF TIFF HEIC HEIF"

SESSION_INFO_TEMPLATE='# Session Info
**Date:**
**Shoot Type:**

---

## Client
- **HubSpot Contact:**
- **Deal Link:**

---

## Crew
- **Primary Shooter:**
- **Secondary Shooter:**
- **Collaboration:**

---

## Equipment
- **Cameras Used:**

---

## Image Count
- **Best Images:** —
- **Unedited RAWs:** —

*Last updated: —*'

# ─────────────────────────────────────────────────────────
# Get target folder
# ─────────────────────────────────────────────────────────

if [[ -n "$1" ]]; then
  target="$1"
else
  echo ""
  echo "═══════════════════════════════════════════════"
  echo "  File Sorting App — Organise Existing Event Folder"
  echo "═══════════════════════════════════════════════"
  echo ""
  echo "  Drag the event folder into this Terminal window"
  echo "  (or type the path manually), then press Enter:"
  echo ""
  read -rp "  Folder path: " target_raw
  # Strip surrounding quotes that drag-and-drop adds
  target="${target_raw//\'/}"
  target="${target//\"/}"
  # Trim whitespace
  target="${target## }"
  target="${target%% }"
fi

# Verify folder exists
if [[ ! -d "$target" ]]; then
  echo ""
  echo "  ❌  Folder not found: $target"
  exit 1
fi

folder_name=$(basename "$target")

# ─────────────────────────────────────────────────────────
# Scan for files to move
# ─────────────────────────────────────────────────────────

echo ""
echo "  Scanning: $folder_name"
echo ""

# Build find expression for RAWs + images
find_expr=()
for ext in $RAW_EXTENSIONS $IMAGE_EXTENSIONS; do
  find_expr+=(-o -name "*.${ext}")
done
# Remove leading -o
find_expr=("${find_expr[@]:1}")

# Find all image/RAW files directly in the folder (not in subfolders)
raw_files=()
xmp_files=()
other_files=()

while IFS= read -r -d $'\0' f; do
  # Skip if it's in a subfolder
  rel="${f#$target/}"
  if [[ "$rel" == */* ]]; then
    continue
  fi
  ext="${f##*.}"
  ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
  if [[ "$ext_lower" == "xmp" ]]; then
    xmp_files+=("$f")
  else
    raw_files+=("$f")
  fi
done < <(find "$target" -maxdepth 1 -type f \( "${find_expr[@]}" -o -name "*.xmp" -o -name "*.XMP" \) -print0)

# Count
raw_count=${#raw_files[@]}
xmp_count=${#xmp_files[@]}
total=$((raw_count + xmp_count))

if [[ $total -eq 0 ]]; then
  echo "  ⚠️   No RAW, image, or XMP files found directly in this folder."
  echo "      Nothing to organise."
  exit 0
fi

echo "  Found:"
echo "    $raw_count  image/RAW files"
echo "    $xmp_count  XMP sidecar files"
echo ""

# Check what already exists
already_has_raw_folder=false
already_has_session_info=false
[[ -d "$target/Unedited RAWs" ]] && already_has_raw_folder=true
[[ -f "$target/_SESSION-INFO.md" ]] && already_has_session_info=true

if $already_has_raw_folder; then
  echo "  ⚠️   'Unedited RAWs' folder already exists — files will be moved into it."
fi

# ─────────────────────────────────────────────────────────
# Preview & confirm
# ─────────────────────────────────────────────────────────

echo "  ─────────────────────────────────────────"
echo "  Will create inside $folder_name/:"
echo ""
echo "    Completed/"
echo "      Best Images/"
echo "    Unedited RAWs/          ← $raw_count files + $xmp_count XMPs move here"
if ! $already_has_session_info; then
  echo "    _SESSION-INFO.md        ← new template"
fi
echo "  ─────────────────────────────────────────"
echo ""
read -rp "  Proceed? [y/N]: " confirm
echo ""

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "  Cancelled. Nothing was changed."
  exit 0
fi

# ─────────────────────────────────────────────────────────
# Create folders
# ─────────────────────────────────────────────────────────

mkdir -p "$target/Completed/Best Images"
mkdir -p "$target/Unedited RAWs"

# ─────────────────────────────────────────────────────────
# Move files
# ─────────────────────────────────────────────────────────

moved=0
skipped=0

for f in "${raw_files[@]}" "${xmp_files[@]}"; do
  fname=$(basename "$f")
  dest="$target/Unedited RAWs/$fname"

  if [[ -e "$dest" ]]; then
    echo "  ⚠️   Skipped (already exists): $fname"
    ((skipped++))
  else
    mv "$f" "$dest"
    ((moved++))
  fi
done

# ─────────────────────────────────────────────────────────
# Create SESSION-INFO.md (only if it doesn't exist)
# ─────────────────────────────────────────────────────────

if ! $already_has_session_info; then
  echo "$SESSION_INFO_TEMPLATE" > "$target/_SESSION-INFO.md"
fi

# ─────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────

echo "  ✓ Done!"
echo ""
echo "  Moved   : $moved files → Unedited RAWs/"
[[ $skipped -gt 0 ]] && echo "  Skipped : $skipped files (already existed in destination)"
echo ""
echo "  Next steps:"
echo "  1. Open _SESSION-INFO.md and fill in client/crew details"
echo "  2. Export selects to: Completed/Best Images/"
echo "  3. Run the image count updater:"
echo "     bash /Volumes/Photography/update-image-counts.sh \"$target\""
echo ""
