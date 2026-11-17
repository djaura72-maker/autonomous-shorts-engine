"""
Phase 6: Sound Design & Audio Mastering (Sound Agent).
Procedural SFX library in /assets/sfx/, dynamic timeline SFX injection,
multi-track mixing (VO + SFX + Ambient bed) and broadcast loudness mastering (-14 LUFS).
"""
import os
import wave
import math
import random
import logging
import subprocess
from typing import List, Dict, Any
import numpy as np
from config import cfg

logger = logging.getLogger("Engine.SoundAgent")

class SoundAgent:
    def __init__(self):
        self.sfx_dir = cfg.sfx_assets_dir
        os.makedirs(self.sfx_dir, exist_ok=True)
        self._ensure_sfx_library()

    def _ensure_sfx_library(self):
        """Synthesize pure procedural cinema-grade SFX WAV assets."""
        w_path = os.path.join(self.sfx_dir, "whoosh.wav")
        i_path = os.path.join(self.sfx_dir, "impact.wav")
        p_path = os.path.join(self.sfx_dir, "pop.wav")
        r_path = os.path.join(self.sfx_dir, "riser.wav")
        a_path = os.path.join(self.sfx_dir, "ambient_bed.wav")

        if not os.path.exists(w_path): self._synth_whoosh(w_path)
        if not os.path.exists(i_path): self._synth_impact(i_path)
        if not os.path.exists(p_path): self._synth_pop(p_path)
        if not os.path.exists(r_path): self._synth_riser(r_path)
        if not os.path.exists(a_path): self._synth_ambient_bed(a_path)

    def _write_wav_np(self, path: str, samples: np.ndarray, sr: int = 44100):
        int_samples = np.clip(samples * 32767.0, -32767, 32767).astype(np.int16)
        with wave.open(path, "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sr)
            wav.writeframes(int_samples.tobytes())

    def _synth_whoosh(self, path: str, duration: float = 0.35, sr: int = 44100):
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        norm_t = t / duration
        env = np.exp(-((norm_t - 0.5) ** 2) / 0.04)
        noise = (np.random.rand(len(t)) * 2.0 - 1.0) * 0.45
        freq = 250.0 + 800.0 * np.sin(np.pi * norm_t)
        tone = np.sin(2.0 * np.pi * freq * t) * 0.55
        self._write_wav_np(path, (noise + tone) * env * 0.85, sr)

    def _synth_impact(self, path: str, duration: float = 0.65, sr: int = 44100):
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        freq = 28.0 + 67.0 * np.exp(-t * 12.0)
        phase = np.cumsum(2.0 * np.pi * freq / sr)
        env = np.exp(-t * 4.5)
        transient = (np.random.rand(len(t)) * 2.0 - 1.0) * np.exp(-t * 90.0) * 0.4
        sub = np.sin(phase) * 0.85
        self._write_wav_np(path, (sub + transient) * env * 0.95, sr)

    def _synth_pop(self, path: str, duration: float = 0.08, sr: int = 44100):
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        freq = 380.0 + 720.0 * np.exp(-t * 60.0)
        phase = np.cumsum(2.0 * np.pi * freq / sr)
        env = np.exp(-t * 40.0)
        self._write_wav_np(path, np.sin(phase) * env * 0.8, sr)

    def _synth_riser(self, path: str, duration: float = 1.8, sr: int = 44100):
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        norm_t = t / duration
        freq = 160.0 * (4.5 ** norm_t)
        phase = np.cumsum(2.0 * np.pi * freq / sr)
        env = (norm_t ** 1.8) * 0.8
        self._write_wav_np(path, np.sin(phase) * env, sr)

    def _synth_ambient_bed(self, path: str, duration: float = 30.0, sr: int = 44100):
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        f1, f2, f3 = 130.81, 196.00, 293.66
        chord = (
            np.sin(2.0 * np.pi * f1 * t) * 0.4 +
            np.sin(2.0 * np.pi * f2 * t) * 0.35 +
            np.sin(2.0 * np.pi * f3 * t) * 0.25
        )
        tremolo = 0.85 + 0.15 * np.sin(2.0 * np.pi * 0.2 * t)
        self._write_wav_np(path, chord * tremolo * 0.25, sr)

    def master_audio_mix(
        self,
        vo_path: str,
        duration: float,
        words: List[Dict[str, Any]],
        output_master_path: str
    ) -> str:
        """
        Mix VO + dynamic SFX + ambient bed and master to -14 LUFS.
        """
        logger.info(f"🎚️  [Phase 6: Sound] Mastering audio track ({duration:.1f}s) to {cfg.target_lufs} LUFS...")
        os.makedirs(os.path.dirname(os.path.abspath(output_master_path)), exist_ok=True)

        ambient_path = os.path.join(self.sfx_dir, "ambient_bed.wav")
        inputs = ["-i", vo_path, "-i", ambient_path]
        filter_parts = [
            "[0:a]volume=1.0[vo]",
            f"[1:a]atrim=0:{duration:.2f},volume={cfg.bg_music_volume_db}dB[bg]"
        ]

        # Plan dynamic SFX hits
        sfx_plan = [
            {"sfx": "impact.wav", "time": 0.0, "vol": 0.95},
            {"sfx": "whoosh.wav", "time": 0.05, "vol": 0.70},
            {"sfx": "pop.wav", "time": 2.4, "vol": 0.55},
        ]
        # Mid-point riser
        riser_t = max(3.5, duration * 0.45)
        sfx_plan.append({"sfx": "riser.wav", "time": round(riser_t, 2), "vol": 0.65})
        climax_t = min(duration - 1.2, riser_t + 1.8)
        if climax_t > riser_t:
            sfx_plan.append({"sfx": "whoosh.wav", "time": round(climax_t, 2), "vol": 0.75})
            sfx_plan.append({"sfx": "impact.wav", "time": round(climax_t + 0.1, 2), "vol": 0.85})

        sfx_labels = []
        for idx, ev in enumerate(sfx_plan, 2):
            sfx_file = os.path.join(self.sfx_dir, ev["sfx"])
            inputs.extend(["-i", sfx_file])
            delay_ms = int(ev["time"] * 1000)
            lbl = f"sfx{idx}"
            filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume={ev['vol']}[{lbl}]")
            sfx_labels.append(f"[{lbl}]")

        total_in = 2 + len(sfx_labels)
        all_lbls = "[vo][bg]" + "".join(sfx_labels)
        filter_parts.append(f"{all_lbls}amix=inputs={total_in}:duration=first:dropout_transition=2[mixed]")
        filter_parts.append(f"[mixed]loudnorm=I={cfg.target_lufs}:TP=-1.5:LRA=11[out]")

        cmd = [
            "ffmpeg", "-v", "error", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            output_master_path
        ]
        subprocess.run(cmd, check=True)
        logger.info(f"✅ [Phase 6: Sound] Master audio locked at {cfg.target_lufs} LUFS: {output_master_path}")
        return output_master_path
