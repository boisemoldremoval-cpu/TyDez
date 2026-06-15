#!/usr/bin/env python3
"""
Video Generation Workflow — turn one episode spec into a complete,
ready-to-shoot package of Veo/Gemini prompts and production files.

Built for the "TyGuy & Kelliee — Bible Adventures" series: a Christian
cartoon Bible lesson for kids and families. TyGuy (the lead) and Kelliee
(the sidekick) are defined once in the SERIES bible and reused — with
identical descriptions — in every episode. Each episode is checked to
include all seven required beats: a Bible verse, a simple life lesson,
a problem, a wrong reaction, a biblical correction, a peaceful ending,
and a call to follow Jesus. Each clip's ending frame is written to flow
straight into the next clip.

From a single JSON spec it scaffolds:

    Videos/Episodes/Episode_001/
        script.txt            full episode script (scenes + dialogue + VO)
        character_sheet.txt   consistency bible for every character
        style_guide.txt       look, palette, rendering, audio, negatives
        scene_prompts/
            scene_01.txt      copy-paste Veo prompt + full breakdown
            scene_02.txt      ...
        voiceover.txt         narrator script, line by line, with timings
        checklist.txt         final pre-generation checklist

Every scene prompt is written the way Veo/Gemini likes it: one flowing
cinematic paragraph (subject -> context -> action -> camera -> light ->
mood -> audio), a separate negative-prompt line, plus a labeled breakdown
covering style, character, location, action, camera, lighting, mood,
dialogue, what must stay consistent, what NOT to show, and an ending-frame
description so the next clip connects smoothly.

Usage
-----
    python3 video_workflow.py demo                  # build the bundled example
    python3 video_workflow.py build episode.json    # build from your spec
    python3 video_workflow.py template my_ep.json   # write a blank spec to fill in
    python3 video_workflow.py build episode.json --base /path/to/Videos

No third-party dependencies; pure standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path

# ----------------------------------------------------------------------------
# Tunables: every clip stays short and cinematic.
# ----------------------------------------------------------------------------
CLIP_MIN_SECONDS = 4
CLIP_MAX_SECONDS = 8
DEFAULT_CLIP_SECONDS = 6
DEFAULT_NEGATIVE = (
    "subtitles, captions, on-screen text, watermark, logo text, distorted face, "
    "extra fingers, extra limbs, deformed hands, warped anatomy, flickering, "
    "morphing character, inconsistent character design, low quality, blurry, "
    "jpeg artifacts, duplicate characters, extra people, scary imagery, violence, "
    "blood, dark or frightening tone"
)

# Every Bible-lesson episode must move through these beats, in this order.
# Each scene is tagged with one beat so the structure is guaranteed.
REQUIRED_BEATS = [
    "verse",               # the Bible verse is introduced
    "lesson",              # the simple life lesson is named
    "problem",             # a relatable problem appears
    "wrong_reaction",      # someone reacts the wrong way
    "biblical_correction", # Scripture corrects the reaction
    "peaceful_ending",     # things are made right, calm and joyful
    "call_to_jesus",       # a warm invitation to follow Jesus
]
BEAT_LABELS = {
    "verse": "BIBLE VERSE",
    "lesson": "LIFE LESSON",
    "problem": "THE PROBLEM",
    "wrong_reaction": "WRONG REACTION",
    "biblical_correction": "BIBLICAL CORRECTION",
    "peaceful_ending": "PEACEFUL ENDING",
    "call_to_jesus": "CALL TO FOLLOW JESUS",
    "intro": "INTRO",
    "": "—",
}


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------
@dataclass
class Character:
    name: str
    role: str = ""
    appearance: str = ""           # the locked physical description
    wardrobe: str = ""
    voice: str = ""
    personality: str = ""
    consistent: str = ""           # what MUST never change shot to shot

    @classmethod
    def from_dict(cls, d: dict) -> "Character":
        return cls(
            name=d["name"],
            role=d.get("role", ""),
            appearance=d.get("appearance", ""),
            wardrobe=d.get("wardrobe", ""),
            voice=d.get("voice", ""),
            personality=d.get("personality", ""),
            consistent=d.get("consistent", ""),
        )

    def short(self) -> str:
        """One-clause physical description for inline use inside a prompt."""
        bits = [self.appearance.strip().rstrip(".")]
        if self.wardrobe:
            bits.append(self.wardrobe.strip().rstrip("."))
        return ", ".join(b for b in bits if b)


@dataclass
class Style:
    name: str = "Cinematic 3D animation"
    description: str = ""
    palette: str = ""
    rendering: str = ""
    audio: str = ""
    negative: str = DEFAULT_NEGATIVE

    @classmethod
    def from_dict(cls, d: dict) -> "Style":
        return cls(
            name=d.get("name", "Cinematic 3D animation"),
            description=d.get("description", ""),
            palette=d.get("palette", ""),
            rendering=d.get("rendering", ""),
            audio=d.get("audio", ""),
            negative=d.get("negative", DEFAULT_NEGATIVE),
        )

    def prompt_clause(self) -> str:
        """The leading style sentence stamped onto every clip."""
        bits = [self.name.strip().rstrip(".")]
        if self.description:
            bits.append(self.description.strip().rstrip("."))
        if self.rendering:
            bits.append(self.rendering.strip().rstrip("."))
        return ", ".join(b for b in bits if b)


@dataclass
class Scene:
    action: str
    location: str = ""
    characters: list = field(default_factory=list)   # names referencing Character
    camera: str = ""
    lighting: str = ""
    mood: str = ""
    dialogue: list = field(default_factory=list)      # ["Name: line", ...]
    consistent: str = ""                              # scene-specific continuity
    avoid: str = ""                                   # scene-specific negatives
    ending_frame: str = ""
    seconds: int = DEFAULT_CLIP_SECONDS
    beat: str = ""                                    # which story beat this fulfills

    @classmethod
    def from_dict(cls, d: dict) -> "Scene":
        dlg = d.get("dialogue", [])
        if isinstance(dlg, str):
            dlg = [dlg] if dlg else []
        chars = d.get("characters", [])
        if isinstance(chars, str):
            chars = [chars] if chars else []
        return cls(
            action=d["action"],
            location=d.get("location", ""),
            characters=list(chars),
            camera=d.get("camera", ""),
            lighting=d.get("lighting", ""),
            mood=d.get("mood", ""),
            dialogue=list(dlg),
            consistent=d.get("consistent", ""),
            avoid=d.get("avoid", ""),
            ending_frame=d.get("ending_frame", ""),
            seconds=int(d.get("seconds", DEFAULT_CLIP_SECONDS)),
            beat=d.get("beat", ""),
        )


@dataclass
class Episode:
    number: int
    title: str
    logline: str = ""
    aspect_ratio: str = "16:9"
    style: Style = field(default_factory=Style)
    characters: list = field(default_factory=list)   # list[Character]
    scenes: list = field(default_factory=list)        # list[Scene]
    voiceover_tone: str = ""
    voiceover: list = field(default_factory=list)      # narrator lines
    model_hint: str = "veo-3.0-generate-001"
    bible_verse: str = ""        # e.g. "Ephesians 4:32 — Be kind to one another..."
    life_lesson: str = ""        # the simple, kid-sized takeaway
    call_to_jesus: str = ""      # the closing invitation line

    @classmethod
    def from_dict(cls, d: dict) -> "Episode":
        return cls(
            number=int(d.get("number", 1)),
            title=d.get("title", "Untitled"),
            logline=d.get("logline", ""),
            aspect_ratio=d.get("aspect_ratio", "16:9"),
            style=Style.from_dict(d.get("style", {})),
            characters=[Character.from_dict(c) for c in d.get("characters", [])],
            scenes=[Scene.from_dict(s) for s in d.get("scenes", [])],
            voiceover_tone=d.get("voiceover", {}).get("tone", "")
            if isinstance(d.get("voiceover"), dict) else d.get("voiceover_tone", ""),
            voiceover=(d.get("voiceover", {}).get("lines", [])
                       if isinstance(d.get("voiceover"), dict)
                       else d.get("voiceover", [])),
            model_hint=d.get("model_hint", "veo-3.0-generate-001"),
            bible_verse=d.get("bible_verse", ""),
            life_lesson=d.get("life_lesson", ""),
            call_to_jesus=d.get("call_to_jesus", ""),
        )

    def char(self, name: str):
        for c in self.characters:
            if c.name.lower() == name.lower():
                return c
        return None

    def folder_name(self) -> str:
        return f"Episode_{self.number:03d}"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _wrap(text: str, width: int = 78, indent: str = "") -> str:
    return "\n".join(
        textwrap.fill(line, width=width, subsequent_indent=indent) if line else ""
        for line in text.splitlines()
    )


def _rule(char: str = "=", width: int = 78) -> str:
    return char * width


def _label(label: str, value: str, pad: int = 22) -> str:
    """Left-labeled, wrapped, hanging-indent block for breakdown cards."""
    value = (value or "—").strip()
    indent = " " * pad
    wrapped = textwrap.fill(value, width=78, initial_indent="",
                            subsequent_indent=indent)
    return f"{label.ljust(pad)}{wrapped}"


def _dialogue_clause(scene: Scene, ep: Episode) -> str:
    """Render dialogue as a natural spoken clause for the flowing prompt."""
    out = []
    for line in scene.dialogue:
        if ":" in line:
            who, said = line.split(":", 1)
            who, said = who.strip(), said.strip().strip('"')
            out.append(f'{who} says, "{said}"')
        else:
            out.append(f'a voice says, "{line.strip().strip(chr(34))}"')
    return ". ".join(out)


def _scene_characters_clause(scene: Scene, ep: Episode) -> str:
    descs = []
    for name in scene.characters:
        c = ep.char(name)
        if c:
            descs.append(f"{c.name} ({c.short()})")
        else:
            descs.append(name)
    return "; ".join(descs)


# ----------------------------------------------------------------------------
# The Veo prompt builder — the heart of the app.
# ----------------------------------------------------------------------------
def build_veo_prompt(scene: Scene, ep: Episode) -> str:
    """Compose one flowing, copy-paste-ready Veo/Gemini prompt paragraph.

    Order follows Veo's preference: style -> subject -> action -> context
    -> camera -> lighting -> mood -> dialogue -> audio.
    """
    parts: list = []

    parts.append(ep.style.prompt_clause() + ".")

    chars = _scene_characters_clause(scene, ep)
    action = scene.action.strip().rstrip(".")
    if chars:
        parts.append(f"{chars}, {action}.")
    else:
        parts.append(action + ".")

    if scene.location:
        parts.append(f"Setting: {scene.location.strip().rstrip('.')}.")

    if scene.camera:
        parts.append(f"Camera: {scene.camera.strip().rstrip('.')}.")

    if scene.lighting:
        parts.append(f"Lighting: {scene.lighting.strip().rstrip('.')}.")

    if scene.mood:
        parts.append(f"Mood: {scene.mood.strip().rstrip('.')}.")

    dlg = _dialogue_clause(scene, ep)
    if dlg:
        parts.append(dlg + ".")

    if ep.style.palette:
        parts.append(f"Color palette: {ep.style.palette.strip().rstrip('.')}.")

    if ep.style.audio:
        parts.append(f"Audio: {ep.style.audio.strip().rstrip('.')}.")

    parts.append(f"Clip length about {scene.seconds} seconds, {ep.aspect_ratio} aspect ratio.")

    return _wrap(" ".join(parts))


def build_negative(scene: Scene, ep: Episode) -> str:
    neg = ep.style.negative
    if scene.avoid:
        neg = f"{neg}, {scene.avoid.strip().rstrip('.')}"
    return _wrap(neg)


# ----------------------------------------------------------------------------
# File renderers
# ----------------------------------------------------------------------------
def render_scene_file(i: int, scene: Scene, ep: Episode) -> str:
    n = len(ep.scenes)
    next_hint = (f"  ->  feeds Scene {i + 1:02d}"
                 if i < n else "  ->  final clip (resolve / CTA)")

    consistency = []
    for name in scene.characters:
        c = ep.char(name)
        if c and c.consistent:
            consistency.append(f"{c.name}: {c.consistent}")
    if scene.consistent:
        consistency.append(scene.consistent)
    consistency_text = " | ".join(consistency) if consistency else \
        "Hold all character designs, wardrobe, and palette identical to the sheet."

    lines = []
    beat = BEAT_LABELS.get(scene.beat, scene.beat.upper()) if scene.beat else ""
    lines.append(_rule("="))
    lines.append(f" EPISODE {ep.number:03d} — \"{ep.title}\"")
    lines.append(f" SCENE {i:02d} of {n}" + (f"   |   BEAT: {beat}" if beat else ""))
    lines.append(f" ~{scene.seconds}s   |   {ep.aspect_ratio}{next_hint}")
    lines.append(_rule("="))
    lines.append("")
    lines.append(">>> COPY-PASTE THIS INTO VEO / GEMINI <<<")
    lines.append(_rule("-"))
    lines.append(build_veo_prompt(scene, ep))
    lines.append(_rule("-"))
    lines.append("")
    lines.append("NEGATIVE PROMPT (paste into the negative / 'avoid' field):")
    lines.append(build_negative(scene, ep))
    lines.append("")
    lines.append(_rule("="))
    lines.append(" SCENE BREAKDOWN (reference — not pasted into Veo)")
    lines.append(_rule("="))
    lines.append(_label("VIDEO STYLE:", ep.style.prompt_clause()))
    lines.append(_label("MAIN CHARACTER:", _scene_characters_clause(scene, ep)))
    lines.append(_label("LOCATION:", scene.location))
    lines.append(_label("ACTION:", scene.action))
    lines.append(_label("CAMERA ANGLE:", scene.camera))
    lines.append(_label("LIGHTING:", scene.lighting))
    lines.append(_label("MOOD:", scene.mood))
    lines.append(_label("DIALOGUE:", " / ".join(scene.dialogue) if scene.dialogue
                        else "(none — visual / voiceover only)"))
    lines.append(_label("MUST STAY CONSISTENT:", consistency_text))
    lines.append(_label("DO NOT SHOW:", scene.avoid or "(use the standard negative prompt above)"))
    lines.append(_label("ENDING FRAME:", scene.ending_frame or
                        "Settle on a clean, centered hold so the next clip can pick up."))
    lines.append(_rule("="))
    lines.append("")
    return "\n".join(lines)


def render_script(ep: Episode) -> str:
    lines = []
    lines.append(_rule("="))
    lines.append(f" EPISODE {ep.number:03d} SCRIPT — \"{ep.title}\"")
    lines.append(_rule("="))
    lines.append("")
    if ep.bible_verse:
        lines.append("BIBLE VERSE")
        lines.append(_wrap(ep.bible_verse))
        lines.append("")
    if ep.life_lesson:
        lines.append("LIFE LESSON")
        lines.append(_wrap(ep.life_lesson))
        lines.append("")
    if ep.logline:
        lines.append("LOGLINE")
        lines.append(_wrap(ep.logline))
        lines.append("")
    if ep.call_to_jesus:
        lines.append("CALL TO FOLLOW JESUS")
        lines.append(_wrap(ep.call_to_jesus))
        lines.append("")
    lines.append(f"Runtime target: ~{sum(s.seconds for s in ep.scenes)}s across "
                 f"{len(ep.scenes)} clips   |   Aspect: {ep.aspect_ratio}")
    lines.append("")
    lines.append(_rule("-"))
    lines.append("")
    for i, s in enumerate(ep.scenes, 1):
        who = _scene_characters_clause(s, ep) or "—"
        beat = BEAT_LABELS.get(s.beat, s.beat.upper()) if s.beat else "—"
        lines.append(f"SCENE {i:02d}  ({s.seconds}s)  [{beat}]  —  {s.location or 'location TBD'}")
        lines.append(_wrap(f"Who: {who}", indent="     "))
        lines.append(_wrap(f"Action: {s.action}", indent="        "))
        if s.dialogue:
            for d in s.dialogue:
                lines.append(_wrap(f"    {d}", indent="        "))
        lines.append("")
    lines.append(_rule("="))
    lines.append("END OF EPISODE")
    lines.append(_rule("="))
    lines.append("")
    return "\n".join(lines)


def render_character_sheet(ep: Episode) -> str:
    lines = []
    lines.append(_rule("="))
    lines.append(f" CHARACTER CONSISTENCY SHEET — Episode {ep.number:03d}")
    lines.append(_rule("="))
    lines.append("")
    lines.append("Paste the matching block into any clip where the character")
    lines.append("appears, and keep these details WORD-FOR-WORD identical across")
    lines.append("every scene. Consistency is what makes the episode feel real.")
    lines.append("")
    if not ep.characters:
        lines.append("(no characters defined)")
    for c in ep.characters:
        lines.append(_rule("-"))
        lines.append(f"{c.name.upper()}" + (f"   —   {c.role}" if c.role else ""))
        lines.append(_rule("-"))
        lines.append(_label("APPEARANCE:", c.appearance))
        lines.append(_label("WARDROBE:", c.wardrobe))
        lines.append(_label("VOICE:", c.voice))
        lines.append(_label("PERSONALITY:", c.personality))
        lines.append(_label("LOCK (never change):", c.consistent))
        lines.append(_label("PROMPT SNIPPET:", c.short()))
        lines.append("")
    lines.append(_rule("="))
    lines.append("")
    return "\n".join(lines)


def render_style_guide(ep: Episode) -> str:
    s = ep.style
    lines = []
    lines.append(_rule("="))
    lines.append(f" VISUAL STYLE GUIDE — Episode {ep.number:03d}")
    lines.append(_rule("="))
    lines.append("")
    lines.append(_label("STYLE NAME:", s.name))
    lines.append(_label("DESCRIPTION:", s.description))
    lines.append(_label("RENDERING:", s.rendering))
    lines.append(_label("COLOR PALETTE:", s.palette))
    lines.append(_label("AUDIO BED:", s.audio))
    lines.append(_label("ASPECT RATIO:", ep.aspect_ratio))
    lines.append(_label("MODEL:", ep.model_hint))
    lines.append("")
    lines.append("LEADING STYLE CLAUSE (stamped on every clip):")
    lines.append(_wrap(s.prompt_clause() + "."))
    lines.append("")
    lines.append("GLOBAL NEGATIVE PROMPT:")
    lines.append(_wrap(s.negative))
    lines.append("")
    lines.append(_rule("="))
    lines.append("")
    return "\n".join(lines)


def render_voiceover(ep: Episode) -> str:
    lines = []
    lines.append(_rule("="))
    lines.append(f" VOICEOVER SCRIPT — Episode {ep.number:03d}")
    lines.append(_rule("="))
    lines.append("")
    if ep.voiceover_tone:
        lines.append(_label("NARRATOR TONE:", ep.voiceover_tone))
        lines.append("")
    if ep.voiceover:
        lines.append("NARRATION (read in order; ~one line per clip):")
        lines.append("")
        for i, line in enumerate(ep.voiceover, 1):
            lines.append(_wrap(f"VO {i:02d}:  {line}", indent="        "))
            lines.append("")
    else:
        lines.append("(No separate voiceover — characters speak on-screen.)")
        lines.append("Per-scene spoken lines, for reference:")
        lines.append("")
        for i, s in enumerate(ep.scenes, 1):
            for d in s.dialogue:
                lines.append(_wrap(f"S{i:02d}:  {d}", indent="        "))
        lines.append("")
    lines.append(_rule("="))
    lines.append("")
    return "\n".join(lines)


def render_checklist(ep: Episode) -> str:
    n = len(ep.scenes)
    lines = []
    lines.append(_rule("="))
    lines.append(f" FINAL CHECKLIST — Episode {ep.number:03d}: \"{ep.title}\"")
    lines.append(_rule("="))
    lines.append("")
    lines.append("Run this BEFORE you spend credits generating. Veo clips are")
    lines.append("paid and async — catching problems here saves real money.")
    lines.append("")
    if ep.bible_verse:
        lines.append("THIS EPISODE")
        lines.append(_wrap(f"  Verse:  {ep.bible_verse}", indent="          "))
        lines.append(_wrap(f"  Lesson: {ep.life_lesson}", indent="          "))
        lines.append("")
    present = {s.beat for s in ep.scenes if s.beat}
    lines.append("REQUIRED BIBLE-LESSON BEATS (every episode must have all 7)")
    for b in REQUIRED_BEATS:
        mark = "x" if b in present else " "
        lines.append(f"  [{mark}] {BEAT_LABELS.get(b, b)}")
    lines.append("")
    lines.append("STORY & STRUCTURE")
    lines.append("  [ ] Logline is clear and the episode has a beginning/middle/end")
    lines.append(f"  [ ] All {n} scenes read in order and tell one coherent story")
    lines.append("  [ ] Bible verse is quoted accurately")
    lines.append("  [ ] The call to follow Jesus is warm and clear at the end")
    lines.append("  [ ] Every clip is between "
                 f"{CLIP_MIN_SECONDS}-{CLIP_MAX_SECONDS}s (short and punchy)")
    lines.append("")
    lines.append("CONSISTENCY (the make-or-break)")
    lines.append("  [ ] TyGuy matches the series bible WORD-FOR-WORD (royal-blue 'T' hoodie)")
    lines.append("  [ ] Kelliee matches the series bible WORD-FOR-WORD (yellow cross hoodie)")
    lines.append("  [ ] Wardrobe / colors match the character sheet in every scene")
    lines.append("  [ ] A seed/reference image is set for TyGuy and Kelliee")
    lines.append("  [ ] Style clause + palette are identical across all clips")
    lines.append("")
    lines.append("EACH SCENE PROMPT INCLUDES")
    lines.append("  [ ] Style, character, location, action")
    lines.append("  [ ] Camera angle, lighting, mood")
    lines.append("  [ ] Dialogue (or marked visual-only)")
    lines.append("  [ ] What must stay consistent + what NOT to show")
    lines.append("  [ ] Ending-frame description that hands off to the next clip")
    lines.append("")
    lines.append("CONTINUITY HANDOFFS")
    for i, s in enumerate(ep.scenes, 1):
        tail = "final clip" if i == n else f"hands to Scene {i + 1:02d}"
        end = (s.ending_frame or "ending frame NOT set — add one").strip()
        end = textwrap.shorten(end, width=58, placeholder="…")
        lines.append(f"  [ ] S{i:02d} {tail}: {end}")
    lines.append("")
    lines.append("TECHNICAL")
    lines.append(f"  [ ] Aspect ratio set to {ep.aspect_ratio} on every clip")
    lines.append("  [ ] Negative prompt pasted into every generation")
    lines.append("  [ ] GEMINI_API_KEY exported (never committed)")
    lines.append(f"  [ ] Model selected: {ep.model_hint}")
    lines.append("")
    lines.append("AFTER GENERATION")
    lines.append("  [ ] Watch clips end-to-start: does each ending match the next opening?")
    lines.append("  [ ] Re-roll any clip where the character drifts off-model")
    lines.append("  [ ] Assemble in order, add music/VO, export")
    lines.append("")
    lines.append(_rule("="))
    lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
def validate(ep: Episode) -> list:
    warnings = []
    if not ep.scenes:
        warnings.append("Episode has no scenes.")

    # Bible-lesson series requirements.
    if not ep.bible_verse:
        warnings.append("No Bible verse set (bible_verse) — every episode needs one.")
    if not ep.life_lesson:
        warnings.append("No life lesson set (life_lesson) — every episode needs one.")
    if not ep.call_to_jesus:
        warnings.append("No call to follow Jesus set (call_to_jesus).")
    present = {s.beat for s in ep.scenes if s.beat}
    for b in REQUIRED_BEATS:
        if b not in present:
            warnings.append(f"Missing required beat '{b}' "
                            f"({BEAT_LABELS.get(b, b)}) — no scene is tagged for it.")
    names = {c.name.lower() for c in ep.characters}
    for required in ("tyguy", "kelliee"):
        if required not in names:
            warnings.append(f"Recurring character '{required}' is missing from the cast.")

    for i, s in enumerate(ep.scenes, 1):
        if not (CLIP_MIN_SECONDS <= s.seconds <= CLIP_MAX_SECONDS):
            warnings.append(
                f"Scene {i:02d}: {s.seconds}s is outside the "
                f"{CLIP_MIN_SECONDS}-{CLIP_MAX_SECONDS}s clip window.")
        for name in s.characters:
            if not ep.char(name):
                warnings.append(
                    f"Scene {i:02d}: character '{name}' is not in the character sheet.")
        if i < len(ep.scenes) and not s.ending_frame:
            warnings.append(
                f"Scene {i:02d}: no ending_frame — the handoff to the next clip is vague.")
    return warnings


def build(ep: Episode, base: Path) -> Path:
    ep_dir = base / "Episodes" / ep.folder_name()
    scenes_dir = ep_dir / "scene_prompts"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    (ep_dir / "script.txt").write_text(render_script(ep))
    (ep_dir / "character_sheet.txt").write_text(render_character_sheet(ep))
    (ep_dir / "style_guide.txt").write_text(render_style_guide(ep))
    (ep_dir / "voiceover.txt").write_text(render_voiceover(ep))
    (ep_dir / "checklist.txt").write_text(render_checklist(ep))

    for i, scene in enumerate(ep.scenes, 1):
        (scenes_dir / f"scene_{i:02d}.txt").write_text(render_scene_file(i, scene, ep))

    return ep_dir


# ----------------------------------------------------------------------------
# Generate — call Veo on each scene prompt and save the clips.
# TyGuy/Kelliee shots are image-seeded from a reference image so they stay
# on-model. Generation is paid and async (~1-3 min/clip); needs GEMINI_API_KEY.
# ----------------------------------------------------------------------------
RECURRING = {"tyguy", "kelliee"}


def _scene_uses_recurring(scene: Scene) -> bool:
    return any(name.lower() in RECURRING for name in scene.characters)


def generate(ep: Episode, base: Path, which=None, seed_path: str = "tyguy_seed.png",
             dry_run: bool = False) -> Path:
    """Generate one mp4 per selected scene into Episode_NNN/clips/."""
    ep_dir = base / "Episodes" / ep.folder_name()
    clips_dir = ep_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    indices = which or list(range(1, len(ep.scenes) + 1))
    seed_available = Path(seed_path).exists()

    print(f"\nEpisode {ep.number:03d} — \"{ep.title}\"  |  model: {ep.model_hint}")
    print(f"Seed image: {seed_path} "
          f"({'found' if seed_available else 'MISSING — recurring shots will not be seeded'})")
    print(f"Generating {len(indices)} clip(s) -> {clips_dir}\n")

    if dry_run:
        for n in indices:
            scene = ep.scenes[n - 1]
            seeded = _scene_uses_recurring(scene) and seed_available
            print(f"[scene {n:02d}] ~{scene.seconds}s  "
                  f"{'SEEDED (image-to-video)' if seeded else 'text-to-video'}  "
                  f"beat={scene.beat or '-'}")
            print("  PROMPT:   " + " ".join(build_veo_prompt(scene, ep).split())[:160] + "…")
            print("  NEGATIVE: " + " ".join(build_negative(scene, ep).split())[:90] + "…")
            print(f"  -> {clips_dir / f'clip_{n:02d}.mp4'}\n")
        print("Dry run only — no API calls made. Drop --dry-run to generate for real.")
        return ep_dir

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("ERROR: set GEMINI_API_KEY (Google AI key with Veo access).")

    from google import genai          # imported lazily so build/demo need no SDK
    from google.genai import types

    client = genai.Client(api_key=key)
    seed_img = None
    if seed_available:
        with open(seed_path, "rb") as f:
            mime = "image/png" if seed_path.lower().endswith("png") else "image/jpeg"
            seed_img = types.Image(image_bytes=f.read(), mime_type=mime)

    for n in indices:
        scene = ep.scenes[n - 1]
        out = clips_dir / f"clip_{n:02d}.mp4"
        seeded = _scene_uses_recurring(scene) and seed_img is not None
        print(f"[scene {n:02d}/{len(ep.scenes)}] {'seeded' if seeded else 'text'} "
              f"({ep.aspect_ratio}) ~{scene.seconds}s …")
        kwargs = dict(
            model=ep.model_hint,
            prompt=" ".join(build_veo_prompt(scene, ep).split()),
            config=types.GenerateVideosConfig(
                aspect_ratio=ep.aspect_ratio,
                number_of_videos=1,
                negative_prompt=" ".join(build_negative(scene, ep).split())),
        )
        if seeded:
            kwargs["image"] = seed_img
        op = client.models.generate_videos(**kwargs)
        t0 = time.time()
        while not op.done:
            time.sleep(10)
            op = client.operations.get(op)
        if getattr(op, "error", None):
            print(f"  !! scene {n} ERROR: {op.error}")
            continue
        resp = op.response
        vids = getattr(resp, "generated_videos", None) if resp else None
        if not vids:
            reasons = getattr(resp, "rai_media_filtered_reasons", None)
            print(f"  !! scene {n} produced NO video (content-filtered). reasons={reasons}")
            continue
        client.files.download(file=vids[0].video)
        vids[0].video.save(str(out))
        print(f"  saved {out}  ({time.time()-t0:.0f}s)")

    print(f"\nDone. Assemble in order with:\n"
          f"  python3 video_workflow.py assemble {ep.number} --base {base}")
    return ep_dir


# ----------------------------------------------------------------------------
# Assemble — stitch the generated clips into one episode file, in order.
# Clips connect via each scene's ending frame; this normalizes size/fps and
# concatenates clip_01..clip_NN (keeping each clip's Veo audio).
# ----------------------------------------------------------------------------
def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        from shutil import which
        exe = which("ffmpeg")
        if not exe:
            raise SystemExit("ERROR: need imageio-ffmpeg (pip install imageio-ffmpeg) "
                             "or a system 'ffmpeg' on PATH.")
        return exe


def assemble(ep: Episode, base: Path, vertical: bool = False,
             out: Path | None = None, xfade: float = 0.0) -> Path:
    import subprocess

    ep_dir = base / "Episodes" / ep.folder_name()
    clips_dir = ep_dir / "clips"
    clips = sorted(clips_dir.glob("clip_*.mp4"))
    if not clips:
        raise SystemExit(f"No clips found in {clips_dir} — run 'generate' first.")
    out = out or (ep_dir / f"episode_{ep.number:03d}.mp4")

    Wt, Ht = (1080, 1920) if vertical else (1280, 720)
    parts, concat = [], ""
    for i in range(len(clips)):
        parts.append(
            f"[{i}:v]split=2[bg{i}][fg{i}];"
            f"[bg{i}]scale={Wt}:{Ht}:force_original_aspect_ratio=increase,"
            f"crop={Wt}:{Ht},gblur=sigma=24[bgb{i}];"
            f"[fg{i}]scale={Wt}:{Ht}:force_original_aspect_ratio=decrease[fg{i}s];"
            f"[bgb{i}][fg{i}s]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=24[v{i}];"
            f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}];"
        )
        concat += f"[v{i}][a{i}]"
    fc = "".join(parts) + f"{concat}concat=n={len(clips)}:v=1:a=1[v][a]"

    cmd = [_ffmpeg_exe(), "-y"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    print(f"Assembling {len(clips)} clips -> {out} ({Wt}x{Ht})")
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode()[-2000:])
        raise SystemExit("assembly failed")
    print(f"Done -> {out}")
    return out


# ----------------------------------------------------------------------------
# SERIES BIBLE — the locked, reused-every-episode definitions.
# TyGuy and Kelliee must look and sound identical in every episode, so their
# descriptions live here (or in series.json) and every episode inherits them.
# ----------------------------------------------------------------------------
SERIES = {
    "title": "TyGuy & Kelliee — Bible Adventures",
    "aspect_ratio": "16:9",
    "model_hint": "veo-3.0-generate-001",
    "style": {
        "name": "Pixar/Disney-style 3D animation",
        "description": ("warm, wholesome Christian kids' cartoon, soft rounded shapes, "
                        "big expressive friendly faces, gentle and reverent, family-friendly"),
        "rendering": ("high-detail subsurface skin, soft cinematic global illumination, "
                      "shallow depth of field, 24fps feature-film feel"),
        "palette": "brand royal-blue, sunny gold, warm cream, soft heavenly light",
        "audio": ("gentle uplifting orchestral score, soft acoustic guitar, light playful "
                  "percussion, warm natural ambience; reverent and never scary"),
        "negative": DEFAULT_NEGATIVE,
    },
    "characters": [
        {
            "name": "TyGuy",
            "role": "host / big-brother mentor (consistent lead, every episode)",
            "appearance": ("a cheerful 3D cartoon young man, early 20s, warm tan skin, "
                           "short dark-brown hair, big friendly brown eyes, bright kind smile"),
            "wardrobe": ("royal-blue hoodie with a white letter 'T' on the chest, "
                         "dark jeans, white sneakers"),
            "voice": "warm, upbeat, encouraging young-adult male voice",
            "personality": "kind, patient, joyful, gently teaches Scripture by example",
            "consistent": ("ALWAYS the same: face shape, dark-brown hair, royal-blue 'T' "
                           "hoodie, brown eyes — never change his design or outfit"),
        },
        {
            "name": "Kelliee",
            "role": "sidekick (consistent, every episode)",
            "appearance": ("a bright, bubbly 3D cartoon girl, age 10, light-brown skin, "
                           "curly auburn hair in two puff pigtails, big hazel eyes, freckles"),
            "wardrobe": ("sunny-yellow hoodie with a small white cross on the chest, "
                         "teal leggings, white-and-pink sneakers"),
            "voice": "cheerful, curious, slightly higher-energy young girl voice",
            "personality": ("eager and warm-hearted, asks the questions kids are thinking, "
                            "sometimes reacts first and learns the lesson"),
            "consistent": ("ALWAYS the same: auburn puff pigtails, yellow cross hoodie, "
                           "freckles, hazel eyes — never change her design or outfit"),
        },
    ],
}


def load_series(path: str | None = None) -> dict:
    """Load the series bible: explicit path > ./series.json > built-in SERIES."""
    if path and Path(path).exists():
        return json.loads(Path(path).read_text())
    local = Path("series.json")
    if local.exists():
        return json.loads(local.read_text())
    return SERIES


def merge_series(data: dict, series: dict) -> dict:
    """Inherit series style + recurring characters; episode values win on conflict.

    Recurring characters (TyGuy, Kelliee) are always present and identical unless
    the episode explicitly overrides a character of the same name.
    """
    merged = dict(data)
    merged.setdefault("aspect_ratio", series.get("aspect_ratio", "16:9"))
    merged.setdefault("model_hint", series.get("model_hint", "veo-3.0-generate-001"))

    # Style: episode keys override series keys.
    style = dict(series.get("style", {}))
    style.update(data.get("style", {}))
    merged["style"] = style

    # Characters: start from series, override/add by name from the episode.
    by_name = {c["name"].lower(): dict(c) for c in series.get("characters", [])}
    for c in data.get("characters", []):
        by_name[c["name"].lower()] = c
    merged["characters"] = list(by_name.values())
    return merged


# ----------------------------------------------------------------------------
# Bundled example (TyGuy + Kelliee Bible lesson — matches this repo's brand)
# ----------------------------------------------------------------------------
def example_spec() -> dict:
    """A complete Bible-lesson episode. TyGuy + Kelliee come from the series
    bible; only the guest character (Ben) and the story scenes are episode-specific.
    Every required beat is present and each clip's ending frame feeds the next."""
    return {
        "number": 1,
        "title": "Taking Turns",
        "logline": ("Kelliee's turn on the swing gets taken, and she wants to shout — "
                    "until TyGuy shows her what God's Word says about kindness and "
                    "forgiveness, and the playground becomes peaceful again."),
        "bible_verse": ("Ephesians 4:32 — \"Be kind to one another, tender-hearted, "
                        "forgiving one another, as God in Christ forgave you.\""),
        "life_lesson": ("When someone is unfair to us, Jesus helps us choose kindness and "
                        "forgiveness instead of anger."),
        "call_to_jesus": ("Jesus forgives us, so we can forgive others. Ask Him into your "
                          "heart and let Him help you be kind every day."),
        "characters": [
            {
                "name": "Ben",
                "role": "guest kid (this episode only)",
                "appearance": "a 3D cartoon boy, age 9, short sandy-blond hair, light skin, round cheeks",
                "wardrobe": "green-striped t-shirt, grey shorts, red sneakers",
                "voice": "energetic young boy, a little impatient at first",
                "personality": "excitable, doesn't realize he cut in line, quick to say sorry",
                "consistent": "sandy-blond hair and green-striped shirt in every shot he appears in",
            }
        ],
        "voiceover": {
            "tone": "warm, gentle picture-book storyteller for young children",
            "lines": [
                "God's Word gives us a special rule for our hearts...",
                "...be kind, and forgive one another.",
                "But being kind is hard when something feels unfair.",
                "When we're hurt, our first feeling can be anger.",
                "Jesus shows us a better way — to forgive.",
                "And when we forgive, peace comes back.",
                "Will you follow Jesus and let Him make your heart kind?",
            ],
        },
        "scenes": [
            {
                "beat": "verse",
                "characters": ["TyGuy", "Kelliee"],
                "location": "a sunny cartoon neighborhood park with a swing set, green grass, and a big leafy tree",
                "action": ("TyGuy waves warmly to camera while Kelliee bounces beside him "
                           "holding an open kids' Bible; he gestures to the page"),
                "camera": "medium two-shot, slow gentle push-in, eye level",
                "lighting": "bright warm morning sunlight, soft golden glow",
                "mood": "cheerful, welcoming, reverent",
                "dialogue": [
                    "TyGuy: Hey friends! Today's verse is Ephesians four, thirty-two.",
                    "Kelliee: \"Be kind to one another, and forgive one another!\""],
                "ending_frame": ("Kelliee proudly holds the Bible up toward camera, then "
                                 "looks off toward the swings — camera ready to follow her"),
                "seconds": 6,
            },
            {
                "beat": "lesson",
                "characters": ["TyGuy", "Kelliee"],
                "location": "the same sunny park, standing on the grass near the swing set",
                "action": ("TyGuy kneels to Kelliee's level and points to his heart, then to "
                           "the swings; Kelliee nods, eager to play"),
                "camera": "two-shot, eye level, soft handheld",
                "lighting": "warm morning sun, soft shadows",
                "mood": "gentle, teaching, hopeful",
                "dialogue": [
                    "TyGuy: That means: be kind, and forgive — even when it's hard.",
                    "Kelliee: Got it! Now can I swing?"],
                "ending_frame": ("Kelliee skips toward an empty swing, the swing clearly "
                                 "open and waiting in frame"),
                "seconds": 6,
            },
            {
                "beat": "problem",
                "characters": ["Kelliee", "Ben"],
                "location": "right at the swing set on the grass",
                "action": ("just as Kelliee reaches for the empty swing, Ben dashes in and "
                           "hops onto it first, not noticing her"),
                "camera": "medium shot, quick gentle whip toward the swing, eye level",
                "lighting": "bright morning sun",
                "mood": "lighthearted but suddenly unfair",
                "dialogue": ["Ben: Woo-hoo! My turn!"],
                "consistent": "Kelliee's reaching hand and surprised face stay clearly readable",
                "ending_frame": ("Kelliee freezes mid-reach, swing now taken, her smile "
                                 "dropping into a shocked frown — hold on her face"),
                "seconds": 5,
            },
            {
                "beat": "wrong_reaction",
                "characters": ["Kelliee"],
                "location": "beside the swing set on the grass",
                "action": ("Kelliee crosses her arms, scrunches her face, stomps one foot, "
                           "and opens her mouth as if to shout"),
                "camera": "medium close-up, slight low angle, holds steady on her",
                "lighting": "warm sun, a touch cooler to feel her frustration",
                "mood": "frustrated, upset (gentle and kid-appropriate, never scary)",
                "dialogue": ["Kelliee: Hey! That was MY turn! That's not fair!"],
                "avoid": "yelling face that looks frightening, tears, anything harsh or mean",
                "ending_frame": ("Kelliee, arms crossed and pouting, as a familiar blue "
                                 "sleeve enters frame — TyGuy's hand resting gently on her shoulder"),
                "seconds": 6,
            },
            {
                "beat": "biblical_correction",
                "characters": ["TyGuy", "Kelliee"],
                "location": "kneeling together on the grass beside the swings",
                "action": ("TyGuy kneels beside Kelliee, hand on her shoulder, gently opens "
                           "the Bible; Kelliee's angry face slowly softens as she listens"),
                "camera": "intimate two-shot, slow push-in, eye level",
                "lighting": "soft warm sunbeam breaking through, a touch of heavenly glow",
                "mood": "calm, gentle, reassuring",
                "dialogue": [
                    "TyGuy: Remember our verse? Be kind, and forgive.",
                    "TyGuy: Jesus forgave us — we can forgive Ben too.",
                    "Kelliee: ...Okay. I can be kind."],
                "ending_frame": ("Kelliee uncrosses her arms and takes a calming breath, a "
                                 "small forgiving smile returning; she turns toward Ben"),
                "seconds": 8,
            },
            {
                "beat": "peaceful_ending",
                "characters": ["Kelliee", "Ben"],
                "location": "at the swing set on the grass",
                "action": ("Kelliee walks up kindly; Ben realizes and hops off, apologizing; "
                           "they smile and Ben offers her the swing, then they take turns happily"),
                "camera": "medium two-shot, warm slow push-in, eye level",
                "lighting": "full bright golden morning sun, warm and glowing",
                "mood": "warm, peaceful, joyful, reconciled",
                "dialogue": [
                    "Ben: Oh — sorry! I didn't see you. You go first!",
                    "Kelliee: Thanks, Ben! Let's take turns."],
                "consistent": "Ben same sandy-blond hair and green-striped shirt; both genuinely happy",
                "ending_frame": ("Kelliee swings gently with Ben pushing, both laughing; "
                                 "TyGuy steps into frame from the side, smiling at camera"),
                "seconds": 7,
            },
            {
                "beat": "call_to_jesus",
                "characters": ["TyGuy", "Kelliee"],
                "location": "in front of the swing set, warm sunny park behind them",
                "action": ("TyGuy and Kelliee stand together facing camera; TyGuy places a "
                           "hand on his heart, Kelliee gives a thumbs-up"),
                "camera": "medium two-shot, gentle slow push-in, eye level",
                "lighting": "warm golden light with soft heavenly glow and floating gold sparkles",
                "mood": "uplifting, sincere, inviting",
                "dialogue": [
                    "TyGuy: Jesus forgives us, so we can forgive others.",
                    "TyGuy: Ask Jesus into your heart, and let Him make you kind!",
                    "Kelliee: Be kind, forgive, and follow Jesus! See you next time!"],
                "ending_frame": ("freeze on TyGuy and Kelliee waving together, golden "
                                 "sparkles and a soft glowing cross, brand-blue tones, "
                                 "clean space at top for an end card"),
                "seconds": 7,
            },
        ],
    }


TEMPLATE_SPEC = {
    "number": 2,
    "title": "Your Episode Title",
    "logline": "One or two sentences: the problem and how the lesson resolves it.",
    "bible_verse": "Book Chapter:Verse — \"the verse text\"",
    "life_lesson": "the simple, kid-sized takeaway in one sentence",
    "call_to_jesus": "the warm closing invitation to follow Jesus",
    "voiceover": {
        "tone": "narrator tone",
        "lines": ["VO line for clip 1", "VO line for clip 2"],
    },
    "_note": ("TyGuy and Kelliee are inherited automatically from the series bible "
              "(series.json / built-in SERIES) — do NOT redefine them here. Only add "
              "guest characters for this episode below."),
    "characters": [
        {
            "name": "GuestKid",
            "role": "guest (this episode only)",
            "appearance": "locked physical description — age, hair, skin, eyes",
            "wardrobe": "exact outfit and colors",
            "voice": "voice description",
            "personality": "key traits",
            "consistent": "what must NEVER change between shots",
        }
    ],
    "scenes": [
        {
            "beat": "verse  (one of: " + ", ".join(REQUIRED_BEATS) + ")",
            "characters": ["TyGuy", "Kelliee"],
            "location": "where it happens, described visually",
            "action": "what happens in this clip (one clear beat)",
            "camera": "shot size, angle, movement",
            "lighting": "light direction, color, quality",
            "mood": "the emotional tone",
            "dialogue": ["TyGuy: a short spoken line"],
            "consistent": "scene-specific continuity notes",
            "avoid": "scene-specific things NOT to show",
            "ending_frame": "how this clip ends so the next one connects",
            "seconds": 6,
        }
    ],
}


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def _load_spec(path: str, series_path: str | None = None) -> Episode:
    data = json.loads(Path(path).read_text())
    series = load_series(series_path)
    return Episode.from_dict(merge_series(data, series))


def _report(ep: Episode, ep_dir: Path) -> None:
    total = sum(s.seconds for s in ep.scenes)
    print(f"\n✓ Built {ep.folder_name()} — \"{ep.title}\"")
    print(f"  {ep_dir}")
    print(f"  {len(ep.scenes)} scene prompts  |  ~{total}s total  |  {ep.aspect_ratio}")
    print("    script.txt  character_sheet.txt  style_guide.txt")
    print("    voiceover.txt  checklist.txt  scene_prompts/scene_01..%02d.txt"
          % len(ep.scenes))
    warns = validate(ep)
    if warns:
        print("\n  ⚠ Review before generating:")
        for w in warns:
            print(f"    - {w}")
    print("\n  Next: open checklist.txt, then copy each scene_prompts/*.txt into Veo/Gemini.\n")


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Video generation workflow — scaffold a full Veo/Gemini episode package.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="build an episode from a JSON spec")
    pb.add_argument("spec", help="path to the episode JSON spec")
    pb.add_argument("--base", default="Videos", help="base output dir (default: Videos)")
    pb.add_argument("--series", default=None,
                    help="path to series bible JSON (default: ./series.json or built-in)")

    pd = sub.add_parser("demo", help="build the bundled example episode")
    pd.add_argument("--base", default="Videos", help="base output dir (default: Videos)")

    pt = sub.add_parser("template", help="write a blank spec you can fill in")
    pt.add_argument("out", help="path for the new spec JSON")

    ps = sub.add_parser("series", help="write the series bible (TyGuy + Kelliee) to a file")
    ps.add_argument("out", nargs="?", default="series.json", help="path (default: series.json)")

    pg = sub.add_parser("generate", help="generate the video clips with Veo (paid; needs GEMINI_API_KEY)")
    pg.add_argument("spec", nargs="?", help="episode JSON spec (omit with --demo)")
    pg.add_argument("--demo", action="store_true", help="generate the bundled demo episode")
    pg.add_argument("--base", default="Videos", help="base output dir (default: Videos)")
    pg.add_argument("--series", default=None, help="path to series bible JSON")
    pg.add_argument("--seed", default="tyguy_seed.png",
                    help="reference image to seed TyGuy/Kelliee shots (default: tyguy_seed.png)")
    pg.add_argument("--scenes", type=int, nargs="+", metavar="N",
                    help="only generate these scene numbers (default: all)")
    pg.add_argument("--dry-run", action="store_true",
                    help="show what would be generated without calling the API")
    pg.add_argument("--assemble", action="store_true",
                    help="stitch the clips into one episode file after generating")
    pg.add_argument("--vertical", action="store_true",
                    help="with --assemble, build a 9:16 (1080x1920) cut")

    pa = sub.add_parser("assemble", help="stitch an episode's clips into one mp4")
    pa.add_argument("number", type=int, help="episode number (e.g. 1)")
    pa.add_argument("--base", default="Videos", help="base output dir (default: Videos)")
    pa.add_argument("--vertical", action="store_true", help="9:16 (1080x1920) cut")
    pa.add_argument("--out", default=None, help="output mp4 path")

    args = p.parse_args(argv)

    if args.cmd == "template":
        Path(args.out).write_text(json.dumps(TEMPLATE_SPEC, indent=2))
        print(f"✓ Wrote spec template to {args.out}")
        print("  Edit it, then: python3 video_workflow.py build " + args.out)
        return 0

    if args.cmd == "series":
        Path(args.out).write_text(json.dumps(SERIES, indent=2))
        print(f"✓ Wrote series bible to {args.out}")
        print("  Edit shared TyGuy/Kelliee details here; episodes inherit them.")
        return 0

    if args.cmd == "assemble":
        # Rebuild the episode object just to resolve its folder name.
        ep = Episode(number=args.number, title="")
        out = Path(args.out) if args.out else None
        assemble(ep, Path(args.base), vertical=args.vertical, out=out)
        return 0

    if args.cmd == "generate":
        if args.demo:
            ep = Episode.from_dict(merge_series(example_spec(), load_series()))
        elif args.spec:
            ep = _load_spec(args.spec, args.series)
        else:
            p.error("generate needs a spec path or --demo")
        # Make sure the package exists alongside the clips.
        build(ep, Path(args.base))
        generate(ep, Path(args.base), which=args.scenes, seed_path=args.seed,
                 dry_run=args.dry_run)
        if args.assemble and not args.dry_run:
            assemble(ep, Path(args.base), vertical=args.vertical)
        return 0

    if args.cmd == "demo":
        ep = Episode.from_dict(merge_series(example_spec(), load_series()))
    else:
        ep = _load_spec(args.spec, args.series)

    base = Path(args.base)
    ep_dir = build(ep, base)
    _report(ep, ep_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
