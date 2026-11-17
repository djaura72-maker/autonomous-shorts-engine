"""
MASTER SYSTEM TASK DIRECTIVE: AUTONOMOUS YOUTUBE SHORTS ENGINE
Sequential 7-Phase Autonomous Video Engineering & Growth Controller.

Phases:
  1. Autonomous Ingestion (Scout Agent) -> /raw_videos/
  2. Transcription & Segment Isolation (Analyst Agent) -> /transcripts/
  3. Hook-Optimized Script Engineering (Copywriting Agent) -> /scripts/
  4. Voiceover Synthesis (VoiceStudio Integration) -> /audio_vo/
  5. Visual Reframing & Kinetic Subtitling (Editor Agent) -> /processed_video/
  6. Sound Design & Audio Mastering (Sound Agent) -> /assets/sfx/
  7. Automated Packaging, Upload, & Scheduling (Publisher Agent) -> /ready_to_upload/

Usage:
  python3 main_engine.py --once             # Execute one full 7-phase cycle
  python3 main_engine.py --daemon           # Continuous 24/7 background scheduler
  python3 main_engine.py --url <YOUTUBE_URL> # Ingest and process a specific video
"""
import os
import sys
import time
import signal
import logging
import argparse

from config import cfg
from database import Database
from scout_agent import ScoutAgent
from analyst_agent import AnalystAgent
from copywriting_agent import CopywritingAgent
from voicestudio_agent import VoiceStudioAgent
from editor_agent import EditorAgent
from sound_agent import SoundAgent
from publisher_agent import PublisherAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(cfg.log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger("Engine.MasterController")

class MasterShortsEngine:
    def __init__(self):
        self.running = True
        self.db = Database(cfg.db_path)

        # Initialize Specialized Agents
        self.scout = ScoutAgent(self.db)
        self.analyst = None
        self.copywriter = CopywritingAgent(self.db)
        self.voicestudio = None
        self.sound = SoundAgent()
        self.editor = EditorAgent(self.db)
        self.publisher = PublisherAgent(self.db)

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info("\n🛑 [Master] Shutdown signal received. Gracefully finishing current phase...")
        self.running = False

    def _lazy_init_models(self):
        if self.analyst is None:
            self.analyst = AnalystAgent(self.db)
        if self.voicestudio is None:
            self.voicestudio = VoiceStudioAgent(self.db, self.analyst.model)

    def process_video_pipeline(self, video_data: dict) -> int:
        video_id = video_data["video_id"]
        logger.info("\n" + "="*65)
        logger.info(f"🚀 [Master Engine] EXECUTING 7-PHASE PIPELINE: {video_data['title']}")
        logger.info(f"   Source URL: {video_data['url']}")
        logger.info(f"   Raw Capture: {video_data.get('raw_video_path', 'pending')}")
        logger.info("="*65)

        self._lazy_init_models()
        self.db.update_video_status(video_id, "processing")

        try:
            # PHASE 1: Autonomous Ingestion (Ensure raw stream in /raw_videos/)
            if "raw_video_path" not in video_data or not os.path.exists(video_data["raw_video_path"]):
                raw_path = self.scout.download_source_stream(video_id, video_data["url"])
                if not raw_path:
                    logger.error(f"❌ Ingestion failed for {video_id}")
                    return 0
                video_data["raw_video_path"] = raw_path
                self.db.update_video_ingested(video_id, raw_path)

            # PHASE 2: Transcription & Segment Isolation
            segments = self.analyst.analyze_source(video_data)
            if not segments:
                logger.warning(f"⚠️  No high-retention segments found in {video_id}. Marking complete.")
                self.db.update_video_status(video_id, "completed")
                return 0

            shorts_packaged = 0
            for seg in segments:
                if not self.running:
                    break

                clip_idx = seg["clip_index"]
                clip_id = seg["clip_id"]
                logger.info(f"\n--- ⚡ Processing Clip #{clip_idx}: [{seg['start']:.1f}s -> {seg['end']:.1f}s] ---")

                # PHASE 3: Hook-Optimized Script Engineering
                script_manifest = self.copywriter.engineer_script(video_data, seg)

                # PHASE 4: Voiceover Synthesis (VoiceStudio Integration)
                vo_path, vo_words = self.voicestudio.synthesize_voiceover(script_manifest, seg)

                # PHASE 6: Sound Design & Audio Mastering (Mixed ahead for editor sync)
                master_audio_path = os.path.join(
                    cfg.processed_video_dir, f"{video_id}_clip{clip_idx}_master.m4a"
                )
                self.sound.master_audio_mix(
                    vo_path=vo_path,
                    duration=script_manifest["estimated_duration"],
                    words=vo_words,
                    output_master_path=master_audio_path
                )

                # PHASE 5: Visual Reframing & Kinetic Subtitling
                processed_video_path = os.path.join(
                    cfg.processed_video_dir, f"{video_id}_clip{clip_idx}_vertical.mp4"
                )
                self.editor.reframe_and_caption(
                    raw_video_path=video_data["raw_video_path"],
                    video_start=seg["start"],
                    video_end=seg["end"],
                    master_audio_path=master_audio_path,
                    vo_words=vo_words,
                    headline_badge=script_manifest["headline_badge"],
                    clip_id=clip_id,
                    output_path=processed_video_path
                )

                # PHASE 7: Automated Packaging, Upload, & Scheduling
                self.publisher.package_and_schedule(
                    video_data=video_data,
                    script_manifest=script_manifest,
                    processed_video_path=processed_video_path,
                    clip_id=clip_id
                )
                shorts_packaged += 1

            self.db.update_video_status(video_id, "completed")
            logger.info(f"\n🎉 [Master Engine] Finished processing {video_id}: {shorts_packaged} shorts ready in /ready_to_upload/")
            return shorts_packaged

        except Exception as e:
            logger.error(f"❌ [Master Engine] Error processing {video_id}: {e}", exc_info=True)
            self.db.update_video_status(video_id, "failed")
            return 0

    def run_cycle(self) -> int:
        logger.info("\n" + "="*65)
        logger.info("🚀 STARTING ZERO-TOUCH PIPELINE CYCLE")
        logger.info("="*65)

        candidates = self.scout.scan_and_ingest()
        if not candidates:
            logger.info("ℹ️  No new high-velocity candidates to process on this scan.")
            return 0

        total_shorts = 0
        for video in candidates:
            if not self.running:
                break
            shorts = self.process_video_pipeline(video)
            total_shorts += shorts

        logger.info(f"\n✨ CYCLE COMPLETE: {total_shorts} new shorts engineered in '{cfg.ready_to_upload_dir}'\n")
        return total_shorts

    def run_daemon(self, interval_seconds: int = 3600):
        logger.info(f"🔄 Starting Autonomous 24/7 Engine Daemon (Interval: {interval_seconds // 60} minutes)...")
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Error in cycle: {e}", exc_info=True)

            if not self.running:
                break

            logger.info(f"💤 Sleeping for {interval_seconds // 60} minutes until next discovery run...")
            sleep_chunks = interval_seconds
            while sleep_chunks > 0 and self.running:
                time.sleep(min(5, sleep_chunks))
                sleep_chunks -= 5
        logger.info("👋 Master Engine Daemon stopped.")

    def run_url(self, url: str):
        logger.info(f"🎯 Direct URL Ingestion: {url}")
        import yt_dlp
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_data = {
                "video_id": info["id"],
                "title": info.get("title", "Untitled"),
                "channel": info.get("uploader", "") or info.get("channel", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "comment_count": info.get("comment_count", 0),
                "upload_timestamp": info.get("timestamp", 0),
                "url": url,
                "viral_score": 100.0
            }
        self.process_video_pipeline(video_data)

def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts Engine - Master System Controller")
    parser.add_argument("--once", action="store_true", help="Execute one complete 7-phase cycle")
    parser.add_argument("--daemon", action="store_true", help="Run 24/7 continuous daemon")
    parser.add_argument("--interval", type=int, default=3600, help="Daemon cycle interval in seconds")
    parser.add_argument("--url", type=str, help="Process a specific YouTube URL immediately")
    args = parser.parse_args()

    engine = MasterShortsEngine()
    if args.url:
        engine.run_url(args.url)
    elif args.daemon:
        engine.run_daemon(args.interval)
    else:
        engine.run_cycle()

if __name__ == "__main__":
    main()
