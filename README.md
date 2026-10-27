# 🎬 Tenglish Auto Caption Generator

> Automatically generate natural **Tenglish** subtitles (*Telugu spoken language written using English letters*) for uploaded videos using **local OpenAI Whisper AI**, **FFmpeg**, and an intelligent **Telugu transliteration engine**.
> **100% Free, Private, and Offline-Ready** — Zero paid API keys, zero external subscription dependencies.

---

## 🌟 Key Features

1. **Video Ingest & Validation**
   - Supports **MP4**, **MOV**, **WebM**, and **MKV** formats up to 500 MB.
   - Drag-and-drop upload zone with file validation and size checking.
   - Built-in **"Try Sample Video"** button for immediate 1-click testing with spoken Telugu.

2. **Local Speech Recognition (OpenAI Whisper)**
   - Runs locally on your machine (CPU or NVIDIA GPU).
   - Word-level timestamps for accurate subtitle synchronization.
   - Supports selectable models:
     - `tiny` (~75 MB) – ultra fast transcription
     - `base` (~140 MB, recommended default) – great balance of speed and Telugu acoustic accuracy
     - `small` (~460 MB) – higher accuracy for complex audio

3. **Natural Tenglish Conversion Engine**
   - Converts Telugu script into readable conversational Roman script (e.g., *"Manam ippudu Python nerchukundam"* instead of academic/awkward uppercase ITRANS like `nErcukundAM`).
   - **Smart English Word Preservation**: Automatically identifies and preserves English technical & colloquial loanwords (e.g., *Python, coding, website, software, YouTube, developer, project, video, subscribe, like, share, etc.*).
   - **Mode Switcher**: Instant switching between **Tenglish** (English letters), **Telugu Script** (తెలుగు), and **English**.

4. **Live Interactive Caption Editor**
   - HTML5 video player with real-time subtitle overlay sync.
   - Editable subtitle segment timeline: adjust start/end timestamps, edit caption text, add new segments, or delete segments.
   - **Replay Segment** button to instantly scrub and listen to any phrase.

5. **Reels-Style Captions & Preset Styles**
   - **✨ Reels Karaoke Highlight**: Words bounce and illuminate dynamically as they are spoken.
   - **🔥 Viral Yellow**: High-contrast bold yellow font with heavy black outline.
   - **🎬 Netflix Classic**: Elegant white text with subtle cinema drop shadows.
   - **💜 Neon Glow**: Glowing purple/cyan aesthetics.
   - **⬛ Minimal Box**: Clean semi-transparent dark background card.
   - Full customization: Font family, size, primary color, highlight color, and vertical position (Bottom / Center / Top).

6. **Flexible Multi-Format Exports**
   - Instant download of standard **SRT** (`.srt`) and WebVTT (`.vtt`) subtitle files.
   - **Hardcoded / Burned Video Export**: FFmpeg embeds styled ASS subtitles directly into the video stream for Instagram Reels, YouTube Shorts, and TikTok.

---

## 🏗️ Architecture & Technology Stack

```
AI Captions/
├── backend/
│   ├── app/
│   │   ├── config.py              # Directory paths, upload limits, FFmpeg detection & setup
│   │   ├── main.py                # FastAPI app entry point, CORS, routes & static mounts
│   │   ├── api/
│   │   │   ├── routes.py          # /api/upload, /api/status, /api/job, /api/export
│   │   │   └── schemas.py         # Pydantic validation schemas
│   │   ├── speech/
│   │   │   ├── audio_extractor.py # 16kHz mono WAV extraction via FFmpeg
│   │   │   └── whisper_engine.py  # Local Whisper runner with resumable model downloader
│   │   ├── transliteration/
│   │   │   ├── tenglish_engine.py # Natural Telugu-to-Tenglish phonetics & word converter
│   │   │   └── english_dict.py    # Loanword dictionary (tech & media terminology)
│   │   ├── video/
│   │   │   ├── ass_builder.py     # ASS subtitle generator with karaoke word styling
│   │   │   └── ffmpeg_subtitles.py# Safe FFmpeg subtitle burner and SRT/VTT formatter
│   │   └── jobs/
│   │       └── job_manager.py     # Background job tracking and state persistence
│   ├── tests/
│   │   ├── test_workflow.py       # End-to-end integration test
│   │   └── test_api_workflow.py   # Full HTTP API integration test
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── index.html                 # Modern Single Page Application (Landing, Processing, Editor)
│   ├── css/
│   │   ├── style.css              # Dark theme with purple accents, glassmorphism, responsive
│   │   └── editor.css             # Video player layout, live overlay, and timeline styling
│   └── js/
│       ├── app.js                 # App router, status polling, toast notifications
│       ├── uploader.js            # Drag & drop, validation, sample video loader
│       ├── editor.js              # Real-time subtitle sync, timeline editing, mode switcher
│       ├── styles.js              # Caption presets and styling manager
│       └── exporter.js            # SRT/VTT downloads and video burning modal
├── bin/                           # Local FFmpeg binary (automatically configured)
├── samples/                       # Bundled Telugu spoken test video
├── uploads/                       # Job-scoped temporary video processing folders
├── exports/                       # Rendered captioned videos
├── run.py                         # One-click launcher
└── README.md
```

---

## 🚀 Windows Installation & Quick Start

### 1. Prerequisites
- **Windows 10 or 11**
- **Python 3.10+** (Tested on Python 3.12, 3.13, and 3.14-64)
- An active internet connection for the very first run (to download the free Whisper model; subsequent runs are 100% offline).

### 2. Install Dependencies
Open **PowerShell** or **Command Prompt** in the project directory:

```powershell
pip install -r backend/requirements.txt
```

> **Note on FFmpeg**: You do **not** need to manually install FFmpeg. The project includes `imageio-ffmpeg` which automatically sets up a full static FFmpeg binary in `bin/ffmpeg.exe` and adds it to your environment PATH on first run.

### 3. Launch the Application
Run the one-click launcher:

```powershell
python run.py
```

The launcher will verify your environment, detect FFmpeg, ensure all directories are configured, and start the local server:

```text
=================================================================
  [*] Tenglish Auto Caption Generator (Telugu -> English Script)
=================================================================
[*] Project Root    : C:\Users\kisho\Desktop\AI Captions
[*] FFmpeg Binary   : C:\Users\kisho\Desktop\AI Captions\bin\ffmpeg.exe
[*] Uploads Dir     : C:\Users\kisho\Desktop\AI Captions\uploads
[*] Exports Dir     : C:\Users\kisho\Desktop\AI Captions\exports
[*] Frontend Static : C:\Users\kisho\Desktop\AI Captions\frontend
-----------------------------------------------------------------
[+] Starting server at http://127.0.0.1:8000
    Open http://127.0.0.1:8000 in your web browser.
=================================================================
```

### 4. Open in Your Browser
Navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🎯 Step-by-Step Usage Guide

### Testing with Bundled Sample Video
1. On the landing page, click **"Load Spoken Telugu Sample Video"** or **"Try Sample Video"** in the top navigation bar.
2. The bundled Telugu spoken video will load instantly.
3. Click **"Generate Tenglish Subtitles"**.
4. Watch the progress stepper (Extracting Audio → Whisper Speech Recognition → Tenglish Transliteration → Synchronization).
5. The web app automatically opens the **Caption Editor**.
6. Press the **Play** button: see live Tenglish subtitles synchronized with the video, complete with karaoke word highlighting!

### Uploading Your Own Video
1. Drag and drop any **MP4**, **MOV**, or **WebM** file onto the dropzone.
2. Select your preferred Whisper model:
   - `tiny`: Fastest (~5 seconds for short videos)
   - `base`: Recommended balance (High accuracy, preserves English technical terms)
   - `small`: Best for noisy audio or fast speech
3. Click **"Generate Tenglish Subtitles"**.

### Customizing & Exporting Captions
1. **Mode Switching**: Click the tabs above the editor to toggle between `✨ Tenglish`, `తెలుగు Script`, or `English`.
2. **Editing**: Click any subtitle text to edit words, or adjust the start/end timestamp numbers.
3. **Style Presets**: Choose between **Reels Highlight**, **Viral Yellow**, **Netflix Classic**, **Neon Glow**, or **Minimal Box**.
4. **Export Subtitles**: Click **SRT** or **VTT** to download subtitle files for Premiere Pro, DaVinci Resolve, or YouTube.
5. **Burn Video**: Click **"Burn Captions into Video"** to render a permanent MP4 video with embedded subtitles. When rendering finishes, preview it in the modal and click **Download Captioned Video (MP4)**.

---

## 🔬 Honest Limitations & Technical Notes

1. **Telugu-English Mixed Speech (Code-Switching)**
   - Whisper is trained on multilingual acoustic data. When speakers rapidly alternate between Telugu and English, small models like `tiny` may occasionally misrecognize conversational English words as Telugu phonemes or vice versa.
   - **Mitigation applied**: The app conditions Whisper using a targeted `initial_prompt` with conversational Telugu and common tech terms (*Python, coding, website, project*), and applies an acoustic dictionary normalization layer. The `base` and `small` models provide significantly higher consistency.
2. **First-Run Model Download**
   - On the very first run, OpenAI Whisper downloads the selected model weights (~140 MB for `base`). We implemented a **resilient chunked downloader with range resume** so interrupted downloads resume automatically without corruption. Once downloaded, the model is cached locally at `~/.cache/whisper/` and runs completely offline.
3. **Audio Quality**
   - Clear vocal audio without heavy background music produces the most accurate timestamps.
4. **Editable by Design**
   - Because no speech recognition system is 100% flawless on mixed dialects, our **live interactive editor** allows you to correct any word or timestamp in seconds before exporting.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status check |
| `POST` | `/api/upload` | Upload video file (`file`, `whisper_model`, `language`) |
| `GET` | `/api/status/{job_id}` | Poll processing progress and stage message |
| `GET` | `/api/job/{job_id}` | Get full job metadata, segments, and styles |
| `GET` | `/api/job/{job_id}/video` | Stream source video with range request support |
| `POST` | `/api/job/{job_id}/segments` | Save edited subtitle segments |
| `POST` | `/api/job/{job_id}/switch-mode` | Switch mode (`tenglish`, `telugu`, `english`) |
| `GET` | `/api/export/{job_id}/srt` | Download generated SubRip (`.srt`) file |
| `GET` | `/api/export/{job_id}/vtt` | Download generated WebVTT (`.vtt`) file |
| `POST` | `/api/export/{job_id}/burn-video` | Trigger permanent FFmpeg subtitle video burning |
| `GET` | `/api/export/{job_id}/burn-status` | Poll burning progress & get download URL |
| `GET` | `/api/export/{job_id}/download-burned` | Download final captioned MP4 video |

---

## 🧪 Testing

Run the automated test suite to verify the complete pipeline:

```powershell
# 1. Pipeline integration test (Extraction -> Whisper -> Tenglish -> Video Burn)
python backend/tests/test_workflow.py

# 2. Full HTTP API integration test
python backend/tests/test_api_workflow.py
```

---

## 📄 License
Open source and free for personal, educational, and commercial use. Built with OpenAI Whisper, FFmpeg, and FastAPI.
