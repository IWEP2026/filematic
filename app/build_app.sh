#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# build_app.sh — Build "File Sorting App.app" for distribution
#
# Usage (from the app/ directory):
#   bash build_app.sh              # auto-detects architecture
#   bash build_app.sh --universal  # universal2 binary (Intel + Apple Silicon)
#   bash build_app.sh --intel      # Intel x86_64 only
#   bash build_app.sh --arm        # Apple Silicon arm64 only
#
# Output:
#   ../File Sorting App.app  — sits at the project root, ready to zip and share
#
# Universal2 builds run on both Intel and Apple Silicon Macs (macOS 11+).
# For macOS 10.15 Catalina, build with --intel or run directly via Launch.command.
#
# Recipients need macOS only. No Python or dependencies required.
# exiftool still needs to be installed separately (brew install exiftool).
# ─────────────────────────────────────────────────────────────────────────────
set -e

cd "$(dirname "$0")"
ROOT="$(pwd)/.."

# ── Determine target architecture ──────────────────────────────────────────

ARCH_FLAG=""

for arg in "$@"; do
  case $arg in
    --universal) ARCH_FLAG="--target-arch universal2" ;;
    --intel)     ARCH_FLAG="--target-arch x86_64" ;;
    --arm)       ARCH_FLAG="--target-arch arm64" ;;
  esac
done

# Default: try universal2 on Apple Silicon (produces a binary that also
# runs on Intel). On Intel, build native only.
if [[ -z "$ARCH_FLAG" ]]; then
  NATIVE=$(uname -m)
  if [[ "$NATIVE" == "arm64" ]]; then
    ARCH_FLAG="--target-arch universal2"
    echo "Apple Silicon detected — building universal2 (Intel + Apple Silicon)"
  else
    ARCH_FLAG="--target-arch x86_64"
    echo "Intel Mac detected — building x86_64"
  fi
fi

echo ""
echo "Installing build dependencies…"
pip3 install Pillow pyinstaller --break-system-packages --quiet

echo "Building File Sorting App.app…"
# shellcheck disable=SC2086
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
    $ARCH_FLAG \
    main.py

echo ""
echo "✓ Done: 'File Sorting App.app' is at the project root"
echo ""
BUILT_ARCH=$(lipo -archs "$ROOT/File Sorting App.app/Contents/MacOS/File Sorting App" 2>/dev/null || echo "unknown")
echo "  Architecture: $BUILT_ARCH"
echo ""
echo "To share:"
echo "  Zip the entire folder and send it."
echo "  Recipients right-click → Open on first launch (macOS Gatekeeper)."
echo "  exiftool must be installed: brew install exiftool"
