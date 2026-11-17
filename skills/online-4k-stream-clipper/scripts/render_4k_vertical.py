#!/usr/bin/env python3
"""
Ultra-HD 4K Vertical Short Renderer.
Reframes sliced 4K horizontal video into 9:16 vertical shorts (2160x3840 or supersampled 1080x1920).
Features:
- Hardware-accelerated encoding via Apple Silicon VideoToolbox.
- Non-overlapping kinetic ASS subtitles.
- Mastered audio at -14.0 LUFS.
- Visual QA contact sheet preview.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile

def clean_text(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\\", "").strip()

def ass_time(t: float) -> str:
    t = max(0.0, float(t))
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

def build_4k_ass(ass_path: str, words: list[dict], hook_text: str = None, resolution_mode: str = "4k"):
    """Builds non-overlapping ASS subtitles scaled for 4K (2160x3840) or 1080p (1080x1920)."""
    if resolution_mode == "4k":
        w_res, h_res = 2160, 3840
        fsize = 144
        margin_v_hook = 440
        margin_v_captions = 960
    else:
        w_res, h_res = 1080, 1920
        fsize = 76
        margin_v_hook = 220
        margin_v_captions = 480
        
    # Clamp word timings to prevent overlap
    clamped = []
    for i, w in enumerate(words):
        s = max(0.0, float(w.get("start", 0.0)))
        e = max(s + 0.05, float(w.get("end", s + 0.2)))
        if i + 1 < len(words):
            next_s = float(words[i+1].get("start", e))
            if e > next_s:
                e = max(s + 0.04, next_s - 0.01)
        clamped.append({
            "word": clean_text(str(w.get("word", ""))),
            "start": round(s, 3),
            "end": round(e, 3)
        })
        
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {w_res}",
        f"PlayResY: {h_res}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Kinetic,Arial Black,{fsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6.0,3.0,2,80,80,{margin_v_captions},1",
        f"Style: HookTop,Arial Black,{int(fsize*0.9)},&H0000FFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,8.0,4.0,8,80,80,{margin_v_hook},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    
    if hook_text:
        clean_hook = clean_text(hook_text).upper()
        lines.append(f"Dialogue: 1,0:00:00.00,0:00:03.00,HookTop,,0,0,0,,{{\\fad(100,200)}}{clean_hook}")
        
    # Group words into 1-3 word blocks
    groups = []
    cur = []
    for w in clamped:
        if cur and (len(cur) >= 3 or (w["start"] - cur[-1]["end"] > 0.45) or re.search(r"[.!?]$", cur[-1]["word"])):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
        
    for grp in groups:
        for w in grp:
            parts = []
            for other in grp:
                if other == w:
                    parts.append(f"{{\\c&H0000F0FF\\fscx112\\fscy112}}{other['word']}{{\\r}}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF}}{other['word']}")
            line_str = " ".join(parts)
            lines.append(f"Dialogue: 0,{ass_time(w['start'])},{ass_time(w['end'])},Kinetic,,0,0,0,,{line_str}")
            
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return ass_path

def render_vertical(
    sliced_mp4: str,
    out_mp4: str,
    words: list[dict],
    hook_text: str = None,
    mode: str = "1080p"  # "4k" or "1080p"
):
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix="render_4k_")
    
    try:
        ass_path = os.path.join(temp_dir, "subtitles.ass")
        build_4k_ass(ass_path, words, hook_text, resolution_mode=mode)
        escaped_ass = ass_path.replace(":", "\\:").replace("'", "\\'")
        
        # Check encoder
        encoders = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True).stdout
        use_vt = "h264_videotoolbox" in encoders
        
        if mode == "4k":
            w, h = 2160, 3840
            bitrate = "35M"
            vf_filter = (
                f"[0:v]split=2[bg_src][fg_src];"
                f"[bg_src]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
                f"boxblur=40:10,eq=brightness=-0.1:saturation=1.2[bg];"
                f"[fg_src]scale=2160:1216:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
                f"[base]ass='{escaped_ass}'[v]"
            )
        else:
            w, h = 1080, 1920
            bitrate = "12M"
            # Supersampled down from 4K input
            vf_filter = (
                f"[0:v]split=2[bg_src][fg_src];"
                f"[bg_src]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"boxblur=25:5,eq=brightness=-0.1:saturation=1.2[bg];"
                f"[fg_src]scale=1080:608:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
                f"[base]ass='{escaped_ass}'[v]"
            )
            
        enc_args = ["-c:v", "h264_videotoolbox", "-b:v", bitrate] if use_vt else ["-c:v", "libx264", "-crf", "18", "-preset", "fast"]
        
        cmd = [
            "ffmpeg", "-y",
            "-i", sliced_mp4,
            "-filter_complex", vf_filter,
            "-map", "[v]", "-map", "0:a?",
            *enc_args,
            "-pix_fmt", "yuv420p",
            "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=11",
            "-c:a", "aac", "-b:a", "256k",
            out_mp4
        ]
        
        print(f"🎬 Rendering {mode.upper()} vertical short with VideoToolbox hardware acceleration...")
        subprocess.run(cmd, check=True)
        print(f"✅ Rendered vertical short: {out_mp4}")
        
        # Preview contact sheet
        preview_path = os.path.splitext(out_mp4)[0] + "_preview.jpg"
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", "1.5", "-i", out_mp4,
            "-vframes", "1", "-vf", f"scale={w//3}:{h//3}",
            preview_path
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(preview_path):
            print(f"📸 Preview frame saved: {preview_path}")
            
        return out_mp4
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Render 4K Vertical Short")
    parser.add_argument("sliced_video", help="Path to sliced 4K MP4 file")
    parser.add_argument("--out", default="shorts/output_short.mp4", help="Output path")
    parser.add_argument("--hook", default="WATCH THIS MOMENT", help="Headline hook")
    parser.add_argument("--transcript", help="Optional transcript.json with word timestamps")
    parser.add_argument("--mode", choices=["4k", "1080p"], default="1080p", help="Output resolution mode")
    args = parser.parse_args()
    
    words = []
    if args.transcript and os.path.exists(args.transcript):
        with open(args.transcript, "r", encoding="utf-8") as f:
            tdata = json.load(f)
        for s in tdata.get("segments", []):
            for w in s.get("words", []):
                words.append(w)
                
    render_vertical(args.sliced_video, args.out, words, args.hook, mode=args.mode)

if __name__ == "__main__":
    main()
