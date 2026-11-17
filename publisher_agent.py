"""
Phase 7: Automated Packaging, Upload, & Scheduling (Publisher Agent).
Packages finalized MP4 and metadata into /ready_to_upload/, authenticates with YouTube Data API v3,
uploads with privacyStatus: "private", and assigns automated ISO 8601 publishAt schedule.
"""
import os
import json
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from config import cfg
from database import Database

logger = logging.getLogger("Engine.PublisherAgent")

VIRAL_TAGS = [
    "#Shorts", "#viral", "#trending", "#mindset", "#success",
    "#podcast", "#advice", "#motivation", "#lifehacks"
]

class PublisherAgent:
    def __init__(self, db: Database):
        self.db = db
        os.makedirs(cfg.ready_to_upload_dir, exist_ok=True)

    def package_and_schedule(
        self,
        video_data: Dict[str, Any],
        script_manifest: Dict[str, Any],
        processed_video_path: str,
        clip_id: int
    ) -> Dict[str, Any]:
        """
        Export final asset to /ready_to_upload/, build metadata, and queue for YouTube API scheduling.
        """
        video_id = video_data["video_id"]
        clip_idx = script_manifest["clip_index"]
        headline_badge = script_manifest["headline_badge"]
        hook_line = script_manifest["hook_line"]

        safe_title = "".join(c for c in video_data["title"][:25] if c.isalnum() or c in " -_").strip()
        package_dir = os.path.join(cfg.ready_to_upload_dir, f"{video_id}_clip{clip_idx}_{safe_title}")
        os.makedirs(package_dir, exist_ok=True)

        final_mp4_path = os.path.join(package_dir, "short.mp4")
        if os.path.abspath(processed_video_path) != os.path.abspath(final_mp4_path):
            subprocess.run(["cp", processed_video_path, final_mp4_path], check=True)

        # Extract Cover Thumbnail
        thumb_path = os.path.join(package_dir, "thumbnail.jpg")
        subprocess.run([
            "ffmpeg", "-v", "error", "-y",
            "-ss", "1.2",
            "-i", final_mp4_path,
            "-frames:v", "1",
            "-q:v", "2",
            thumb_path
        ], check=False)

        # Title Engineering (<60 chars, emojis, #shorts)
        clean_badge = headline_badge.title()
        title = f"{clean_badge} 🤯 #shorts"
        if len(title) > 60:
            title = f"{clean_badge[:45]} #shorts"

        # Description with creator attribution and timestamps
        channel = video_data.get("channel", "Original Creator")
        description = (
            f"{headline_badge}\n\n"
            f"{hook_line}\n\n"
            f"Original Video by {channel}: {video_data['url']}\n\n"
            f"Full credit to {channel} for the original broadcast.\n\n"
            f"#shorts #viral #mindset #podcast"
        )

        tags = list(dict.fromkeys(VIRAL_TAGS + [video_data.get("channel", "").replace(" ", "").lower()]))

        # Calculate Automated ISO 8601 publishAt Release Timestamp
        publish_dt = datetime.now(timezone.utc) + timedelta(hours=cfg.schedule_delay_hours)
        publish_at_iso = publish_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        metadata = {
            "video_id": video_id,
            "clip_index": clip_idx,
            "title": title,
            "description": description,
            "tags": tags,
            "category_id": "22",  # People & Blogs
            "privacy_status": "private",
            "publish_at": publish_at_iso,
            "video_file": final_mp4_path,
            "thumbnail_file": thumb_path if os.path.exists(thumb_path) else None,
            "source_url": video_data["url"],
            "source_channel": channel
        }

        meta_path = os.path.join(package_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"📦 [Phase 7: Publisher] Final asset packaged in /ready_to_upload/:")
        logger.info(f"   Video: {final_mp4_path}")
        logger.info(f"   Scheduled Release: {publish_at_iso} (privacy: private)")

        # Execute YouTube API Upload & Scheduling if credentials are present
        upload_result = self._execute_youtube_upload(metadata)

        youtube_id = upload_result.get("id") if upload_result else None
        status = "scheduled" if youtube_id else "packaged"

        self.db.update_clip_stage(clip_id, {
            "ready_video_path": final_mp4_path,
            "metadata_path": meta_path,
            "youtube_id": youtube_id,
            "privacy_status": "private",
            "scheduled_publish_at": publish_at_iso,
            "status": status
        })

        return metadata

    def _execute_youtube_upload(self, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Uploads asset via YouTube Data API v3 with privacyStatus: private and publishAt.
        """
        if not os.path.exists(cfg.youtube_client_secrets):
            logger.info("ℹ️  [Phase 7: Publisher] Note: YouTube client_secrets.json not found in root. Asset is packaged and queued in /ready_to_upload/.")
            return None

        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow

            SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
            creds = None
            if os.path.exists(cfg.youtube_token_file):
                creds = Credentials.from_authorized_user_file(cfg.youtube_token_file, SCOPES)

            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(cfg.youtube_client_secrets, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(cfg.youtube_token_file, "w") as token:
                    token.write(creds.to_json())

            youtube = build("youtube", "v3", credentials=creds)

            body = {
                "snippet": {
                    "title": meta["title"],
                    "description": meta["description"],
                    "tags": meta["tags"],
                    "categoryId": meta["category_id"]
                },
                "status": {
                    "privacyStatus": "private",
                    "publishAt": meta["publish_at"],
                    "selfDeclaredMadeForKids": False
                }
            }

            media = MediaFileUpload(meta["video_file"], chunksize=1024*1024*10, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            logger.info(f"🚀 [Phase 7: Publisher] Uploading Short to YouTube with scheduled publishAt={meta['publish_at']}...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"   Upload progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            logger.info(f"🎉 [Phase 7: Publisher] Successfully uploaded to YouTube: ID={video_id}")
            return response

        except Exception as e:
            logger.warning(f"⚠️  [Phase 7: Publisher] YouTube API upload error: {e}. Asset remains safe in /ready_to_upload/.")
            return None
