#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Filematic — Linux Installer
#  Run once after cloning the repo.
#  Safe to re-run for updates.
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"

ok()   { echo "  ✓  $1"; }
info() { echo "  →  $1"; }
fail() { echo "  ✗  $1"; exit 1; }
hr()   { echo ""; echo "  ─────────────────────────────────────────"; echo ""; }

echo ""
echo "  ═══════════════════════════════════════════"
echo "    Filematic — Linux Setup"
echo "  ═══════════════════════════════════════════"
echo ""

# ── 1. Python 3 ────────────────────────────────────────────────

info "Checking Python 3..."

if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
  ok "Python $PY_VER found"
else
  echo "  Python 3 is not installed."
  echo "  Install it with your package manager, e.g.:"
  echo "    sudo apt install python3 python3-pip     # Debian/Ubuntu"
  echo "    sudo dnf install python3                 # Fedora"
  echo "    sudo pacman -S python                    # Arch"
  fail "Python 3 required"
fi

PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
if [[ "$PY_MAJOR" -lt 3 || ("$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8) ]]; then
  fail "Python 3.8+ required. Found: $(python3 --version)"
fi

hr

# ── 2. tkinter ─────────────────────────────────────────────────

info "Checking tkinter..."

if python3 -c "import tkinter" 2>/dev/null; then
  ok "tkinter available"
else
  echo "  tkinter not found. Install it with:"
  echo "    sudo apt install python3-tk              # Debian/Ubuntu"
  echo "    sudo dnf install python3-tkinter         # Fedora"
  echo "    sudo pacman -S tk                        # Arch"
  fail "tkinter required"
fi

hr

# ── 3. exiftool ────────────────────────────────────────────────

info "Checking exiftool..."

if command -v exiftool &>/dev/null; then
  ok "exiftool $(exiftool -ver) found"
else
  info "exiftool not found. Trying to install..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get install -y libimage-exiftool-perl
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y perl-Image-ExifTool
  elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm perl-image-exiftool
  elif command -v zypper &>/dev/null; then
    sudo zypper install -y exiftool
  else
    echo ""
    echo "  Could not auto-install exiftool."
    echo "  Install it manually for your distro, then re-run this script."
    fail "exiftool required"
  fi
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

# ── Done ───────────────────────────────────────────────────────

echo "  ═══════════════════════════════════════════"
echo "    Setup complete."
echo "  ═══════════════════════════════════════════"
echo ""
echo "  To launch:"
echo "    cd app && python3 main.py"
echo ""
echo "  Your settings are stored at:"
echo "    ~/.config/Filematic/settings.json"
echo "  (created on first launch)"
echo ""
