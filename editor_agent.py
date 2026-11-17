"""
Phase 5: Visual Reframing & Kinetic Subtitling (Editor Agent).
Reframes horizontal footage into 1080x1920 (9:16) vertical canvas with blurred frame stack,
burns in word-by-word highlighted kinetic captions and top headline box, and saves to /processed_video/.
"""
import os
import re
import logging
import subprocess
from typing import List, Dict, Any
from config import cfg
from database import Database

logger = logging.getLogger("Engine.EditorAgent")

def format_ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    cs = int(round(seconds * 100))
    h = cs // 360000
    m = (cs // 6000) % 60
    s = (cs // 100) % 60
    return f"{h}:{m:02d}:{s:02d}.{cs % 100:02d}"

def clean_ass_text(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\\", "").strip()

def group_words_for_display(words: List[Dict[str, Any]], max_words: int = 3, max_gap: float = 0.5) -> List[List[Dict[str, Any]]]:
    groups, cur = [], []
    for w in words:
        if cur:
            gap = w["s"] - cur[-1]["e"]
            has_punc = bool(re.search(r"[.!?,]$", cur[-1]["w"]))
            if len(cur) >= max_words or gap > max_gap or has_punc:
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups

class EditorAgent:
    def __init__(self, db: Database):
        self.db = db
        os.makedirs(cfg.processed_video_dir, exist_ok=True)

    def reframe_and_caption(
        self,
        raw_video_path: str,
        video_start: float,
        video_end: float,
        master_audio_path: str,
        vo_words: List[Dict[str, Any]],
        headline_badge: str,
        clip_id: int,
        output_path: str
    ) -> str:
        """
        Reframe slice to 9:16 vertical, burn kinetic karaoke captions, and multiplex master audio.
        Output saved to /processed_video/.
        """
        logger.info(f"🎞️  [Phase 5: Editor] Reframing and burning captions into 9:16 vertical canvas...")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Probe duration of master audio
        dur_probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", master_audio_path
        ], capture_output=True, text=True).stdout.strip()
        clip_dur = float(dur_probe or (video_end - video_start))

        # 1. Slice raw source video to matching duration
        slice_temp = output_path + ".temp_slice.mp4"
        subprocess.run([
            "ffmpeg", "-v", "error", "-y",
            "-ss", f"{video_start:.3f}",
            "-i", raw_video_path,
            "-t", f"{clip_dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-an", slice_temp
        ], check=True)

        # 2. Build ASS Subtitle Manifest
        ass_path = output_path + ".ass"
        self._build_ass_script(ass_path, vo_words, clip_dur, headline_badge)

        # 3. 9:16 Blurred Background Frame Stack Filter
        W, H = cfg.canvas_width, cfg.canvas_height
        fg_w = 1140
        escaped_ass = ass_path.replace(':', '\\:').replace("'", "\\'")
        vf = (
            f"[0:v]split[bg_in][fg_in];"
            f"[bg_in]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=25:3,eq=brightness=-0.12[bg];"
            f"[fg_in]scale={fg_w}:-2,crop={W}:ih[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2-50[v_stack];"
            f"[v_stack]ass='{escaped_ass}',format=yuv420p[v_out]"
        )

        # 4. Final Render
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-i", slice_temp,
            "-i", master_audio_path,
            "-filter_complex", vf,
            "-map", "[v_out]",
            "-map", "1:a",
            "-t", f"{clip_dur:.3f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-r", str(cfg.canvas_fps),
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        subprocess.run(cmd, check=True)

        # Cleanup temp slice and ASS file
        if os.path.exists(slice_temp): os.remove(slice_temp)
        if os.path.exists(ass_path): os.remove(ass_path)

        # Update database
        self.db.update_clip_stage(clip_id, {
            "processed_video_path": output_path,
            "status": "edited"
        })

        logger.info(f"✅ [Phase 5: Editor] Rendered vertical short to: {output_path}")
        return output_path

    def _build_ass_script(self, ass_path: str, words: List[Dict[str, Any]], clip_dur: float, headline: str):
        W, H = cfg.canvas_width, cfg.canvas_height
        font = cfg.font_family

        lines = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
            "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: KineticCap,{font},92,{cfg.caption_color_normal},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,4,2,70,70,580,1",
            f"Style: HookBox,{font},74,{cfg.headline_box_text_color},&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,80,80,240,1",
            "", "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        # Top headline badge fixed for first 2.0 seconds
        if headline:
            h_end = min(2.0, clip_dur)
            clean_head = clean_ass_text(headline.upper())
            lines.append(f"Dialogue: 1,{format_ass_time(0.0)},{format_ass_time(h_end)},HookBox,,0,0,0,,{{\\fad(80,180)}}{clean_head}")

        # Synchronized word-by-word karaoke captions
        groups = group_words_for_display(words, max_words=3)
        for g in groups:
            g_end = g[-1]["e"]
            for i, w in enumerate(g):
                s = w["s"]
                e = g[i + 1]["s"] if i + 1 < len(g) else g_end + 0.15
                formatted = []
                for j, target in enumerate(g):
                    txt = clean_ass_text(target["w"]).upper()
                    if j == i:
                        formatted.append(f"{{\\c{cfg.caption_color_highlight}\\fscx114\\fscy114}}{txt}{{\\c{cfg.caption_color_normal}\\fscx100\\fscy100}}")
                    else:
                        formatted.append(txt)
                lines.append(f"Dialogue: 0,{format_ass_time(s)},{format_ass_time(min(e, clip_dur))},KineticCap,,0,0,0,,{' '.join(formatted)}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
