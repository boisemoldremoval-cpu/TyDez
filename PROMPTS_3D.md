# TyGuy — Pixar-Style 3D Prompt Pack for **Veo** 🎬

Tailored for **Google Veo 3** (via Gemini app, Google AI Studio, Vertex AI, or **Flow**).
Veo 3 generates **native audio** — dialogue, sound effects, and music — and produces
**~8-second** cinematic shots at 16:9. Generate each shot, send me the clips, and I'll
sequence them and splice **your intro → the 3D story → your outro** (and add/clean audio
if you want).

---

## Veo tips that matter (read first)

- **One shot per prompt, ≤ 8 seconds.** Don't cram multiple actions; describe a single
  continuous moment.
- **Structure each prompt:** `Subject (look) → Action → Setting → Camera → Lighting/Mood
  → Style → Audio/Dialogue`. Veo responds well to that order.
- **Dialogue:** put the spoken line in quotes and say who speaks it. Veo will voice it.
  Always add **“no subtitles, no on-screen text”** or Veo may burn in captions.
- **Negative prompt** goes in Veo's separate *Negative prompt* field — don't write
  "no X" in the main prompt (use the field instead).
- **Character consistency:** use **Flow** and generate a TyGuy **reference image** first
  (Imagen), then add it as an *ingredient / reference* for every shot. Keep the TyGuy
  description **word-for-word identical** each time. Reusing the reference is what keeps
  him on-model across shots.
- **Settings:** 16:9, 1080p if available, 24fps.

**Negative prompt (paste into Veo's Negative field for every shot):**
> subtitles, captions, on-screen text, watermark, logo, distorted face, extra fingers,
> extra limbs, flat 2D, hand-drawn, low quality, blurry, deformed

---

## Reference identities (keep wording identical every time)

**TyGuy:** a friendly, upbeat young man in his late 20s with warm tan skin, short
dark-brown spiky quiff hair with neatly faded sides, light stubble, thick dark eyebrows,
big genuine smile, expressive brown eyes. He wears a **royal-blue pullover hoodie with a
bold white “T” on the chest** and white drawstrings, black joggers, and **royal-blue
high-top sneakers with white soles**. Rendered as an appealing **Pixar-style 3D character**
with slightly caricatured proportions (larger head, very expressive face).

**Mia:** a shy 9-year-old girl with fair skin, brown hair in a side ponytail, big
expressive eyes, wearing a coral-pink top, blue jeans, and white sneakers. Same Pixar 3D
look.

**Global style suffix (append to each prompt):** *Pixar/Disney-style 3D animation,
cinematic three-point lighting, soft global illumination, subsurface-scattering skin,
shallow depth of field, warm vibrant colors, volumetric sunlight, high-detail studio
render, family-friendly.*

---

## SHOT LIST — "The New Kid" (8 × ~8s)

> Paste TyGuy/Mia description + the shot text + the style suffix into the prompt box, and
> the negative prompt into the negative field.

**Shot 1 — Establish**
> A Pixar-style 3D young girl, **Mia** *(paste Mia description)*, sits alone on a wooden
> bench in a sunny, cheerful elementary-school yard — green grass, a big leafy tree, fluffy
> clouds, a friendly two-story school building behind her. She slumps her shoulders and
> looks down at her backpack, lonely. **Camera:** slow cinematic dolly-in from a wide shot.
> **Mood:** gentle, a little lonely, hopeful. **Audio:** soft ambient playground sounds,
> distant kids, birds; warm mellow piano. **No subtitles, no on-screen text.**

**Shot 2 — Ignored**
> Two cheerful Pixar-style 3D kids walk past **Mia** *(paste Mia)*, chatting and laughing,
> not noticing her; Mia watches them pass then lowers her head. Same schoolyard. **Camera:**
> medium tracking shot following the kids past the bench. **Mood:** slightly lonely.
> **Audio:** kids laughing as they pass, footsteps; soft wistful score. *Mia (quiet sigh).*
> **No subtitles, no on-screen text.**

**Shot 3 — TyGuy notices**
> **TyGuy** *(paste TyGuy description)* stands a short distance away and notices Mia sitting
> alone; his grin softens into a warm, caring expression. **Camera:** over-the-shoulder from
> behind TyGuy looking toward lonely Mia, then a gentle push-in on his kind face.
> **Lighting:** warm sunlight. **Audio:** TyGuy says warmly, *"Hey there! Are you new here?"*
> gentle hopeful music. **No subtitles, no on-screen text.**

**Shot 4 — The welcome**
> **TyGuy** *(paste TyGuy)* walks over and crouches to Mia's eye level beside the bench,
> smiling warmly with an open, friendly gesture; **Mia** looks up, surprised and hopeful.
> **Camera:** smooth medium two-shot, slight arc around them. **Lighting:** warm golden
> sun. **Audio:** TyGuy says cheerfully, *"Hi, I'm Ty! Come hang out with us!"* uplifting
> music swells gently. **No subtitles, no on-screen text.**

**Shot 5 — Mia lights up**
> **Mia** *(paste Mia)* breaks into a big joyful smile, eyes bright, cheeks blushing, with a
> happy little bounce. **Camera:** medium close-up, subtle push-in. **Lighting:** warm, soft
> bokeh sparkles behind her. **Audio:** Mia says brightly, *"Really? Thank you!"* warm
> heartfelt music. **No subtitles, no on-screen text.**

**Shot 6 — Together**
> **TyGuy** and **Mia** *(paste both)* walk side by side across the schoolyard toward a small
> group of welcoming kids, both smiling and chatting happily. **Camera:** tracking shot
> moving with them, slight low angle. **Lighting:** golden, uplifting. **Audio:** cheerful
> kids greeting them, warm triumphant music. **Narrator (warm):** *"One small kindness
> changed her whole day."* **No subtitles, no on-screen text.**

**Shot 7 — Scripture beat**
> **TyGuy** *(paste TyGuy)* stands in soft, bright, heavenly light with gentle golden
> sparkles and subtle glowing cross motifs in the background, hand on his heart, looking to
> camera with a warm, sincere expression. **Camera:** slow reverent push-in. **Audio:**
> TyGuy says sincerely, *"Be kind to one another, tender-hearted, forgiving one another."*
> soft inspirational strings. **No subtitles, no on-screen text.**

**Shot 8 — Outro tie-in**
> **TyGuy** *(paste TyGuy)* faces camera and gives an enthusiastic thumbs-up with a big
> grin and an energetic pose; bright brand-blue background with golden sparkle accents and
> floating golden crosses. **Camera:** dynamic slight zoom-in. **Audio:** TyGuy says
> energetically, *"Be kind, have fun, and be you!"* upbeat playful music sting.
> **No subtitles, no on-screen text.**

---

## Audio: two options
- **Let Veo voice it (simplest):** keep the dialogue lines above; Veo 3 generates the
  speech, SFX, and music per clip. I'll just sequence the clips + add your intro/outro.
- **Or clean plates + my audio:** remove the dialogue lines (keep only ambient/music
  cues), and I'll lay in TyGuy's & Mia's voices (TTS) and a consistent music bed across
  the whole film so the audio matches end-to-end.

## When you send the clips (`shot1.mp4 … shot8.mp4`)
I'll: trim to the beats, sequence shots 1–8, normalize/clean the audio (or add voices +
music), add optional Scripture captions, then splice **your intro → 3D story → your
outro** and export the final movie at 1080p.

> If TyGuy looks different between shots, regenerate with the **same reference image** in
> Flow + the identical description — that's the fix for consistency.
