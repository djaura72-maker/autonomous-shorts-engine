#!/usr/bin/env python3
"""
Zero-Download Online Caption / Transcript Ingestion.
Extracts YouTube automated subtitles in under 2 seconds without downloading video.
Falls back to streaming low-bitrate audio directly into Whisper if no captions exist.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

def parse_vtt_timestamps(vtt_path: str) -> list[dict]:
    """Parse WebVTT subtitle file into clean timed segments."""
    segments = []
    time_pat = re.compile(r"(\d{2}:)?(\d{2}):(\d{2})\.(\d{3})\s+-->\s+(\d{2}:)?(\d{2}):(\d{2})\.(\d{3})")
    
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    blocks = content.split("\n\n")
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
            
        time_match = None
        text_lines = []
        for line in lines:
            m = time_pat.search(line)
            if m:
                time_match = line
            elif not line.startswith("NOTE") and not line.isdigit() and "WEBVTT" not in line:
                # Strip HTML tags
                clean_line = re.sub(r"<[^>]+>", "", line).strip()
                if clean_line:
                    text_lines.append(clean_line)
                    
        if time_match and text_lines:
            # Parse start and end in seconds
            parts = time_match.split("-->")
            s_str = parts[0].strip()
            e_str = parts[1].strip().split()[0]
            
            def to_secs(ts):
                p = ts.split(":")
                if len(p) == 3:
                    return float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])
                return float(p[0]) * 60 + float(p[1])
                
            start = to_secs(s_str)
            end = to_secs(e_str)
            text = " ".join(text_lines)
            
            # De-duplicate consecutive identical lines common in rolling auto-subs
            if segments and segments[-1]["text"] == text:
                segments[-1]["end"] = max(segments[-1]["end"], end)
            else:
                segments.append({
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "text": text
                })
                
    return segments

def fetch_online_captions(url: str, out_dir: str) -> tuple[bool, str]:
    os.makedirs(out_dir, exist_ok=True)
    out_template = os.path.join(out_dir, "subs.%(ext)s")
    
    print(f"⚡ Fetching instant subtitles without downloading video: {url}")
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-langs", "en.*,en",
        "--sub-format", "vtt",
        "--output", out_template,
        url
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    vtt_files = glob.glob(os.path.join(out_dir, "subs*.vtt"))
    
    if vtt_files:
        vtt_path = vtt_files[0]
        segments = parse_vtt_timestamps(vtt_path)
        json_path = os.path.join(out_dir, "transcript.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"source": "online_captions", "segments": segments}, f, indent=2)
            
        txt_path = os.path.join(out_dir, "transcript.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for s in segments:
                m_start = int(s["start"] // 60)
                s_start = int(s["start"] % 60)
                f.write(f"[{m_start:02d}:{s_start:02d}] {s['text']}\n")
                
        print(f"✅ Instant transcript fetched ({len(segments)} segments) in <1 second!")
        print(f"   Manifest: {json_path}")
        return True, json_path
    else:
        print("ℹ️  No automated subtitles found on remote stream. Falling back to low-bitrate audio transcription...")
        return False, ""

def fallback_audio_whisper(url: str, out_dir: str):
    """Downloads audio-only stream (~1MB/min) and transcribes with faster-whisper."""
    os.makedirs(out_dir, exist_ok=True)
    audio_path = os.path.join(out_dir, "audio.m4a")
    
    print("🎧 Downloading lightweight audio track only...")
    cmd = [
        "yt-dlp",
        "-f", "ba[ext=m4a]/ba",
        "-o", audio_path,
        url
    ]
    subprocess.run(cmd, check=True)
    
    from faster_whisper import WhisperModel
    import numpy as np
    
    print("🎙️  Running faster-whisper on lightweight audio stream...")
    pcmd = ["ffmpeg", "-v", "error", "-i", audio_path, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    res = subprocess.run(pcmd, stdout=subprocess.PIPE, check=True)
    audio_arr = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segs, info = model.transcribe(audio_arr, word_timestamps=True, vad_filter=False)
    
    segments = []
    txt_lines = []
    for s in segs:
        words = []
        if s.words:
            for w in s.words:
                words.append({"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)})
        segments.append({
            "start": round(s.start, 2),
            "end": round(s.end, 2),
            "text": s.text.strip(),
            "words": words
        })
        m = int(s.start // 60)
        sec = int(s.start % 60)
        txt_lines.append(f"[{m:02d}:{sec:02d}] {s.text.strip()}")
        
    json_path = os.path.join(out_dir, "transcript.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"source": "whisper_audio_only", "segments": segments}, f, indent=2)
        
    txt_path = os.path.join(out_dir, "transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")
        
    print(f"✅ Audio-only Whisper transcription complete: {json_path}")
    return json_path

def main():
    parser = argparse.ArgumentParser(description="Fetch Instant Online Captions / Transcript")
    parser.add_argument("url", help="YouTube video or stream URL")
    parser.add_argument("--out", default="work/remote", help="Output directory")
    args = parser.parse_args()
    
    ok, path = fetch_online_captions(args.url, args.out)
    if not ok:
        fallback_audio_whisper(args.url, args.out)

if __name__ == "__main__":
    main()
