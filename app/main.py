#!/usr/bin/env python3
"""
Filematic — Personal & Professional Workflow for Creatives
Step-by-step launcher with folder browser.

Requirements:
    pip install Pillow
"""

import os
import re
import sys
import json
import queue
import shlex
import shutil
import platform
import subprocess
import threading
from datetime import datetime, date, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# ─── Platform ─────────────────────────────────────────────────────────────────

PLATFORM = platform.system()   # 'Darwin', 'Linux', 'Windows'

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ─── Settings ────────────────────────────────────────────────────────────────

def _settings_path():
    if PLATFORM == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Filematic" / "settings.json"
    elif PLATFORM == "Windows":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "Filematic" / "settings.json"
    else:  # Linux / BSD
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(base) / "Filematic" / "settings.json"

def _default_volume():
    if PLATFORM == "Darwin":
        return "/Volumes/Photography"
    elif PLATFORM == "Windows":
        return "D:\\Photography"
    else:
        return str(Path.home() / "Photography")

SETTINGS_PATH  = _settings_path()
DEFAULT_VOLUME = _default_volume()

def load_settings():
    try:
        if SETTINGS_PATH.exists():
            s = json.loads(SETTINGS_PATH.read_text())
            s.setdefault("backup_dest", "")
            s.setdefault("jpg_dest", "")
            s.setdefault("personal_root", "Personal")
            s.setdefault("events_root", "Events")
            s.setdefault("client_label", "Client Name")
            s.setdefault("project_types", DEFAULT_PROJECT_TYPES)
            return s
    except Exception:
        pass
    return {
        "volume": DEFAULT_VOLUME,
        "backup_dest": "",
        "jpg_dest": "",
        "personal_root": "Personal",
        "events_root": "Events",
        "client_label": "Client Name",
        "project_types": DEFAULT_PROJECT_TYPES,
    }

def save_settings(s):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(s, indent=2))

def get_script_dir():
    if getattr(sys, 'frozen', False):
        root = Path(sys.executable).resolve().parent.parent.parent.parent
        candidate = root / "app"
        return str(candidate) if candidate.exists() else str(root)
    return str(Path(__file__).resolve().parent)

# ─── Colours ─────────────────────────────────────────────────────────────────

BG         = "#fafafa"   # single background throughout
PANEL      = "#fafafa"   # same — no alternating shading
STEP_BG    = "#fafafa"   # same
BORDER     = "#e0e0e2"   # clean, light separator
ACCENT     = "#0071e3"
ACCENT_HOV = "#0060c7"
TEXT       = "#1d1d1f"
GREY       = "#6e6e73"
DIM        = "#9a9a9f"
GREEN      = "#1a8c3a"
RED        = "#d93025"
YELLOW     = "#b06a00"
INPUT_BG   = "#ffffff"
INPUT_BD   = "#d0d0d5"
BTN_INACT  = "#e8e8ec"   # clean light grey for inactive buttons
BTN_PRESS  = "#d8d8de"

# ─── Fonts ───────────────────────────────────────────────────────────────────

if PLATFORM == "Darwin":
    F_UI   = "SF Pro Display"
    F_MONO = "SF Pro Mono"
elif PLATFORM == "Windows":
    F_UI   = "Segoe UI"
    F_MONO = "Consolas"
else:  # Linux / BSD
    F_UI   = "Helvetica"
    F_MONO = "Courier"

# ─── New Event data ───────────────────────────────────────────────────────────

DEFAULT_PROJECT_TYPES = [
    "Wedding",
    "Corporate",
    "Model",
    "Personal-Headshots",
    "Musician",
    "Baptism",
    "Media-Client",
    "Other",
]

SESSION_INFO_TEMPLATE = """\
# Session Info
**Date:** {date}
**Shoot Type:** {shoot_type}

---

## Client
- **HubSpot Contact:**
- **Deal Link:**

---

## Crew
- **Primary Shooter:**
- **Secondary Shooter:**
- **Collaboration:**

---

## Equipment
- **Cameras Used:**

---

## Image Count
- **Best Images:** —
- **Unedited RAWs:** —

*Last updated: —*"""

# ─── Step guides ─────────────────────────────────────────────────────────────

STEP_HINTS = {
    "personal": (
        "Select your camera card or source folder (e.g. DCIM) in the panel below, then click Run. "
        "Reads the capture/creation date from every file and sorts into your Personal folder. "
        "Photos (RAW + JPG) land in Personal/YYYY/Week WW · Mon DD–DD/. "
        "Video, audio, design and motion files each get their own subfolder "
        "(Personal/Video/, Personal/Audio/, Personal/Design/, Personal/Motion/) "
        "so different file types are never mixed. "
        "Multi-camera sessions are merged by exact capture time regardless of format or camera. "
        "Requires exiftool (brew install exiftool)."
    ),
    "new_event": (
        "Fill in the event details in the form below, then click Run. "
        "The app creates the full folder structure — no Terminal needed."
    ),
    "organise": (
        "Select an event folder that has RAW files dumped loosely inside it. Click Run — Terminal shows a "
        "preview then creates Completed/Best Images/ and Unedited RAWs/ inside that folder, moves all RAW, "
        "image, and XMP files into Unedited RAWs/, and creates _SESSION-INFO.md if one doesn't exist yet."
    ),
    "counts": (
        "Select a session folder (e.g. 0001_CLIENT_Wedding_2026-03-08/). The script counts images in "
        "Best Images/ and Unedited RAWs/ and updates those numbers in _SESSION-INFO.md. "
        "Runs automatically when you select a folder — no need to press Run."
    ),
    "backup": (
        "No folder needed — click Run. Rsyncs your entire Photography Volume to the Backup Destination "
        "set in Settings. New and changed files are copied; files deleted from the source are left "
        "on the backup. Terminal opens so you can monitor progress."
    ),
    "split_jpgs": (
        "Select an event session folder in the panel below, then click Run. "
        "JPG/JPEG files inside Unedited RAWs/ are moved to the JPGs folder on your Photography Volume "
        "(Photography/JPGs/[folder-name]/), keeping them separate from your RAWs. "
        "Files inside Best Images/ are never touched. "
        "Runs silently — no Terminal window."
    ),
    "rename_edited": (
        "Select a folder of edited or exported images in the panel below, then click Run. "
        "Every file is renamed in-place using its EXIF capture date — "
        "no files are moved, no subfolders are created. "
        "Files already using the correct date-based name are skipped. "
        "Files inside any Best Images/ subfolder are always left untouched. "
        "Requires exiftool (brew install exiftool)."
    ),
}

# ─── Thumbnail constants ──────────────────────────────────────────────────────

THUMB_W    = 140
THUMB_H    = 105
THUMB_GAP  = 10
IMAGE_EXTS = {
    '.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.webp',
    '.heic', '.heif', '.raw', '.cr2', '.cr3', '.arw', '.nef', '.dng',
    '.orf', '.rw2', '.pef', '.srw', '.raf',
}
FILE_ICONS = {
    # Documents
    '.pdf':  '📄', '.txt': '📝', '.md': '📝',
    '.docx': '📋', '.doc': '📋', '.pages': '📋',
    '.xlsx': '📊', '.csv': '📊', '.numbers': '📊',
    # Sidecar / metadata
    '.xmp':  '🔧', '.lrcat': '🔧', '.lrdata': '🔧',
    # Video
    '.mp4':  '🎬', '.mov': '🎬', '.avi': '🎬', '.mkv': '🎬',
    '.m4v':  '🎬', '.mts': '🎬', '.m2ts': '🎬', '.3gp': '🎬',
    '.braw': '🎬', '.r3d': '🎬', '.wmv': '🎬', '.webm': '🎬', '.flv': '🎬',
    # Audio
    '.mp3':  '🎵', '.aac': '🎵', '.wav': '🎵', '.aiff': '🎵', '.aif': '🎵',
    '.flac': '🎵', '.m4a': '🎵', '.ogg': '🎵', '.wma': '🎵', '.opus': '🎵',
    # Adobe design
    '.psd':  '🎨', '.psb': '🎨',
    '.ai':   '🎨', '.eps': '🎨',
    '.indd': '🎨', '.idml': '🎨',
    '.xd':   '🎨',
    # Other design tools
    '.fig':     '🎨',
    '.sketch':  '🎨',
    '.afdesign':'🎨', '.afphoto': '🎨', '.afpub': '🎨',
    '.svg':     '🎨',
    # Motion / video production
    '.aep':      '🎞', '.aepx': '🎞',
    '.prproj':   '🎞',
    '.drp':      '🎞',
    '.fcpx':     '🎞', '.fcpbundle': '🎞',
    '.motion':   '🎞',
    '.mogrt':    '🎞',
    '.veg':      '🎞',
    '.kdenlive': '🎞', '.mlt': '🎞',
    '.edl':      '🎞', '.otio': '🎞', '.xml': '🎞',
    # 3D design
    '.blend':    '🧊', '.c4d': '🧊',
    '.ma':       '🧊', '.mb': '🧊',
    '.obj':      '🧊', '.fbx': '🧊',
    '.glb':      '🧊', '.gltf': '🧊',
    '.stl':      '🧊',
    '.usd':      '🧊', '.usda': '🧊', '.usdc': '🧊', '.usdz': '🧊',
    # Colour grading / LUTs
    '.cube':     '🎨', '.3dl': '🎨', '.look': '🎨',
    # Free design tools
    '.xcf':      '🎨', '.kra': '🎨', '.ora': '🎨',
    '.cdr':      '🎨', '.cdrx': '🎨',
    # Broadcast / legacy video
    '.mxf':      '🎬', '.gxf': '🎬', '.dv': '🎬',
    '.mpg':      '🎬', '.mpeg': '🎬', '.vob': '🎬',
    '.ts':       '🎬', '.tp': '🎬', '.rm': '🎬', '.rmvb': '🎬',
    # Hi-res / specialist audio
    '.dsf':      '🎵', '.dff': '🎵',
    '.ape':      '🎵', '.wv': '🎵', '.tta': '🎵',
    '.caf':      '🎵', '.mid': '🎵', '.midi': '🎵',
    '.amr':      '🎵', '.mka': '🎵',
    # Archives
    '.zip':  '🗜', '.gz': '🗜', '.tar': '🗜', '.rar': '🗜', '.7z': '🗜',
    # Scripts / config
    '.sh':   '⚙',  '.py': '⚙', '.json': '⚙', '.yaml': '⚙', '.toml': '⚙',
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def relative_time(mtime: float) -> str:
    """Human-readable modification age, e.g. 'today', '3 days ago', '2 months ago'."""
    delta = datetime.now() - datetime.fromtimestamp(mtime)
    days = delta.days
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "1 week ago"
    if days < 30:
        return f"{days // 7} weeks ago"
    if days < 60:
        return "1 month ago"
    if days < 365:
        return f"{days // 30} months ago"
    return f"{days // 365}y ago"

# ─── Thumbnail Loader ─────────────────────────────────────────────────────────

class ThumbnailLoader:
    def __init__(self, folder_path, result_queue, cancel_flag):
        self._path   = folder_path
        self._queue  = result_queue
        self._cancel = cancel_flag
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            path = Path(self._path)
            entries = [p for p in path.iterdir() if not p.name.startswith('.')]
            # Sort: folders first, then files — both groups newest-modified first
            entries.sort(key=lambda p: (not p.is_dir(), -p.stat().st_mtime))
            for entry in entries:
                if self._cancel[0]:
                    return
                if entry.is_dir():
                    self._queue.put(("dir", entry, entry.stat().st_mtime))
                elif entry.suffix.lower() in IMAGE_EXTS:
                    pil = self._make_thumb(entry)
                    self._queue.put(("img", entry, pil))
                else:
                    self._queue.put(("file", entry, None))
        except (PermissionError, OSError):
            pass
        self._queue.put(("done", None, None))

    @staticmethod
    def _make_thumb(path):
        if not HAS_PIL:
            return None
        try:
            img = Image.open(path)
            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
            bg = Image.new("RGB", (THUMB_W, THUMB_H), (255, 255, 255))
            ox = (THUMB_W - img.width)  // 2
            oy = (THUMB_H - img.height) // 2
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                bg.paste(img, (ox, oy), img)
            else:
                bg.paste(img.convert("RGB"), (ox, oy))
            return bg
        except Exception:
            return None

# ─── Folder Tree ─────────────────────────────────────────────────────────────

class FolderTree(tk.Frame):
    PINNED = [
        ("Home",      "🏠", lambda: Path.home()),
        ("Desktop",   "📋", lambda: Path.home() / "Desktop"),
        ("Documents", "📁", lambda: Path.home() / "Documents"),
        ("Pictures",  "🖼", lambda: Path.home() / "Pictures"),
        ("Downloads", "⬇", lambda: Path.home() / "Downloads"),
    ]

    def __init__(self, parent, on_select, **kwargs):
        super().__init__(parent, bg=PANEL, **kwargs)
        self.on_select     = on_select
        self._paths        = {}
        self._selected_iid = None
        self._style_tree()
        self._build()

    def _style_tree(self):
        style = ttk.Style()
        style.configure("PH.Treeview",
            background=PANEL, foreground=TEXT,
            fieldbackground=PANEL, rowheight=28,
            font=(F_UI, 12), borderwidth=0,
        )
        style.map("PH.Treeview",
            background=[("selected", "#dce8fb")],
            foreground=[("selected", ACCENT)],
        )

    def _build(self):
        tk.Label(self, text="FOLDERS", bg=PANEL, fg=DIM,
                 font=(F_UI, 9), anchor="w", padx=14, pady=8
                 ).pack(fill="x")

        frame = tk.Frame(self, bg=PANEL)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, style="PH.Treeview",
                                  show="tree", selectmode="browse")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("sep", foreground=DIM, font=(F_UI, 9))
        self._populate()
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<<TreeviewOpen>>",   self._on_open)

    def _populate(self):
        for name, icon, path_fn in self.PINNED:
            p = path_fn()
            if p.exists():
                iid = self.tree.insert("", "end", text=f"  {icon}  {name}")
                self._paths[iid] = str(p)
                self._maybe_add_dummy(iid, p)

        if PLATFORM == "Darwin":
            self.tree.insert("", "end", text="  ── Volumes", tags=("sep",))
            vols = Path("/Volumes")
            if vols.exists():
                try:
                    for v in sorted(vols.iterdir(), key=lambda p: p.name.lower()):
                        if v.is_dir() and not v.name.startswith('.'):
                            iid = self.tree.insert("", "end", text=f"  💿  {v.name}")
                            self._paths[iid] = str(v)
                            self._maybe_add_dummy(iid, v)
                except PermissionError:
                    pass

        elif PLATFORM == "Linux":
            self.tree.insert("", "end", text="  ── Volumes", tags=("sep",))
            for mount_root in [Path("/media"), Path("/mnt")]:
                if not mount_root.exists():
                    continue
                try:
                    for v in sorted(mount_root.iterdir(), key=lambda p: p.name.lower()):
                        if v.is_dir() and not v.name.startswith('.'):
                            iid = self.tree.insert("", "end", text=f"  💿  {v.name}")
                            self._paths[iid] = str(v)
                            self._maybe_add_dummy(iid, v)
                except PermissionError:
                    pass

        elif PLATFORM == "Windows":
            import string
            self.tree.insert("", "end", text="  ── Drives", tags=("sep",))
            for letter in string.ascii_uppercase:
                drive = Path(f"{letter}:\\")
                try:
                    if drive.exists():
                        iid = self.tree.insert("", "end", text=f"  💿  {letter}:")
                        self._paths[iid] = str(drive)
                        self._maybe_add_dummy(iid, drive)
                except (PermissionError, OSError):
                    pass

    def _maybe_add_dummy(self, iid, path):
        try:
            has_dirs = any(
                p.is_dir() and not p.name.startswith('.')
                for p in Path(path).iterdir()
            )
            if has_dirs:
                dummy = self.tree.insert(iid, "end", text="")
                self._paths[dummy] = "__dummy__"
        except (PermissionError, OSError):
            pass

    def _on_open(self, event):
        iid = self.tree.focus()
        path_str = self._paths.get(iid)
        if not path_str or path_str == "__dummy__":
            return
        children = self.tree.get_children(iid)
        if len(children) == 1 and self._paths.get(children[0]) == "__dummy__":
            self.tree.delete(children[0])
            del self._paths[children[0]]
            self._load_children(iid, Path(path_str))

    def _load_children(self, iid, path):
        try:
            dirs = sorted(
                [p for p in path.iterdir() if p.is_dir() and not p.name.startswith('.')],
                key=lambda p: p.name.lower()
            )
            for d in dirs:
                child = self.tree.insert(iid, "end", text=f"  📂  {d.name}")
                self._paths[child] = str(d)
                self._maybe_add_dummy(child, d)
        except (PermissionError, OSError):
            pass

    def _on_select(self, event):
        iid = self.tree.focus()
        path_str = self._paths.get(iid)
        if path_str and path_str != "__dummy__":
            p = Path(path_str)
            if p.is_dir():
                self._selected_iid = iid
                self.on_select(path_str)

    def update_selected_count(self, img_count, dir_count, file_count):
        iid = self._selected_iid
        if not iid:
            return
        text = self.tree.item(iid, "text")
        if " (" in text:
            text = text[:text.rfind(" (")]
        parts = []
        if img_count:  parts.append(f"{img_count} photo{'s' if img_count != 1 else ''}")
        if dir_count:  parts.append(f"{dir_count} folder{'s' if dir_count != 1 else ''}")
        if file_count: parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")
        if parts:
            text = f"{text} ({', '.join(parts)})"
        self.tree.item(iid, text=text)

# ─── Thumbnail Grid ───────────────────────────────────────────────────────────

class ThumbnailGrid(tk.Frame):

    def __init__(self, parent, on_load_complete=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._refs             = []
        self._items            = []   # (kind, path, photo_or_mtime)
        self._cancel           = [False]
        self._q                = queue.Queue()
        self._resize_id        = None
        self._on_load_complete = on_load_complete
        self._selected_path    = None
        self._cell_frames      = {}   # path → cell Frame
        self._build()

    def _build(self):
        # Breadcrumb + count bar
        self._header = tk.Frame(self, bg=STEP_BG)
        self._header.pack(fill="x")
        tk.Frame(self._header, bg=BORDER, height=1).pack(side="bottom", fill="x")

        self._breadcrumb = tk.Label(
            self._header, text="No folder selected",
            bg=STEP_BG, fg=DIM,
            font=(F_MONO, 11), anchor="w", padx=12, pady=6
        )
        self._breadcrumb.pack(side="left", fill="x", expand=True)

        self._count_lbl = tk.Label(
            self._header, text="",
            bg=STEP_BG, fg=DIM,
            font=(F_UI, 11), anchor="e", padx=12
        )
        self._count_lbl.pack(side="right")

        # Canvas
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.inner = tk.Frame(self.canvas, bg=BG)
        self._win  = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        for w in (self.canvas, self.inner):
            w.bind("<MouseWheel>", self._scroll)
            w.bind("<Button-4>",   self._scroll)
            w.bind("<Button-5>",   self._scroll)

        self._hint = tk.Label(self.canvas, text="Select a folder",
                               fg=DIM, bg=BG, font=(F_UI, 14))
        self._hint.place(relx=0.5, rely=0.5, anchor="center")

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._win, width=event.width)
        if self._items:
            if self._resize_id:
                self.after_cancel(self._resize_id)
            self._resize_id = self.after(150, self._relayout)

    def _scroll(self, event):
        if event.num == 4:   self.canvas.yview_scroll(-1, "units")
        elif event.num == 5: self.canvas.yview_scroll(1, "units")
        else: self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def load(self, folder_path):
        self._cancel[0] = True
        self._cancel = [False]
        self._clear()
        self._hint.configure(text="Loading…")
        self._hint.place(relx=0.5, rely=0.5, anchor="center")
        home = str(Path.home())
        display = folder_path.replace(home, "~") if folder_path.startswith(home) else folder_path
        self._breadcrumb.configure(text=display, fg=TEXT)
        self._count_lbl.configure(text="")
        self._q = queue.Queue()
        ThumbnailLoader(folder_path, self._q, self._cancel)
        self.after(50, self._poll)

    def _poll(self):
        batch = 0
        try:
            while batch < 8:
                kind, path, extra = self._q.get_nowait()
                if kind == "done":
                    if not self._items:
                        self._hint.configure(text="Folder is empty")
                        self._hint.place(relx=0.5, rely=0.5, anchor="center")
                    img_c  = sum(1 for k, _, _ in self._items if k == "img")
                    dir_c  = sum(1 for k, _, _ in self._items if k == "dir")
                    file_c = sum(1 for k, _, _ in self._items if k == "file")
                    parts = []
                    if img_c:  parts.append(f"{img_c} photo{'s' if img_c != 1 else ''}")
                    if dir_c:  parts.append(f"{dir_c} folder{'s' if dir_c != 1 else ''}")
                    if file_c: parts.append(f"{file_c} file{'s' if file_c != 1 else ''}")
                    self._count_lbl.configure(text="  ".join(parts))
                    if self._on_load_complete:
                        self._on_load_complete(img_c, dir_c, file_c)
                    return
                # extra = mtime for dirs, PIL image for imgs, None for files
                photo = None
                if kind == "img" and extra is not None and HAS_PIL:
                    photo = ImageTk.PhotoImage(extra)
                    self._refs.append(photo)
                    self._items.append((kind, path, photo))
                elif kind == "dir":
                    self._items.append((kind, path, extra))   # extra = mtime
                else:
                    self._items.append((kind, path, None))
                self._place_cell(len(self._items) - 1, *self._items[-1])
                batch += 1
        except queue.Empty:
            pass
        self.after(50, self._poll)

    def _place_cell(self, idx, kind, path, extra):
        self._hint.place_forget()
        w    = self.canvas.winfo_width() or 500
        cols = max(1, w // (THUMB_W + THUMB_GAP * 2))
        row, col = divmod(idx, cols)
        self._add_cell_widget(row, col, kind, path, extra)

    def _relayout(self):
        for w in self.inner.winfo_children():
            w.destroy()
        canvas_w = self.canvas.winfo_width() or 500
        cols = max(1, canvas_w // (THUMB_W + THUMB_GAP * 2))
        for i, (kind, path, extra) in enumerate(self._items):
            row, col = divmod(i, cols)
            self._add_cell_widget(row, col, kind, path, extra)
        self.canvas.yview_moveto(0)
        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _add_cell_widget(self, row, col, kind, path, extra):
        cell = tk.Frame(self.inner, bg=BG)
        cell.grid(row=row, column=col, padx=THUMB_GAP, pady=THUMB_GAP, sticky="n")
        self._cell_frames[path] = cell

        if kind == "dir":
            tk.Label(cell, text="📂", bg=BG, font=(F_UI, 40)).pack()
        elif kind == "img":
            if extra:  # extra = PhotoImage
                tk.Label(cell, image=extra, bg=BG, bd=0, highlightthickness=0).pack()
            else:
                tk.Label(cell, text="📷", bg=BG, font=(F_UI, 36)).pack()
        else:
            icon = FILE_ICONS.get(path.suffix.lower(), "📄")
            tk.Label(cell, text=icon, bg=BG, font=(F_UI, 36)).pack()
            tk.Label(cell, text=path.suffix.upper().lstrip(".") or "FILE",
                     bg=BG, fg=DIM, font=(F_UI, 9)).pack()

        name = path.name
        if len(name) > 20:
            name = name[:17] + "…"
        tk.Label(cell, text=name, bg=BG, fg=GREY,
                 font=(F_UI, 10), wraplength=THUMB_W).pack(pady=(2, 0))

        # Show relative modified time for directories
        if kind == "dir" and extra is not None:
            tk.Label(cell, text=relative_time(extra),
                     bg=BG, fg=DIM, font=(F_UI, 9)).pack()

        # Bindings: left-click to select, right-click for context menu,
        # double-click images to preview
        right_btn = "<Button-2>" if PLATFORM == "Darwin" else "<Button-3>"
        for w in [cell] + cell.winfo_children():
            w.bind("<Button-1>",  lambda e, p=path, c=cell: self._select_cell(p, c))
            w.bind(right_btn,     lambda e, p=path: self._show_context_menu(e, p))
            if kind == "img":
                w.bind("<Double-Button-1>", lambda e, p=path: self._preview_image(p))

        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _open_in_finder(self, path):
        p = str(path)
        if PLATFORM == "Darwin":
            subprocess.Popen(["open", "-R", p])
        elif PLATFORM == "Windows":
            subprocess.Popen(["explorer", "/select,", p])
        else:
            subprocess.Popen(["xdg-open", str(Path(p).parent)])

    def _show_context_menu(self, event, path):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Open in Finder", command=lambda: self._open_in_finder(path))
        if path.is_file() and path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic', '.heif', '.webp', '.bmp', '.gif'}:
            menu.add_command(label="Preview", command=lambda: self._preview_image(path))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _preview_image(self, path):
        if not HAS_PIL:
            return
        try:
            img = Image.open(path)
            # Scale to fit screen (max 1200×900)
            img.thumbnail((1200, 900), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            win = tk.Toplevel(self)
            win.title(path.name)
            win.configure(bg=BG)
            win.resizable(True, True)
            lbl = tk.Label(win, image=photo, bg=BG)
            lbl.pack(padx=12, pady=12)
            lbl.image = photo  # keep reference
            # Close on click or Escape
            win.bind("<Escape>", lambda e: win.destroy())
            lbl.bind("<Button-1>", lambda e: win.destroy())
        except Exception:
            pass

    def _select_cell(self, path, cell):
        # Deselect previous
        prev = self._cell_frames.get(self._selected_path)
        if prev and prev.winfo_exists():
            for w in [prev] + prev.winfo_children():
                try:
                    w.configure(bg=BG)
                except Exception:
                    pass
        self._selected_path = path
        # Highlight new selection
        sel_bg = "#e8f0fe"
        for w in [cell] + cell.winfo_children():
            try:
                w.configure(bg=sel_bg)
            except Exception:
                pass

    def _clear(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self._refs.clear()
        self._items.clear()
        self._cell_frames.clear()
        self._selected_path = None

# ─── App ─────────────────────────────────────────────────────────────────────

class App(tk.Tk):

    OPERATIONS = [
        ("Sort Personal",  "personal"),
        ("New Event",      "new_event"),
        ("Organise Event", "organise"),
        ("Update Counts",  "counts"),
        ("Split JPGs",     "split_jpgs"),
        ("Rename Edited",  "rename_edited"),
        ("Backup Drive",   "backup"),
    ]

    def __init__(self):
        super().__init__()
        self.settings     = load_settings()
        self.dropped_path = None
        self._op          = "personal"
        self._op_btns     = {}

        self._setup_window()
        self._build_ui()
        self.after(200, self._check_exiftool_startup)

    def _check_exiftool_startup(self):
        if shutil.which("exiftool"):
            return  # already installed — nothing to do

        win = tk.Toplevel(self)
        win.title("exiftool required")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        # Centre over main window
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 460) // 2
        y = self.winfo_y() + (self.winfo_height() - 240) // 2
        win.geometry(f"460x240+{x}+{y}")

        tk.Label(win, text="One dependency needed",
                 bg=BG, fg=TEXT, font=(F_UI, 14, "bold"),
                 anchor="w").pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(win,
                 text="Filematic uses exiftool to read photo and video dates.\n"
                      "It needs to be installed once — takes about 30 seconds.",
                 bg=BG, fg=GREY, font=(F_UI, 12),
                 justify="left").pack(anchor="w", padx=24, pady=(0, 16))

        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))

        def _install_brew():
            win.destroy()
            cmd = "brew install exiftool"
            self._to_terminal(cmd)

        def _open_download():
            import webbrowser
            webbrowser.open("https://exiftool.org")
            win.destroy()

        has_brew = bool(shutil.which("brew"))

        if has_brew:
            tk.Button(btn_frame, text="Install with Homebrew",
                      bg=ACCENT, fg="#ffffff", font=(F_UI, 12),
                      bd=0, relief="flat", padx=20, pady=8,
                      activebackground=ACCENT_HOV, activeforeground="#ffffff",
                      command=_install_brew).pack(side="left")
            tk.Label(btn_frame, text="  or  ", bg=BG, fg=DIM,
                     font=(F_UI, 11)).pack(side="left")

        tk.Button(btn_frame,
                  text="Download from exiftool.org" if not has_brew else "Download manually",
                  bg=BTN_INACT, fg=TEXT, font=(F_UI, 12),
                  bd=0, relief="flat", padx=20, pady=8,
                  activebackground=BTN_PRESS, activeforeground=TEXT,
                  command=_open_download).pack(side="left")

        tk.Button(btn_frame, text="Later",
                  bg=BG, fg=DIM, font=(F_UI, 11),
                  bd=0, relief="flat", padx=12, pady=8,
                  activebackground=BG, activeforeground=GREY,
                  command=win.destroy).pack(side="right")

    def _jpg_dest(self):
        """Resolved JPG destination path (custom or default)."""
        custom = self.settings.get("jpg_dest", "").strip()
        return custom if custom else str(Path(self.settings["volume"]) / "JPGs")

    def _jpg_dest_display(self):
        custom = self.settings.get("jpg_dest", "").strip()
        vol = self.settings["volume"]
        raw = custom if custom else f"{vol}/JPGs"
        return raw.replace(str(Path.home()), "~")

    def _setup_window(self):
        self.title("Filematic")
        self.geometry("1040x760")
        self.resizable(True, True)
        self.minsize(800, 600)
        self.configure(bg=BG)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_step1_drive()
        self._build_step2_operation()
        self._build_step3_hint()
        self._build_new_event_form()   # hidden initially
        self._build_folder_panel()
        self._build_bottom_bar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=BORDER, height=1).pack(side="bottom", fill="x")

        tk.Label(hdr, text="Filematic",
                 bg=BG, fg=TEXT, font=(F_UI, 17, "bold"),
                 padx=20).pack(side="left", pady=14)
        tk.Label(hdr, text="Personal & Professional Workflow for Creatives",
                 bg=BG, fg=DIM, font=(F_UI, 12)).pack(side="left", pady=14)
        tk.Button(hdr, text="Settings",
                  bg=BG, fg=GREY, font=(F_UI, 12),
                  bd=0, relief="flat",                   activebackground=PANEL, activeforeground=TEXT,
                  padx=16, command=self._open_settings).pack(side="right", pady=8)

    def _build_step1_drive(self):
        row = tk.Frame(self, bg=STEP_BG)
        row.pack(fill="x")
        tk.Frame(row, bg=BORDER, height=1).pack(side="bottom", fill="x")

        inner = tk.Frame(row, bg=STEP_BG)
        inner.pack(fill="x", padx=20, pady=8)

        tk.Label(inner, text="1", bg=ACCENT, fg="#ffffff",
                 font=(F_UI, 11, "bold"),
                 width=2, anchor="center").pack(side="left")
        tk.Label(inner, text="Photography Volume",
                 bg=STEP_BG, fg=TEXT,
                 font=(F_UI, 12, "bold"), padx=10).pack(side="left")

        self._vol_lbl = tk.Label(inner, text=self.settings["volume"],
                                  bg=STEP_BG, fg=GREY, font=(F_MONO, 12))
        self._vol_lbl.pack(side="left")

        tk.Label(inner, text="  |  Backup →",
                 bg=STEP_BG, fg=DIM, font=(F_UI, 11)).pack(side="left")

        self._backup_lbl = tk.Label(
            inner,
            text=self.settings.get("backup_dest") or "not set",
            bg=STEP_BG,
            fg=GREY if self.settings.get("backup_dest") else RED,
            font=(F_MONO, 12),
        )
        self._backup_lbl.pack(side="left")

        tk.Label(inner, text="  |  JPGs →",
                 bg=STEP_BG, fg=DIM, font=(F_UI, 11)).pack(side="left")

        jpg_default = self._jpg_dest_display()
        self._jpg_lbl = tk.Label(
            inner, text=jpg_default,
            bg=STEP_BG, fg=GREY, font=(F_MONO, 12),
        )
        self._jpg_lbl.pack(side="left")

    def _build_step2_operation(self):
        row = tk.Frame(self, bg=PANEL)
        row.pack(fill="x")
        tk.Frame(row, bg=BORDER, height=1).pack(side="bottom", fill="x")

        inner = tk.Frame(row, bg=PANEL)
        inner.pack(fill="x", padx=20, pady=8)

        tk.Label(inner, text="2", bg=ACCENT, fg="#ffffff",
                 font=(F_UI, 11, "bold"),
                 width=2, anchor="center").pack(side="left")
        tk.Label(inner, text="What to do",
                 bg=PANEL, fg=TEXT,
                 font=(F_UI, 12, "bold"), padx=10).pack(side="left")

        for label, val in self.OPERATIONS:
            active = val == self._op
            # Use Frame+Label instead of Button to avoid macOS Aqua highlight flash
            border = tk.Frame(inner,
                bg=ACCENT if active else BORDER,
                padx=1, pady=1)
            border.pack(side="left", padx=(0, 6))
            lbl = tk.Label(border, text=label,
                bg=ACCENT if active else "#ffffff",
                fg="#ffffff" if active else TEXT,
                font=(F_UI, 12),
                padx=13, pady=5)
            lbl.pack()
            for widget in (border, lbl):
                widget.bind("<Button-1>", lambda e, v=val: self._select_op(v))
                widget.bind("<Enter>",    lambda e, b=border, l=lbl, v=val: self._op_hover(b, l, v, True))
                widget.bind("<Leave>",    lambda e, b=border, l=lbl, v=val: self._op_hover(b, l, v, False))
            self._op_btns[val] = (border, lbl)

    def _build_step3_hint(self):
        self._step3_row = tk.Frame(self, bg=STEP_BG)
        self._step3_row.pack(fill="x")
        tk.Frame(self._step3_row, bg=BORDER, height=1).pack(side="bottom", fill="x")

        inner = tk.Frame(self._step3_row, bg=STEP_BG)
        inner.pack(fill="x", padx=20, pady=8)

        tk.Label(inner, text="3", bg=ACCENT, fg="#ffffff",
                 font=(F_UI, 11, "bold"),
                 width=2, anchor="center").pack(side="left")
        tk.Label(inner, text="Select folder",
                 bg=STEP_BG, fg=TEXT,
                 font=(F_UI, 12, "bold"), padx=10).pack(side="left")

        self._step3_hint = tk.Label(
            inner, text=STEP_HINTS[self._op],
            bg=STEP_BG, fg=GREY,
            font=(F_UI, 11),
            justify="left", wraplength=720,
        )
        self._step3_hint.pack(side="left")

    def _build_new_event_form(self):
        """Form panel — packed/unpacked dynamically when New Event is selected."""
        self._form_frame = tk.Frame(self, bg=PANEL)
        # Not packed here; _select_op inserts it before the folder panel.

        tk.Frame(self._form_frame, bg=BORDER, height=1).pack(side="top",    fill="x")
        tk.Frame(self._form_frame, bg=BORDER, height=1).pack(side="bottom", fill="x")

        body = tk.Frame(self._form_frame, bg=PANEL)
        body.pack(fill="x", padx=24, pady=14)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(3, weight=1)

        def lbl(text, r, c):
            tk.Label(body, text=text, bg=PANEL, fg=GREY,
                     font=(F_UI, 11), anchor="w"
                     ).grid(row=r, column=c, sticky="w", padx=(0, 8), pady=5)

        def entry(var, r, c, width=None, **kw):
            e = tk.Entry(body, textvariable=var,
                         font=(F_MONO, 12), bg=INPUT_BG, fg=TEXT,
                         relief="flat", bd=0, insertbackground=TEXT,
                         highlightthickness=2, highlightbackground=INPUT_BD,
                         highlightcolor=ACCENT, **kw)
            if width:
                e.configure(width=width)
            e.grid(row=r, column=c+1, sticky="ew", padx=(0, 24), pady=5, ipady=6)
            return e

        # Row 0: Year  |  Date
        self._ev_year = tk.StringVar(value=str(date.today().year))
        lbl("Year", 0, 0);  entry(self._ev_year, 0, 0, width=8)

        self._ev_date = tk.StringVar(value=str(date.today()))
        lbl("Shoot Date", 0, 2);  entry(self._ev_date, 0, 2)

        # Row 1: Project Type  |  Client Name
        lbl("Project Type", 1, 0)
        project_types = self.settings.get("project_types", DEFAULT_PROJECT_TYPES)
        self._ev_type = tk.StringVar(value=project_types[0] if project_types else "")
        self._ev_type_cb = ttk.Combobox(body, textvariable=self._ev_type,
                                         values=project_types, state="readonly",
                                         font=(F_UI, 12))
        self._ev_type_cb.grid(row=1, column=1, sticky="ew", padx=(0, 24), pady=5, ipady=4)
        self._ev_type_cb.bind("<<ComboboxSelected>>", lambda e: self._on_type_changed())

        client_label = self.settings.get("client_label", "Client Name")
        self._ev_client_lbl = tk.Label(body, text=client_label,
                                        bg=PANEL, fg=GREY,
                                        font=(F_UI, 11), anchor="w")
        self._ev_client_lbl.grid(row=1, column=2, sticky="w", padx=(0, 8), pady=5)
        self._ev_client = tk.StringVar()
        tk.Entry(body, textvariable=self._ev_client,
                 font=(F_MONO, 12), bg=INPUT_BG, fg=TEXT,
                 relief="flat", bd=0, insertbackground=TEXT,
                 highlightthickness=2, highlightbackground=INPUT_BD,
                 highlightcolor=ACCENT
                 ).grid(row=1, column=3, sticky="ew", padx=(0, 24), pady=5, ipady=6)

        # Row 2: Wedding-only — prenuptials toggle
        self._ev_prenup = tk.BooleanVar(value=True)
        self._prenup_row = tk.Frame(body, bg=PANEL)
        self._prenup_row.grid(row=2, column=0, columnspan=4, sticky="w", pady=(2, 4))
        tk.Checkbutton(
            self._prenup_row, text="Include prenuptials sessions",
            variable=self._ev_prenup,
            bg=PANEL, fg=GREY, font=(F_UI, 11),
            activebackground=PANEL, selectcolor=INPUT_BG,
        ).pack(side="left")
        # Show only when Wedding is selected
        self._update_prenup_visibility()

        # Hint
        tk.Label(body,
                 text="Name: use hyphens, no spaces — e.g.  Smith-Jones  or  Acme-Corp",
                 bg=PANEL, fg=DIM, font=(F_UI, 10)
                 ).grid(row=3, column=2, columnspan=2, sticky="w")

    def _on_type_changed(self):
        self._update_prenup_visibility()

    def _update_prenup_visibility(self):
        if self._ev_type.get() == "Wedding":
            self._prenup_row.grid()
        else:
            self._prenup_row.grid_remove()

    def _build_folder_panel(self):
        self._folder_paned = tk.PanedWindow(
            self, orient="horizontal",
            bg=BORDER, sashwidth=1, sashrelief="flat",
            bd=0, showhandle=False, opaqueresize=True
        )
        self._folder_paned.pack(fill="both", expand=True)

        self._folder_tree = FolderTree(
            self._folder_paned, on_select=self._on_folder_select
        )
        self._folder_paned.add(self._folder_tree, minsize=180, width=240)

        self._thumb_grid = ThumbnailGrid(
            self._folder_paned, on_load_complete=self._on_thumb_load_complete
        )
        self._folder_paned.add(self._thumb_grid, minsize=400)

    def _build_bottom_bar(self):
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", side="bottom")
        tk.Frame(bar, bg=BORDER, height=1).pack(side="top", fill="x")

        inner = tk.Frame(bar, bg=PANEL)
        inner.pack(fill="x", padx=20, pady=10)

        tk.Label(inner, text="4", bg=ACCENT, fg="#ffffff",
                 font=(F_UI, 11, "bold"),
                 width=2, anchor="center").pack(side="left")

        self._status_lbl = tk.Label(
            inner, text="Select a folder to begin",
            bg=PANEL, fg=DIM,
            font=(F_UI, 11),
            anchor="w", padx=12
        )
        self._status_lbl.pack(side="left", fill="x", expand=True)

        self._run_btn = tk.Button(
            inner, text="Run",
            bg=ACCENT, fg="#ffffff",
            font=(F_UI, 14, "bold"),
            bd=0, relief="flat",             padx=28, pady=8,
            activebackground=ACCENT_HOV, activeforeground="#ffffff",
            command=self._run
        )
        self._run_btn.pack(side="right")

    # ── Interaction ───────────────────────────────────────────────────────────

    def _on_folder_select(self, path):
        self.dropped_path = path
        self._set_status(self._short_path(path), TEXT)
        self._thumb_grid.load(path)
        if self._op == "counts":
            self._auto_counts()

    def _on_thumb_load_complete(self, img_count, dir_count, file_count):
        self._folder_tree.update_selected_count(img_count, dir_count, file_count)

    def _auto_counts(self):
        here = get_script_dir()
        cmd = (f"bash {shlex.quote(os.path.join(here, 'update-image-counts.sh'))} "
               f"{shlex.quote(self.dropped_path)}")
        threading.Thread(target=self._bg_counts, args=(cmd,), daemon=True).start()

    def _op_hover(self, border, lbl, val, entering):
        active = val == self._op
        if active:
            return  # don't change active button on hover
        border.configure(bg=ACCENT if entering else BORDER)
        lbl.configure(bg=BTN_PRESS if entering else "#ffffff")

    def _select_op(self, val):
        self._op = val
        for k, (border, lbl) in self._op_btns.items():
            active = k == val
            border.configure(bg=ACCENT if active else BORDER)
            lbl.configure(
                bg=ACCENT if active else "#ffffff",
                fg="#ffffff" if active else TEXT,
            )
        self._step3_hint.configure(text=STEP_HINTS[val])

        # Show / hide the New Event form between step3 and the folder panel
        if val == "new_event":
            self._form_frame.pack(fill="x", before=self._folder_paned)
        else:
            self._form_frame.pack_forget()

        if val == "counts" and self.dropped_path:
            self._auto_counts()

    def _set_status(self, msg, colour=DIM):
        self._status_lbl.configure(text=msg, fg=colour)
        self.update_idletasks()

    # ── Run ───────────────────────────────────────────────────────────────────

    def _run(self):
        op   = self._op
        vol  = self.settings["volume"]
        here = get_script_dir()

        def script(name):
            return os.path.join(here, name)

        if op == "personal":
            if not self.dropped_path:
                self._set_status("Choose a card folder first (step 3)", RED); return
            personal_root = self.settings.get("personal_root", "Personal")
            cmd = (
                f"{shlex.quote(sys.executable)} {shlex.quote(script('sort-photos.py'))} --ingest "
                f"{shlex.quote(self.dropped_path)} "
                f"{shlex.quote(os.path.join(vol, personal_root))}"
            )
            self._to_terminal(cmd)

        elif op == "new_event":
            self._run_new_event(vol)

        elif op == "organise":
            if not self.dropped_path:
                self._set_status("Choose an event folder first (step 3)", RED); return
            bash = self._find_bash()
            if not bash:
                self._set_status("bash not found — install WSL or Git for Windows", RED); return
            cmd = (f"{shlex.quote(bash)} {shlex.quote(script('organise-existing-event.sh'))} "
                   f"{shlex.quote(self.dropped_path)}")
            self._to_terminal(cmd)

        elif op == "counts":
            if not self.dropped_path:
                self._set_status("Choose a session folder first (step 3)", RED); return
            bash = self._find_bash()
            if not bash:
                self._set_status("bash not found — install WSL or Git for Windows", RED); return
            cmd = (f"{shlex.quote(bash)} {shlex.quote(script('update-image-counts.sh'))} "
                   f"{shlex.quote(self.dropped_path)}")
            threading.Thread(target=self._bg_counts, args=(cmd,), daemon=True).start()

        elif op == "split_jpgs":
            if not self.dropped_path:
                self._set_status("Choose a folder first (step 3)", RED); return
            threading.Thread(
                target=self._bg_split_jpgs,
                args=(self.dropped_path, self._jpg_dest()),
                daemon=True
            ).start()

        elif op == "rename_edited":
            if not self.dropped_path:
                self._set_status("Choose a folder first (step 3)", RED); return
            cmd = (
                f"{shlex.quote(sys.executable)} {shlex.quote(script('sort-photos.py'))} --rename-only "
                f"{shlex.quote(self.dropped_path)}"
            )
            self._to_terminal(cmd)

        elif op == "backup":
            dest = self.settings.get("backup_dest", "").strip()
            if not dest:
                self._set_status("Set a Backup Destination in Settings first", RED); return
            Path(dest).mkdir(parents=True, exist_ok=True)
            if PLATFORM == "Windows":
                cmd = f'robocopy "{vol}" "{dest}" /MIR /MT:4 /NP'
            else:
                src = vol.rstrip("/") + "/"
                cmd = f"rsync -av --progress {shlex.quote(src)} {shlex.quote(dest)}"
            self._to_terminal(cmd)

    # ── New Event (in-app) ────────────────────────────────────────────────────

    def _run_new_event(self, vol):
        year       = self._ev_year.get().strip()
        shoot_type = self._ev_type.get().strip()
        client_raw = self._ev_client.get().strip()
        shoot_date = self._ev_date.get().strip()

        if not year.isdigit() or len(year) != 4:
            self._set_status("Year must be a 4-digit number", RED); return
        if not client_raw:
            label = self.settings.get("client_label", "Client Name")
            self._set_status(f"Enter a {label.lower()}", RED); return
        try:
            datetime.strptime(shoot_date, "%Y-%m-%d")
        except ValueError:
            self._set_status("Date must be YYYY-MM-DD", RED); return

        # Sanitise: spaces → hyphens, strip unsafe chars
        client = re.sub(r'[^a-zA-Z0-9_\-]', '', client_raw.replace(' ', '-'))
        if not client:
            self._set_status("Client name contains no valid characters", RED); return
        client_upper = client.upper()

        events_folder_name = self.settings.get("events_root", "Events")
        events_root = Path(vol) / events_folder_name
        if not events_root.exists():
            self._set_status(
                f"{events_folder_name}/ folder not found: {events_root}  (is your drive connected?)", RED)
            return

        # Event folder includes the shoot date so it sorts chronologically in Finder
        event_folder = events_root / year / f"{shoot_date}_{client}_{shoot_type}"

        if shoot_type == "Wedding":
            if self._ev_prenup.get():
                sessions = [
                    f"0001_{client_upper}_Prenuptials_{shoot_date}",
                    f"0002_{client_upper}_Bridesmaids_{shoot_date}",
                    f"0003_{client_upper}_Groomsmen_{shoot_date}",
                    f"0004_{client_upper}_Ceremony_{shoot_date}",
                    f"0005_{client_upper}_Reception_{shoot_date}",
                ]
            else:
                sessions = [
                    f"0001_{client_upper}_Bridesmaids_{shoot_date}",
                    f"0002_{client_upper}_Groomsmen_{shoot_date}",
                    f"0003_{client_upper}_Ceremony_{shoot_date}",
                    f"0004_{client_upper}_Reception_{shoot_date}",
                ]
        elif shoot_type == "Corporate":
            sessions = [
                f"0001_{client_upper}_Corporate-Event_{shoot_date}",
                f"0002_{client_upper}_Group-Headshots_{shoot_date}",
            ]
        else:
            sessions = [
                f"0001_{client_upper}_{shoot_type}_{shoot_date}",
            ]

        try:
            for sname in sessions:
                sdir = event_folder / sname
                (sdir / "Completed" / "Best Images").mkdir(parents=True, exist_ok=True)
                (sdir / "Unedited RAWs").mkdir(parents=True, exist_ok=True)
                info_path = sdir / "_SESSION-INFO.md"
                if not info_path.exists():
                    info_path.write_text(
                        SESSION_INFO_TEMPLATE.format(
                            date=shoot_date, shoot_type=shoot_type
                        )
                    )
        except Exception as e:
            self._set_status(f"Error creating folders: {e}", RED)
            return

        short = f"{events_folder_name}/{year}/{shoot_date}_{client}_{shoot_type}/"
        self._set_status(f"Created: {short}  ✓", GREEN)

        # Refresh grid if we're already viewing the year folder
        if self.dropped_path and Path(self.dropped_path) == events_root / year:
            self._thumb_grid.load(self.dropped_path)

    # ── Terminal / background ─────────────────────────────────────────────────

    @staticmethod
    def _find_bash():
        """Return path to bash, or None if not found."""
        if PLATFORM == "Windows":
            # Try WSL bash, then Git for Windows bash
            candidates = [
                r"C:\Windows\System32\bash.exe",
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c
            return shutil.which("bash")
        return "bash"   # macOS and Linux always have bash

    def _to_terminal(self, cmd):
        if PLATFORM == "Darwin":
            esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.run([
                "osascript", "-e",
                f'tell application "Terminal" to activate\n'
                f'tell application "Terminal" to do script "{esc}"'
            ])

        elif PLATFORM == "Linux":
            hold = f'{cmd}; echo; read -rp "Press Enter to close…"'
            launched = False
            for emulator, args in [
                ("gnome-terminal", ["--", "bash", "-c", hold]),
                ("konsole",        ["-e", "bash", "-c", hold]),
                ("xfce4-terminal", ["-e", f'bash -c {shlex.quote(hold)}']),
                ("xterm",          ["-e", f'bash -c {shlex.quote(hold)}']),
                ("x-terminal-emulator", ["-e", f'bash -c {shlex.quote(hold)}']),
            ]:
                if shutil.which(emulator):
                    subprocess.Popen([emulator] + args)
                    launched = True
                    break
            if not launched:
                # Headless fallback — run in background thread
                threading.Thread(
                    target=lambda: subprocess.run(cmd, shell=True), daemon=True
                ).start()

        elif PLATFORM == "Windows":
            subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", cmd])

        self._set_status("Running in Terminal…", GREEN)

    def _bg_counts(self, cmd):
        self.after(0, lambda: self._set_status("Updating counts…", YELLOW))
        self.after(0, lambda: self._run_btn.configure(state="disabled"))
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if r.returncode == 0:
                self.after(0, lambda: self._set_status("Counts updated ✓", GREEN))
            else:
                self.after(0, lambda: self._set_status("Error — see console", RED))
                print(r.stderr)
        except Exception as e:
            msg = str(e)[:60]
            self.after(0, lambda: self._set_status(msg, RED))
        finally:
            self.after(0, lambda: self._run_btn.configure(state="normal"))

    def _bg_split_jpgs(self, source: str, jpg_root: str):
        import shutil as _shutil
        self.after(0, lambda: self._set_status("Splitting JPGs…", YELLOW))
        self.after(0, lambda: self._run_btn.configure(state="disabled"))
        try:
            src_path    = Path(source)
            folder_name = src_path.name
            dest_dir    = Path(jpg_root) / folder_name
            dest_dir.mkdir(parents=True, exist_ok=True)

            # If the folder contains an "Unedited RAWs" subfolder, target only
            # that subfolder — those are the camera JPGs that belong elsewhere.
            # Otherwise scan the whole folder but never touch Best Images.
            unedited = src_path / "Unedited RAWs"
            search_root = unedited if unedited.is_dir() else src_path

            jpg_exts = {'.jpg', '.jpeg'}
            found = sorted(
                [p for p in search_root.rglob('*')
                 if p.is_file()
                 and p.suffix.lower() in jpg_exts
                 and 'Best Images' not in p.parts],
                key=lambda p: p.name.lower()
            )

            if not found:
                self.after(0, lambda: self._set_status(
                    f"No JPG files found in {folder_name}", DIM))
                return

            moved = skipped = 0
            for f in found:
                dest_file = dest_dir / f.name
                if dest_file.exists():
                    skipped += 1
                    continue
                _shutil.move(str(f), str(dest_file))
                moved += 1

            msg = f"Moved {moved} JPG{'s' if moved != 1 else ''} → JPGs/{folder_name}/"
            if skipped:
                msg += f"  ({skipped} skipped — already exist)"
            self.after(0, lambda: self._set_status(msg + "  ✓", GREEN))

            # Refresh grid so moved files disappear
            if self.dropped_path:
                self.after(0, lambda: self._thumb_grid.load(self.dropped_path))

        except Exception as e:
            msg = str(e)[:80]
            self.after(0, lambda: self._set_status(msg, RED))
        finally:
            self.after(0, lambda: self._run_btn.configure(state="normal"))

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("460x640")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.grab_set()

        def _field(label, default):
            tk.Label(win, text=label, bg=BG, fg=TEXT,
                     font=(F_UI, 12, "bold"), anchor="w"
                     ).pack(anchor="w", padx=24, pady=(16, 4))
            e = tk.Entry(win, font=(F_MONO, 12),
                         bg=INPUT_BG, fg=TEXT, relief="flat", bd=0,
                         insertbackground=TEXT, highlightthickness=2,
                         highlightbackground=INPUT_BD, highlightcolor=ACCENT)
            e.insert(0, default)
            e.pack(fill="x", padx=24, pady=(0, 0), ipady=8)
            return e

        vol_entry    = _field("Photography Volume",  self.settings["volume"])
        backup_entry = _field("Backup Destination",  self.settings.get("backup_dest", ""))
        tk.Label(win, text="e.g. /Volumes/BackupDrive/Photography",
                 bg=BG, fg=DIM, font=(F_UI, 10)
                 ).pack(anchor="w", padx=24, pady=(2, 0))
        jpg_entry = _field("JPG Split Destination",  self.settings.get("jpg_dest", ""))
        tk.Label(win, text="Leave blank to use Photography/JPGs/  (default)",
                 bg=BG, fg=DIM, font=(F_UI, 10)
                 ).pack(anchor="w", padx=24, pady=(2, 0))
        personal_entry = _field("Personal Folder Name",  self.settings.get("personal_root", "Personal"))
        events_entry   = _field("Events Folder Name",    self.settings.get("events_root", "Events"))
        tk.Label(win, text="Folder names inside your Photography Volume",
                 bg=BG, fg=DIM, font=(F_UI, 10)
                 ).pack(anchor="w", padx=24, pady=(2, 0))
        client_entry = _field("Client Label",  self.settings.get("client_label", "Client Name"))
        tk.Label(win, text="Label shown next to the name field in New Event  (e.g. Client, Artist, Couple)",
                 bg=BG, fg=DIM, font=(F_UI, 10)
                 ).pack(anchor="w", padx=24, pady=(2, 0))
        types_raw = ", ".join(self.settings.get("project_types", DEFAULT_PROJECT_TYPES))
        types_entry = _field("Project Types",  types_raw)
        tk.Label(win, text="Comma-separated list shown in the Project Type dropdown",
                 bg=BG, fg=DIM, font=(F_UI, 10)
                 ).pack(anchor="w", padx=24, pady=(2, 0))

        def _save():
            self.settings["volume"]        = vol_entry.get().rstrip("/")
            self.settings["backup_dest"]   = backup_entry.get().rstrip("/")
            self.settings["jpg_dest"]      = jpg_entry.get().rstrip("/")
            self.settings["personal_root"] = personal_entry.get().strip() or "Personal"
            self.settings["events_root"]   = events_entry.get().strip() or "Events"
            self.settings["client_label"]  = client_entry.get().strip() or "Client Name"
            raw_types = [t.strip() for t in types_entry.get().split(",") if t.strip()]
            self.settings["project_types"] = raw_types if raw_types else DEFAULT_PROJECT_TYPES
            save_settings(self.settings)
            # Update live UI
            self._vol_lbl.configure(text=self.settings["volume"])
            bd = self.settings["backup_dest"]
            self._backup_lbl.configure(text=bd or "not set", fg=GREY if bd else RED)
            self._jpg_lbl.configure(text=self._jpg_dest_display())
            # Update New Event form labels/dropdown without rebuilding
            self._ev_client_lbl.configure(text=self.settings["client_label"])
            self._ev_type_cb.configure(values=self.settings["project_types"])
            if self._ev_type.get() not in self.settings["project_types"]:
                self._ev_type.set(self.settings["project_types"][0] if self.settings["project_types"] else "")
            win.destroy()

        tk.Button(win, text="Save",
                  bg=ACCENT, fg="#ffffff",
                  font=(F_UI, 13),
                  bd=0, relief="flat", pady=10,
                  activebackground=ACCENT_HOV, activeforeground="#ffffff",
                  command=_save).pack(fill="x", padx=24, pady=(14, 0))

    # ── Utils ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _short_path(p):
        home = str(Path.home())
        return p.replace(home, "~") if p.startswith(home) else p

# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
