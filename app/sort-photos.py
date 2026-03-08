#!/usr/bin/env python3
"""
sort-photos.py — Personal photo organiser
─────────────────────────────────────────
Renames files using their EXIF capture date and sorts them into:
    Personal/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.ext

Requires: exiftool  →  brew install exiftool

━━━ USAGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Sort existing files already in your Personal folder:
    python3 sort-photos.py /Volumes/Photography/Personal

  Preview without moving anything (dry run):
    python3 sort-photos.py --dry-run /Volumes/Photography/Personal

  Ingest from a memory card (move files onto the SSD):
    python3 sort-photos.py --ingest /Volumes/CARD /Volumes/Photography/Personal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import subprocess
import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────

# File types to process
IMAGE_EXTENSIONS = {
    # Fujifilm + common RAW formats
    '.raf', '.cr2', '.cr3', '.nef', '.arw', '.dng', '.rw2', '.orf', '.pef',
    # Standard
    '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.heic', '.heif',
}

# ── Helpers ────────────────────────────────────────────────────────

def check_exiftool():
    result = subprocess.run(['which', 'exiftool'], capture_output=True)
    if result.returncode != 0:
        print("\n❌  exiftool not found.")
        print("    Install it with:  brew install exiftool")
        print("    (If you don't have Homebrew: https://brew.sh)\n")
        sys.exit(1)


def get_exif_date(filepath: Path):
    """
    Read DateTimeOriginal from EXIF. This is the moment the shutter fired —
    always accurate regardless of when the file was copied or what the
    filesystem says.

    Falls back to file modification date if EXIF is missing.
    """
    result = subprocess.run(
        ['exiftool', '-DateTimeOriginal', '-s3', '-d', '%Y:%m:%d %H:%M:%S', str(filepath)],
        capture_output=True, text=True
    )
    raw = result.stdout.strip()
    if raw:
        try:
            return datetime.strptime(raw, '%Y:%m:%d %H:%M:%S'), 'exif'
        except ValueError:
            pass

    # No EXIF — fall back to file modification date
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime), 'mtime'


def week_folder_name(dt: datetime):
    """
    Returns (folder_name, iso_year) e.g. ('Week 10 · Mar 02–08', 2026)
    Uses ISO week so weeks always start on Monday and belong to the
    correct year (important for late-December / early-January weeks).
    """
    iso_year, iso_week, _ = dt.isocalendar()

    # Monday of this ISO week
    monday = datetime.fromisocalendar(iso_year, iso_week, 1)
    sunday = monday + timedelta(days=6)

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    if monday.month == sunday.month:
        date_range = f"{months[monday.month - 1]} {monday.day:02d}–{sunday.day:02d}"
    else:
        date_range = (
            f"{months[monday.month - 1]} {monday.day:02d}–"
            f"{months[sunday.month - 1]} {sunday.day:02d}"
        )

    return f"Week {iso_week:02d} · {date_range}", iso_year


def make_filename(dt: datetime, ext: str, seq: int):
    """
    Produces a clean, sortable filename.
    Example: 2021-07-24_111900_001.raf
    """
    return f"{dt.strftime('%Y-%m-%d_%H%M%S')}_{seq:03d}{ext.lower()}"


# ── Core ───────────────────────────────────────────────────────────

def process(source_dir: Path, dest_dir: Path, dry_run: bool, ingest: bool):
    # Gather all image files recursively
    files = sorted([
        f for f in source_dir.rglob('*')
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not files:
        print(f"  No image files found in {source_dir}")
        return

    mode = "INGEST" if ingest else "SORT"
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Mode: {mode}")
    print(f"Source:      {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Files found: {len(files)}\n")

    moved = skipped = errors = 0

    # Track used filenames per destination folder to handle same-second bursts
    used: dict = {}

    for filepath in files:
        try:
            dt, date_source = get_exif_date(filepath)
            week_name, iso_year = week_folder_name(dt)

            dest_folder = dest_dir / str(iso_year) / week_name

            # Find a non-colliding filename (burst shots share same timestamp)
            seq = 1
            folder_key = str(dest_folder)
            if folder_key not in used:
                used[folder_key] = set()
            ext = filepath.suffix
            candidate = make_filename(dt, ext, seq)
            while candidate in used[folder_key]:
                seq += 1
                candidate = make_filename(dt, ext, seq)
            used[folder_key].add(candidate)

            dest_file = dest_folder / candidate

            flag = f"[{date_source.upper()}]" if date_source == 'mtime' else ""
            print(f"  {'[DRY RUN] ' if dry_run else ''}→  {filepath.name}  {flag}")
            print(f"       {dest_file}")

            if not dry_run:
                dest_folder.mkdir(parents=True, exist_ok=True)
                shutil.move(str(filepath), str(dest_file))

            moved += 1

        except Exception as e:
            print(f"  ❌  {filepath.name}: {e}")
            errors += 1

    # Clean up empty folders left behind
    if not dry_run and not ingest:
        _remove_empty_dirs(source_dir)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}{'─' * 40}")
    print(f"  Processed : {moved}")
    print(f"  Errors    : {errors}")
    if dry_run:
        print("\n  Nothing was moved. Remove --dry-run to apply.\n")
    else:
        print()


def _remove_empty_dirs(root: Path):
    """Remove directories that are now empty after sorting."""
    for dirpath in sorted(root.rglob('*'), reverse=True):
        if dirpath.is_dir():
            try:
                dirpath.rmdir()  # Only removes if empty
            except OSError:
                pass


# ── Entry point ────────────────────────────────────────────────────

def main():
    check_exiftool()

    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    ingest  = '--ingest'  in args
    paths   = [a for a in args if not a.startswith('--')]

    if ingest:
        if len(paths) < 2:
            print(__doc__)
            print("  ⚠️  --ingest requires: <source-folder> <personal-folder>\n")
            sys.exit(1)
        source = Path(paths[0])
        dest   = Path(paths[1])
    else:
        if len(paths) < 1:
            print(__doc__)
            sys.exit(1)
        source = Path(paths[0])
        dest   = Path(paths[0])

    if not source.exists():
        print(f"\n❌  Source not found: {source}\n")
        sys.exit(1)

    process(source, dest, dry_run=dry_run, ingest=ingest)


if __name__ == '__main__':
    main()
