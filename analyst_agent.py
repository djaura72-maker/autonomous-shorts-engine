"""
Phase 2: Transcription & Segment Isolation (Analyst Agent).
Transcribes audio with word-level timestamps via Whisper, saves manifests to /transcripts/,
and isolates 30 to 55-second high-retention segments.
"""
import os
import re
import json
import logging
import subprocess
from typing import List, Dict, Any, Tuple
import numpy as np
from faster_whisper import WhisperModel
from config import cfg
from database import Database

logger = logging.getLogger("Engine.AnalystAgent")

HOOK_PATTERNS = [
    re.compile(r"\b(why\s+(you|people|nobody|everyone)|the\s+truth\s+about|the\s+secret\s+to)\b", re.I),
    re.compile(r"\b(never\s+(do|say|use)|stop\s+(doing|making)|biggest\s+(mistake|lie|myth))\b", re.I),
    re.compile(r"\b(how\s+to\s+actually|the\s+number\s+one\s+reason|most\s+people\s+don'?t\s+know)\b", re.I),
    re.compile(r"\b(this\s+changed\s+everything|if\s+you\s+want\s+to|here'?s\s+the\s+thing)\b", re.I),
]

class AnalystAgent:
    def __init__(self, db: Database):
        self.db = db
        os.makedirs(cfg.transcripts_dir, exist_ok=True)
        logger.info(f"🧠 [Phase 2: Analyst] Initializing Whisper model '{cfg.whisper_model_size}'...")
        self.model = WhisperModel(
            cfg.whisper_model_size,
            device=cfg.whisper_device,
            compute_type="int8" if cfg.whisper_device == "cpu" else "float16"
        )

    def analyze_source(self, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transcribe raw video and isolate viral 30-55s segments.
        Saves transcription manifest to /transcripts/<video_id>_transcript.json.
        """
        video_id = video_data["video_id"]
        raw_video_path = video_data["raw_video_path"]
        manifest_path = os.path.join(cfg.transcripts_dir, f"{video_id}_transcript.json")

        # 1. Transcribe or Load Cached Manifest
        if os.path.exists(manifest_path):
            logger.info(f"📄 [Phase 2: Analyst] Loading cached transcript manifest: {manifest_path}")
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                words = manifest["words"]
        else:
            logger.info(f"🎙️  [Phase 2: Analyst] Running word-level Whisper transcription on {raw_video_path}...")
            words = self._transcribe_audio(raw_video_path)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({"video_id": video_id, "words": words}, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 [Phase 2: Analyst] Saved timing manifest ({len(words)} words) to: {manifest_path}")

        # 2. Extract Loudness Dynamics Profile
        loudness = self._calculate_loudness_profile(raw_video_path)

        # 3. Isolate High-Retention Windows (30-55 seconds)
        candidate_segments = self._isolate_viral_segments(words, loudness, video_data)

        # 4. Record to Database
        db_records = []
        for idx, seg in enumerate(candidate_segments, 1):
            clip_id = self.db.record_clip_segmented(
                video_id=video_id,
                clip_index=idx,
                start=seg["start"],
                end=seg["end"],
                score=seg["score"],
                headline=seg["headline"]
            )
            seg["clip_id"] = clip_id
            seg["clip_index"] = idx
            seg["manifest_path"] = manifest_path
            db_records.append(seg)

        logger.info(f"✨ [Phase 2: Analyst] Isolated {len(db_records)} high-retention segments for {video_id}.")
        return db_records

    def _transcribe_audio(self, video_path: str) -> List[Dict[str, Any]]:
        segments_gen, _ = self.model.transcribe(
            video_path,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=450)
        )
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

    def _calculate_loudness_profile(self, video_path: str) -> np.ndarray:
        sr = 8000
        cmd = ["ffmpeg", "-v", "error", "-i", video_path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw, _ = p.communicate()
        if not raw:
            return np.zeros(1)
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        n_chunks = len(samples) // sr
        if n_chunks == 0:
            return np.zeros(1)
        reshaped = samples[:n_chunks * sr].reshape(n_chunks, sr)
        rms = np.sqrt(np.mean(reshaped ** 2, axis=1) + 1e-10)
        norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-6)
        return norm

    def _isolate_viral_segments(self, words: List[Dict[str, Any]], loudness: np.ndarray, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not words:
            return []

        total_dur = words[-1]["e"]
        step = 5.0
        target_durations = [35.0, 45.0, 52.0]
        scored = []

        for target_len in target_durations:
            cur = 0.0
            while cur + target_len <= total_dur:
                w_in = [w for w in words if w["s"] >= cur and w["e"] <= cur + target_len]
                if len(w_in) >= 20:
                    start_snap = w_in[0]["s"]
                    end_snap = w_in[-1]["e"]
                    dur_snap = end_snap - start_snap

                    if cfg.min_clip_duration <= dur_snap <= cfg.max_clip_duration:
                        # 0-2s hook score
                        first_words = " ".join(w["w"] for w in w_in if w["s"] - start_snap <= 2.5).lower()
                        hook_pts = 4.0 if any(p.search(first_words) for p in HOOK_PATTERNS) else 1.0
                        if "?" in first_words:
                            hook_pts += 1.5

                        # Audio energy
                        s_idx = int(start_snap)
                        e_idx = min(len(loudness), int(end_snap))
                        audio_pts = float(np.mean(loudness[s_idx:e_idx])) * 3.0 if e_idx > s_idx else 0.0

                        # Speaking rate
                        wps = len(w_in) / dur_snap
                        pace_pts = max(0.0, 1.0 - abs(wps - 2.8) / 1.5) * 2.5

                        score = hook_pts * 0.4 + audio_pts * 0.35 + pace_pts * 0.25

                        # Headline
                        headline = "THE UNTOLD TRUTH"
                        if "why" in first_words:
                            headline = "WHY NOBODY NOTICED"
                        elif "never" in first_words or "stop" in first_words:
                            headline = "STOP MAKING THIS MISTAKE"
                        elif "how" in first_words:
                            headline = "HOW IT ACTUALLY WORKS"

                        scored.append({
                            "start": start_snap,
                            "end": end_snap,
                            "duration": round(dur_snap, 2),
                            "score": round(score, 2),
                            "headline": headline,
                            "words": w_in,
                            "raw_text": " ".join(w["w"] for w in w_in)
                        })
                cur += step

        scored.sort(key=lambda x: x["score"], reverse=True)
        chosen = []
        for c in scored:
            if not any(not (c["end"] <= sel["start"] + 5.0 or c["start"] >= sel["end"] - 5.0) for sel in chosen):
                chosen.append(c)
                if len(chosen) >= cfg.max_clips_per_video:
                    break
        return chosen
