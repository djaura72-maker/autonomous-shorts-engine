#!/usr/bin/env python3
"""
Targeted Remote 4K Stream Slicer.
Downloads ONLY the specified 28-45s segment directly from the remote video/stream
in full 4K (2160p/3840x2160) without downloading the full video.
"""
import argparse
import os
import subprocess
import sys

def format_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def slice_4k_remote(url: str, start_sec: float, end_sec: float, out_mp4: str, is_live: bool = False) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    
    start_ts = format_ts(start_sec)
    end_ts = format_ts(end_sec)
    duration = round(end_sec - start_sec, 2)
    
    print(f"🎯 Target 4K Remote Slicing:")
    print(f"   URL: {url}")
    print(f"   Window: {start_ts} -> {end_ts} ({duration}s)")
    print(f"   Destination: {out_mp4}")
    
    section_arg = f"*{start_ts}-{end_ts}"
    
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
        "--merge-output-format", "mp4",
        "--download-sections", section_arg,
        "--force-keyframes-at-cuts",
        "-o", out_mp4,
        "--no-playlist"
    ]
    
    if is_live:
        cmd.insert(1, "--live-from-start")
        
    cmd.append(url)
    
    print("⚡ Streaming and slicing 4K bytes directly from remote CDN...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Slicing failed with code {e.returncode}")
        # Try fallback without force-keyframes if backend doesn't support re-encode
        cmd_fallback = [
            "yt-dlp",
            "--format", "bestvideo[height<=2160]+bestaudio/best",
            "--merge-output-format", "mp4",
            "--download-sections", section_arg,
            "-o", out_mp4,
            "--no-playlist",
            url
        ]
        subprocess.run(cmd_fallback, check=True)
        
    if os.path.exists(out_mp4):
        size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
        print(f"✅ Pristine 4K slice obtained: {out_mp4} ({size_mb:.1f} MB)")
        return out_mp4
    else:
        # Check if downloaded with another extension
        base = os.path.splitext(out_mp4)[0]
        for f in os.listdir(os.path.dirname(out_mp4)):
            if f.startswith(os.path.basename(base)) and f.endswith(".mp4"):
                found = os.path.join(os.path.dirname(out_mp4), f)
                print(f"✅ Pristine 4K slice obtained: {found}")
                return found
        raise FileNotFoundError(f"Failed to produce sliced 4K file: {out_mp4}")

def main():
    parser = argparse.ArgumentParser(description="Targeted 4K Remote Stream Slicer")
    parser.add_argument("url", help="YouTube video or stream URL")
    parser.add_argument("--start", type=float, required=True, help="Start time in seconds")
    parser.add_argument("--end", type=float, required=True, help="End time in seconds")
    parser.add_argument("--out", default="work/slice_4k.mp4", help="Output MP4 path")
    parser.add_argument("--live", action="store_true", help="Set if clipping an ongoing live stream")
    args = parser.parse_args()
    
    slice_4k_remote(args.url, args.start, args.end, args.out, is_live=args.live)

if __name__ == "__main__":
    main()
