#!/usr/bin/env python3
"""
sort-photos.py — Personal media organiser
──────────────────────────────────────────
Renames files using their capture/creation date and sorts them into:
    Personal/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.ext

Supports:
  Photos  — Canon (CR2/CR3/CRW), Nikon (NEF/NRW), Sony (ARW/SR2/SRF),
             Fujifilm (RAF), Olympus (ORF), Panasonic (RW2), Pentax (PEF/PTX),
             Hasselblad (3FR/FFF), Phase One (IIQ/CAP/EIP), Mamiya (MEF),
             Leaf (MOS), Sigma (X3F), Leica (RWL), Minolta (MRW), Kodak (KDC/DCR),
             Samsung (SRW), Epson (ERF), Universal (DNG),
             Standard (JPG/PNG/TIFF/HEIC/HEIF/WEBP/BMP)
  Video   — MP4, MOV, MKV, AVI, M4V, MTS/M2TS (AVCHD), BRAW, R3D,
             MXF (broadcast), DV, MPG/MPEG, WMV, WEBM, VOB, 3GP
  Audio   — MP3, WAV, AIFF, FLAC, M4A, AAC, OGG, ALAC, OPUS, WMA,
             DSF/DFF (DSD hi-res), APE, WV, TTA, CAF, AMR, MID/MIDI
  Design  — PSD/PSB (Photoshop), AI/EPS (Illustrator), INDD (InDesign),
             FIG (Figma), Sketch, Affinity suite, XCF (GIMP), KRA (Krita),
             CDR (CorelDRAW), SVG, PDF, BLEND (Blender), C4D, MA/MB (Maya),
             OBJ, FBX, GLB/GLTF, USD/USDZ (AR), LUT (CUBE/3DL/LOOK)
  Motion  — AEP (After Effects), PRPROJ (Premiere), DRP (DaVinci),
             FCPX (Final Cut), VEG (Vegas Pro), KDENlive, Shotcut (MLT),
             MOGRT, EDL, OTIO, FCP XML

Multi-camera sessions:
  Files from different cameras shot on the same day are merged into the same
  weekly folder, sorted by exact capture time. If you shoot with a Fujifilm
  (RAF) and a Nikon (NEF) in the same session, both appear together in the
  correct chronological order. Format and camera model are irrelevant — only
  the EXIF timestamp matters.

Sidecar files travel with their source:
  XMP (Lightroom/Capture One), PP3 (RawTherapee), DOP (DxO PhotoLab),
  COS (Capture One), THM (camera thumbnails) are automatically moved
  alongside their source file and renamed to match:
    DSC_0042.RAF + DSC_0042.xmp  →  2026-03-08_143022_001.raf
                                    2026-03-08_143022_001.xmp

Date source priority:
  1. DateTimeOriginal (camera shutter / recorder start)
  2. CreateDate / ContentCreateDate (most video cameras)
  3. MediaCreateDate / TrackCreateDate (container-level)
  4. File modification date (last resort — logged as [MTIME])

Requires: exiftool  →  brew install exiftool

━━━ USAGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Sort existing files already in your Personal folder:
    python3 sort-photos.py /Volumes/Photography/Personal

  Preview without moving anything (dry run):
    python3 sort-photos.py --dry-run /Volumes/Photography/Personal

  Ingest from a memory card or drive (move files onto the SSD):
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
    # Canon
    '.cr2', '.cr3', '.crw',
    # Nikon
    '.nef', '.nrw',
    # Sony
    '.arw', '.srf', '.sr2',
    # Fujifilm
    '.raf',
    # Adobe / universal
    '.dng',
    # Olympus / OM System
    '.orf', '.obm',
    # Panasonic / Leica
    '.rw2', '.rwl',
    # Pentax
    '.pef', '.ptx',
    # Samsung
    '.srw',
    # Sigma
    '.x3f',
    # Minolta / Konica Minolta
    '.mrw',
    # Hasselblad
    '.3fr', '.fff',
    # Phase One
    '.iiq', '.cap', '.eip',
    # Mamiya / Leaf / Sinar
    '.mef', '.mos', '.cs1',
    # Kodak
    '.kdc', '.dcr',
    # Epson
    '.erf',
    # Standard photo
    '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.heic', '.heif',
    '.webp', '.bmp', '.ico',
}

VIDEO_EXTENSIONS = {
    # Common containers
    '.mp4', '.mov', '.mkv', '.avi', '.m4v',
    # AVCHD (Sony, Panasonic cameras)
    '.mts', '.m2ts', '.ts', '.tp',
    # Mobile
    '.3gp', '.3g2',
    # Professional / cinema RAW
    '.braw',                                  # Blackmagic RAW
    '.r3d',                                   # RED RAW
    # Broadcast / professional
    '.mxf',                                   # Material Exchange Format
    '.gxf',                                   # General Exchange Format
    '.lxf',                                   # Leitch/Harris
    '.dv',                                    # Digital Video (DV tape)
    # MPEG
    '.mpg', '.mpeg', '.m2v', '.m2p',
    # Other
    '.wmv', '.asf',                           # Windows Media
    '.flv', '.f4v',                           # Flash (legacy)
    '.webm', '.ogv',                          # Web / open
    '.divx', '.xvid',                         # Legacy compressed
    '.vob',                                   # DVD
    '.rm', '.rmvb',                           # RealMedia
}

AUDIO_EXTENSIONS = {
    # Lossy
    '.mp3', '.aac', '.ogg', '.wma', '.opus', '.m4a',
    '.amr', '.3ga',                           # Mobile / phone recordings
    # Lossless
    '.wav', '.aiff', '.aif', '.flac', '.alac',
    '.ape',                                   # Monkey's Audio
    '.wv',                                    # WavPack
    '.tta',                                   # True Audio
    # High-res / audiophile
    '.dsf', '.dff',                           # DSD (Direct Stream Digital)
    '.caf',                                   # Core Audio Format (Apple)
    '.pcm', '.au',                            # Raw / legacy
    # Project / MIDI
    '.mid', '.midi',
    # Other
    '.mka',                                   # Matroska Audio
    '.spx',                                   # Speex
    '.mpc',                                   # Musepack
}

DESIGN_EXTENSIONS = {
    # Adobe Creative Suite
    '.psd', '.psb',                           # Photoshop
    '.ai', '.eps',                            # Illustrator
    '.indd', '.idml',                         # InDesign
    '.xd',                                    # Adobe XD
    # Figma / Sketch / Affinity
    '.fig',                                   # Figma
    '.sketch',                                # Sketch
    '.afdesign', '.afphoto', '.afpub',        # Affinity suite
    # Free / open source design
    '.xcf',                                   # GIMP
    '.kra',                                   # Krita
    '.ora',                                   # OpenRaster
    # CorelDRAW
    '.cdr', '.cdrx',
    # Vector / print
    '.svg', '.pdf',
    # 3D / spatial design
    '.blend',                                 # Blender
    '.c4d',                                   # Cinema 4D
    '.ma', '.mb',                             # Autodesk Maya
    '.max',                                   # 3ds Max
    '.obj', '.fbx',                           # Universal 3D exchange
    '.glb', '.gltf',                          # GL Transmission Format (web/AR)
    '.stl',                                   # 3D printing
    '.usd', '.usda', '.usdc', '.usdz',        # Universal Scene Description (Apple AR)
    # Colour grading (LUTs)
    '.cube', '.3dl', '.look',                 # LUT files
    # Lightroom
    '.lrcat', '.lrtemplate',
}

MOTION_EXTENSIONS = {
    '.aep', '.aepx',                          # After Effects
    '.prproj',                                # Premiere Pro
    '.drp',                                   # DaVinci Resolve
    '.fcpx', '.fcpbundle',                    # Final Cut Pro
    '.motion',                                # Apple Motion
    '.mogrt',                                 # Motion Graphics Template
    '.veg',                                   # Vegas Pro (MAGIX)
    '.kdenlive',                              # KDENlive (Linux / cross-platform)
    '.mlt',                                   # Shotcut / MLT framework
    '.edl',                                   # Edit Decision List
    '.otio',                                  # OpenTimelineIO (cross-platform)
    '.xml',                                   # FCP XML / interchange
}

MEDIA_EXTENSIONS = (
    IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
    | DESIGN_EXTENSIONS | MOTION_EXTENSIONS
)

# exiftool date tags in priority order (first non-empty value wins)
DATE_TAGS = [
    'DateTimeOriginal',     # Camera shutter / recorder start — most accurate
    'CreateDate',           # Common in video (QuickTime, MP4)
    'ContentCreateDate',    # Some Sony/Canon video
    'MediaCreateDate',      # MP4 container level
    'TrackCreateDate',      # MP4 track level
]

# ── Helpers ────────────────────────────────────────────────────────

def check_exiftool():
    result = subprocess.run(['which', 'exiftool'], capture_output=True)
    if result.returncode != 0:
        print("\n❌  exiftool not found.")
        print("    Install it with:  brew install exiftool")
        print("    (If you don't have Homebrew: https://brew.sh)\n")
        sys.exit(1)


def get_media_date(filepath: Path):
    """
    Read the capture/creation date from any media file via exiftool.
    Tries DATE_TAGS in priority order — first non-empty value wins.
    Falls back to file modification date if nothing is found.

    Returns (datetime, source_label) where source_label is the tag name
    that provided the date, or 'mtime' if we fell back to filesystem time.
    """
    tag_flags = [f'-{tag}' for tag in DATE_TAGS]
    result = subprocess.run(
        ['exiftool'] + tag_flags + ['-s', '-d', '%Y:%m:%d %H:%M:%S', str(filepath)],
        capture_output=True, text=True
    )

    # Output format: "TagName                         : 2026:03:08 14:30:22"
    for line in result.stdout.splitlines():
        if ':' not in line:
            continue
        tag_part, _, value_part = line.partition(':')
        value = value_part.strip()
        tag = tag_part.strip()
        if not value or value.startswith('0000'):
            continue
        try:
            return datetime.strptime(value, '%Y:%m:%d %H:%M:%S'), tag
        except ValueError:
            continue

    # Nothing found — fall back to filesystem modification time
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


# Sidecar extensions that travel with a source file.
# When a media file is moved, any sidecar with the same stem is moved too,
# renamed to match the new media filename (e.g. 2026-03-08_143022_001.xmp).
SIDECAR_EXTENSIONS = {
    '.xmp',    # Lightroom / Capture One / Bridge edit metadata
    '.pp3',    # RawTherapee processing profile
    '.pp',     # RawTherapee (older)
    '.dop',    # DxO PhotoLab sidecar
    '.cos',    # Capture One settings
    '.lrprev', # Lightroom preview cache
    '.thm',    # Camera-generated thumbnail (Canon, Sony)
}


def make_filename(dt: datetime, ext: str, seq: int):
    """
    Produces a clean, sortable filename.
    Example: 2021-07-24_111900_001.raf
    """
    return f"{dt.strftime('%Y-%m-%d_%H%M%S')}_{seq:03d}{ext.lower()}"


def move_sidecars(source_file: Path, dest_file: Path, dry_run: bool):
    """
    After moving source_file → dest_file, look for any sidecar files
    (same stem, known sidecar extension) in the same source directory
    and move them to dest_file's folder with a matching renamed stem.

    Example:
      DSC_0042.RAF  →  2026-03-08_143022_001.raf
      DSC_0042.xmp  →  2026-03-08_143022_001.xmp   (same folder)
      DSC_0042.pp3  →  2026-03-08_143022_001.pp3
    """
    stem = source_file.stem
    source_dir = source_file.parent
    dest_stem = dest_file.stem   # e.g. "2026-03-08_143022_001"
    dest_dir = dest_file.parent

    # Normalise to lowercase for dedup — macOS Path.resolve() preserves the
    # case you supply rather than the on-disk name, so "foo.XMP" and "foo.xmp"
    # would compare as different even though they're the same file.
    seen: set[str] = set()
    for sidecar_ext in SIDECAR_EXTENSIONS:
        # Check both lower and upper case (cameras write .XMP, .THM etc.)
        for candidate in (stem + sidecar_ext, stem + sidecar_ext.upper()):
            sidecar = source_dir / candidate
            if not sidecar.exists():
                continue
            resolved_lower = str(sidecar.resolve()).lower()
            if resolved_lower in seen:
                continue
            seen.add(resolved_lower)
            sidecar_dest = dest_dir / (dest_stem + sidecar_ext.lower())
            print(f"       + sidecar: {sidecar.name}  →  {sidecar_dest.name}")
            if not dry_run:
                if not sidecar_dest.exists():
                    shutil.move(str(sidecar), str(sidecar_dest))
                else:
                    print(f"         (skipped — destination exists)")


# ── Core ───────────────────────────────────────────────────────────

def process(source_dir: Path, dest_dir: Path, dry_run: bool, ingest: bool):
    # Gather all media files recursively
    files = sorted([
        f for f in source_dir.rglob('*')
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS
    ])

    if not files:
        print(f"  No supported files found in {source_dir}")
        print(f"  Supported types:")
        print(f"    Photos  — All major RAW formats (Canon/Nikon/Sony/Fuji/Hasselblad/Phase One...)")
        print(f"               + JPG, PNG, TIFF, HEIC, WEBP, BMP")
        print(f"    Video   — MP4, MOV, MKV, BRAW, R3D, MXF, DV, MPEG, WMV, WEBM, VOB...")
        print(f"    Audio   — MP3, WAV, FLAC, AIFF, DSD, APE, CAF, MIDI...")
        print(f"    Design  — PSD, AI, FIG, Sketch, GIMP, Krita, CorelDRAW, Blender,")
        print(f"               Cinema 4D, Maya, FBX, USD/USDZ, LUT files...")
        print(f"    Motion  — AEP, PRPROJ, DRP, FCPX, Vegas Pro, KDENlive, EDL, OTIO...")
        return

    # Summarise by type
    photos  = sum(1 for f in files if f.suffix.lower() in IMAGE_EXTENSIONS)
    videos  = sum(1 for f in files if f.suffix.lower() in VIDEO_EXTENSIONS)
    audios  = sum(1 for f in files if f.suffix.lower() in AUDIO_EXTENSIONS)
    designs = sum(1 for f in files if f.suffix.lower() in DESIGN_EXTENSIONS)
    motions = sum(1 for f in files if f.suffix.lower() in MOTION_EXTENSIONS)

    mode = "INGEST" if ingest else "SORT"
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Mode: {mode}")
    print(f"Source:      {source_dir}")
    print(f"Destination: {dest_dir}")
    parts = [f"photos: {photos}", f"video: {videos}", f"audio: {audios}"]
    if designs: parts.append(f"design: {designs}")
    if motions: parts.append(f"motion: {motions}")
    print(f"Files found: {len(files)}  ({',  '.join(parts)})\n")

    moved = skipped = errors = 0

    # Track used filenames per destination folder to handle same-second bursts
    used: dict = {}

    for filepath in files:
        try:
            dt, date_source = get_media_date(filepath)
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

            flag = f"[{date_source.upper()}]" if date_source == 'mtime' else f"[{date_source}]" if date_source != 'DateTimeOriginal' else ""
            print(f"  {'[DRY RUN] ' if dry_run else ''}→  {filepath.name}  {flag}")
            print(f"       {dest_file}")

            if not dry_run:
                dest_folder.mkdir(parents=True, exist_ok=True)
                shutil.move(str(filepath), str(dest_file))

            # Move sidecar files (XMP, PP3, DOP, etc.) alongside their source
            move_sidecars(filepath, dest_file, dry_run)

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
