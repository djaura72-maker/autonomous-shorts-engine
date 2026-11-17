#!/usr/bin/env python3
"""
Find high-engagement moments in GTA VI content.
Combines audio loudness spikes, speech excitement, and chat velocity.
Enforces strict 28-45s duration and word-boundary snapping with +0.3s cutoff pad.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import numpy as np

def analyze_audio_spikes(video_path: str, chunk_sec: float = 1.0) -> list[float]:
    """Calculate RMS volume envelope across 1s chunks."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        samples = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32)
        chunk_size = int(8000 * chunk_sec)
        num_chunks = len(samples) // chunk_size
        
        rms_list = []
        for i in range(num_chunks):
            chunk = samples[i * chunk_size : (i + 1) * chunk_size]
            rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
            rms_list.append(rms)
        return rms_list
    except Exception as e:
        print(f"⚠️  Audio spike analysis warning: {e}")
        return []

def analyze_chat_velocity(chat_path: str, duration_sec: float, chunk_sec: float = 1.0) -> list[int]:
    """Calculate chat message density per second."""
    if not os.path.exists(chat_path):
        return [0] * int(duration_sec // chunk_sec + 1)
        
    num_chunks = int(duration_sec // chunk_sec + 1)
    velocity = [0] * num_chunks
    try:
        with open(chat_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    offset_usec = int(data.get("replayChatItemAction", {})
                                     .get("actions", [{}])[0]
                                     .get("addChatItemAction", {})
                                     .get("item", {})
                                     .get("liveChatTextMessageRenderer", {})
                                     .get("timestampUsec", 0))
                    # Map to chunk
                    idx = int((offset_usec / 1_000_000) // chunk_sec)
                    if 0 <= idx < num_chunks:
                        velocity[idx] += 1
                except Exception:
                    continue
    except Exception:
        pass
    return velocity

def find_candidate_clips(work_dir: str, min_dur: float = 28.0, max_dur: float = 45.0, top_n: int = 5):
    transcript_path = os.path.join(work_dir, "transcript.json")
    video_path = os.path.join(work_dir, "source.mp4")
    chat_path = os.path.join(work_dir, "chat.json")
    
    if not os.path.exists(transcript_path):
        print(f"❌ Missing transcript: {transcript_path}")
        return []
        
    with open(transcript_path, "r", encoding="utf-8") as f:
        tdata = json.load(f)
        
    total_dur = tdata.get("duration", 0.0)
    all_words = []
    for s in tdata.get("segments", []):
        for w in s.get("words", []):
            all_words.append(w)
            
    if not all_words:
        print("❌ No word-level timestamps in transcript.")
        return []
        
    rms_envelope = analyze_audio_spikes(video_path) if os.path.exists(video_path) else []
    chat_envelope = analyze_chat_velocity(chat_path, total_dur)
    
    # Slide across word groups to build 28-45s candidates
    candidates = []
    
    i = 0
    while i < len(all_words):
        start_word = all_words[i]
        start_time = max(0.0, start_word["start"] - 0.1)
        
        # Seek words to hit min_dur <= dur <= max_dur
        best_end_word = None
        for j in range(i + 1, len(all_words)):
            w = all_words[j]
            dur = w["end"] - start_time
            if dur >= min_dur and dur <= max_dur:
                # Prioritize sentence endings
                if re.search(r"[.!?]$", w["word"]) or dur >= 35.0:
                    best_end_word = w
                    break
            elif dur > max_dur:
                break
                
        if best_end_word:
            end_time = round(best_end_word["end"] + 0.35, 2)  # At least 0.3s after final word
            dur = round(end_time - start_time, 2)
            
            # Score this window
            start_s = int(start_time)
            end_s = int(end_time)
            
            # 1. Loudness score
            rms_score = 0.0
            if rms_envelope and len(rms_envelope) > start_s:
                window_rms = rms_envelope[start_s : min(len(rms_envelope), end_s)]
                if window_rms:
                    rms_score = float(np.mean(window_rms))
                    
            # 2. Chat score
            chat_score = 0.0
            if chat_envelope and len(chat_envelope) > start_s:
                window_chat = chat_envelope[start_s : min(len(chat_envelope), end_s)]
                if window_chat:
                    chat_score = float(np.sum(window_chat))
                    
            # 3. Speech velocity & emotional words
            clip_words = [w["word"] for w in all_words if start_time <= w["start"] <= end_time]
            speech_rate = len(clip_words) / dur if dur > 0 else 0
            
            text_str = " ".join(clip_words)
            excitement_bonus = 0.0
            for kw in ["gta", "insane", "crazy", "secret", "rockstar", "look", "omg", "leak", "mission", "cops"]:
                if kw in text_str.lower():
                    excitement_bonus += 1.5
                    
            total_score = round(rms_score * 0.001 + chat_score * 0.5 + speech_rate * 2.0 + excitement_bonus, 2)
            
            candidates.append({
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "duration": dur,
                "score": total_score,
                "text": text_str[:120] + "..." if len(text_str) > 120 else text_str
            })
            
            # Step forward ~15s to find diverse moments
            i += max(15, int(dur * 2.0))
        else:
            i += 10
            
    # Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = candidates[:top_n]
    
    # Format into clips.json
    clips = []
    for idx, c in enumerate(selected, 1):
        # Generate hook headline
        words = c["text"].split()
        hook_headline = " ".join(words[:4]).upper().replace(".", "").replace(",", "")
        if len(hook_headline) < 8:
            hook_headline = "THE GTA 6 TRUTH"
            
        clips.append({
            "id": idx,
            "start": c["start"],
            "end": c["end"],
            "duration": c["duration"],
            "hook": hook_headline,
            "title": f"The Untold Truth in GTA 6 #shorts",
            "reason": f"High retention score: {c['score']}",
            "score": c["score"],
            "text": c["text"]
        })
        
    clips_path = os.path.join(work_dir, "clips.json")
    with open(clips_path, "w", encoding="utf-8") as f:
        json.dump(clips, f, indent=2)
        
    print(f"✅ Found {len(clips)} candidate clips (28-45s duration snapped to word boundaries):")
    for cp in clips:
        print(f"  #{cp['id']}: [{cp['start']}s -> {cp['end']}s] ({cp['duration']}s) Hook: {cp['hook']} | Score: {cp['score']}")
    print(f"💾 Saved to: {clips_path}")
    return clips

def main():
    parser = argparse.ArgumentParser(description="Find high-engagement 28-45s GTA VI clips")
    parser.add_argument("work_dir", help="Work directory containing source.mp4 and transcript.json")
    parser.add_argument("--top", type=int, default=5, help="Number of clips to select")
    args = parser.parse_args()
    
    find_candidate_clips(args.work_dir, top_n=args.top)

if __name__ == "__main__":
    main()
