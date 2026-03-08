#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  File Sorting App — Installer
#  Run once after cloning the repo.
#  Safe to re-run for updates.
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
BUILD_APP=true

# ── Parse flags ────────────────────────────────────────────────

for arg in "$@"; do
  case $arg in
    --no-build) BUILD_APP=false ;;
  esac
done

# ── Helpers ────────────────────────────────────────────────────

ok()   { echo "  ✓  $1"; }
info() { echo "  →  $1"; }
fail() { echo "  ✗  $1"; exit 1; }
hr()   { echo ""; echo "  ─────────────────────────────────────────"; echo ""; }

# ── Header ─────────────────────────────────────────────────────

echo ""
echo "  ═══════════════════════════════════════════"
echo "    File Sorting App — Setup"
echo "  ═══════════════════════════════════════════"
echo ""

# ── 1. Python 3 ────────────────────────────────────────────────

info "Checking Python 3..."

if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
  ok "Python $PY_VER found"
else
  fail "Python 3 not found. Install from https://www.python.org/downloads/"
fi

# Check version is 3.10+
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
if [[ "$PY_MAJOR" -lt 3 || ("$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 10) ]]; then
  fail "Python 3.10 or later is required. Found: $(python3 --version)"
fi

hr

# ── 2. Homebrew ────────────────────────────────────────────────

info "Checking Homebrew..."

if command -v brew &>/dev/null; then
  ok "Homebrew found at $(command -v brew)"
else
  echo ""
  echo "  Homebrew is not installed. Installing now..."
  echo "  (You may be asked for your Mac password)"
  echo ""
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # Add brew to PATH for Apple Silicon Macs
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi

  ok "Homebrew installed"
fi

hr

# ── 3. exiftool ────────────────────────────────────────────────

info "Checking exiftool..."

if command -v exiftool &>/dev/null; then
  ok "exiftool $(exiftool -ver) found"
else
  info "Installing exiftool..."
  brew install exiftool
  ok "exiftool installed"
fi

hr

# ── 4. Pillow ──────────────────────────────────────────────────

info "Installing Python dependencies..."

python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet "Pillow>=10.0"
ok "Pillow installed"

hr

# ── 5. Make scripts executable ─────────────────────────────────

info "Setting file permissions..."

chmod +x "$APP_DIR/Launch.command"
chmod +x "$APP_DIR/build_app.sh"
chmod +x "$APP_DIR/update-image-counts.sh"
chmod +x "$APP_DIR/new-event.sh"
chmod +x "$APP_DIR/organise-existing-event.sh"

ok "Scripts are executable"

hr

# ── 6. Build .app (optional) ───────────────────────────────────

if $BUILD_APP; then
  info "Building File Sorting App.app..."
  echo ""

  # PyInstaller needed for build only
  python3 -m pip install --quiet "pyinstaller>=6.0"

  cd "$APP_DIR"
  bash build_app.sh

  if [[ -d "$SCRIPT_DIR/File Sorting App.app" ]]; then
    ok "File Sorting App.app built successfully"
    echo ""
    echo "  ─────────────────────────────────────────"
    echo ""
    echo "  You can now double-click to launch:"
    echo "  File Sorting App.app"
    echo ""
  else
    echo ""
    echo "  ⚠️  App bundle not found after build."
    echo "     Try running manually: cd app && bash build_app.sh"
    echo "     Or launch without building: double-click app/Launch.command"
    echo ""
  fi
else
  echo ""
  echo "  Skipped app build (--no-build)"
  echo ""
  echo "  To launch without the .app bundle:"
  echo "  → Double-click app/Launch.command"
  echo "  → Or: cd app && python3 main.py"
  echo ""
fi

# ── Done ───────────────────────────────────────────────────────

echo "  ═══════════════════════════════════════════"
echo "    Setup complete."
echo "  ═══════════════════════════════════════════"
echo ""
echo "  Your settings are stored at:"
echo "  ~/Library/Application Support/FileSortingApp/settings.json"
echo "  (created on first launch — not committed to the repo)"
echo ""
