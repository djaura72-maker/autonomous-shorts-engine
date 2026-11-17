#!/usr/bin/env python3
"""
Download YouTube videos, VODs, or livestreams with yt-dlp and fetch live chat replay.
"""
import argparse
import json
import os
import subprocess
import sys

def download_video(url: str, out_dir: str, section: str = None, cookies_browser: str = None):
    os.makedirs(out_dir, exist_ok=True)
    out_template = os.path.join(out_dir, "source.%(ext)s")
    info_path = os.path.join(out_dir, "info.json")
    
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "--output", out_template,
        "--no-playlist"
    ]
    
    if cookies_browser:
        cmd.extend(["--cookies-from-browser", cookies_browser])
        
    if section:
        cmd.extend(["--download-sections", f"*{section}"])
        
    cmd.append(url)
    
    print(f"📥 Downloading source: {url}")
    print(f"   Target directory: {out_dir}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ yt-dlp download failed with code {e.returncode}")
        return False
        
    # Attempt live chat replay download if available
    chat_cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--sub-langs", "live_chat",
        "--output", os.path.join(out_dir, "chat.%(ext)s"),
        url
    ]
    if cookies_browser:
        chat_cmd.extend(["--cookies-from-browser", cookies_browser])
        
    try:
        subprocess.run(chat_cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(os.path.join(out_dir, "chat.live_chat.json")):
            os.rename(os.path.join(out_dir, "chat.live_chat.json"), os.path.join(out_dir, "chat.json"))
            print("💬 Saved live chat replay: chat.json")
    except Exception:
        pass
        
    source_mp4 = os.path.join(out_dir, "source.mp4")
    if os.path.exists(source_mp4):
        print(f"✅ Download complete: {source_mp4}")
        return True
    else:
        # Check if downloaded with another extension
        for f in os.listdir(out_dir):
            if f.startswith("source.") and not f.endswith(".json"):
                print(f"✅ Download complete: {os.path.join(out_dir, f)}")
                return True
        print("❌ Could not find downloaded source video file.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download YouTube source for clipping")
    parser.add_argument("url", help="YouTube video or livestream URL")
    parser.add_argument("--out", default="work/source", help="Output directory")
    parser.add_argument("--section", help="Section to download, e.g. 00:15:00-00:30:00")
    parser.add_argument("--cookies-from-browser", help="e.g. chrome, safari, brave")
    args = parser.parse_args()
    
    ok = download_video(args.url, args.out, args.section, args.cookies_from_browser)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
