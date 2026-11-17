#!/usr/bin/env python3
"""
One-click batch publisher for all scheduled shorts in ready_to_upload/.
Iterates through packages, checks metadata.json, and uploads to YouTube Data API v3
with publishAt scheduling.
"""
import glob
import json
import logging
import os
import sys

from publisher_agent import PublisherAgent, PublisherConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("UploadScheduler")

def main():
    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    ready_dir = os.path.join(pipeline_dir, "ready_to_upload")
    
    config = PublisherConfig(
        client_secrets_path=os.path.join(pipeline_dir, "client_secrets.json"),
        token_path=os.path.join(pipeline_dir, "youtube_token.json")
    )
    publisher = PublisherAgent(config)
    
    packages = sorted(glob.glob(os.path.join(ready_dir, "short_*")))
    logger.info(f"Found {len(packages)} shorts in {ready_dir}")
    
    success_count = 0
    quota_hit = False
    
    for pkg in packages:
        meta_path = os.path.join(pkg, "metadata.json")
        video_path = os.path.join(pkg, "short.mp4")
        thumb_path = os.path.join(pkg, "thumbnail.jpg")
        
        if not os.path.exists(meta_path) or not os.path.exists(video_path):
            continue
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        if meta.get("uploaded"):
            logger.info(f"⏭️  Already uploaded: {meta.get('title')} (ID: {meta.get('video_id')})")
            continue
            
        logger.info(f"🚀 Uploading: {meta.get('title')}")
        logger.info(f"   Scheduled for: {meta.get('publish_at')}")
        
        try:
            res = publisher.upload_short(
                video_path=video_path,
                title=meta["title"],
                description=meta["description"],
                tags=meta.get("tags", []),
                scheduled_publish_time=meta.get("publish_at"),
                thumbnail_path=thumb_path if os.path.exists(thumb_path) else None
            )
            
            if res.get("uploaded"):
                meta["uploaded"] = True
                meta["video_id"] = res["video_id"]
                meta["youtube_url"] = res["url"]
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
                logger.info(f"✅ Success! URL: {res['url']}")
                success_count += 1
            else:
                err = str(res.get("error", ""))
                logger.warning(f"⚠️  Upload deferred: {err}")
                if "uploadLimitExceeded" in err:
                    quota_hit = True
                    break
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            if "uploadLimitExceeded" in str(e):
                quota_hit = True
                break

    print(f"\nUpload summary: {success_count}/{len(packages)} uploaded.")
    if quota_hit:
        print("Note: YouTube daily upload limit is currently active on your channel.")
        print("Run this script again once YouTube resets your daily rolling limit (typically 24 hours):")
        print(f"  cd {pipeline_dir} && python3 upload_all_scheduled.py")

if __name__ == "__main__":
    main()
