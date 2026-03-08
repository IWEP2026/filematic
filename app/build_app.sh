#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# build_app.sh — Build "File Sorting App.app" for distribution
#
# Usage (from the app/ directory):
#   ./build_app.sh
#
# Output:
#   ../File Sorting App.app  — sits at the project root, ready to zip and share
#
# Recipients need macOS only. No Python or dependencies required.
# exiftool still needs to be installed separately (brew install exiftool).
# ─────────────────────────────────────────────────────────────────────────────
set -e

cd "$(dirname "$0")"
ROOT="$(pwd)/.."

echo "Installing build dependencies…"
pip3 install Pillow pyinstaller --break-system-packages --quiet

echo "Building File Sorting App.app…"
pyinstaller \
    --name "File Sorting App" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --distpath "$ROOT" \
    --workpath "$ROOT/.build/work" \
    --specpath "$ROOT/.build" \
    --osx-bundle-identifier "com.filesortingapp.app" \
    --collect-all PIL \
    main.py

echo ""
echo "✓ Done: 'File Sorting App.app' is at the project root"
echo ""
echo "To share:"
echo "  Zip the entire folder and send it."
echo "  Recipients right-click → Open on first launch (macOS Gatekeeper)."
echo "  exiftool must be installed: brew install exiftool"
