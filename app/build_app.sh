#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# build_app.sh — Build Filematic.app for distribution
#
# Usage (from the app/ directory):
#   bash build_app.sh              # auto-detects architecture
#   bash build_app.sh --arm        # Apple Silicon arm64  → Filematic.app
#   bash build_app.sh --intel      # Intel x86_64         → Filematic-Intel.app
#
# Note: universal2 (combined) builds are not supported with Python 3.14.
# Use build-releases.sh to build both versions in one command.
#
# Recipients need macOS only. No Python or dependencies required.
# exiftool still needs to be installed separately (brew install exiftool).
# ─────────────────────────────────────────────────────────────────────────────
set -e

cd "$(dirname "$0")"
ROOT="$(pwd)/.."

# ── Determine target architecture ──────────────────────────────────────────

TARGET=""

for arg in "$@"; do
  case $arg in
    --intel) TARGET="intel" ;;
    --arm)   TARGET="arm"   ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  NATIVE=$(uname -m)
  if [[ "$NATIVE" == "arm64" ]]; then
    TARGET="arm"
    echo "Apple Silicon detected — building arm64"
  else
    TARGET="intel"
    echo "Intel Mac detected — building x86_64"
  fi
fi

# ── Select Python and output name ───────────────────────────────────────────

if [[ "$TARGET" == "intel" ]]; then
  # Use Rosetta Python 3.9 for Intel build
  PYTHON="arch -x86_64 /usr/bin/python3"
  PYINSTALLER="$HOME/Library/Python/3.9/bin/pyinstaller"
  ARCH_FLAG="--target-arch x86_64"
  APP_NAME="Filematic-Intel"
  echo "Building Intel (x86_64) build via Rosetta Python 3.9..."
else
  # Use native Python for arm64 build
  PYTHON="python3"
  PYINSTALLER="pyinstaller"
  ARCH_FLAG="--target-arch arm64"
  APP_NAME="Filematic"
  echo "Building Apple Silicon (arm64) build..."
fi

# ── Install build dependencies ──────────────────────────────────────────────

echo ""
echo "Installing build dependencies..."
if [[ "$TARGET" == "intel" ]]; then
  arch -x86_64 /usr/bin/python3 -m pip install --quiet --user "Pillow>=10.0" pyinstaller
else
  pip3 install Pillow pyinstaller --break-system-packages --quiet
fi

# ── Build ────────────────────────────────────────────────────────────────────

echo "Building ${APP_NAME}.app..."
# shellcheck disable=SC2086
$PYINSTALLER \
    --name "$APP_NAME" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --distpath "$ROOT" \
    --workpath "$ROOT/.build/work" \
    --specpath "$ROOT/.build" \
    --osx-bundle-identifier "com.filematic.app" \
    --collect-all PIL \
    $ARCH_FLAG \
    main.py

echo ""
echo "✓ Done: '${APP_NAME}.app' is at the project root"
echo ""
BUILT_ARCH=$(lipo -archs "$ROOT/${APP_NAME}.app/Contents/MacOS/${APP_NAME}" 2>/dev/null || echo "unknown")
echo "  Architecture: $BUILT_ARCH"
echo ""
echo "To share:"
echo "  Zip ${APP_NAME}.app and send it."
echo "  Recipients right-click → Open on first launch (macOS Gatekeeper)."
echo "  exiftool must be installed: brew install exiftool"
