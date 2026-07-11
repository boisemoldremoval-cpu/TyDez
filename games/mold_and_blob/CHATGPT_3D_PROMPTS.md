# Mold & Blob — 3D Asset Prompt Pack (for ChatGPT / image models)

Drop this whole file into ChatGPT, **attach the style reference image**
(`art_export/reference_3d/tyguy_3d.png` — the teal 3D TyGuy figure), and ask it
to generate the assets one at a time using the prompts below. Each finished
image goes into the game's `assets/` folder under the filename listed.

---

## How to use

1. Start a chat and **upload `tyguy_3d.png`** as the style reference.
2. Paste the **MASTER STYLE** block once, then paste **one asset prompt** at a
   time (image models do one subject best).
3. Ask for: **transparent background (PNG with alpha), no ground shadow,
   1024×1024 (or the aspect noted), subject centered and filling ~85% of frame.**
   - If the model can't do transparency, ask for a **flat solid white
     background** and remove it afterward (any background remover, or tell me and
     I'll cut it).
4. Download and rename to the exact filename (e.g. `tyguy.png`) and drop it in
   `games/mold_and_blob/assets/`. The game picks it up automatically.

**Consistency is everything:** keep the SAME camera angle, SAME lighting, and
SAME palette across every asset so they look like one set. Re-attach the
reference image with each prompt.

---

## MASTER STYLE (paste first, and prepend to each asset)

> Style: a **collectible designer vinyl toy** rendered in 3D — chibi proportions
> (slightly oversized head, chunky rounded forms), smooth matte surfaces with
> soft glossy highlights, subtle ambient occlusion, gentle rim light, clean soft
> studio softbox lighting from the upper left. High-detail Octane/Redshift look,
> like the attached reference figure. **Match the reference's colours exactly:**
> vivid teal-green (approx `#12B48C`), black accents, warm skin tone, white "T"
> logo. Friendly, premium, slightly cartoonish. **Transparent background, no
> ground shadow, no text captions, subject centred.** PNG.

Game palette for reference: `#12B48C`/`#56D6A5` teals · `#101816` near-black ·
`#EAC8A8` skin · `#7EAC52`/`#486A2E` mold greens · `#D2B060` door gold.

---

## ASSET PROMPTS

### 1. `tyguy.png` — the player  (1024×1024, transparent)
> A cheerful mold-removal technician character (same figure as the reference),
> **full body, side-on 3/4 view facing RIGHT, in a mid-stride walking pose**.
> Teal coverall, black hard hat with a rounded brim, black backpack sprayer tank,
> holding a **spray wand/nozzle pointing forward** in the near hand. Round black
> chest badge with a white "T". Clean and readable as a small game sprite. Feet
> near the bottom of the frame. Transparent background, no shadow.

*(The game mirrors this image automatically when he walks left.)*

### 2. `blob.png` — the companion  (1024×1024, transparent)
> A cute round **teal-green slime/blob creature**, glossy and jelly-like, with two
> big friendly cartoon eyes and a small smile, a soft highlight on top. Same
> vinyl-toy 3D style and teal as the reference. Roughly circular, centred.
> Transparent background, no shadow.

### 3. `mold.png` — the enemy  (1024×1024, transparent)
> A lumpy **mold spore blob**, sickly yellow-green (`#7EAC52` with darker
> `#486A2E` patches), fuzzy/bumpy surface, a few tiny spore dots floating around
> it, a faintly gross but cartoonish look. Same 3D toy render style. Roughly
> circular, centred. Transparent background, no shadow.

### 4. `trampoline.png` — Blob as a trampoline  (1200×520, transparent)
> The teal blob creature morphed into a **bouncy trampoline / spring pad**: a wide
> rounded teal top cushion on little spring legs, two small cartoon eyes on the
> front rim. Horizontal, wider than tall. Same style. Transparent background.

### 5. `bridge.png` — Blob as a bridge  (1600×220, transparent)
> The teal blob creature stretched into a **long horizontal bridge / plank**,
> rounded ends, a subtle top surface sheen, two small cartoon eyes near one end.
> Long and thin. Same style. Transparent background.

### 6. `ladder.png` — Blob as a ladder  (360×1200, transparent)
> The teal blob creature formed into a **vertical ladder**: two rounded teal side
> rails with soft rungs between them, jelly-like glossy finish. Tall and narrow.
> Same style. Transparent background.

### 7. `door_closed.png` — exit, locked  (720×880, transparent)
> A small **stylised exit door** as a 3D toy prop, warm gold/brass frame
> (`#D2B060`), dark inset panel, a little round knob. Slightly cartoonish. Portrait
> orientation. Transparent background, no shadow.

### 8. `door_open.png` — exit, cleared  (720×880, transparent)
> The same exit door but **glowing bright green (`#78E096`)**, welcoming, with a
> soft green light spilling from the doorway. Same size and framing as
> `door_closed`. Transparent background.

### 9. `background.png` — the level backdrop  (1536×1024, landscape) *(optional)*
> A **moody, softly-lit backdrop** for a side-scrolling platformer: gentle rolling
> dark-teal hills receding into a hazy gradient sky, faint mist, a soft glow near
> the top. No characters, no platforms, no text. Painterly-but-clean, matches the
> teal 3D toy world. Full-bleed landscape image (a background, not a sprite).

### 10. `platform.png` — the ground tile  (1024×256) *(optional)*
> A **chunky stylised ground/platform block** seen from the front: dark soil body
> with a bright mossy teal-green top edge, rounded corners, subtle texture, 3D toy
> look. Designed to tile/stretch horizontally. Transparent or plain background.

---

## After you have the images

Rename each to the filename above and drop them in
`games/mold_and_blob/assets/`. Start the game and they replace the drawn art
everywhere; anything you haven't made yet stays as the built-in vector version.
See `assets/README.md` for exact framing/size notes.
