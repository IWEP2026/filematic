#!/bin/bash
# ─────────────────────────────────────────────────────────
# new-event.sh — File Sorting App Event Folder Creator
#
# Creates a properly structured client event folder on your
# Photography SSD, ready for ingesting RAWs after a shoot.
#
# SETUP: Put this file at /Volumes/Photography/new-event.sh
#        (alongside sort-photos.py)
#
# USAGE:
#   bash /Volumes/Photography/new-event.sh
#
# ─────────────────────────────────────────────────────────

# Path is passed in via PHOTOGRAPHY_ROOT env var (set by PostHaste.py),
# or falls back to the default volume if run directly from Terminal.
EVENTS_ROOT="${PHOTOGRAPHY_ROOT:-/Volumes/Photography}/Events"

# ─────────────────────────────────────────────────────────

SESSION_INFO_TEMPLATE='# Session Info
**Date:** DATE_PLACEHOLDER
**Shoot Type:** TYPE_PLACEHOLDER

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

echo ""
echo "═══════════════════════════════════════════════"
echo "  File Sorting App — New Event Setup"
echo "═══════════════════════════════════════════════"
echo ""

# ── Year ────────────────────────────────────────────────
current_year=$(date +%Y)
read -rp "  Year [$current_year]: " year
year="${year:-$current_year}"

# ── Shoot type ──────────────────────────────────────────
echo ""
echo "  Shoot type:"
echo "    1) Wedding"
echo "    2) Corporate"
echo "    3) Model"
echo "    4) Personal-Headshots"
echo "    5) Musician"
echo "    6) Baptism"
echo "    7) Media-Client"
echo "    8) Other (type it)"
echo ""
read -rp "  Choose [1-8]: " type_choice

case "$type_choice" in
  1) shoot_type="Wedding" ;;
  2) shoot_type="Corporate" ;;
  3) shoot_type="Model" ;;
  4) shoot_type="Personal-Headshots" ;;
  5) shoot_type="Musician" ;;
  6) shoot_type="Baptism" ;;
  7) shoot_type="Media-Client" ;;
  8)
    read -rp "  Shoot type: " shoot_type
    ;;
  *)
    shoot_type="$type_choice"
    ;;
esac

# ── Client name ─────────────────────────────────────────
echo ""
if [[ "$shoot_type" == "Wedding" ]]; then
  read -rp "  Couple name (e.g. Smith-Jones): " client_raw
else
  read -rp "  Client / business name (e.g. Acme-Corp): " client_raw
fi

# Sanitise: replace spaces with hyphens, remove unsafe chars
client=$(echo "$client_raw" | sed 's/ /-/g' | sed "s/[^a-zA-Z0-9_\-]//g")

if [[ -z "$client" ]]; then
  echo "  ❌  Client name cannot be empty."
  exit 1
fi

# ── Shoot date ──────────────────────────────────────────
today=$(date +%Y-%m-%d)
echo ""
read -rp "  Shoot date [$today] (YYYY-MM-DD): " shoot_date
shoot_date="${shoot_date:-$today}"

# Validate date format
if ! echo "$shoot_date" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
  echo "  ❌  Date must be in YYYY-MM-DD format."
  exit 1
fi

# ─────────────────────────────────────────────────────────
# Build paths depending on shoot type
# ─────────────────────────────────────────────────────────

event_folder="${EVENTS_ROOT}/${year}/${year}_${client}_${shoot_type}"
CLIENT_UPPER=$(echo "$client" | tr '[:lower:]' '[:upper:]')

if [[ "$shoot_type" == "Wedding" ]]; then
  # Wedding: 4 numbered session subfolders
  sessions=(
    "0001_${CLIENT_UPPER}_Prenuptials_${shoot_date}"
    "0002_${CLIENT_UPPER}_Bridesmaids_${shoot_date}"
    "0003_${CLIENT_UPPER}_Groomsmen_${shoot_date}"
    "0004_${CLIENT_UPPER}_Wedding_${shoot_date}"
  )
elif [[ "$shoot_type" == "Corporate" ]]; then
  # Corporate: event + headshots
  sessions=(
    "0001_${CLIENT_UPPER}_Corporate-Event_${shoot_date}"
    "0002_${CLIENT_UPPER}_Group-Headshots_${shoot_date}"
  )
else
  # All others: single session subfolder
  sessions=(
    "0001_${CLIENT_UPPER}_${shoot_type}_${shoot_date}"
  )
fi

# ─────────────────────────────────────────────────────────
# Preview & confirm
# ─────────────────────────────────────────────────────────

echo ""
echo "  ─────────────────────────────────────────"
echo "  Will create:"
echo ""
echo "  Events/${year}/${year}_${client}_${shoot_type}/"
for s in "${sessions[@]}"; do
  echo "  └── ${s}/"
  echo "      ├── Completed/"
  echo "      │   └── Best Images/"
  echo "      ├── Unedited RAWs/"
  echo "      └── _SESSION-INFO.md"
done
echo "  ─────────────────────────────────────────"
echo ""
read -rp "  Create these folders? [y/N]: " confirm
echo ""

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "  Cancelled. Nothing was created."
  exit 0
fi

# ─────────────────────────────────────────────────────────
# Create the folders
# ─────────────────────────────────────────────────────────

if [[ ! -d "$EVENTS_ROOT" ]]; then
  echo "  ❌  Events folder not found: $EVENTS_ROOT"
  echo "      Is your SSD connected?"
  exit 1
fi

# Make year folder if needed
mkdir -p "${EVENTS_ROOT}/${year}"

for session_name in "${sessions[@]}"; do
  session_dir="${event_folder}/${session_name}"

  mkdir -p "${session_dir}/Completed/Best Images"
  mkdir -p "${session_dir}/Unedited RAWs"

  # Write SESSION-INFO.md with real date and shoot type
  info="${SESSION_INFO_TEMPLATE/DATE_PLACEHOLDER/$shoot_date}"
  info="${info/TYPE_PLACEHOLDER/$shoot_type}"
  echo "$info" > "${session_dir}/_SESSION-INFO.md"

  echo "  ✓ ${session_name}"
done

echo ""
echo "  ✓ Done! Folder created at:"
echo "    ${event_folder}/"
echo ""
echo "  Next steps:"
echo "  1. Open _SESSION-INFO.md in each subfolder and fill in"
echo "     the client/crew details (HubSpot link, cameras, etc.)"
echo "  2. After the shoot, copy RAWs into: Unedited RAWs/"
echo "  3. Export selects to: Completed/Best Images/"
echo "  4. Run the image count updater:"
echo "     bash update-image-counts.sh \"${event_folder}/...\""
echo ""
