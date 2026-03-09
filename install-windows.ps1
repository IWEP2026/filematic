# ═══════════════════════════════════════════════════════════════
#  Filematic — Windows Installer (PowerShell)
#  Run once after cloning the repo.
#  Safe to re-run for updates.
#
#  Run with:
#    Right-click → Run with PowerShell
#  Or from PowerShell:
#    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#    .\install-windows.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

function ok   { Write-Host "  [OK]  $args" -ForegroundColor Green }
function info { Write-Host "  -->   $args" -ForegroundColor Cyan }
function fail { Write-Host "  [!]   $args" -ForegroundColor Red; exit 1 }
function hr   { Write-Host ""; Write-Host "  -----------------------------------------"; Write-Host "" }

Write-Host ""
Write-Host "  ==========================================="
Write-Host "    Filematic -- Windows Setup"
Write-Host "  ==========================================="
Write-Host ""

# ── 1. Python 3 ────────────────────────────────────────────────

info "Checking Python 3..."

$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 8) {
                $python = $cmd
                ok "Python $ver found ($cmd)"
                break
            }
        }
    } catch {}
}

if (-not $python) {
    Write-Host ""
    Write-Host "  Python 3.8 or later is required."
    Write-Host "  Download from: https://www.python.org/downloads/"
    Write-Host "  Make sure to tick 'Add Python to PATH' during install."
    fail "Python 3.8+ required"
}

hr

# ── 2. exiftool ────────────────────────────────────────────────

info "Checking exiftool..."

if (Get-Command exiftool -ErrorAction SilentlyContinue) {
    $exifver = exiftool -ver
    ok "exiftool $exifver found"
} else {
    Write-Host ""
    Write-Host "  exiftool not found. Install options:"
    Write-Host ""
    Write-Host "  Option A — Chocolatey (if installed):"
    Write-Host "    choco install exiftool"
    Write-Host ""
    Write-Host "  Option B — Manual:"
    Write-Host "    1. Download from https://exiftool.org"
    Write-Host "    2. Extract exiftool(-k).exe"
    Write-Host "    3. Rename to exiftool.exe"
    Write-Host "    4. Move to C:\Windows or any folder in your PATH"
    Write-Host ""

    $choice = Read-Host "  Try to install via Chocolatey now? [y/N]"
    if ($choice -match "^[Yy]$") {
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            choco install exiftool -y
            ok "exiftool installed via Chocolatey"
        } else {
            Write-Host "  Chocolatey not found."
            Write-Host "  Install exiftool manually (see above) then re-run this script."
            fail "exiftool required"
        }
    } else {
        Write-Host "  Skipping exiftool — Sort Personal will fall back to file dates."
        Write-Host "  Install exiftool later for accurate EXIF-based sorting."
    }
}

hr

# ── 3. Pillow ──────────────────────────────────────────────────

info "Installing Python dependencies..."
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet "Pillow>=10.0"
ok "Pillow installed"

hr

# ── 4. Optional — WSL or Git Bash for shell-script operations ──

info "Checking for bash (needed for Organise Event and Update Counts)..."

$bashFound = $false
foreach ($path in @(
    "C:\Windows\System32\bash.exe",
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe"
)) {
    if (Test-Path $path) {
        ok "bash found at $path"
        $bashFound = $true
        break
    }
}

if (-not $bashFound) {
    Write-Host ""
    Write-Host "  bash not found. Organise Event and Update Counts require bash."
    Write-Host "  Install one of:"
    Write-Host "    WSL (Windows Subsystem for Linux) — recommended"
    Write-Host "      wsl --install   (in an admin PowerShell)"
    Write-Host "    Git for Windows — includes Git Bash"
    Write-Host "      https://gitforwindows.org"
    Write-Host ""
    Write-Host "  Sort Personal, New Event, Backup, and Split JPGs work without bash."
}

hr

# ── Done ───────────────────────────────────────────────────────

Write-Host "  ==========================================="
Write-Host "    Setup complete."
Write-Host "  ==========================================="
Write-Host ""
Write-Host "  To launch:"
Write-Host "    cd app"
Write-Host "    python main.py"
Write-Host ""
Write-Host "  Your settings are stored at:"
Write-Host "    $env:APPDATA\Filematic\settings.json"
Write-Host "  (created on first launch)"
Write-Host ""

Read-Host "  Press Enter to close"
