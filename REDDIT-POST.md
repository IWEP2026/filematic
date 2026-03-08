# Reddit post — ready to copy/paste
# Adjust the subreddit and any personal details before posting.
# Works for: r/photography, r/editors, r/videography, r/MacOS, r/opensource,
#            r/fujifilm, r/analog, r/photojournalism, r/filmmakers

---

**Title:**
I built a free, open-source macOS app to replace Adobe Bridge and Photo Mechanic — no subscription, no cloud, no bullshit

---

**Body:**

I got tired of paying for apps to do things that should be free: rename files by date, sort them into folders, and keep a client archive clean over time.

So I built one. It's called **File Sorting App**, it's open source, local-only (no internet connection, no telemetry, no account), and free to use forever.

---

**Who it's for**

- Photographers managing RAW files and client shoots
- Videographers keeping footage organised by project
- Any creative who has ever stared at a drive full of `DSC_0042.jpg` and `Untitled Sequence 03` and felt despair

---

**What it does**

**Sort Personal** — reads the EXIF capture date from your photos and automatically renames and sorts them into clean weekly folders:
```
Personal/2026/Week 10 · Mon 02–08/2026-03-02_143022_001.raf
```
Duplicate detection is EXIF-based (timestamp + extension + file size). Re-ingesting the same memory card is safe — duplicates are skipped and logged, never overwritten.

**New Event** — builds a full client event folder structure from a form inside the app. Pick shoot type (Wedding, Corporate, Musician, etc.), enter the client name and date, and it creates:
```
Events/2026/2026-03-08_Smith-Jones_Wedding/
  0001_SMITH-JONES_Prenuptials_2026-03-08/
    Completed/Best Images/
    Unedited RAWs/
    _SESSION-INFO.md
  0002_SMITH-JONES_Bridesmaids/
  ...
```
Each session gets a Markdown info file to track client details, crew, equipment, and image counts — readable in Finder without opening any app.

**Organise Event** — you already have a folder with RAWs dumped flat in it? Select it, and the app restructures it in-place. No manual folder creation.

**Update Counts** — silently counts files in your Best Images and Unedited RAWs folders and writes the numbers back into the session info file. Runs in the background.

**Split JPGs** — moves JPGs out of your Events/Personal folders into a separate destination. Useful if your camera shoots RAW+JPG and you want to separate them after ingesting.

**Backup** — rsync between your working drive and a backup destination. Drive-to-drive only, nothing leaves your local network.

**Folder browser** — built-in file browser with thumbnail previews. Shows all file types: RAW, JPG, video (MP4, MOV), audio (MP3, WAV), PSD, PDF, docs. Folders sort by most recently modified so active projects float to the top.

---

**What it replaces**

| You were paying for | This does it instead |
|---|---|
| Adobe Bridge (ingest + browse) | Sort Personal + folder browser |
| Photo Mechanic (folder structure) | New Event + Organise Event |
| Lightroom metadata panels | _SESSION-INFO.md per shoot |
| Manual rsync scripts | Backup |

---

**What it is not**

- Not a DAM (no star ratings, no catalogue database)
- Not a culling tool
- The personal photo sorter is image/RAW only (video files aren't EXIF-sortable the same way — that's on the roadmap for contributors to tackle)
- macOS only for now

---

**How to install**

```bash
git clone https://github.com/YOUR_USERNAME/file-sorting-app.git
cd file-sorting-app
bash install.sh
```

That's it. The script handles Python, Homebrew, exiftool, and builds the .app.

Repo: **github.com/YOUR_USERNAME/file-sorting-app**

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
github.com/YOUR_USERNAME/file-sorting-app

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

github.com/YOUR_USERNAME/file-sorting-app

Happy to take feedback on the workflow structure if yours is different.
