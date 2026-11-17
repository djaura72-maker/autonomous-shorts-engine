#!/usr/bin/env python3
"""
Retentive VoiceOver Script Generator for ViceLoop GTA VI Engine.
Engineers 35-45s (100-130 words) scripts structured as:
Hook (0-3s) -> Escalation (3-18s) -> Payoff & Comment Trigger (18-32s) -> Seamless Loop (32-40s).
"""
import argparse
import json
import os
import re
import sys

DEBATE_TRIGGERS = [
    "Clean or Psycho? Vote below.",
    "Real or Overrated? Comment below.",
    "Jason or Lucia? Who are you playing first?",
    "First day cop chase or explore Vice City? Drop your take.",
    "Brilliant game physics or too realistic? Vote in comments."
]

def engineer_script(topic: str, raw_text: str = None) -> dict:
    """
    Constructs a 4-phase viral hook-to-loop script.
    """
    clean_topic = topic.strip()
    
    # Standardize hook
    hook = f"Rockstar just hid the most dangerous detail in GTA 6."
    if "cop" in clean_topic.lower() or "police" in clean_topic.lower():
        hook = "The new police AI in GTA 6 won't just arrest you."
    elif "lucia" in clean_topic.lower():
        hook = "Lucia's prison ankle monitor is hiding a massive secret."
    elif "jason" in clean_topic.lower():
        hook = "Everyone got Jason's military background completely wrong."
    elif "map" in clean_topic.lower() or "vice city" in clean_topic.lower():
        hook = "The Vice City map size is triple what leakers predicted."
    elif raw_text:
        # Extract first key sentence, under 12 words
        first_sent = raw_text.split(".")[0].strip()
        words = first_sent.split()
        if len(words) <= 12 and len(words) >= 4:
            hook = " ".join(words)
            
    escalation = (
        "Look closely at the Leonida patrol routes. When you pull a weapon in broad daylight, "
        "the local dispatch doesn't instantly teleport squad cars. Instead, witnesses pull out their phones, "
        "recording your license plates and uploading footage in real-time."
    )
    
    payoff_lead = (
        "By the time backup arrives, SWAT has blocked every highway exit out of Vice City. "
        "You either ditch your vehicle or face an airtight roadblock."
    )
    
    comment_trigger = DEBATE_TRIGGERS[0]
    if "lucia" in clean_topic.lower() or "jason" in clean_topic.lower():
        comment_trigger = DEBATE_TRIGGERS[2]
    elif "police" in clean_topic.lower() or "cop" in clean_topic.lower():
        comment_trigger = DEBATE_TRIGGERS[0]
        
    loop_connector = (
        "Which leaves you with one impossible choice: escape clean or go full psycho? Vote below. "
        "Because if you mess up even once, you'll discover why—"
    )
    
    full_voiceover = f"{hook} {escalation} {payoff_lead} {loop_connector}"
    words = full_voiceover.split()
    
    script_data = {
        "topic": clean_topic,
        "word_count": len(words),
        "estimated_duration_sec": round(len(words) / 2.8, 1),
        "phases": {
            "hook_0_3s": hook,
            "escalation_3_18s": escalation,
            "payoff_18_32s": payoff_lead,
            "debate_trigger": comment_trigger,
            "loop_connector_32_40s": loop_connector
        },
        "full_text": full_voiceover,
        "pinned_comment": f"Question of the day: {comment_trigger}",
        "headline_badge": hook.split()[0:4]
    }
    script_data["headline_badge"] = " ".join(hook.split()[0:4]).upper().replace(".", "")
    return script_data

def main():
    parser = argparse.ArgumentParser(description="Generate 4-Phase Retentive Script")
    parser.add_argument("--topic", default="GTA 6 Police AI", help="Topic or title")
    parser.add_argument("--raw", help="Optional raw transcript excerpt")
    parser.add_argument("--out", help="Output JSON path")
    args = parser.parse_args()
    
    script = engineer_script(args.topic, args.raw)
    
    print("\n" + "="*60)
    print("🎬 VICE-LOOP RETENTIVE SCRIPT GENERATED")
    print(f"   Word Count: {script['word_count']} words (~{script['estimated_duration_sec']}s)")
    print(f"   Top Badge: [{script['headline_badge']}]")
    print("="*60)
    print(f"0-3s HOOK:          {script['phases']['hook_0_3s']}")
    print(f"3-18s ESCALATION:   {script['phases']['escalation_3_18s']}")
    print(f"18-32s PAYOFF:      {script['phases']['payoff_18_32s']}")
    print(f"32-40s LOOP:        {script['phases']['loop_connector_32_40s']}")
    print(f"PINNED COMMENT:     {script['pinned_comment']}")
    print("="*60)
    
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)
        print(f"💾 Saved to: {args.out}")

if __name__ == "__main__":
    main()
