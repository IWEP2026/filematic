#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# build-releases.sh — Build both Filematic releases from the project root
#
#   Filematic.app        → Apple Silicon (arm64)
#   Filematic-Intel.app  → Intel Mac (x86_64, via Rosetta)
#
# Run from the project root:
#   bash build-releases.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"

ok()   { echo "  ✓  $1"; }
info() { echo "  →  $1"; }
hr()   { echo ""; echo "  ─────────────────────────────────────────"; echo ""; }

echo ""
echo "  ═══════════════════════════════════════════"
echo "    Filematic — Build Releases"
echo "  ═══════════════════════════════════════════"
echo ""

# ── Apple Silicon build ─────────────────────────────────────────────────────

info "Building Apple Silicon (arm64)..."
cd "$APP_DIR"
bash build_app.sh --arm
ok "Filematic.app built"

hr

# ── Intel build ─────────────────────────────────────────────────────────────

info "Building Intel (x86_64)..."
cd "$APP_DIR"
bash build_app.sh --intel
ok "Filematic-Intel.app built"

hr

# ── Summary ─────────────────────────────────────────────────────────────────

echo "  ═══════════════════════════════════════════"
echo "    Both builds complete"
echo "  ═══════════════════════════════════════════"
echo ""
echo "  Filematic.app        → Apple Silicon (M1/M2/M3/M4)"
echo "  Filematic-Intel.app  → Intel Mac"
echo ""
echo "  Distribute:"
echo "    Zip each .app separately and share the right one for each machine."
echo "    Both require: brew install exiftool"
echo ""
