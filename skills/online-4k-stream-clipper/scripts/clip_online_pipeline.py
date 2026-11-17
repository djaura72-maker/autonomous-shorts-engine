#!/usr/bin/env python3
"""
Master Online 4K Video & Live Stream Clipper.
Runs the entire zero-download pipeline:
1. Online transcript extraction in seconds
2. High-retention moment scoring
3. Targeted 4K remote segment slicing (transfers only ~80MB instead of 40GB)
4. Hardware-accelerated 9:16 vertical render with kinetic captions and -14 LUFS mastering.
"""
import argparse
import json
import os
import sys

from fetch_transcript_online import fetch_online_captions, fallback_audio_whisper
from find_moments_online import find_viral_segments
from slice_4k_remote import slice_4k_remote
from render_4k_vertical import render_vertical

def clip_online(url: str, out_dir: str = "output_shorts", top_n: int = 1, mode: str = "1080p", is_live: bool = False):
    os.makedirs(out_dir, exist_ok=True)
    work_dir = os.path.join(out_dir, "manifests")
    os.makedirs(work_dir, exist_ok=True)
    
    print("="*65)
    print("🚀 ONLINE 4K STREAM CLIPPER INITIATED")
    print(f"   Target URL: {url}")
    print(f"   Mode: {mode.upper()} 9:16 Vertical | Live Broadcast: {is_live}")
    print("="*65)
    
    # 1. Zero-download transcript
    ok, transcript_path = fetch_online_captions(url, work_dir)
    if not ok:
        transcript_path = fallback_audio_whisper(url, work_dir)
        
    # 2. Score viral moments
    clips = find_viral_segments(transcript_path, top_n=top_n)
    if not clips:
        print("❌ No valid moments found.")
        return []
        
    rendered_shorts = []
    
    for c in clips:
        clip_id = c["id"]
        start_t = c["start"]
        end_t = c["end"]
        hook = c["hook"]
        
        print("\n" + "-"*60)
        print(f"🎬 Processing Clip #{clip_id}: {hook}")
        print(f"   Window: {start_t}s -> {end_t}s ({c['duration']}s)")
        print("-"*60)
        
        # 3. Targeted 4K remote slice
        slice_path = os.path.join(work_dir, f"slice_4k_{clip_id:02d}.mp4")
        slice_4k_remote(url, start_t, end_t, slice_path, is_live=is_live)
        
        # 4. Render vertical short
        out_short = os.path.join(out_dir, f"short_{clip_id:02d}.mp4")
        
        # Extract clip-relative words
        words = []
        with open(transcript_path, "r", encoding="utf-8") as f:
            tdata = json.load(f)
        for s in tdata.get("segments", []):
            for w in s.get("words", []):
                if w["start"] >= start_t and w["end"] <= end_t:
                    words.append({
                        "word": w["word"],
                        "start": round(w["start"] - start_t, 3),
                        "end": round(w["end"] - start_t, 3)
                    })
                    
        render_vertical(slice_path, out_short, words, hook_text=hook, mode=mode)
        rendered_shorts.append(out_short)
        
    print("\n" + "="*65)
    print(f"🎉 COMPLETED: Rendered {len(rendered_shorts)} 4K-sourced Vertical Shorts!")
    for s in rendered_shorts:
        print(f"  👉 {s}")
    print("="*65)
    return rendered_shorts

def main():
    parser = argparse.ArgumentParser(description="Online 4K Stream Clipper Pipeline")
    parser.add_argument("url", help="YouTube video or live stream URL")
    parser.add_argument("--out", default="output_shorts", help="Output directory")
    parser.add_argument("--top", type=int, default=1, help="Number of shorts to generate")
    parser.add_argument("--mode", choices=["4k", "1080p"], default="1080p", help="Output canvas mode")
    parser.add_argument("--live", action="store_true", help="Set for live broadcasts")
    args = parser.parse_args()
    
    clip_online(args.url, args.out, top_n=args.top, mode=args.mode, is_live=args.live)

if __name__ == "__main__":
    main()
