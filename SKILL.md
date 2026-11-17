---
name: autonomous-shorts-engine
description: Autonomous, zero-touch YouTube Shorts discovery, clipping, VO scriptwriting, VoiceStudio narration, programmatic SFX, 9:16 kinetic captions, and automated scheduling engine.
---

# Autonomous YouTube Shorts Engine

An enterprise-grade autonomous pipeline that discovers trending long-form YouTube content, isolates high-retention moments, writes aggressive 0-2s hooks, synthesizes VoiceStudio narration tracks, mixes programmatic sound effects (808 Impacts, Whooshes, Pops, Risers) mastered to -14 LUFS, reframes to 9:16 vertical shorts with kinetic captions, and exports or schedules them directly to YouTube.

## Quick Start

```bash
# Single autonomous discovery and clipping cycle
python3 main_engine.py --once

# Continuous 24/7 background scheduler (hourly scans)
python3 main_engine.py --daemon --interval 3600

# Ingest and process a specific long-form URL
python3 main_engine.py --url "https://www.youtube.com/watch?v=EXAMPLE_ID"
```

## Directory Structure
- `raw_videos/`: Maximum resolution source stream captures (up to 1080p MP4)
- `transcripts/`: Whisper word-level timing manifests
- `scripts/`: Hook-engineered spoken scripts
- `audio_vo/`: VoiceStudio synthesized narration tracks
- `processed_video/`: 9:16 vertical reframed, captioned, and mixed video assets
- `ready_to_upload/`: Final master encoded MP4 packages, thumbnails, and metadata
- `assets/sfx/`: Procedural Whooshes, 808 Impacts, Pops, and Risers
