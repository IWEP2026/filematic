# Reddit post — ready to copy/paste
# Adjust the subreddit and any personal details before posting.
# Works for: r/photography, r/editors, r/videography, r/MacOS, r/opensource,
#            r/fujifilm, r/analog, r/photojournalism, r/filmmakers

---

**Title:**
I built Filematic — a free, open-source app to replace Adobe Bridge and Photo Mechanic. macOS, Linux, Windows. No subscription, no cloud, no bullshit

---

**Body:**

I got tired of paying for apps to do things that should be free: rename files by date, sort them into folders, and keep a client archive clean over time.

So I built **Filematic** — open source, local-only (no internet connection, no telemetry, no account), and free to use forever.

---

**Who it's for**

- Photographers managing RAW files and client shoots
- Videographers keeping footage organised by project
- Any creative who has ever stared at a drive full of `DSC_0042.jpg` and `Untitled Sequence 03` and felt despair

---

**What it does**

**Sort Personal** — reads the EXIF/creation date from every file and automatically renames and sorts into clean weekly folders, separated by type:
```
Personal/2026/Week 10 · Mon 02–08/2026-03-02_143022_001.raf   ← photos
Personal/Video/2026/Week 10 · Mon 02–08/2026-03-02_143045_001.mp4
Personal/Audio/2026/Week 10 · Mon 02–08/2026-03-02_150012_001.wav
```
Photos, video, audio, design files, and motion projects each get their own folder — never mixed. Multi-camera sessions (e.g. RAF + NEF from two bodies) merge into the same photo folder by EXIF timestamp. Duplicate detection is EXIF-based — re-ingesting the same card is safe.

**New Event** — builds a full client event folder structure from a form inside the app. Pick project type (Wedding, Corporate, Musician, etc.), enter the client name and date, and it creates every session folder instantly:
```
Events/2026/2026-03-08_Smith-Jones_Wedding/
  0001_SMITH-JONES_Prenuptials_2026-03-08/   ← optional toggle
    Completed/Best Images/
    Unedited RAWs/
    _SESSION-INFO.md
  0002_SMITH-JONES_Bridesmaids/
  0003_SMITH-JONES_Groomsmen/
  0004_SMITH-JONES_Ceremony/
  0005_SMITH-JONES_Reception/
```
Weddings split Ceremony and Reception into separate sessions automatically. Every session gets its own `Completed/Best Images/` and `Unedited RAWs/`. Everything is configurable — folder names, project types, client label — set once in Settings and done.

Each session gets a Markdown info file to track client details, crew, equipment, and image counts — readable in Finder without opening any app.

**Organise Event** — you already have a folder with RAWs dumped flat in it? Select it, and the app restructures it in-place. No manual folder creation.

**Update Counts** — silently counts files in your Best Images and Unedited RAWs folders and writes the numbers back into the session info file. Runs in the background.

**Split JPGs** — targets `Unedited RAWs/` inside an event session and moves camera JPGs to a separate destination. Never touches `Best Images/`. Useful if your camera shoots RAW+JPG.

**Rename Edited** — renames files in-place using their EXIF date (no moving, no subfolder creation). Companion sidecars (XMP, PP3, etc.) are renamed to match automatically. `Best Images/` folders are always untouched.

**Backup** — drive-to-drive sync to a backup destination (`rsync` on macOS/Linux, `robocopy` on Windows). Nothing leaves your local machine.

**Folder browser** — built-in file browser with thumbnail previews. Shows all file types: RAW, JPG, video (MP4, MOV), audio (MP3, WAV), PSD, PDF, docs. Folders sort by most recently modified so active projects float to the top.

---

**What it replaces**

| You were paying for | This does it instead |
|---|---|
| Adobe Bridge (ingest + browse) | Sort Personal + folder browser |
| Photo Mechanic (folder structure) | New Event + Organise Event |
| Lightroom metadata panels | _SESSION-INFO.md per shoot |
| Manual batch rename tools | Rename Edited |
| Manual rsync scripts | Backup |

---

**What it is not**

- Not a DAM (no star ratings, no catalogue database)
- Not a culling tool
- macOS, Linux, and Windows supported. macOS gets a native `.app` bundle; Linux/Windows run via `python3 main.py`

---

**How to install**

macOS:
```bash
git clone https://github.com/IWEP2026/filematic.git
cd filematic
bash install.sh
```

Linux:
```bash
bash install-linux.sh
```

Windows (PowerShell):
```powershell
.\install-windows.ps1
```

Scripts handle Python, exiftool, and all dependencies automatically.

Repo: **github.com/IWEP2026/filematic**

---

**Licence**

Noncommercial open source. Free to use, fork, and modify. Cannot be sold,
bundled into a paid product, or used to train AI/ML models.

---

Happy to answer questions. If you've got a workflow it doesn't handle, open an
issue — the folder structure and event management side works for any creative
discipline, not just photography.

---

# Shorter version (for Twitter/X, Discord, Slack)
# ~280 characters per tweet, thread below

Tweet 1:
I built a free macOS app to replace Adobe Bridge + Photo Mechanic.
No subscription. No cloud. No account. Just clean file management.
Open source, local-only.
github.com/IWEP2026/filematic

Tweet 2:
What it does:
→ Renames + sorts photos by EXIF date into weekly folders
→ Creates structured client event folders from a form
→ Browses your drive (RAW, video, audio, PSD — all file types)
→ rsync backup between drives
→ Counts best images + RAWs per session

Tweet 3:
Who it's for: photographers, videographers, anyone managing a
creative archive who's sick of paying for tools that do simple things.

Install in one command:
bash install.sh

Noncommercial licence — cannot be sold or used to train AI.

---

# Forum version (Fred Miranda, DPReview, Redditesque photo forums)
# More detail, less punchy

**Title:** Free macOS tool for file management — replaces Bridge/Photo Mechanic workflow

I've been building a free, open-source macOS app to handle the parts of my
photography workflow that don't need a subscription to work.

The core problem: I shoot RAW+JPG, run a mix of personal and client work,
and wanted a single tool that could:

1. Ingest and rename personal photos by EXIF date automatically
2. Create properly structured client folders without manual work
3. Browse my drive and see what's in it without launching Lightroom
4. Back up to a second drive without a separate app

I couldn't find anything free that did all four without a subscription or a
cloud account, so I built it.

**Stack:** Python + tkinter (built-in), Pillow for thumbnails, exiftool for
EXIF reading, rsync for backup. Builds to a standalone .app via PyInstaller.
No third-party services. No internet connection. Settings stored locally.

**Folder structure it creates/expects:**
- Events: `Events/YYYY/YYYY-MM-DD_Client_Type/NNNN_CLIENT_Type_YYYY-MM-DD/`
  - Each session: `Completed/Best Images/`, `Unedited RAWs/`, `_SESSION-INFO.md`
- Personal: `Personal/YYYY/Week WW · Mon DD–DD/YYYY-MM-DD_HHMMSS_NNN.ext`

The session info file is plain Markdown — readable in Finder's Quick Look,
any text editor, or directly in the app. Tracks client, crew, equipment, and
image counts.

One-command install: `bash install.sh` (handles Python, Homebrew, exiftool,
builds the .app — works on Intel and Apple Silicon).

Noncommercial open source licence — free to use and fork, cannot be sold or
used commercially.

github.com/IWEP2026/filematic

Happy to take feedback on the workflow structure if yours is different.
