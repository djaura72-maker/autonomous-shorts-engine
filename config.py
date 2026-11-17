"""
Master Configuration: Autonomous YouTube Shorts Engine.
Strictly maps to the mandatory directory architecture and enterprise pipeline specifications.
"""
import os
from dataclasses import dataclass, field
from typing import List

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

@dataclass
class EngineConfig:
    # --- Mandatory Directory Architecture ---
    root_dir: str = ROOT_DIR
    raw_videos_dir: str = os.path.join(ROOT_DIR, "raw_videos")
    transcripts_dir: str = os.path.join(ROOT_DIR, "transcripts")
    scripts_dir: str = os.path.join(ROOT_DIR, "scripts")
    audio_vo_dir: str = os.path.join(ROOT_DIR, "audio_vo")
    processed_video_dir: str = os.path.join(ROOT_DIR, "processed_video")
    ready_to_upload_dir: str = os.path.join(ROOT_DIR, "ready_to_upload")
    sfx_assets_dir: str = os.path.join(ROOT_DIR, "assets", "sfx")

    # --- Database & Telemetry ---
    db_path: str = os.path.join(ROOT_DIR, "pipeline_state.sqlite")
    log_file: str = os.path.join(ROOT_DIR, "engine.log")

    # --- Phase 1: Scout Agent ---
    search_queries: List[str] = field(default_factory=lambda: [
        "podcast clips full episode high quality",
        "tech interview future of ai deep dive",
        "business mindset motivation speech masterclass",
        "wild story animated explainer documentary"
    ])
    creator_channels: List[str] = field(default_factory=lambda: [])
    max_search_results: int = 12
    max_candidates_to_process: int = 2
    min_video_duration_secs: int = 300       # 5 minutes
    max_video_duration_secs: int = 7200      # 2 hours
    max_video_age_hours: int = 48            # Filter uploaded within last 48 hours

    # --- Phase 2: Analyst Agent ---
    whisper_model_size: str = "base"        # "tiny", "base", "small", "medium"
    whisper_device: str = "cpu"              # "cpu" or "cuda"
    min_clip_duration: float = 30.0          # 30-55s target
    max_clip_duration: float = 55.0
    max_clips_per_video: int = 2

    # --- Phase 3: Copywriting Agent ---
    target_spoken_wps: float = 2.8           # Conversational energetic words per second

    # --- Phase 4: VoiceStudio Integration ---
    voicestudio_path: str = "/Users/dilpreetjaura/.gemini/antigravity/scratch/antigravity/VoiceStudio"
    voicestudio_voice: str = "default"       # Custom-cloned or neural voice name

    # --- Phase 5: Editor Agent ---
    canvas_width: int = 1080
    canvas_height: int = 1920
    canvas_fps: int = 30
    font_family: str = "Helvetica"
    caption_color_highlight: str = "&H0000F0FF"  # Electric Yellow (&HBBGGRR)
    caption_color_normal: str = "&H00FFFFFF"     # Crisp White
    headline_box_text_color: str = "&H00000000"  # Black text on pill badge

    # --- Phase 6: Sound Agent ---
    bg_music_volume_db: float = -24.0
    target_lufs: float = -14.0                   # EBU R128 YouTube broadcast spec

    # --- Phase 7: Publisher Agent & YouTube Scheduling ---
    youtube_client_secrets: str = os.path.join(ROOT_DIR, "client_secrets.json")
    youtube_token_file: str = os.path.join(ROOT_DIR, "youtube_token.json")
    schedule_delay_hours: int = 4                # Default publishAt offset

cfg = EngineConfig()
