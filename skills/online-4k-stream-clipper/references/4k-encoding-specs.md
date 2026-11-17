# 4K Vertical Video Encoding & Mastering Specifications

## 1. Resolution & Canvas Modes
YouTube Shorts natively supports up to 2160x3840 (4K Vertical) and 1080x1920 (FHD Vertical).

### Mode A: Pristine 4K Vertical (2160x3840)
- Canvas: 2160x3840, 60fps or source fps.
- Bitrate: 35–45 Mbps (H.264) or 22–30 Mbps (H.265 / HEVC).
- Ideal for high-end gaming, cinematic trailers, and premium creators.

### Mode B: 4K Supersampled FHD (1080x1920)
- Input: Sliced 4K source (3840x2160).
- Scale / Crop: Center crop `2160x2160` downsampled to `1080x1080` with blurred 4K background stacked underneath.
- Result: Far superior sharpness and texture definition compared to native 1080p source downloads due to downsampling from 4K chroma.

## 2. Hardware Acceleration on macOS
- FFmpeg on Apple Silicon / macOS supports native hardware encoders:
  - `-c:v h264_videotoolbox -b:v 30M`
  - `-c:v hevc_videotoolbox -b:v 20M`
- Renders 4K 60fps in real-time (~2-4 seconds for a 30s clip).

## 3. Kinetic Subtitle Typography at 4K vs 1080p
- In 4K (2160x3840):
  - Font size: `140pt - 160pt` Arial Black.
  - Safe margin bottom: `960px` (above bottom 25% UI bar).
  - Safe margin top: `440px` (below top header).
- In 1080p (1080x1920):
  - Font size: `72pt - 80pt` Arial Black.
  - Safe margin bottom: `480px`.
  - Safe margin top: `220px`.
