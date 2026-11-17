# Online 4K Video & Live Stream Clipping Architecture

## 1. Why Downloading Full 4K Streams Fails
- A 2-hour 4K (2160p) stream ranges from **20 GB to 80 GB**.
- Downloading the entire file causes:
  1. 10 to 45 minute waiting times.
  2. Severe network throttling and IP bans from video platforms.
  3. Disk exhaustion on local machines.

## 2. Zero-Download Moment Discovery
Instead of downloading gigabytes of video to find clips:
1. **Instant Subtitle / Transcript Ingestion:**
   Fetch automated captions using `yt-dlp --write-auto-sub --sub-langs "en.*" --skip-download`. This downloads a **~50 KB** JSON/VTT manifest in **0.8 seconds**.
2. **Audio-Only Stream Ingestion (Fallback):**
   If no subtitles exist, pipe only the low-bitrate AAC/Opus audio track (`-f "ba[ext=m4a]"`) into Whisper. Transcribing 100MB of audio is 50x faster than handling a 25GB 4K video.
3. **Live Chat Density Velocity:**
   Extract live chat replay (`--sub-langs live_chat`) to detect chat spam peaks (LMAO, OMG, W, ???, CLUTCH).

## 3. Targeted Remote Slicing (Byte-Range & Fragmented DASH/HLS)
Once timestamps are located (e.g. `00:14:15` to `00:14:55`):
- `yt-dlp --download-sections "*00:14:15-00:14:55" -f "bestvideo[height<=2160]+bestaudio/best"` downloads **ONLY** the specified 40-second window in native 4K (3840x2160).
- Data transferred: **~120 MB** instead of **35,000 MB** (99.7% bandwidth and time savings).

## 4. Live Stream Clipping (Active Broadcasts)
- When a stream is currently live, platforms use HTTP Live Streaming (HLS) with rotating media playlists (`.m3u8`).
- Using `--live-from-start` with section slicing allows extracting historical segments from an ongoing stream while the streamer is still broadcasting.
