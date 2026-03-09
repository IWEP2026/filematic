# Filematic — Free media management for creatives

A free, open-source app for photographers, videographers, and creatives who want
clean, consistent file management — without paying for Adobe Bridge, Photo
Mechanic, or similar tools.

Built for real creative workflows: ingesting RAWs, tracking client events,
sorting personal shoots, and keeping your drives organised over time.

Works on **macOS**, **Linux**, and **Windows**.

---

## Why this exists

Apps like Adobe Bridge and Photo Mechanic charge subscription fees to do things
that should be simple: rename files by date, sort them into folders, and keep
your archive clean. This app replaces that for the operations photographers
actually need day-to-day.

**What it replaces:**

| Paid tool | What this does instead |
|---|---|
| Adobe Bridge (ingest) | Sort Personal — renames and sorts by EXIF date |
| Photo Mechanic (culling folders) | New Event — creates structured client folders |
| Manual folder restructuring | Organise Event — wraps loose RAWs in proper structure |
| Lightroom metadata panels | Session Info — Markdown file per shoot with counts |
| Bridge image count panels | Update Counts — live count of Best Images + RAWs |
| Manual JPG separation | Split JPGs — moves camera JPGs out of Unedited RAWs |
| Manual batch rename | Rename Edited — in-place EXIF date rename, no move |
| Manual rsync backup | Backup — syncs your drive to a backup destination |

Everything runs locally. No cloud, no subscription, no account.

---

## What it does

### Sort Personal
Reads the capture/creation date from every file and sorts it into a clean
weekly folder structure:

```
Personal/
├── 2026/
│   └── Week 10 · Mon 02–08/
│       ├── 2026-03-02_143022_001.raf    ← Fujifilm body
│       ├── 2026-03-02_143022_001.nef    ← Nikon second body, same session
│       └── 2026-03-02_143022_001.jpg
├── Video/
│   └── 2026/
│       └── Week 10 · Mon 02–08/
│           └── 2026-03-02_143045_001.mp4
├── Audio/
│   └── 2026/
│       └── Week 10 · Mon 02–08/
│           └── 2026-03-02_150012_001.wav
└── Design/
    └── 2026/
        └── Week 10 · Mon 02–08/
            └── 2026-03-02_163000_001.psd
```

**Multi-camera sessions work automatically.** If you shoot with two bodies —
say a Fujifilm (RAF) and a Nikon (NEF) — all files land in the same weekly
folder, interleaved in the exact order each shot was taken. Camera model and
file format are irrelevant. Only the EXIF timestamp matters.

Duplicate detection is EXIF-based (timestamp + extension + file size). Re-ingesting
the same card is safe — duplicates are skipped and logged, never overwritten.

Supports all major RAW formats (Canon, Nikon, Sony, Fujifilm, Olympus, Panasonic,
Pentax, Hasselblad, Phase One, Sigma, Leica, Minolta, Kodak and more), standard
photos, video, audio, design files (PSD, FIG, Blender, Cinema 4D...) and motion
projects (After Effects, Premiere, DaVinci, Final Cut...).

### New Event
Creates a fully structured client event folder, ready for RAWs after the shoot.

```
Events/
└── 2026/
    └── 2026-03-08_Smith-Jones_Wedding/
        ├── 0001_SMITH-JONES_Prenuptials_2026-03-08/   ← optional (toggle in form)
        │   ├── Completed/
        │   │   └── Best Images/
        │   ├── Unedited RAWs/
        │   └── _SESSION-INFO.md
        ├── 0002_SMITH-JONES_Bridesmaids_2026-03-08/
        ├── 0003_SMITH-JONES_Groomsmen_2026-03-08/
        ├── 0004_SMITH-JONES_Ceremony_2026-03-08/
        └── 0005_SMITH-JONES_Reception_2026-03-08/
```

Wedding events split Ceremony and Reception into separate sessions — each with
their own `Completed/Best Images/` and `Unedited RAWs/` folders. Prenuptials
sessions are optional (checkbox in the form).

Default project types: Wedding, Corporate, Model, Personal-Headshots, Musician,
Baptism, Media-Client, Other. **All of these are fully customisable in Settings**
— edit the list, change the labels, rename Event folders to whatever suits your
workflow.

Each session gets a `_SESSION-INFO.md` file to track client details, crew,
equipment, and image counts — readable in Finder and any text editor.

### Organise Event
Takes an existing folder where RAWs have been dumped flat and restructures it
in-place:

```
Before:                         After:
MyShoot/                        MyShoot/
  DSC_001.NEF                     Completed/
  DSC_002.NEF         →               Best Images/
  DSC_001.xmp                     Unedited RAWs/
                                      DSC_001.NEF
                                      DSC_002.NEF
                                      DSC_001.xmp
                                  _SESSION-INFO.md
```

### Update Counts
Reads the number of files in each session's `Best Images/` and
`Unedited RAWs/` folders and writes the counts back into `_SESSION-INFO.md`.
Runs silently in the background — no Terminal window.

### Split JPGs
Moves JPG/JPEG files out of an event session's `Unedited RAWs/` folder into a
separate destination (default: `Photography/JPGs/`). If no `Unedited RAWs/`
subfolder exists it searches the whole selected folder. Files inside
`Best Images/` are never touched.

### Rename Edited
Renames all media files in a selected folder in-place using their EXIF capture
date — no files are moved, no subfolders are created. Companion sidecar files
(XMP, PP3, DOP, etc.) are renamed to match automatically. Files already using
the correct date-based name are skipped. Files inside `Best Images/` are always
left untouched. Requires exiftool.

### Backup
Syncs your Photography drive to a backup destination. Copies new files,
updates changed ones, removes deleted ones. Shows live progress in the app.
Uses `rsync` on macOS/Linux and `robocopy` on Windows.

---

## Folder structure on your drive

The app expects (and creates) this layout on your photography drive. You set
the root path in the app's settings — it can be any external drive or folder.

```
[Your Drive]/
├── Events/
│   └── YYYY/
│       └── YYYY-MM-DD_Client_ShootType/
│           └── NNNN_CLIENT_ShootType_YYYY-MM-DD/
│               ├── Completed/
│               │   └── Best Images/
│               ├── Unedited RAWs/
│               └── _SESSION-INFO.md
├── Personal/
│   ├── YYYY/
│   │   └── Week WW · Mon DD–DD/
│   │       └── YYYY-MM-DD_HHMMSS_NNN.ext    ← photos/RAWs
│   ├── Video/YYYY/Week WW · Mon DD–DD/       ← video files
│   ├── Audio/YYYY/Week WW · Mon DD–DD/       ← audio files
│   ├── Design/YYYY/Week WW · Mon DD–DD/      ← design files
│   └── Motion/YYYY/Week WW · Mon DD–DD/      ← motion projects
└── JPGs/                    ← optional, for Split JPGs
```

---

## Requirements

- **Python 3.8+** — install from [python.org](https://www.python.org) if needed
- **exiftool** — for reading EXIF dates when sorting photos/media
- **Pillow** — installed automatically by the setup script

---

## Platform support

| Platform | Status | Notes |
|---|---|---|
| macOS 11+ Apple Silicon | ✓ Full | `Filematic.app` (arm64) |
| macOS 11+ Intel | ✓ Full | `Filematic-Intel.app` (x86_64) |
| macOS 10.15 Catalina | ✓ | Use `python3 main.py` — `.app` build may not work |
| Linux (Ubuntu, Fedora, Arch, etc.) | ✓ Full | Run via `python3 main.py` |
| Windows 10/11 | ✓ | Run via `python main.py`. Bash operations need WSL or Git for Windows |

### Windows — bash operations

Two operations use bash scripts under the hood: **Organise Event** and **Update Counts**.
On Windows these require either:
- **WSL** (Windows Subsystem for Linux) — `wsl --install` in an admin PowerShell
- **Git for Windows** — includes Git Bash ([gitforwindows.org](https://gitforwindows.org))

All other operations (Sort Personal, New Event, Split JPGs, Backup) work natively on Windows.

---

## Installation

### macOS

```bash
git clone https://github.com/YOUR_USERNAME/filematic.git
cd filematic
bash install.sh
```

The script checks Python, installs Homebrew + exiftool, installs Pillow, and builds both app bundles:
- `Filematic.app` — Apple Silicon (M1/M2/M3/M4)
- `Filematic-Intel.app` — Intel Mac

Double-click the right one for your machine. Or run directly: `cd app && python3 main.py`

To skip the `.app` build: `bash install.sh --no-build`
To rebuild both apps at any time: `bash build-releases.sh`

### Linux

```bash
git clone https://github.com/YOUR_USERNAME/filematic.git
cd filematic
bash install-linux.sh
```

The script detects your package manager (apt/dnf/pacman/zypper) and installs exiftool automatically.
After setup: `cd app && python3 main.py`

### Windows

```powershell
git clone https://github.com/YOUR_USERNAME/filematic.git
cd filematic
.\install-windows.ps1
```

Or if PowerShell execution is restricted:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install-windows.ps1
```

After setup: `cd app && python main.py`

---

## Updating

```bash
cd filematic
git pull

# macOS
bash install.sh

# Linux
bash install-linux.sh

# Windows
.\install-windows.ps1
```

The install script is safe to re-run. It won't overwrite your settings.

---

## Settings

Open the Settings panel inside the app. Everything is configurable:

| Setting | Default | What it controls |
|---------|---------|-----------------|
| Photography Volume | `/Volumes/Photography` | Root path for all operations |
| Backup Destination | — | Target drive for Backup |
| JPG Split Destination | `volume/JPGs` | Where Split JPGs sends files |
| Personal Folder Name | `Personal` | Subfolder name for Sort Personal |
| Events Folder Name | `Events` | Subfolder name for New Event |
| Client Label | `Client Name` | Label in New Event form (e.g. Artist, Couple) |
| Project Types | Wedding, Corporate… | Comma-separated dropdown list for New Event |

Settings are stored at:
- macOS:   `~/Library/Application Support/Filematic/settings.json`
- Linux:   `~/.config/Filematic/settings.json`
- Windows: `%APPDATA%\Filematic\settings.json`

This file is not committed to the repo. It is created automatically on first run.

---

## Security

**This app is intentionally local-only. It makes no network connections.**

- All file operations happen on your local machine and connected drives only
- No data is sent anywhere — no analytics, no telemetry, no cloud sync
- No account, login, or internet connection is required or used
- Settings are stored locally:
  - macOS: `~/Library/Application Support/Filematic/settings.json`
  - Linux: `~/.config/Filematic/settings.json`
  - Windows: `%APPDATA%\Filematic\settings.json`
- The backup feature uses `rsync` (macOS/Linux) or `robocopy` (Windows) — local drives only

**What this means for contributors:**

Do not add network features to this repository. This is a hard rule, not a
preference. If you want to build a networked or cloud-connected variant, fork
the project and make it clearly distinct. Network access (including HTTP
requests, remote APIs, cloud storage, or telemetry of any kind) will not be
merged into this codebase.

The only subprocess calls the app makes are:
- `exiftool` — local CLI tool, reads file metadata only
- `rsync` / `robocopy` — local drive-to-drive sync only
- `bash` — runs local shell scripts only
- `osascript` / terminal emulator — opens a local Terminal window only

---

## Contributing

Pull requests welcome. A few things to keep in mind:

- The duplicate detection logic in `sort-photos.py` uses EXIF data only —
  never filenames. Do not change this.
- The folder naming convention in Events is fixed format. Scripts depend on
  it. Do not change the structure.
- The app uses Python's built-in `tkinter` + `Pillow` only. No additional
  GUI frameworks.
- Fonts use the system default per platform (SF Pro on macOS, Segoe UI on
  Windows, Helvetica on Linux). Do not add third-party font dependencies.
- **No network features.** See Security section above.
- Keep the interface minimal. This is a utility, not a product.

To suggest a new shoot type, operation, or workflow improvement — open an
issue describing the use case.

---

## Licence

**Polyform Noncommercial.** Free to use, fork, and modify for personal or
non-commercial purposes.

You may **not**:
- Sell it or charge for access to it
- Bundle it into a paid product or subscription service
- Use it to provide a commercial service to others
- Use it or its outputs to train or improve any AI/ML model or commercial product

This project exists to give photographers a free alternative to expensive tools.
It is intentionally kept independent of any commercial interest — including AI
companies, SaaS providers, and subscription software vendors.

See the [LICENSE](LICENSE) file for full terms.
