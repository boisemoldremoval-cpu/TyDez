# Boise Mold Removal — Pixar-style ad: cast sheet + 4-beat storyboard

Reusable continuity sheet for the Disney-Pixar 3D animated ad. Paste the STYLE LOCK
verbatim into every gpt-image-2 prompt; chain each approved still as a reference into
the next beat to hold character identity.

Brand: **Boise Mold Removal** (boise-moldremoval.com)
Accent color: teal-green `#56D6A5` (brand badge) + clean white.
Phone: (208) 412-0899 · 24/7 · Veteran-supported · Treasure Valley (Boise, Meridian, Kuna, Nampa, Caldwell)
Services: mold removal & remediation, attic/crawlspace blow-in insulation, water-damage remodels, pre-inspections.

---

## Cast & continuity

PROTAGONIST (human hero) — the technician "Ty"
- 30s, friendly, average build, light stubble, warm smile, large expressive Pixar eyes with multiple catchlights.
- Outfit: clean teal-green work polo with a small white shield logo, ballcap (subtle veteran/flag patch), nitrile gloves, respirator pushed up on the cap.
- Personality cue: calm, reassuring, "we've got this" head-tilt and nod.

ANTHROPOMORPHIC PROBLEM CHARACTER (beat 1) — "Moldy"
- What object: a fuzzy black-green mold patch spreading in a damp crawlspace ceiling corner.
- Face placement: two big smug half-lidded eyes and a sly grin embedded in the fuzz; little spore puffs when it talks.
- Voice/personality: smug squatter, gloating, lazy ("I LOVE your damp crawlspace…").

MASCOT CHARACTERS (beat 3) — "the Crew"
- Form: chibi blob technicians, 2–3 inches "tall", smooth matte rubbery ivory material with tiny teal hard-hats.
- Eyes: oversized black dot pupils, single highlight.
- Behavior: cooperative team — HEPA-vacuuming, scrubbing, sealing; glowing teal "clean" energy lines trail behind them.

SETTING
- Beat 1: dim damp crawlspace cross-section, water stain, single shaft of light.
- Beat 2 & 4: bright tidy home interior / front porch, sunlit, plant in clay pot, warm color grade.
- Beat 3: stylized cross-section of the crawlspace/attic with the chibi Crew at work.

PRODUCT / BRAND OBJECT
- The brand "packaging" = the Boise Mold Removal service van + white shield logo on the teal polo, and a small yard sign reading "Boise Mold Removal · (208) 412-0899".

STYLE LOCK (paste verbatim into every image prompt)
"Disney-Pixar 3D animated feature film aesthetic, soft volumetric golden-hour lighting,
subsurface scattering on skin, large expressive eyes with multiple catchlights, stylized
but believable proportions, rich material rendering, shallow depth of field, warm cozy
color palette, painterly background."

---

## 4-beat script (9:16, ~60s, caption-only unless VO added)

**Beat 1 — Hook (anthropomorphized problem) · ~6s**
Visual: macro push-in on "Moldy" the smug mold patch in a dim crawlspace corner, spore puffs.
Caption / VO: "Oh hey… I LOVE your damp crawlspace. I'm never leaving."

**Beat 2 — Reveal (protagonist meets product) · ~7s**
Visual: cut to bright porch — Ty the technician kneels at the crawlspace hatch, flashlight on, confident smile, teal polo + shield logo.
Caption / VO: "Yeah? We'll see about that. Boise Mold Removal — on it."

**Beat 3 — Mechanism (mascot crew at work) · ~10s**
Visual: stylized crawlspace cross-section, the chibi Crew HEPA-vacuum, scrub, and seal; teal clean-energy lines sweep across; Moldy shrinks and gulps.
Caption / VO: "HEPA scrub. Full remediation. Sealed, dried, gone — for good."

**Beat 4 — CTA (resolution + brand) · ~6s**
Visual: bright clean home, happy homeowner shakes Ty's hand; yard sign + van with logo; Moldy is gone.
Caption / VO: "Mold gone for good. Veteran-owned. 24/7. Call (208) 412-0899."

---

## Generation order (once Arcads key is in)
1. gpt-image-2 Beat 1 still → approve.
2. gpt-image-2 Beats 2–4 stills, chaining prior approved still as reference → approve each.
3. Seedance 2.0 image-to-video per beat (9:16, 720p, duration = beat length).
4. Stitch with ffmpeg/imageio-ffmpeg; burn captions (white, black stroke, lower third).
5. (Optional) ElevenLabs VO in one consistent voice; trim each clip to VO + 0.5s.

Negative prompt (every video beat): no live-action, no photorealistic faces, no 2D cel-shaded,
no extra fingers, no melted features, no morphing, no warped labels, no unintended on-screen text.
Seedance forbidden words to avoid: cinematic, professional, stunning, 8k, studio, perfect.
