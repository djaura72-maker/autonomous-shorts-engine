"""
Phase 4: Voiceover Synthesis (VoiceStudio Integration Agent).
Interfaces with local VoiceStudio (debpalash/VoiceStudio) via CLI/API,
synthesizes professional narration track to /audio_vo/, and extracts word-level timing metadata.
"""
import os
import sys
import json
import logging
import subprocess
from typing import Dict, Any, List, Tuple
from faster_whisper import WhisperModel
from config import cfg
from database import Database

logger = logging.getLogger("Engine.VoiceStudioAgent")

class VoiceStudioAgent:
    def __init__(self, db: Database, whisper_model: WhisperModel):
        self.db = db
        self.whisper = whisper_model
        self.voicestudio_cli = os.path.join(cfg.voicestudio_path, "cli")
        os.makedirs(cfg.audio_vo_dir, exist_ok=True)

    def synthesize_voiceover(
        self,
        script_manifest: Dict[str, Any],
        segment_data: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Synthesize narration track and save to /audio_vo/<video_id>_clip<idx>_vo.wav.
        Extracts word-level timestamps for kinetic caption synchronization.
        """
        video_id = script_manifest["video_id"]
        clip_idx = script_manifest["clip_index"]
        script_text = script_manifest["full_script"]

        vo_path = os.path.join(cfg.audio_vo_dir, f"{video_id}_clip{clip_idx}_vo.wav")
        timing_path = os.path.join(cfg.audio_vo_dir, f"{video_id}_clip{clip_idx}_vo_words.json")

        logger.info(f"🎙️  [Phase 4: VoiceStudio] Synthesizing narration for Clip #{clip_idx}...")

        # 1. Synthesize via VoiceStudio CLI or Local Neural Fallback
        success = self._invoke_voicestudio(script_text, vo_path)
        if not success:
            logger.info("⚠️  [Phase 4: VoiceStudio] Daemon not running, executing local neural voice synthesis...")
            self._invoke_local_neural(script_text, vo_path)

        # 2. Extract Word-Level Timings from Synthesized Track
        logger.info(f"⏱️  [Phase 4: VoiceStudio] Aligning word-level timing manifest...")
        vo_words = self._extract_word_timings(vo_path)

        with open(timing_path, "w", encoding="utf-8") as f:
            json.dump({
                "video_id": video_id,
                "clip_index": clip_idx,
                "audio_file": vo_path,
                "words": vo_words
            }, f, indent=2, ensure_ascii=False)

        # Update database
        self.db.update_clip_stage(segment_data["clip_id"], {
            "vo_audio_path": vo_path,
            "status": "voiced"
        })

        logger.info(f"💾 [Phase 4: VoiceStudio] Exported VO narration ({len(vo_words)} words) to: {vo_path}")
        return vo_path, vo_words

    def _invoke_voicestudio(self, text: str, output_path: str) -> bool:
        if not os.path.exists(self.voicestudio_cli):
            return False

        env = os.environ.copy()
        env["PYTHONPATH"] = self.voicestudio_cli

        cmd = [
            sys.executable, "-m", "voicestudio_cli",
            "speak",
            "--voice", cfg.voicestudio_voice,
            "-o", output_path,
            "--overwrite",
            text
        ]
        try:
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=90)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info("✅ [Phase 4: VoiceStudio] Synthesized via VoiceStudio CLI.")
                return True
        except Exception as e:
            logger.debug(f"VoiceStudio CLI execution: {e}")
        return False

    def _invoke_local_neural(self, text: str, output_path: str):
        temp_aiff = output_path + ".aiff"
        try:
            subprocess.run(["say", "-v", "Daniel", "-r", "195", "-o", temp_aiff, text], check=True)
        except Exception:
            subprocess.run(["say", "-r", "195", "-o", temp_aiff, text], check=True)

        # Convert to 48kHz WAV with dynamic range compression and warmth EQ
        subprocess.run([
            "ffmpeg", "-v", "error", "-y",
            "-i", temp_aiff,
            "-af", "highpass=f=75,lowpass=f=12000,compand=0.02|0.05:6:-60/-60|-20/-10|0/-3:6:0:0.05",
            "-ar", "48000",
            output_path
        ], check=True)

        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)

    def _extract_word_timings(self, audio_path: str) -> List[Dict[str, Any]]:
        segments_gen, _ = self.whisper.transcribe(audio_path, word_timestamps=True, vad_filter=True)
        words = []
        for s in segments_gen:
            if s.words:
                for w in s.words:
                    clean = w.word.strip()
                    if clean:
                        words.append({
                            "w": clean,
                            "s": round(w.start, 3),
                            "e": round(w.end, 3)
                        })
        return words
