#!/usr/bin/env python3
"""
Transcribe video with faster-whisper and output word-level timestamps.
"""
import argparse
import json
import os
import subprocess
import sys
import numpy as np
from faster_whisper import WhisperModel

def transcribe_audio(video_path: str, model_size: str = "base", language: str = None) -> tuple[dict, str]:
    work_dir = os.path.dirname(os.path.abspath(video_path))
    json_path = os.path.join(work_dir, "transcript.json")
    txt_path = os.path.join(work_dir, "transcript.txt")
    
    print(f"🎙️  Extracting and transcribing audio: {video_path}")
    print(f"   Model: {model_size} | Language: {language or 'auto'}")
    
    # Extract 16kHz mono PCM directly via FFmpeg to avoid PyAV metadata issues
    cmd = [
        "ffmpeg", "-v", "error", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    raw_audio = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    
    print(f"   Audio duration: {len(raw_audio) / 16000.0:.1f}s")
    
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        raw_audio,
        word_timestamps=True,
        language=language,
        vad_filter=False
    )
    
    results = {
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "segments": []
    }
    
    txt_lines = []
    
    for seg in segments:
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
                })
        seg_data = {
            "id": seg.id,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": words
        }
        results["segments"].append(seg_data)
        
        m_start = int(seg.start // 60)
        s_start = int(seg.start % 60)
        txt_lines.append(f"[{m_start:02d}:{s_start:02d}] {seg.text.strip()}")
        
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")
        
    print(f"✅ Transcribed {len(results['segments'])} segments")
    print(f"   JSON manifest: {json_path}")
    print(f"   Text summary: {txt_path}")
    return results, json_path

def main():
    parser = argparse.ArgumentParser(description="Word-level Whisper Transcription")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--model", default="base", help="tiny, base, small, medium, large-v3")
    parser.add_argument("--language", help="Optional language code (e.g. en, hi)")
    args = parser.parse_args()
    
    if not os.path.exists(args.video):
        print(f"❌ File not found: {args.video}")
        sys.exit(1)
        
    transcribe_audio(args.video, args.model, args.language)

if __name__ == "__main__":
    main()
