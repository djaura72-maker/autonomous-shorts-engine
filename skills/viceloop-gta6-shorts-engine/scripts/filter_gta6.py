#!/usr/bin/env python3
"""
Strict GTA VI Topic Lock (Scout Filter)
Enforces strict allowlist verification before downloading or transcribing source clips.
"""
import argparse
import json
import re
import subprocess
import sys

GTA6_ALLOWLIST = [
    r"\bgta\s*6\b",
    r"\bgta\s*vi\b",
    r"\bgrand\s*theft\s*auto\s*vi\b",
    r"\bvice\s*city\b",
    r"\bleonida\b",
    r"\bjason\b",
    r"\blucia\b",
    r"\brockstar\s*games\b",
    r"\brockstar\b"
]

REJECT_PATTERNS = [
    r"\bfortnite\b",
    r"\bvalorant\b",
    r"\bwarzone\b",
    r"\bapex\s*legends\b",
    r"\bminecraft\b",
    r"\broblox\b",
    r"\bcsgo\b",
    r"\bcounter\s*strike\b",
    r"\bleague\s*of\s*legends\b"
]

def check_text(text: str) -> tuple[bool, str]:
    if not text:
        return False, "Empty metadata/text."
        
    text_lower = text.lower()
    
    # Check for direct reject patterns
    for rej in REJECT_PATTERNS:
        if re.search(rej, text_lower):
            return False, f"Matched non-GTA rejection pattern: {rej}"
            
    # Check for allowlist matches
    matched = []
    for pat in GTA6_ALLOWLIST:
        if re.search(pat, text_lower):
            matched.append(pat)
            
    if matched:
        return True, f"Verified GTA VI match: {', '.join(matched)}"
    else:
        return False, "No GTA VI keywords (GTA 6, Vice City, Leonida, Jason, Lucia, Rockstar) found."

def check_url(url: str) -> tuple[bool, str, dict]:
    cmd = ["yt-dlp", "--dump-json", "--no-warnings", url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        title = data.get("title", "")
        desc = data.get("description", "")
        tags = " ".join(data.get("tags", []))
        full_meta = f"{title} {desc} {tags}"
        
        ok, reason = check_text(full_meta)
        return ok, reason, data
    except Exception as e:
        return False, f"Failed to fetch metadata from URL: {e}", {}

def main():
    parser = argparse.ArgumentParser(description="Strict GTA VI Topic Lock Filter")
    parser.add_argument("--url", help="YouTube video or livestream URL")
    parser.add_argument("--text", help="Text/metadata to evaluate")
    args = parser.parse_args()
    
    if args.url:
        ok, reason, meta = check_url(args.url)
        if ok:
            print(f"✅ [APPROVED] Source meets GTA VI criteria: {meta.get('title')}")
            print(f"   Reason: {reason}")
            sys.exit(0)
        else:
            print(f"❌ [REJECTED] Source does not meet GTA VI criteria.")
            print(f"   Reason: {reason}")
            sys.exit(1)
    elif args.text:
        ok, reason = check_text(args.text)
        if ok:
            print(f"✅ [APPROVED] {reason}")
            sys.exit(0)
        else:
            print(f"❌ [REJECTED] {reason}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
