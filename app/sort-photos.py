#!/usr/bin/env python3
"""
sort-photos.py — Personal media organiser
──────────────────────────────────────────
Renames files using their capture/creation date and sorts them into
type-separated subfolders:

    Personal/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.raf   ← photos
    Personal/Video/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.mp4
    Personal/Audio/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.wav
    Personal/Design/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.psd
    Personal/Motion/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.aep

Photos (all RAW formats and standard images) stay at the Personal root.
Video, audio, design files, and motion projects each go into their own
subfolder so different file types and uses are never mixed.

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
  XMP (Lightroom/Capture One/Bridge/ACR), PP3 (RawTherapee), DOP (DxO PhotoLab),
  COS (Capture One), THM (camera thumbnails), VRD/DR4 (Canon DPP recipe),
  NKSC (Nikon NX Studio), SPD (Silkypix), ARP (AfterShot Pro) are automatically
  moved alongside their source file and renamed to match.

  Both naming conventions are handled:
    DSC_0042.xmp      (stem-based — Lightroom, Capture One, most apps)
    DSC_0042.RAF.xmp  (fullname-based — Darktable, some ACR exports)

  Result either way:
    DSC_0042.RAF + DSC_0042.xmp  →  2026-03-08_143022_001.raf
                                     2026-03-08_143022_001.xmp

Date source priority:
  1. DateTimeOriginal (camera shutter / recorder start)
  2. CreateDate / ContentCreateDate (most video cameras)
  3. MediaCreateDate / TrackCreateDate (container-level)
  4. File modification date (last resort — logged as [MTIME])

Requires: exiftool
  macOS:   brew install exiftool
  Linux:   sudo apt install libimage-exiftool-perl  (or dnf/pacman equivalent)
  Windows: choco install exiftool  (or download from https://exiftool.org)

━━━ USAGE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Sort existing files already in your Personal folder:
    python3 sort-photos.py /Volumes/Photography/Personal

  Preview without moving anything (dry run):
    python3 sort-photos.py --dry-run /Volumes/Photography/Personal

  Ingest from a memory card or drive (move files onto the SSD):
    python3 sort-photos.py --ingest /Volumes/CARD /Volumes/Photography/Personal

  Rename files in-place using their EXIF date (no subfolders created):
    python3 sort-photos.py --rename-only /Volumes/Photography/Events/CLIENT/Completed
    Files under a "Best Images" subfolder are left completely untouched.

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
    import shutil as _shutil
    if not _shutil.which('exiftool'):
        print("\n❌  exiftool not found.")
        if sys.platform == "darwin":
            print("    macOS:   brew install exiftool")
        elif sys.platform.startswith("linux"):
            print("    Linux:   sudo apt install libimage-exiftool-perl")
            print("             (or: dnf install perl-Image-ExifTool / pacman -S perl-image-exiftool)")
        else:
            print("    Windows: choco install exiftool")
            print("             (or download from https://exiftool.org)")
        print()
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
    '.xmp',    # Lightroom / Capture One / Bridge / ACR edit metadata
    '.pp3',    # RawTherapee processing profile
    '.pp',     # RawTherapee (older)
    '.dop',    # DxO PhotoLab sidecar
    '.cos',    # Capture One settings
    '.lrprev', # Lightroom preview cache
    '.thm',    # Camera-generated thumbnail (Canon, Sony)
    '.vrd',    # Canon Digital Photo Professional recipe (v1–3)
    '.dr4',    # Canon Digital Photo Professional recipe (v4)
    '.nksc',   # Nikon ViewNX-i / NX Studio sidecar
    '.spd',    # Silkypix Developer Studio sidecar
    '.arp',    # Corel AfterShot Pro sidecar
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
    stem = source_file.stem                # e.g. "DSC_0042"
    full_name = source_file.name           # e.g. "DSC_0042.RAF" (for multi-ext sidecars)
    source_dir = source_file.parent
    dest_stem = dest_file.stem             # e.g. "2026-03-08_143022_001"
    dest_dir = dest_file.parent

    # Normalise to lowercase for dedup — macOS Path.resolve() preserves the
    # case you supply rather than the on-disk name, so "foo.XMP" and "foo.xmp"
    # would compare as different even though they're the same file.
    seen: set[str] = set()
    for sidecar_ext in SIDECAR_EXTENSIONS:
        # Two naming conventions used by different apps:
        #   stem-based:      DSC_0042.xmp      (Lightroom, Capture One, most apps)
        #   fullname-based:  DSC_0042.RAF.xmp  (Darktable, some ACR exports)
        # Check both, and both lower/upper case variants.
        candidates = [
            stem + sidecar_ext,
            stem + sidecar_ext.upper(),
            full_name + sidecar_ext,
            full_name + sidecar_ext.upper(),
        ]
        for candidate in candidates:
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


# ── Orphan sidecar rescue ───────────────────────────────────────────

def _rescue_orphan_sidecars(
    source_dir: Path,
    dest_dir: Path,
    stem_index: dict,   # lowercase original stem → new dest Path
    dry_run: bool,
):
    """
    After the main sort pass, find any sidecar files left behind that have
    no matching media file in their current directory.

    Two outcomes:
      A) A matching media file WAS sorted this run (tracked in stem_index).
         → Move the sidecar to sit alongside that new file, renamed to match.
      B) No match found anywhere (truly orphaned — source deleted, etc.).
         → Sort the sidecar by its own embedded date into the week folder,
           keeping its original filename so it's not silently lost.
    """
    orphans = [
        f for f in source_dir.rglob('*')
        if f.is_file() and f.suffix.lower() in SIDECAR_EXTENSIONS
    ]
    if not orphans:
        return

    print(f"\n  Checking {len(orphans)} orphaned sidecar(s)…")

    for sidecar in orphans:
        ext_lower = sidecar.suffix.lower()

        # Derive the "owner" stem in two ways:
        #   stem-based:      DSC_0042.xmp      → owner_stem = "dsc_0042"
        #   fullname-based:  DSC_0042.RAF.xmp  → owner_stem = "dsc_0042"
        #   (Path.stem strips only the last suffix, so .stem of DSC_0042.RAF is DSC_0042)
        raw_stem   = Path(sidecar.stem).stem.lower()   # handles double-ext
        plain_stem = sidecar.stem.lower()

        # Check if this sidecar still has a buddy in the SAME directory
        # (shouldn't happen — these are the ones left behind — but be safe)
        has_local_buddy = any(
            (sidecar.parent / (sidecar.stem + ext)).exists()
            for ext in MEDIA_EXTENSIONS
        )
        if has_local_buddy:
            continue  # will be caught by move_sidecars on next sort run

        # Case A: media file was moved this run — we know where it went
        new_media = stem_index.get(plain_stem) or stem_index.get(raw_stem)
        if new_media and new_media.exists():
            new_name   = new_media.stem + ext_lower
            sidecar_dest = new_media.parent / new_name
            print(f"  + orphan → reunite: {sidecar.name}  →  {sidecar_dest.relative_to(dest_dir)}")
            if not dry_run:
                if not sidecar_dest.exists():
                    shutil.move(str(sidecar), str(sidecar_dest))
                else:
                    print(f"    (skipped — destination exists)")
            continue

        # Case B: truly orphaned — rename by its own date, sort to week folder
        try:
            dt, date_source = get_media_date(sidecar)
            week_name, iso_year = week_folder_name(dt)
            dest_folder = dest_dir / str(iso_year) / week_name

            # Generate a date-based name (same convention as media files)
            seq = 1
            new_name = make_filename(dt, ext_lower, seq)
            while (dest_folder / new_name).exists():
                seq += 1
                new_name = make_filename(dt, ext_lower, seq)

            sidecar_dest = dest_folder / new_name
            flag = f" [{date_source}]" if date_source != 'DateTimeOriginal' else ""
            print(f"  + orphan → by date: {sidecar.name}{flag}  →  {sidecar_dest.relative_to(dest_dir)}")
            if not dry_run:
                dest_folder.mkdir(parents=True, exist_ok=True)
                shutil.move(str(sidecar), str(sidecar_dest))
        except Exception as e:
            print(f"  ❌  orphan {sidecar.name}: {e}")


# ── Core ───────────────────────────────────────────────────────────

def process(source_dir: Path, dest_dir: Path, dry_run: bool, ingest: bool):
    # Gather all media files recursively (skip macOS resource fork ._* files)
    files = sorted([
        f for f in source_dir.rglob('*')
        if f.is_file()
        and f.suffix.lower() in MEDIA_EXTENSIONS
        and not f.name.startswith('._')
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

    # Track used filenames per destination folder to handle same-second bursts.
    # Also track original stem → new dest path so orphaned sidecars can be reunited.
    used: dict = {}
    stem_index: dict = {}   # lowercase original stem → new dest Path

    for filepath in files:
        try:
            dt, date_source = get_media_date(filepath)
            week_name, iso_year = week_folder_name(dt)

            # Route each type into its own subfolder so photos, video,
            # audio, design, and motion projects never share a folder.
            ext_lower = filepath.suffix.lower()
            if ext_lower in VIDEO_EXTENSIONS:
                type_root = dest_dir / "Video"
            elif ext_lower in AUDIO_EXTENSIONS:
                type_root = dest_dir / "Audio"
            elif ext_lower in DESIGN_EXTENSIONS:
                type_root = dest_dir / "Design"
            elif ext_lower in MOTION_EXTENSIONS:
                type_root = dest_dir / "Motion"
            else:
                type_root = dest_dir   # photos stay at the root

            dest_folder = type_root / str(iso_year) / week_name

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

            # Record original stem so orphaned sidecars can find their new home
            stem_index[filepath.stem.lower()] = dest_file

            # Move sidecar files (XMP, PP3, DOP, etc.) alongside their source
            move_sidecars(filepath, dest_file, dry_run)

            moved += 1

        except Exception as e:
            print(f"  ❌  {filepath.name}: {e}")
            errors += 1

    # Rescue any sidecar files left behind (orphaned or missed this pass)
    _rescue_orphan_sidecars(source_dir, dest_dir, stem_index, dry_run)

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


# ── Orphan sidecar rename (rename-only mode) ───────────────────────

def _rename_orphan_sidecars_in_place(folder: Path, stem_index: dict, dry_run: bool):
    """
    In rename-only mode, find sidecar files that have no matching media file
    in the same directory and rename them to match the date-based convention.

    Two cases:
      A) Sidecar's source was renamed this run (in stem_index).
         → Rename to match the new media filename.
      B) Sidecar has no known source anywhere.
         → Rename by its own embedded date.

    Files under Best Images/ are always skipped.
    """
    orphans = [
        f for f in folder.rglob('*')
        if f.is_file()
        and f.suffix.lower() in SIDECAR_EXTENSIONS
        and 'Best Images' not in f.parts
    ]
    if not orphans:
        return

    print(f"\n  Checking {len(orphans)} companion sidecar(s)…")

    for sidecar in orphans:
        ext_lower    = sidecar.suffix.lower()
        plain_stem   = sidecar.stem.lower()
        raw_stem     = Path(sidecar.stem).stem.lower()

        # Skip if a media buddy still exists right beside it (move_sidecars handled it)
        has_buddy = any(
            (sidecar.parent / (sidecar.stem + ext)).exists()
            for ext in MEDIA_EXTENSIONS
        )
        if has_buddy:
            continue

        folder_key = str(sidecar.parent)

        # Case A: source was renamed this run
        new_media = stem_index.get(plain_stem) or stem_index.get(raw_stem)
        if new_media:
            new_name     = new_media.stem + ext_lower
            sidecar_dest = sidecar.parent / new_name
            if sidecar_dest == sidecar:
                continue
            print(f"  + companion: {sidecar.name}  →  {sidecar_dest.name}")
            if not dry_run and not sidecar_dest.exists():
                sidecar.rename(sidecar_dest)
            continue

        # Case B: rename by own date
        try:
            dt, date_source = get_media_date(sidecar)
            seq = 1
            new_name = make_filename(dt, ext_lower, seq)
            while (sidecar.parent / new_name).exists():
                seq += 1
                new_name = make_filename(dt, ext_lower, seq)
            sidecar_dest = sidecar.parent / new_name
            if sidecar_dest == sidecar:
                continue
            flag = f" [{date_source}]" if date_source != 'DateTimeOriginal' else ""
            print(f"  + companion → by date: {sidecar.name}{flag}  →  {new_name}")
            if not dry_run:
                sidecar.rename(sidecar_dest)
        except Exception as e:
            print(f"  ❌  companion {sidecar.name}: {e}")


# ── Rename-only mode ───────────────────────────────────────────────

def rename_in_place(folder: Path, dry_run: bool):
    """
    Rename all media files in `folder` using their EXIF capture date.
    Files are renamed in-place — no subfolders are created, nothing is moved.

    Files that already have the correct date-based name are skipped.
    Files under a 'Best Images' subdirectory are left completely untouched.
    Sidecar files (XMP, PP3, DOP, etc.) are renamed alongside their source.
    """
    files = sorted([
        f for f in folder.rglob('*')
        if f.is_file()
        and f.suffix.lower() in MEDIA_EXTENSIONS
        and 'Best Images' not in f.parts
        and not f.name.startswith('._')
    ])

    if not files:
        print(f"  No supported files found in {folder}")
        print("  (Files inside 'Best Images' subfolders are always skipped.)")
        return

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Mode: RENAME-ONLY")
    print(f"Folder: {folder}")
    print(f"Files:  {len(files)}\n")

    # Track used names per directory to handle burst shots in the same folder.
    # Also build stem_index so orphaned sidecars can be renamed to match.
    used: dict = {}
    stem_index: dict = {}   # lowercase original stem → new Path
    renamed = already_correct = errors = 0

    for filepath in files:
        try:
            dt, date_source = get_media_date(filepath)

            folder_key = str(filepath.parent)
            if folder_key not in used:
                used[folder_key] = set()

            seq = 1
            ext = filepath.suffix
            candidate = make_filename(dt, ext, seq)
            while candidate in used[folder_key]:
                seq += 1
                candidate = make_filename(dt, ext, seq)
            used[folder_key].add(candidate)

            dest_file = filepath.parent / candidate

            if dest_file == filepath:
                print(f"  ─  {filepath.name}  (already correct)")
                stem_index[filepath.stem.lower()] = dest_file
                already_correct += 1
                continue

            flag = f"[{date_source}]" if date_source != 'DateTimeOriginal' else ""
            print(f"  {'[DRY RUN] ' if dry_run else ''}→  {filepath.name}  →  {candidate}  {flag}")

            if not dry_run:
                filepath.rename(dest_file)

            stem_index[filepath.stem.lower()] = dest_file
            move_sidecars(filepath, dest_file, dry_run)
            renamed += 1

        except Exception as e:
            print(f"  ❌  {filepath.name}: {e}")
            errors += 1

    # Rename any companion sidecars that were left behind (no live media buddy)
    _rename_orphan_sidecars_in_place(folder, stem_index, dry_run)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}{'─' * 40}")
    print(f"  Renamed         : {renamed}")
    print(f"  Already correct : {already_correct}")
    print(f"  Errors          : {errors}")
    if dry_run:
        print("\n  Nothing was changed. Remove --dry-run to apply.\n")
    else:
        print()


# ── Entry point ────────────────────────────────────────────────────

def main():
    check_exiftool()

    args = sys.argv[1:]
    dry_run     = '--dry-run'     in args
    ingest      = '--ingest'      in args
    rename_only = '--rename-only' in args
    paths       = [a for a in args if not a.startswith('--')]

    if rename_only:
        if len(paths) < 1:
            print(__doc__)
            print("  ⚠️  --rename-only requires: <folder>\n")
            sys.exit(1)
        folder = Path(paths[0])
        if not folder.exists():
            print(f"\n❌  Folder not found: {folder}\n")
            sys.exit(1)
        rename_in_place(folder, dry_run=dry_run)
        return

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
