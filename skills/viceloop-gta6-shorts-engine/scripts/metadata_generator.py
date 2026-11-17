#!/usr/bin/env python3
"""
Clean Metadata & Pre-Upload QA Generator for ViceLoop GTA VI Engine.
Enforces:
- Title < 60 characters, curiosity-driven, ZERO emojis.
- Matching pinned comment debate question for comment velocity.
- 3-5 niche hashtags (#gta6 #gtavi #vicecity #rockstargames #shorts).
"""
import argparse
import json
import os
import re
import sys

DEBATE_QUESTIONS = [
    "Clean or Psycho? Vote below in the comments.",
    "Real or Overrated? Drop your honest take below.",
    "Jason or Lucia? Who are you playing as on day one?",
    "First cop chase or beach cruise? What are you doing first?",
    "Insane physics or too realistic? What do you think?"
]

NICHE_TAGS = ["#gta6", "#gtavi", "#vicecity", "#rockstargames", "#shorts"]

def generate_clean_title(raw_title: str) -> str:
    # Strip emojis
    cleaned = re.sub(r"[^\w\s\-,.?!']", "", raw_title).strip()
    # Normalize spaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Ensure under 60 chars including hashtag
    suffix = " #shorts"
    max_len = 60 - len(suffix)
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(" ", 1)[0]
    return f"{cleaned}{suffix}"

def create_metadata_package(
    clip_id: int,
    base_title: str,
    hook_text: str,
    debate_q: str = None,
    channel_credit: str = "Rockstar Games / Source Broadcaster"
) -> dict:
    clean_title = generate_clean_title(base_title)
    chosen_debate = debate_q or DEBATE_QUESTIONS[clip_id % len(DEBATE_QUESTIONS)]
    
    desc_lines = [
        hook_text.upper(),
        "",
        f"Pinned Question: {chosen_debate}",
        "",
        f"Credit: {channel_credit}",
        "",
        " ".join(NICHE_TAGS)
    ]
    
    metadata = {
        "clip_id": clip_id,
        "title": clean_title,
        "title_length": len(clean_title),
        "has_emojis": False,
        "description": "\n".join(desc_lines),
        "pinned_comment": chosen_debate,
        "tags": [t.replace("#", "") for t in NICHE_TAGS] + ["gta6gameplay", "vicecitymap"],
        "category_id": "20",  # Gaming
        "privacy_status": "private"
    }
    return metadata

def main():
    parser = argparse.ArgumentParser(description="ViceLoop Metadata Generator")
    parser.add_argument("--id", type=int, default=1, help="Clip index")
    parser.add_argument("--title", default="The Secret Cop AI in GTA 6", help="Base title")
    parser.add_argument("--hook", default="THE SECRET COP AI REVEALED", help="Hook text")
    parser.add_argument("--out", help="Output JSON path")
    args = parser.parse_args()
    
    meta = create_metadata_package(args.id, args.title, args.hook)
    print("\n" + "="*50)
    print("🏷️  CLEAN METADATA PACKAGE GENERATED")
    print("="*50)
    print(f"TITLE ({meta['title_length']} chars, zero emojis): {meta['title']}")
    print(f"PINNED COMMENT: {meta['pinned_comment']}")
    print(f"HASHTAGS: {' '.join(NICHE_TAGS)}")
    print("="*50)
    
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"💾 Saved to: {args.out}")

if __name__ == "__main__":
    main()
