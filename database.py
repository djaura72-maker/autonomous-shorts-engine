"""
Database Persistence & State Tracking for Autonomous YouTube Shorts Engine.
"""
import sqlite3
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("Engine.Database")

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                channel TEXT,
                duration INTEGER,
                view_count INTEGER,
                comment_count INTEGER,
                upload_timestamp INTEGER,
                view_velocity REAL,
                engagement_ratio REAL,
                viral_score REAL,
                raw_video_path TEXT,
                status TEXT DEFAULT 'discovered', -- discovered, ingested, analyzed, completed, failed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                clip_index INTEGER,
                start_time REAL,
                end_time REAL,
                duration REAL,
                viral_score REAL,
                hook_headline TEXT,
                script_path TEXT,
                vo_audio_path TEXT,
                processed_video_path TEXT,
                ready_video_path TEXT,
                metadata_path TEXT,
                youtube_id TEXT,
                privacy_status TEXT,
                scheduled_publish_at TEXT,
                status TEXT DEFAULT 'segmented', -- segmented, scripted, voiced, edited, mixed, packaged, scheduled, failed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            );
            """)

    def is_video_processed(self, video_id: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
            return cur.fetchone() is not None

    def record_discovered_video(self, data: Dict[str, Any]):
        with self._get_conn() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO videos (
                video_id, title, channel, duration, view_count, comment_count,
                upload_timestamp, view_velocity, engagement_ratio, viral_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered')
            """, (
                data["video_id"], data["title"], data.get("channel", ""),
                data.get("duration", 0), data.get("view_count", 0),
                data.get("comment_count", 0), data.get("upload_timestamp", 0),
                data.get("view_velocity", 0.0), data.get("engagement_ratio", 0.0),
                data.get("viral_score", 0.0)
            ))

    def update_video_ingested(self, video_id: str, raw_video_path: str):
        with self._get_conn() as conn:
            conn.execute("""
            UPDATE videos
            SET status = 'ingested', raw_video_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE video_id = ?
            """, (raw_video_path, video_id))

    def update_video_status(self, video_id: str, status: str):
        with self._get_conn() as conn:
            conn.execute("""
            UPDATE videos SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE video_id = ?
            """, (status, video_id))

    def record_clip_segmented(self, video_id: str, clip_index: int, start: float, end: float, score: float, headline: str) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO clips (video_id, clip_index, start_time, end_time, duration, viral_score, hook_headline, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'segmented')
            """, (video_id, clip_index, start, end, round(end - start, 2), score, headline))
            return cur.lastrowid

    def update_clip_stage(self, clip_id: int, updates: Dict[str, Any]):
        fields = []
        vals = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            vals.append(v)
        vals.append(clip_id)
        with self._get_conn() as conn:
            conn.execute(f"UPDATE clips SET {', '.join(fields)} WHERE id = ?", tuple(vals))
