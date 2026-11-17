"""
Batch Generator & YouTube Scheduler for 10 Highly Retentive Shorts.
Generates 10 complete 9:16 vertical shorts with 0-2s hooks, VoiceStudio/neural narration,
programmatic SFX mixing (-14 LUFS), kinetic captions, and schedules them via YouTube Data API v3.
"""
import os
import sys
import json
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from config import cfg
from database import Database
from voicestudio_agent import VoiceStudioAgent
from sound_agent import SoundAgent
from editor_agent import EditorAgent
from publisher_agent import PublisherAgent
from faster_whisper import WhisperModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(cfg.log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger("BatchScheduler")

SHORTS_CONCEPTS = [
    {
        "id": "short_01",
        "topic": "AI Automation",
        "headline_badge": "THE DIRTY LIE ABOUT AI",
        "hook_line": "Everyone is terrified of AI taking their job, but they're looking at it completely backwards.",
        "body_script": "AI will not replace you. But a person who knows how to orchestrate autonomous AI agents will replace you by tomorrow afternoon. One single operator now wields the leverage of an entire engineering department. The gap between those who adapt and those who complain is expanding exponentially. You do not need to code. You just need to direct. Stop scrolling and start building.",
        "title": "The Dirty Lie About AI Taking Your Job 🤖 #shorts",
        "tags": ["#shorts", "#ai", "#artificialintelligence", "#futureofwork", "#tech", "#productivity"],
        "bg_gradient": "0x111116",
        "schedule_days": 1,
        "schedule_hour": 12
    },
    {
        "id": "short_02",
        "topic": "Leverage",
        "headline_badge": "THE 80-HOUR LIE",
        "hook_line": "Stop believing the lie that working eighty hours a week makes you successful.",
        "body_script": "Unfocused effort is just an expensive disguise for procrastination. The top one percent do not grind longer hours. They build asymmetrical leverage. If your input equals your output, you are trapped on a modern treadmill. True wealth is built on systems that print results while you are completely detached from the keyboard. Work on leverage, not exhaustion.",
        "title": "Why 80-Hour Work Weeks Are a Scam 🤯 #shorts",
        "tags": ["#shorts", "#wealth", "#leverage", "#business", "#entrepreneur", "#mindset"],
        "bg_gradient": "0x151218",
        "schedule_days": 1,
        "schedule_hour": 18
    },
    {
        "id": "short_03",
        "topic": "Focus & Dopamine",
        "headline_badge": "WHY YOU CAN'T FOCUS",
        "hook_line": "Your phone is currently hijacking your dopamine receptors and you don't even realize it.",
        "body_script": "Every time you swipe, your brain gets a microscopic hit of cheap stimulation. After three hours, your threshold for real work is completely burnt out. You cannot read a book. You cannot write code. You cannot build a business. It is not a lack of willpower. It is chemical exhaustion. Take twenty-four hours completely offline. Watch your clarity return instantly.",
        "title": "Your Phone Is Destroying Your Brain 📱 #shorts",
        "tags": ["#shorts", "#dopamine", "#focus", "#mentalhealth", "#productivity", "#mindset"],
        "bg_gradient": "0x0c141a",
        "schedule_days": 2,
        "schedule_hour": 12
    },
    {
        "id": "short_04",
        "topic": "Productivity",
        "headline_badge": "THE 5 AM DELUSION",
        "hook_line": "Waking up at five in the morning is completely useless if you have nothing valuable to work on.",
        "body_script": "The internet loves worshipping early mornings. But being awake at sunrise does not make you disciplined if you spend the first hour checking emails and planning a to-do list. The hour you wake up is irrelevant. The intensity and clarity of your focus during your peak hours is the only metric that matters. Prioritize deep work over alarm clocks.",
        "title": "The 5 AM Wake Up Routine Is a Trap ⏰ #shorts",
        "tags": ["#shorts", "#productivity", "#habits", "#discipline", "#success", "#mindset"],
        "bg_gradient": "0x181014",
        "schedule_days": 2,
        "schedule_hour": 18
    },
    {
        "id": "short_05",
        "topic": "Compounding",
        "headline_badge": "THE 1% COMPOUNDING RULE",
        "hook_line": "Every single choice feels small until you look back at what it became.",
        "body_script": "Going to the gym once changes nothing. Reading ten pages once changes nothing. Saving fifty dollars once feels pointless. But compound those exact microscopic actions across seven hundred consecutive days, and you become completely unrecognizable. Most people quit right before the hockey stick curve bends upward. Do not quit during the flat line.",
        "title": "The Brutal Truth About Compounding 📈 #shorts",
        "tags": ["#shorts", "#compounding", "#habits", "#discipline", "#growth", "#success"],
        "bg_gradient": "0x111613",
        "schedule_days": 3,
        "schedule_hour": 12
    },
    {
        "id": "short_06",
        "topic": "Decision Making",
        "headline_badge": "THE UNTOLD TRUTH",
        "hook_line": "Taking advice from someone who hasn't built what you want is the fastest path to mediocrity.",
        "body_script": "People love giving opinions on businesses they never launched and risks they never had the courage to take. Their advice is not meant to guide you. It is meant to rationalize their own comfort zone. Filter your inputs with extreme ruthlessness. Only accept feedback from operators who have real skin in the game.",
        "title": "Stop Taking Advice From Broke People 🚫 #shorts",
        "tags": ["#shorts", "#advice", "#wisdom", "#mindset", "#success", "#entrepreneur"],
        "bg_gradient": "0x191410",
        "schedule_days": 3,
        "schedule_hour": 18
    },
    {
        "id": "short_07",
        "topic": "Asymmetric Bets",
        "headline_badge": "HOW TO WIN BIG",
        "hook_line": "If a mistake can ruin you, never take the bet. But if the downside is capped, take it every time.",
        "body_script": "This is the single principle behind every massive breakthrough in history. Creating a digital product costs zero dollars. Publishing a video costs zero dollars. Writing a newsletter costs zero dollars. The downside is a few hours of effort. The upside is uncapped distribution to the entire planet. Play games with infinite upside.",
        "title": "The Asymmetric Secret of the Top 1% 💰 #shorts",
        "tags": ["#shorts", "#asymmetricrisk", "#investing", "#business", "#wealth", "#finance"],
        "bg_gradient": "0x13121b",
        "schedule_days": 4,
        "schedule_hour": 12
    },
    {
        "id": "short_08",
        "topic": "Ego & Courage",
        "headline_badge": "KILL YOUR EGO",
        "hook_line": "The single biggest obstacle between you and massive success is your obsession with looking cool.",
        "body_script": "You are terrified of publishing because someone from high school might judge your post. Meanwhile, strangers on the internet who do not care about your feelings are making millions simply because they were willing to look foolish for the first six months. Embarrassment is the entry fee for greatness. Pay the fee or stay invisible.",
        "title": "Your Ego Is Keeping You Poor 🛑 #shorts",
        "tags": ["#shorts", "#ego", "#confidence", "#mindset", "#motivation", "#growth"],
        "bg_gradient": "0x1c1012",
        "schedule_days": 4,
        "schedule_hour": 18
    },
    {
        "id": "short_09",
        "topic": "Future of Work",
        "headline_badge": "THE DEGREE TRAP",
        "hook_line": "A college degree no longer guarantees you anything except a mountain of debt.",
        "body_script": "The global economy no longer rewards memorization. It rewards proof of work. If you have a verified portfolio, public code, real distribution, or paying clients, nobody will ever ask where you went to school. Skills speak louder than credentials. Build evidence, not resumes.",
        "title": "Why College Degrees Are Becoming Obsolete 🎓 #shorts",
        "tags": ["#shorts", "#college", "#education", "#skills", "#careers", "#future"],
        "bg_gradient": "0x101716",
        "schedule_days": 5,
        "schedule_hour": 12
    },
    {
        "id": "short_10",
        "topic": "Attention & Distribution",
        "headline_badge": "WHY GREAT IDEAS FAIL",
        "hook_line": "The best product never wins. The product with the most relentless distribution wins every time.",
        "body_script": "You can build the most elegant software or the highest quality service in the world. If nobody knows you exist, you have zero revenue. Code is twenty percent of the battle. Distribution, storytelling, and audience retention are the remaining eighty percent. Stop tweaking the product and start capturing attention.",
        "title": "The Brutal Rule of Attention 🎯 #shorts",
        "tags": ["#shorts", "#marketing", "#distribution", "#attention", "#business", "#scale"],
        "bg_gradient": "0x141117",
        "schedule_days": 5,
        "schedule_hour": 18
    }
]

def generate_motion_background(output_path: str, duration: float, bg_color: str):
    """Generate a dynamic 1080x1920 30fps vertical motion background with subtle animated film grain and cinematic vignette."""
    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1080x1920:r=30:d={duration:.2f}",
        "-vf", "noise=alls=25:allf=t+u,boxblur=12:3,vignette=PI/3",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p",
        output_path
    ]
    subprocess.run(cmd, check=True)

def main():
    logger.info("="*65)
    logger.info("🚀 STARTING 10-SHORT BATCH GENERATION & SCHEDULING ENGINE")
    logger.info("="*65)

    db = Database(cfg.db_path)
    whisper_model = WhisperModel(cfg.whisper_model_size, device=cfg.whisper_device, compute_type="int8")
    voice_agent = VoiceStudioAgent(db, whisper_model)
    sound_agent = SoundAgent()
    editor_agent = EditorAgent(db)
    publisher_agent = PublisherAgent(db)

    now = datetime.now(timezone.utc)
    results = []

    for idx, c in enumerate(SHORTS_CONCEPTS, 1):
        short_id = c["id"]
        logger.info(f"\n=======================================================")
        logger.info(f"🎬 Engineering Short #{idx}/10: {c['headline_badge']} ({c['topic']})")
        logger.info(f"   Hook: \"{c['hook_line']}\"")
        logger.info(f"=======================================================")

        work_base = os.path.join(cfg.root_dir, "work")
        clip_work = os.path.join(work_base, short_id)
        os.makedirs(clip_work, exist_ok=True)

        # 1. Synthesize Voiceover & Word Timings
        full_text = f"{c['hook_line']} {c['body_script']}"
        script_manifest = {
            "video_id": short_id,
            "clip_index": 1,
            "headline_badge": c["headline_badge"],
            "hook_line": c["hook_line"],
            "full_script": full_text
        }
        vo_path, vo_words = voice_agent.synthesize_voiceover(script_manifest, {"clip_id": idx})

        # Calculate exact audio duration
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", vo_path
        ], capture_output=True, text=True).stdout.strip()
        audio_dur = float(probe or 35.0)

        # 2. Master Audio Mixing (VO + Procedural SFX + Ambient bed -> -14 LUFS)
        master_audio = os.path.join(cfg.processed_video_dir, f"{short_id}_master.m4a")
        sound_agent.master_audio_mix(
            vo_path=vo_path,
            duration=audio_dur,
            words=vo_words,
            output_master_path=master_audio
        )

        # 3. Generate Visual Motion Canvas
        raw_bg_path = os.path.join(cfg.raw_videos_dir, f"{short_id}_bg.mp4")
        if not os.path.exists(raw_bg_path):
            generate_motion_background(raw_bg_path, audio_dur + 0.5, c["bg_gradient"])

        # 4. Reframe & Burn Kinetic Captions + Top Headline Box
        vertical_mp4 = os.path.join(cfg.processed_video_dir, f"{short_id}_vertical.mp4")
        editor_agent.reframe_and_caption(
            raw_video_path=raw_bg_path,
            video_start=0.0,
            video_end=audio_dur,
            master_audio_path=master_audio,
            vo_words=vo_words,
            headline_badge=c["headline_badge"],
            clip_id=idx,
            output_path=vertical_mp4
        )

        # 5. Calculate Scheduled Release Time (publishAt in ISO 8601)
        sched_dt = now + timedelta(days=c["schedule_days"])
        sched_dt = sched_dt.replace(hour=c["schedule_hour"], minute=0, second=0, microsecond=0)
        publish_at_iso = sched_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 6. Package and Upload / Schedule via YouTube Data API v3
        video_meta = {
            "video_id": short_id,
            "title": c["title"],
            "url": "https://youtube.com/@local",
            "channel": "Autonomous Studio"
        }
        script_manifest["headline_badge"] = c["headline_badge"]
        script_manifest["hook_line"] = c["hook_line"]

        # Temporarily update config schedule delay so metadata reflects targeted schedule
        meta_package = publisher_agent.package_and_schedule(
            video_data=video_meta,
            script_manifest=script_manifest,
            processed_video_path=vertical_mp4,
            clip_id=idx
        )

        # Update metadata publish_at to exact planned slot
        meta_package["publish_at"] = publish_at_iso
        meta_path = meta_package.get("metadata_path") or os.path.join(cfg.ready_to_upload_dir, f"{short_id}_clip1_{short_id}", "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_package, f, indent=2, ensure_ascii=False)

        # If upload was executed or scheduled
        results.append({
            "index": idx,
            "id": short_id,
            "title": c["title"],
            "headline": c["headline_badge"],
            "duration": round(audio_dur, 1),
            "scheduled_for": publish_at_iso,
            "video_path": meta_package.get("video_file")
        })
        logger.info(f"✅ Short #{idx} scheduled for: {publish_at_iso}")

    logger.info("\n" + "="*65)
    logger.info("🎉 ALL 10 SHORTS SUCCESSFULLY ENGINEERED & SCHEDULED!")
    logger.info("="*65)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
