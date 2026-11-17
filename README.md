# 🎬 Autonomous YouTube Shorts Engine: Master Directive Architecture

An enterprise-grade, zero-touch autonomous AI video engineering and growth system. Ingests long-form YouTube source content, isolates high-retention segments, engineers viral hook scripts, synthesizes custom voiceovers via VoiceStudio, designs dynamic procedural SFX, masters broadcast audio to -14 LUFS, reframes to 9:16 vertical shorts with kinetic captions, and automates packaging, upload, and scheduled release to YouTube.

---

## 🏗️ Mandatory Directory Architecture

```
antigravity_pipeline/
├── raw_videos/          # Phase 1: Source video & audio captures (up to 1080p MP4)
├── transcripts/         # Phase 2: Whisper word-level timing manifests (*_transcript.json)
├── scripts/             # Phase 3: Hook-engineered voiceover scripts (*_script.json)
├── audio_vo/            # Phase 4: VoiceStudio narration tracks (*_vo.wav, *_vo_words.json)
├── processed_video/     # Phase 5 & 6: 9:16 reframed, captioned, and mixed video assets
├── ready_to_upload/     # Phase 7: Final MP4 packages, thumbnails, and upload manifests
└── assets/
    └── sfx/             # Procedural Whooshes, 808 Impacts, Pops, and Risers
```

---

## ⚡ 7-Phase Execution Pipeline

| Phase | Specialized Agent | Operations |
| :--- | :--- | :--- |
| **Phase 1** | **Scout Agent** (`scout_agent.py`) | Autonomous ingestion via `yt-dlp`. Filters for 24-48h recency, computes view-velocity ($\text{Views} / \text{Age}$) and engagement ratios. Downloads maximum resolution streams (up to 1080p) to `/raw_videos/`. |
| **Phase 2** | **Analyst Agent** (`analyst_agent.py`) | Faster-Whisper word-level timestamping. Evaluates 8kHz audio RMS dynamics and transcript retention metrics to isolate coherent 30–55s segments. Manifests saved to `/transcripts/`. |
| **Phase 3** | **Copywriting Agent** (`copywriting_agent.py`) | **The 0-2 Second Rule:** Rewrites opening lines using psychological loops (*Open Loops, Contrarian Assertions, Direct Callouts*). Eliminates filler, shortens sentences, and saves to `/scripts/`. |
| **Phase 4** | **VoiceStudio Agent** (`voicestudio_agent.py`) | Synthesizes custom-cloned or neural narration via local `VoiceStudio` (`debpalash/VoiceStudio`) CLI/API to `/audio_vo/`. Aligns word timings for kinetic captioning. |
| **Phase 5** | **Editor Agent** (`editor_agent.py`) | Reframes to 1080x1920 (9:16) with blurred-background frame stack. Burns in word-by-word highlighted kinetic captions (Electric Yellow `#00F0FF` at 114% scale pop) + top 3–5 word headline box for the first 2 seconds. Saves to `/processed_video/`. |
| **Phase 6** | **Sound Agent** (`sound_agent.py`) | Procedurally synthesizes SFX into `/assets/sfx/`. Injects timed **808 Impacts** (0.0s), **Whooshes**, **Pops**, and tension **Risers**. Blends VO + SFX + ambient bed (`-24 dB`) mastered to **-14 LUFS** (`loudnorm=I=-14:TP=-1.5:LRA=11`). |
| **Phase 7** | **Publisher Agent** (`publisher_agent.py`) | Packages final MP4 + metadata into `/ready_to_upload/`. Connects to YouTube Data API v3, uploads as `privacyStatus: "private"`, and queues automated ISO 8601 release timestamp (`publishAt`). |

---

## 🚀 Execution Commands

Navigate to the pipeline root:
```bash
cd ~/antigravity_pipeline
```

### 1. Single Autonomous Cycle
```bash
python3 main_engine.py --once
```

### 2. Continuous 24/7 Background Scheduler (Scans every hour)
```bash
python3 main_engine.py --daemon --interval 3600
```

### 3. Ingest and Process a Specific Video URL
```bash
python3 main_engine.py --url "https://www.youtube.com/watch?v=EXAMPLE_ID"
```

---

## 🔑 YouTube Data API v3 Authentication (Optional)

To enable zero-touch automatic YouTube uploads & scheduling:
1. Place your Google Cloud OAuth client credentials in:
   `~/antigravity_pipeline/client_secrets.json`
2. On first run, the Publisher Agent opens a local browser authentication flow and caches your token in `youtube_token.json`.
3. Videos are uploaded with `privacyStatus: "private"` and scheduled for release via `publishAt`. If no credentials are provided, finalized packages are cleanly queued in `/ready_to_upload/`.
