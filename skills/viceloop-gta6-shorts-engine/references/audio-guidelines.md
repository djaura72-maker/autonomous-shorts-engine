# ViceLoop Audio Mastering & Copyright Safety Guidelines

## 1. Zero Copyrighted Audio Policy
- **The Threat:** Rockstar Games trailers utilize licensed commercial music (e.g., Tom Petty - "Love Is a Long Road"). Livestreams frequently play copyrighted Spotify/radio music in the background. Content ID triggers instant monetization claims, visibility restrictions, or regional blocks.
- **The Protocol:**
  1. Completely strip or isolate source background music tracks from game SFX and speech using bandpass filtering, stem isolation, or full audio replacement.
  2. If using gameplay footage, retain or synthesize clean in-game sound effects (engines, gunshots, crowd chatter) while wiping any licensed radio music.
  3. Replace all background score with royalty-free synthwave, dark phonk, or cinematic ambient beds.

## 2. Loudness Specifications (EBU R128)
- VoiceOver narration track: `-12.0` to `-14.0 LUFS`.
- Background music (BGM): Ducked under speech to **-24 dB relative to speech** (approx 10-15% linear volume).
- Sound Effects (SFX):
  - 808 Sub-Impact at 0.0s hook: `-6 dBTP` peak.
  - Transition whooshes & risers: `-16 dBFS`.
  - Word pop clicks: `-18 dBFS`.
- Final Integrated Master: Exactly **`-14.0 LUFS`** with True Peak **`-1.5 dBTP`** and Max Loudness Range **`11.0 LU`**.

## 3. VoiceStudio Profile Tuning
- Model: Fast neural speech synthesis or cloned voice profile.
- Delivery style: Confident, fast-paced (145-165 WPM), conversational, zero vocal fry.
- Timestamp synchronization: Extract exact word boundaries via faster-whisper on the synthesized narration file before burning captions into ASS.
