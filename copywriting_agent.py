"""
Phase 3: Hook-Optimized Script Engineering (Copywriting Agent).
Applies the 0-2 Second Hook Rule (open loops, contrarian assertions, psychological pattern interrupts),
structures high-retention body copy with short sentences and zero jargon, and saves to /scripts/.
"""
import os
import re
import json
import logging
from typing import Dict, Any, List
from config import cfg
from database import Database

logger = logging.getLogger("Engine.CopywritingAgent")

HOOK_PATTERNS = {
    "open_loop": [
        "Nobody wants to admit this about {topic}, but it changes everything.",
        "There is a hidden reason why top performers dominate {topic}.",
        "What you are not being told about {topic} will shock you."
    ],
    "contrarian": [
        "Everything you've been taught about {topic} is completely backwards.",
        "Stop approaching {topic} the way everyone else does.",
        "The biggest lie in modern {topic} is this."
    ],
    "direct_callout": [
        "If you are still struggling with {topic}, listen very closely.",
        "If you want to master {topic} in 2026, stop making this fatal mistake.",
        "You are losing massive momentum every single day with {topic}."
    ],
    "shocking_stat": [
        "99% of people fail at {topic} because of this one blindspot.",
        "This one simple pivot in {topic} changed my entire career.",
        "Only 1 in 1,000 people truly understand how {topic} works."
    ]
}

RETENTION_BRIDGES = [
    "Here is the brutal truth.",
    "Look closely at what happens next.",
    "Pay very close attention right here.",
    "And it gets even crazier.",
    "Most people completely overlook this."
]

class CopywritingAgent:
    def __init__(self, db: Database):
        self.db = db
        os.makedirs(cfg.scripts_dir, exist_ok=True)

    def engineer_script(self, video_data: Dict[str, Any], segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rewrite raw segment transcript into a hook-engineered voiceover script.
        Saves output to /scripts/<video_id>_clip<idx>_script.json.
        """
        video_id = video_data["video_id"]
        clip_idx = segment_data["clip_index"]
        raw_text = segment_data["raw_text"]
        title = video_data["title"]

        logger.info(f"✍️  [Phase 3: Copywriter] Engineering hook script for Clip #{clip_idx}...")

        # 1. Identify Topic
        topic = self._extract_topic(title, raw_text)

        # 2. Apply 0-2 Second Hook Rule
        hook_line, framework = self._engineer_hook(topic, raw_text)

        # 3. Optimize Body Copy (Short sentences, fast pacing, zero filler)
        clean_body = self._optimize_spoken_body(raw_text)

        # 4. Integrate Retention Bridge
        script_sentences = [hook_line]
        mid = max(1, len(clean_body) // 2)
        for idx, sentence in enumerate(clean_body):
            if idx == mid and len(clean_body) > 3:
                script_sentences.append(RETENTION_BRIDGES[hash(topic) % len(RETENTION_BRIDGES)])
            script_sentences.append(sentence)

        full_script = " ".join(script_sentences)
        word_count = len(full_script.split())
        est_duration = round(word_count / cfg.target_spoken_wps, 1)

        # Top 3-5 word high-contrast headline box
        headline_badge = self._engineer_headline_badge(hook_line, topic)

        script_manifest = {
            "video_id": video_id,
            "clip_index": clip_idx,
            "hook_framework": framework,
            "hook_line": hook_line,
            "headline_badge": headline_badge,
            "body_sentences": clean_body,
            "full_script": full_script,
            "word_count": word_count,
            "estimated_duration": est_duration,
            "topic": topic
        }

        script_path = os.path.join(cfg.scripts_dir, f"{video_id}_clip{clip_idx}_script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script_manifest, f, indent=2, ensure_ascii=False)

        # Update database
        self.db.update_clip_stage(segment_data["clip_id"], {
            "script_path": script_path,
            "hook_headline": headline_badge,
            "status": "scripted"
        })

        logger.info(f"💾 [Phase 3: Copywriter] Script engineered ({word_count} words, ~{est_duration}s) -> {script_path}")
        logger.info(f"   Hook: \"{hook_line}\"")
        logger.info(f"   Badge: \"{headline_badge}\"")

        return script_manifest

    def _extract_topic(self, title: str, text: str) -> str:
        words = re.findall(r"\b[A-Za-z]{4,}\b", title)
        stop = {"this", "that", "with", "from", "video", "full", "episode", "podcast", "shorts", "clip"}
        candidates = [w for w in words if w.lower() not in stop]
        return candidates[0].capitalize() if candidates else "Success"

    def _engineer_hook(self, topic: str, text: str) -> (str, str):
        t_low = text.lower()
        if "mistake" in t_low or "wrong" in t_low or "lie" in t_low:
            fw = "contrarian"
        elif "secret" in t_low or "truth" in t_low or "nobody" in t_low:
            fw = "open_loop"
        elif "you" in t_low or "stop" in t_low:
            fw = "direct_callout"
        else:
            fw = "shocking_stat"

        templates = HOOK_PATTERNS[fw]
        chosen = templates[hash(topic) % len(templates)]
        return chosen.format(topic=topic), fw

    def _optimize_spoken_body(self, text: str) -> List[str]:
        raw = re.split(r"[.!?]+", text)
        clean = []
        for s in raw:
            s_clean = s.strip()
            # Remove filler phrases
            s_clean = re.sub(r"\b(um|uh|you know|literally|basically|sort of|kind of|i mean)\b", "", s_clean, flags=re.I)
            s_clean = re.sub(r"\s+", " ", s_clean).strip()
            words = s_clean.split()
            if len(words) >= 4:
                if len(words) > 13:
                    half = len(words) // 2
                    clean.append(" ".join(words[:half]) + ".")
                    clean.append(" ".join(words[half:]) + ".")
                else:
                    clean.append(s_clean + ".")
        return clean[:6]

    def _engineer_headline_badge(self, hook: str, topic: str) -> str:
        h_low = hook.lower()
        if "backwards" in h_low or "lie" in h_low:
            return "THE DIRTY LIE"
        elif "secret" in h_low or "admit" in h_low:
            return "THE UNTOLD TRUTH"
        elif "mistake" in h_low or "stop" in h_low:
            return "STOP DOING THIS"
        elif "99%" in h_low:
            return "WHY 99% FAIL"
        else:
            return f"THE REALITY OF {topic.upper()}"
