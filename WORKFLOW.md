# Video Generation Workflow — TyGuy & Kelliee Bible Adventures

A workflow app that turns one small JSON spec into a complete, ready-to-shoot
package of **Veo / Gemini** prompts and production files for a Christian cartoon
Bible lesson — built so **TyGuy** (lead) and **Kelliee** (sidekick) look and
sound identical in every episode, and every episode hits the same teaching arc.

It's a single, dependency-free script: [`video_workflow.py`](video_workflow.py).

## What it builds

For each episode it scaffolds exactly this:

```
Videos/
  Episodes/
    Episode_001/
      script.txt            # full script: verse, lesson, scenes, dialogue
      character_sheet.txt   # locked descriptions for every character
      style_guide.txt       # look, palette, rendering, audio, negatives
      scene_prompts/
        scene_01.txt        # copy-paste Veo prompt + full breakdown
        scene_02.txt
        ...
      voiceover.txt         # narrator script, line by line
      checklist.txt         # final pre-generation checklist
```

## The required story beats (every episode)

The app verifies all seven are present and tags each scene with its beat:

1. **Bible verse** — the verse is introduced
2. **Life lesson** — the simple, kid-sized takeaway
3. **The problem** — a relatable situation goes wrong
4. **Wrong reaction** — someone responds the wrong way
5. **Biblical correction** — Scripture corrects the reaction
6. **Peaceful ending** — things are made right, calm and joyful
7. **Call to follow Jesus** — a warm closing invitation

If any beat (or the verse / lesson / recurring characters) is missing, the
build prints a warning so you fix it before spending Veo credits.

## Each scene prompt contains

Every `scene_NN.txt` has a clean **copy-paste block** for Veo/Gemini followed
by a labeled breakdown covering:

- Video style · Main character description · Location · Action
- Camera angle · Lighting · Mood · Dialogue
- **What must stay consistent** · **What NOT to show**
- **Ending frame** — written to flow straight into the next clip

The copy-paste prompt is one flowing cinematic paragraph (the order Veo
prefers: style → subject → action → setting → camera → light → mood →
dialogue → audio), plus a separate negative-prompt line. Clips stay **4–8s**.

## Character consistency

TyGuy and Kelliee are defined **once** in the series bible
([`series.json`](series.json)) and inherited by every episode automatically —
so their descriptions are word-for-word identical every time. Episodes only
add *guest* characters (e.g. a kid in one story).

To pair this with image-seeding for even tighter consistency, generate each
clip seeded from a reference image of TyGuy (see `veo_gen.py` /
`tyguy_seed.png` in this repo).

## Usage

```bash
# Build the bundled example episode ("Taking Turns")
python3 video_workflow.py demo

# Start a new episode from a blank template
python3 video_workflow.py template episode_002.json
# ...edit episode_002.json (TyGuy & Kelliee are inherited — only add guests)...
python3 video_workflow.py build episode_002.json

# Edit the shared TyGuy/Kelliee bible if their look ever changes
python3 video_workflow.py series series.json

# Build into a custom location / with a custom bible
python3 video_workflow.py build episode_002.json --base /path/to/Videos --series series.json
```

[`example_episode.json`](example_episode.json) is a real, editable spec you can
copy for new episodes.

## Generate the actual clips

The app can call Veo for you and save one `clip_NN.mp4` per scene into
`Episode_XXX/clips/`. Shots with TyGuy or Kelliee are **image-seeded** from a
reference image (`tyguy_seed.png`) so they stay on-model.

> Generation is **paid** (~a few $ per ~8s clip) and **async** (1–3 min each),
> and needs `google-genai` plus a Veo-enabled key. Preview first with `--dry-run`.

```bash
pip install google-genai
export GEMINI_API_KEY=...                 # never commit this

# Preview exactly what will be generated — no API calls, no cost:
python3 video_workflow.py generate --demo --dry-run

# Generate every clip for the demo episode:
python3 video_workflow.py generate --demo

# Generate from your own spec, or just specific scenes:
python3 video_workflow.py generate episode_002.json
python3 video_workflow.py generate episode_002.json --scenes 3 4 5
python3 video_workflow.py generate episode_002.json --seed kelliee_seed.png
```

Then assemble in order (clips connect via each scene's ending frame), add
music/voiceover, and export — e.g. with this repo's `assemble_3d.py`.

## From prompts to video, manually

If you'd rather drive Veo/Gemini by hand:

1. Run `build`, then open `Episode_XXX/checklist.txt` and tick it through.
2. Copy each `scene_prompts/scene_NN.txt` prompt + negative into Veo/Gemini
   (seed TyGuy/Kelliee shots with a reference image).
3. Keep each clip 4–8s; re-roll any clip where a character drifts off-model.
4. Assemble the clips in order, add music/voiceover, and export.
