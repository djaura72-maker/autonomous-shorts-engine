# ViceLoop GTA VI Viral Shorts Blueprint

## 1. The 28-45s Sweet Spot
Shorts under 15 seconds fail YouTube's absolute watch time and test-batch expansion requirements. Shorts over 50 seconds struggle to hit the >90-100% Average Percentage Viewed (APV) required to break through the 3,000-view ceiling.
- Target: 28 to 45 seconds.
- Pacing: 100-130 spoken words (approx 2.8 - 3.2 words per second).

## 2. The 4-Phase Retentive Hook-to-Loop Arc

```
[0-3s Hook] ➔ [3-18s Escalation] ➔ [18-32s Payoff + Debate] ➔ [32-40s Infinite Loop]
```

### Phase 1: 0-3s Pattern-Interrupt Hook
- Under 12 words.
- Starts on frame 1 (0.00s). No introductory filler ("Hey guys", "In this video", "Welcome back").
- Creates an immediate open loop or counter-intuitive shock.
- Examples:
  - *"Rockstar just confirmed the wildest police AI in GTA history."*
  - *"Lucia's prison ankle monitor isn't just a story device."*
  - *"You completely missed this Jason detail in the Leonida trailer."*

### Phase 2: 3-18s Escalation Loop
- Raise the stakes every 3 to 5 seconds.
- Introduce micro-reveals, gameplay physics, or NPC behavior mechanics.
- Pair each beat with visual punches (zoom in, pan, B-roll switch) every 2-3 seconds.

### Phase 3: 18-32s Payoff + Comment Debate Trigger
- Deliver the core answer or climactic gameplay moment.
- Immediately trigger audience engagement with a high-friction binary debate question:
  - *"Clean or Psycho? Vote below."*
  - *"Real or Rendered? Comment your take."*
  - *"Jason or Lucia? Who are you playing first?"*
- Comment velocity within the first 60 minutes signals high retention and triggers algorithmic distribution.

### Phase 4: 32-40s Infinite Grammatical Loop
- The closing sentence must end on a dangling connector that connects directly into the 0-3s opening line when the video loops back to 0.0s.
- Example:
  - Ending line: *"...and that is why everyone is starting to realize that—"*
  - Loops back to: *"Rockstar just confirmed the wildest police AI in GTA history."*

## 3. Visual & Kinetic Subtitle Rules
- 1 to 3 words on screen at any time.
- Dynamic color pop highlight on spoken word.
- Clamp word end timestamps (`end <= next_word_start`) to prevent overlapping text artifacts.
- Safe zone: Top 20% reserved for headline badges, bottom 25% cleared for YouTube Shorts player controls (channel name, sound, subscribe button).
