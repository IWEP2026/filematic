# File Sorting App

A free, open-source macOS app for photographers who want clean, consistent file
management — without paying for Adobe Bridge, Photo Mechanic, or similar tools.

Built for real creative workflows: ingesting RAWs, tracking client events,
sorting personal shoots, and keeping your drives organised over time.

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
| Manual JPG separation | Split JPGs — moves JPGs out of Events/Personal |
| Manual rsync backup | Backup — syncs your drive to a backup destination |

Everything runs locally. No cloud, no subscription, no account.

---

## What it does

### Sort Personal
Reads the EXIF capture date from every photo and moves it into a clean weekly
folder structure on your drive:

```
Personal/
└── 2026/
    └── Week 10 · Mon 02–08/
        ├── 2026-03-02_143022_001.raf
        ├── 2026-03-02_143022_001.jpg
        └── ...
```

Duplicate detection is EXIF-based (timestamp + extension + file size), not
filename-based. Re-ingesting the same card is safe — duplicates are skipped
and logged, never overwritten.

Supports: RAW (RAF, CR2, CR3, NEF, ARW, DNG, RW2, ORF, PEF), JPG, PNG,
TIFF, HEIC.

### New Event
Creates a fully structured client event folder, ready for RAWs after the shoot.

```
Events/
└── 2026/
    └── 2026-03-08_Smith-Jones_Wedding/
        ├── 0001_SMITH-JONES_Prenuptials_2026-03-08/
        │   ├── Completed/
        │   │   └── Best Images/
        │   ├── Unedited RAWs/
        │   └── _SESSION-INFO.md
        ├── 0002_SMITH-JONES_Bridesmaids_2026-03-08/
        ├── 0003_SMITH-JONES_Groomsmen_2026-03-08/
        └── 0004_SMITH-JONES_Wedding_2026-03-08/
```

Shoot types: Wedding (4 sessions), Corporate (2 sessions), Model, Musician,
Baptism, Personal Headshots, Media Client, and custom.

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
Moves all JPG/JPEG files out of the currently selected folder into a
separate destination (default: `Photography/JPGs/`). Useful if your camera
shoots RAW+JPG and you want to separate them after ingesting.

### Backup
Syncs your Photography drive to a backup destination using `rsync`. Copies
new files, updates changed ones, removes deleted ones. Shows live progress
in the app.

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
│   └── YYYY/
│       └── Week WW · Mon DD–DD/
│           └── YYYY-MM-DD_HHMMSS_NNN.ext
└── JPGs/                    ← optional, for Split JPGs
```

---

## Requirements

- **macOS** (tested on macOS 13+)
- **Python 3.10+** — comes with macOS, or install from [python.org](https://www.python.org)
- **Homebrew** — for installing exiftool ([brew.sh](https://brew.sh))
- **exiftool** — for reading EXIF dates when sorting personal photos

---

## Installation

### Option 1 — One-command setup (recommended)

Clone the repo and run the install script:

```bash
git clone https://github.com/YOUR_USERNAME/file-sorting-app.git
cd file-sorting-app
bash install.sh
```

The script will:
1. Check Python 3 is installed
2. Install Homebrew if missing
3. Install `exiftool` via Homebrew
4. Install `Pillow` (Python image library)
5. Make all scripts executable
6. Build the `File Sorting App.app` bundle

Then double-click `File Sorting App.app` to launch.

### Option 2 — Run without building

If you don't want to build the `.app`:

```bash
git clone https://github.com/YOUR_USERNAME/file-sorting-app.git
cd file-sorting-app/app
bash install.sh --no-build
double-click Launch.command
```

Or from Terminal:

```bash
cd file-sorting-app/app
python3 main.py
```

---

## Updating

```bash
cd file-sorting-app
git pull
bash install.sh
```

The install script is safe to re-run. It won't overwrite your settings.

---

## Settings

Runtime settings are stored at:

```
~/Library/Application Support/FileSortingApp/settings.json
```

This file is not committed to the repo — your drive paths and preferences
stay private. It is created automatically on first run.

---

## Contributing

Pull requests welcome. A few things to keep in mind:

- The duplicate detection logic in `sort-photos.py` uses EXIF data only —
  never filenames. Do not change this.
- The folder naming convention in Events is fixed format. Scripts depend on
  it. Do not change the structure.
- The app uses Python's built-in `tkinter` + `Pillow` only. No additional
  GUI frameworks.
- macOS system fonts (SF Pro Display, SF Pro Mono) are used throughout.
  Do not add third-party font dependencies.
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
