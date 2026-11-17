"""
Phase 1: Autonomous Ingestion (Scout Agent).
Scans feeds, filters by view-velocity and engagement, and downloads top streams to /raw_videos/.
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
import yt_dlp
from config import cfg
from database import Database

logger = logging.getLogger("Engine.ScoutAgent")

class ScoutAgent:
    def __init__(self, db: Database):
        self.db = db
        os.makedirs(cfg.raw_videos_dir, exist_ok=True)

    def scan_and_ingest(self) -> List[Dict[str, Any]]:
        """Scout feeds, select top candidates, download to /raw_videos/."""
        logger.info("🔭 [Phase 1: Scout] Scanning YouTube target queries & feeds...")
        candidates = {}

        for query in cfg.search_queries:
            logger.info(f"🔎 [Phase 1: Scout] Querying: '{query}'")
            results = self._search_feed(query, cfg.max_search_results)
            for vid in results:
                vid_id = vid["video_id"]
                if vid_id not in candidates and not self.db.is_video_processed(vid_id):
                    candidates[vid_id] = vid

        now = time.time()
        scored_candidates = []

        for vid_id, data in candidates.items():
            duration = data.get("duration", 0)
            if not (cfg.min_video_duration_secs <= duration <= cfg.max_video_duration_secs):
                continue

            upload_ts = data.get("upload_timestamp") or 0
            age_hours = (now - upload_ts) / 3600.0 if upload_ts > 0 else 24.0
            if age_hours > cfg.max_video_age_hours:
                continue

            views = data.get("view_count", 0)
            comments = data.get("comment_count", 0)

            velocity = views / max(0.2, age_hours)
            engagement = (comments * 100.0) / (views + 1.0)
            score = (velocity ** 0.5) * (1.0 + (engagement * 0.5))

            data["view_velocity"] = round(velocity, 2)
            data["engagement_ratio"] = round(engagement, 3)
            data["viral_score"] = round(score, 2)
            data["age_hours"] = round(age_hours, 1)

            self.db.record_discovered_video(data)
            scored_candidates.append(data)

        scored_candidates.sort(key=lambda x: x["viral_score"], reverse=True)
        top_candidates = scored_candidates[:cfg.max_candidates_to_process]

        logger.info(f"🎯 [Phase 1: Scout] Selected top {len(top_candidates)} videos for ingestion:")
        for idx, item in enumerate(top_candidates, 1):
            logger.info(f"   #{idx} [{item['viral_score']:.1f} pts] {item['title'][:50]}... ({item['view_count']} views, {item['view_velocity']}/hr)")

        # Ingest top videos into /raw_videos/
        ingested = []
        for item in top_candidates:
            raw_path = self.download_source_stream(item["video_id"], item["url"])
            if raw_path:
                item["raw_video_path"] = raw_path
                self.db.update_video_ingested(item["video_id"], raw_path)
                ingested.append(item)

        return ingested

    def download_source_stream(self, video_id: str, url: str) -> Optional[str]:
        target_path = os.path.join(cfg.raw_videos_dir, f"{video_id}.mp4")
        if os.path.exists(target_path) and os.path.getsize(target_path) > 100000:
            logger.info(f"📂 [Phase 1: Scout] Source stream already present: {target_path}")
            return target_path

        logger.info(f"⬇️  [Phase 1: Scout] Ingesting source stream up to 1080p for {video_id}...")
        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "outtmpl": target_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if os.path.exists(target_path):
                logger.info(f"✅ [Phase 1: Scout] Saved raw capture ({os.path.getsize(target_path) // (1024*1024)} MB) to: {target_path}")
                return target_path
        except Exception as e:
            logger.error(f"❌ [Phase 1: Scout] Download failed for {video_id}: {e}")
        return None

    def _search_feed(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                if info and "entries" in info:
                    for e in info["entries"]:
                        if e and e.get("id"):
                            results.append({
                                "video_id": e["id"],
                                "title": e.get("title", ""),
                                "channel": e.get("uploader", "") or e.get("channel", ""),
                                "duration": e.get("duration") or 0,
                                "view_count": e.get("view_count") or 0,
                                "comment_count": e.get("comment_count") or 0,
                                "upload_timestamp": e.get("timestamp") or 0,
                                "url": f"https://www.youtube.com/watch?v={e['id']}"
                            })
        except Exception as e:
            logger.error(f"Search query error: {e}")
        return results
