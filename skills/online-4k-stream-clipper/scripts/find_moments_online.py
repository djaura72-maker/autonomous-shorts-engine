#!/usr/bin/env python3
"""
Find viral moments from lightweight online transcript.
Outputs clips.json with precise start and end times for targeted 4K slicing.
"""
import argparse
import json
import os
import re
import sys

VIRAL_KEYWORDS = [
    "secret", "insane", "crazy", "truth", "revealed", "leaked", "why", "never",
    "mistake", "look at", "watch this", "omg", "shocking", "cheat", "glitch",
    "unbelievable", "huge", "confirmed", "finally", "hidden"
]

def find_viral_segments(transcript_path: str, min_dur: float = 28.0, max_dur: float = 45.0, top_n: int = 5):
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    segments = data.get("segments", [])
    if not segments:
        print("❌ No transcript segments found.")
        return []
        
    candidates = []
    
    i = 0
    while i < len(segments):
        start_seg = segments[i]
        start_time = start_seg["start"]
        
        # Accumulate segments until min_dur <= duration <= max_dur
        acc_text = []
        end_time = start_time
        for j in range(i, len(segments)):
            cur_seg = segments[j]
            acc_text.append(cur_seg["text"])
            end_time = cur_seg["end"]
            dur = end_time - start_time
            if dur >= min_dur:
                break
                
        dur = round(end_time - start_time, 2)
        if dur >= min_dur and dur <= max_dur:
            full_text = " ".join(acc_text)
            
            # Score
            score = 5.0
            text_lower = full_text.lower()
            for kw in VIRAL_KEYWORDS:
                if kw in text_lower:
                    score += 1.5
            if "?" in full_text:
                score += 2.0
            if "!" in full_text:
                score += 1.0
                
            # Words per second (speech density)
            words = full_text.split()
            wps = len(words) / dur if dur > 0 else 0
            if 2.2 <= wps <= 3.8:
                score += 2.0
                
            # Hook line
            first_sentence = full_text.split(".")[0].split("?")[0].strip()
            hook_words = first_sentence.split()[:5]
            hook = " ".join(hook_words).upper()
            if len(hook) < 6:
                hook = "WATCH THIS CAREFULLY"
                
            candidates.append({
                "start": start_time,
                "end": round(end_time + 0.35, 2),  # cushion to prevent mid-sentence cutoff
                "duration": round(end_time + 0.35 - start_time, 2),
                "score": round(score, 2),
                "hook": hook,
                "text": full_text[:120] + "..." if len(full_text) > 120 else full_text
            })
            i += max(1, int(dur // 4))  # slide window
        else:
            i += 1
            
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = candidates[:top_n]
    
    # Format into clips.json
    clips = []
    for idx, c in enumerate(selected, 1):
        clips.append({
            "id": idx,
            "start": c["start"],
            "end": c["end"],
            "duration": c["duration"],
            "hook": c["hook"],
            "score": c["score"],
            "text": c["text"]
        })
        
    out_path = os.path.join(os.path.dirname(transcript_path), "clips.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clips, f, indent=2)
        
    print(f"✅ Found {len(clips)} high-retention clip candidates:")
    for cp in clips:
        m1, s1 = int(cp['start'] // 60), int(cp['start'] % 60)
        m2, s2 = int(cp['end'] // 60), int(cp['end'] % 60)
        print(f"  #{cp['id']}: [{m1:02d}:{s1:02d} -> {m2:02d}:{s2:02d}] ({cp['duration']}s) Hook: {cp['hook']} | Score: {cp['score']}")
    print(f"💾 Saved candidate manifest to: {out_path}")
    return clips

def main():
    parser = argparse.ArgumentParser(description="Find high-retention moments from online transcript")
    parser.add_argument("transcript", help="Path to transcript.json")
    parser.add_argument("--top", type=int, default=5, help="Number of clips to rank")
    args = parser.parse_args()
    
    find_viral_segments(args.transcript, top_n=args.top)

if __name__ == "__main__":
    main()
