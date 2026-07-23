# 🟢 START HERE — Mold Mission (the one handoff doc)

**This is the single source of truth.** Read this first in any new chat.
Everything we've built lives on GitHub and comes back automatically — nothing
is stuck in a chat window.

- **Repo:** `boisemoldremoval-cpu/TyDez`
- **Branch:** `claude/install-repository-xlm50f`  ← always use this exact branch
- **Latest commit:** `3e2812f`
- **The game:** `games/mold_mission/mold_mission.py` (~2,900 lines, pygame)

---

## ▶ HOW TO CONTINUE IN A NEW CHAT (3 steps)
1. Start a **new session** in Claude Code (the “+ / New session” button).
2. Choose repo **`boisemoldremoval-cpu/TyDez`** and the **existing** branch
   **`claude/install-repository-xlm50f`** (do NOT create a new branch).
3. Paste this as your first message:
   > Read START_HERE.md, then do the OPEN REQUESTS. Verify with
   > `python3 games/mold_mission/mold_mission.py --selftest`.

That's it — the new chat has every file on disk and this doc tells it exactly
what to do. No data is lost; git is the memory.

---

## ⚠ THE ONE THING THAT NEEDS A FRESH CHAT
This session's **image reader is used up** — it rejects every new image
(that's why new art can't be viewed/cut here). A fresh chat resets it.
(Cutting art with code/PIL has no limit; only *looking at* images does.)

---

## ✅ OPEN REQUESTS  (both done — see notes)
1. **"Allow these movements."** ✅ DONE. The sheet
   (`art_reference/pending/upload_new_8ea6eccc.png`) is Ty's **crouch** move-set.
   All **15 poses** were cut cleanly (transparent, de-spilled, autocropped) via
   `cut_crouch.py` into `assets/player_crouch*.png`, and the crouch state was
   rebuilt from a frozen duck into a full move-set that the gameplay drives:
   - **Crouch-walk** — hold ↓/S + Left/Right to shuffle along while ducked
     (slower, short hurtbox) → `player_crouch_walk`.
   - **Crouch slide** — L/Shift + a direction while ducked = a low evasive slide
     (keeps the short hurtbox) → `player_crouch_slide`.
   - **Crouch melee** — L/Shift while ducked and still = a short front swing that
     clears nearby mold (and chips a boss / open weak point) →
     `player_crouch_melee`.
   - **Crouch jump** — springing up out of a crouch → `player_crouch_jump`.
   - **Ducked combat/status** — fire (`_shoot`), charge-aim (`_aim`/`_aim_ds`),
     take-damage (`_hurt`), low-health (`_low`), low-energy (`_reload`), and a
     pickup grab (`_item`) all pick the matching crouch pose automatically.
   - `player_crouch_roll`, `player_crouch_cover` + `player_crouch_interact` are
     also cut and loaded; roll overlaps the slide dodge, and cover/interact
     embed set-dressing (crate / console), so these are kept available for
     scripted moments rather than auto-shown.
   Note: this sheet is a darker *tactical* Ty, while the standing sprites are the
   art-bible blue-and-white kid — so Ty's look shifts a little when he ducks (a
   deliberate choice — you asked to use these animations for TyGuy).
   *(Also: every character bobs while moving, so nothing looks frozen.)*
1b. **"Use these animations in the gameplay. We will allow item pick up."** ✅ DONE
   (Batch 7). The leftover TyGuy video clips are now a real interact mechanic:
   - **Pick up / carry / throw / place a supply crate.** Press **E** (or **F**)
     next to a crate to grab it → `player_pickup`, then Ty carries it in his
     hands → `player_carry`. While carrying, **J/X throws** it (arcs forward,
     smashes the first enemy it hits) → `player_throw`; **E places** it gently
     on the ground → `player_place`. Crates are non-solid, so they never block
     the run; a thrown crate does 6 dmg.
   - **Use a console.** Press **E** at a wall terminal → `player_use`; it powers
     on (green glow → grey), refills energy, and pops a "TERMINAL ONLINE" toast.
   - **Crouch-run.** Moving fast while ducked now plays `player_crouch_run`
     (slow ducked shuffle still plays `player_crouch_walk`).
   Crates (2/level) + a console (1/level) are placed off the main sprint line as
   optional interacts. The auto-bot ignores the interact key, so they're pure
   scenery to `--selftest` and it stays green. Clips cut by `cut_tyguy_anim.py`.
2. **"Make sure all words look professional and in the right place."** ✅ DONE.
   Every text screen was rendered and eyeballed (HQ hub incl. every menu row,
   in-mission HUD, objective + boss health bar + weak-point hint, boss-intro
   banner, weapon-pickup toast, all mission-win teases, the mission-5 finale,
   and game-over). Wording proofread — consistent and clean. Fixed one overlap:
   on the finale the "Press Enter" prompt collided with the "remote sensor"
   tease line; the prompt now drops lower on that screen only.

---

## 🎮 WHAT THE GAME IS / HOW TO RUN IT
A Mega Man–style run-and-gun: play **Ty**, blast mold across 5 missions to a
boss each, with a HQ hub for mission select, upgrades, and weapon pickups.
```bash
cd games/mold_mission
pip install -r requirements.txt
python3 mold_mission.py            # play it
python3 mold_mission.py --demo     # watch an auto-playthrough of all 5 missions
python3 mold_mission.py --selftest # must print: selftest OK: all 5 missions win
```

### 🎬 TyGuy — MULTI-FRAME video animations + video SFX
Ty's poses are now full **frame-sequence animations** clipped from four movement
videos (`cut_tyguy_anim.py` — imageio-ffmpeg + scipy, magenta-keyed, feet-aligned
onto one canvas per clip so they cycle with no wobble). Each state is
`player_<state>_0.png … _N.png`; `AssetPack.anims` groups them and the draw
cycles the frames (`ANIM_FPS` per state, timed off the draw clock). Full set:
idle, walk, run, dash, jump, peak, fall, land, wall-slide, crouch, crouch-walk,
roll, **aim (rifle)**, **shoot (rifle + muzzle)**, reload, use. The three newer
videos added the crouch set, roll, and the gun poses — so Ty now shoots/aims
with a real rifle, all still 100 % video art.
**Video SFX:** short clips pulled from the videos' audio tracks live in
`assets/sfx/*.wav` (`shot / jump / land / dash / wall / vacuum / reload`) and
override the synth tones in `Sound` — so his moves sound like the videos.

### 🎞 TyGuy — VIDEO ANIMATIONS ONLY (physics-driven)
Ty now uses **only** his video-sourced poses everywhere in the game (pulled from
the movement video via `cut_tyguy_video.py` — imageio-ffmpeg + scipy, chroma-keyed
off magenta, largest-connected-component to drop the on-screen labels). The full
set: `player` (idle), `player_walk`, `player_run`, `player_jump`, `player_peak`
(apex), `player_fall`, `player_land`, `player_dash`, `player_wallslide`,
`player_crouch`. The draw picks a pose purely from **physics state** (vx for
walk/run, vy for jump/peak/fall, `land_t` for landing, `sliding` for wall-slide,
`crouching` for the duck, `dash_t` for dash) — so the animation reacts to the
world's physics. The old magenta-sheet poses (shoot / aim / crouch sub-set /
climb / reload / victory / the `ty_<weapon>` overlays) are **no longer used**:
firing shows the matching move pose and the shot still leaves the muzzle point,
so Ty never leaves the video look. More videos (his other actions + the rest of
the cast) can be pulled the same way.

### 🦸 TyGuy character art (unified)
Ty is now the **tactical TyGuy** everywhere. Standing / run / dash / jump / fall
/ aim / shoot / hurt / victory / reload / ladder-climb were cut from the bright
**magenta** chroma sheet
`art_reference/pending/tyguy_full_animation_guide_magenta.png` (see
`cut_tyguy.py` — magenta shares no colour with Ty, so it keys cleanest and cuts
at higher res) and the crouch move-set from the crouch sheet — one consistent
character in every pose. `player_climb` shows front-on while on a ladder
(ladders recoloured to warm wood so the pose's own grip blends), and
`player_reload` shows when Ty stands with his energy drained.

### 👾 Enemies added from art sheets
- **Micro Mold** (`micromold`) — a small common swarm unit cut from its chroma
  sheet (`cut_micromold.py`). Scattered in clusters across **all 5 missions**;
  crawls steadily (no pounce) so a swarm can't shove Ty into a spike.
- **Spore Drifter** (`sporedrifter`) — a floating spore-shooter cut via
  `cut_sporedrifter.py` (idle / drift / attack / hurt / **charge** / **enraged**).
  Deployed on **certain air-heavy stages (missions 3 & 5)**: it hovers in the air
  lanes, floats toward Ty's level, and fires an aimed **spore shot** that damages
  him — telegraphed by a brief **charge** wind-up pose. Once wounded it **enrages**
  (enraged pose, faster drift/fire, a 3-way spore spread). Placed clear of the
  spike/pit leaps and short-ranged so its knockback can't turn a hazard jump into
  a death.

- **Toxic Slime** (`toxicslime`) — a slow corrosive ground blob cut via
  `cut_toxicslime.py` (idle / crawl / attack / hurt / **enraged**). Deployed on
  **certain non-air stages (missions 1, 2 & 4)** in open ground clear of the
  leaps: it crawls at Ty, spits an arcing **acid glob** that damages him, and
  leaves a short-lived **acid-pool trail** (`Game.acids`) that corrodes Ty with a
  gentle no-knockback tick while he stands in it. Enrages when wounded (enraged
  pose, faster, a corrosive spit spread).

- **Corrupt Cyst** (`corruptcyst`) — a slow pulsating eyeball blob cut via
  `cut_corruptcyst.py` (idle / roll / acid-glob / hurt). It rolls at Ty and lobs
  arcing acid, and its signature is that it **explodes on death** — a radial
  8-way spore burst + acid pool (handled in `Game._split`, buffered via
  `_new_shots`), so a point-blank kill catches Ty in the blast. On missions 3 & 5.
- **Spore Turret** (`sporeturret`) — a stationary cannon **mounted on the level
  platforms** (cut via `cut_sporeturret.py`: idle / firing / hurt). It never
  moves, rotates to track Ty, and fires an aimed spore down at him — one per
  stage on a back-field ledge. This is the clearest **environment engagement**:
  the enemy sits on a platform object and shoots from it. (Audited: no enemy
  floats on any level; every level has working movers, ladders and props, and
  the player rides moving platforms and climbs ladders.)
- **Fungus Brute** (`fungusbrute`) — a large, heavy **elite** cut via
  `cut_fungusbrute.py` (idle / run / club-attack / hurt / **rage**). High health
  (14) and high melee damage (5); lumbers toward Ty, hurls arcing **toxic
  spores**, and **enrages** when wounded (rage pose, faster, spore-burst spread).
  Dropped as a set-piece on **missions 2 & 4** in clear open stretches.
- **Mold Crawler** (`moldcrawler`) — the Mission-1 crawler now has **real art**
  (idle / run / attack / hurt / **enraged**) cut via `cut_moldcrawler.py`
  (its thin legs are detached from the body on the sheet, so the cutter takes
  the body blob then all non-bg pixels in a small expansion — no leg clipped).
  It's now a **fast** skitterer (speed 105) that lunges, and goes **INFECTED**
  (enraged, speed 150) once wounded.

### 🎯 Enemy hitboxes track the art (accurate hits)
Sprite enemies are drawn height-normalised (`self.h * CHAR_H`) so their art is
larger than the raw `(w,h)`. `Enemy.rect()` now returns a collision box that
matches the **drawn** sprite (feet-anchored, aspect from the loaded art, small
fairness inset), so a shot or contact lands where the animation actually is.
Every enemy's drawn aspect is tagged in `Game.reset()` via `ENEMY_ASSET`. Enemy
spawn spots are placed in the gaps between the base roster and clear of the
hazard leaps — **verified zero overlaps on all 5 levels**, spread Mega-Man style.

### 🧬 Dr. Mira — support ally (`Ally` class)
Dr. Mira (Field Scientist) now **deploys with Ty in every mission**. She trails
just behind him (idle / run / heal-cast sprites cut from her magenta sheet via
`cut_mira.py`) and fires a green **Bio-Cleaner heal beam** whenever his health
drops below ~65%, restoring HP over ~1.5s (beam drawn in-engine so it always
reaches Ty). She's a non-combatant — enemies pass through her, she takes no
damage — so she smooths the run and the tough boss fights without disrupting the
core game. Her HQ portrait now uses the same art.

### 🕹 Mega Man feel (moves · levels · buttons)
- **Moves:** variable-height jump (hold higher / tap hop) + double jump; the
  Mega Man **slide** (↓+Jump); a full crouch move-set (sneak-walk, ducked
  fire/aim, slide, melee); hold-to-**charge** buster; ladder **climbing**;
  dash. Buttons: A/D move · Space/W/Z jump · J fire · K vacuum · ↑↓ climb ·
  L dash · ↓+Jump slide.
- **Levels:** each stage is a Mega Man platforming run — **pits** (a fall is
  instant death), **spike** strips to leap, **ladders** up to bonus platforms
  with pickups, floating platforms, and a solid boss approach.
- **Moving dynamics (`Mover` class):** horizontal patrol platforms, vertical
  **elevators**, **collapsing** platforms (step on → shake → fall → respawn),
  and **conveyor belts** that shove you. Whatever Ty rides carries him by the
  platform's per-frame delta, so momentum feels real; each carries a coin as a
  reward for using it.
- **Consistent sizing:** every character is drawn at one size across all its
  poses/screens, scaled to its collision box and planted at the feet
  (`blit_char` + `CHAR_H`/`BOSS_H`) — no more pose-to-pose size popping.
- **Animation juice:** `blit_char` takes a `squash` factor — Ty squashes on
  landing (with a dust puff) and stretches on the rise; every enemy has an idle
  breathing pulse + a hit-squash; all 5 bosses breathe. Sprite enemies still
  walk-cycle / hurt / attack on top of that.

## 🧩 WHAT'S BUILT (91 sprites; self-test passes all 5)
- **Ty** — full animation: idle/run/jump/fall/dash/crouch/aim/shoot/victory.
- **Weapons** — 5 pickup weapons Ty finds & fires; gunfire colour matches the
  weapon; HUD shows the equipped one.
- **HUD** — player-status panel, resource panel, boss health bar.
- **Audio / game-feel** — per-action sound effects, music, screen shake,
  hit-stop, knockback.
- **MOLD-E** drone companion — follow / scan / alert.
- **Mold Turret** — allied auto-defense (idle + firing pose).
- **Enemies** — 12 animated mold blobs with distinct attack patterns; the rest
  are vector but now bob when moving.
- **Bosses** — `boss3` Spore Queen, `boss4` Crawlor, `boss5` final SporeMother
  (enrage pose).
- **HQ cast** — Commander Ellis, Captain Rex, Dr. Mira, HQ Engineer, Field
  Medic, Purification Core; Dr. Sporead villain on the win-tease.
- **Systems** — drop-in auto-animating art; oversized-file split/reassemble
  loader; `--demo`; `--selftest`.

## 🎨 STILL NEEDS REAL ART (recolors can't fake these shapes)
- Enemies: `moldbat`, `sporehawk`, `roofleech`, `centipede`, `pipeparasite`,
  `sporeworm`, `sentinel`, `ventstalker`.
- Bosses: `boss` (Sludge King), `boss2` (Shower Beast).
- Per-mission backgrounds/tiles.

## 🖼 HOW NEW ART BECOMES ANIMATED SPRITES
Drop transparent PNGs in `games/mold_mission/assets/`, named by key — they
override vector art and animate automatically:
- Player: `player`, `player_run`, `player_jump`, `player_crouch`, `player_shoot`,
  `player_aim`, `player_victory`.
- Enemy `<kind>`: `<kind>` + `<kind>_run` + `<kind>_hurt` + `<kind>_attack`.
- Boss `<key>`: `<key>` + `<key>_hurt` (shown while its weak point is exposed).
- **Too-big file?** `split_asset("assets/x.png")` splits it across folders and
  the game reassembles it at load.

Cutting recipe (used throughout): crop the pose from the sheet's "ANIMATION
POSES" row → flood-fill the solid background from the edges → keep the largest
connected shape (protects enclosed logos/eyes) → light de-spill → autocrop.

## 📁 WHERE THINGS ARE
- Game: `games/mold_mission/mold_mission.py`
- Sprites in use: `games/mold_mission/assets/`
- Cut source art: `games/mold_mission/art_reference/`
- Art still to cut: `games/mold_mission/art_reference/pending/`
- Deeper technical notes: `games/mold_mission/HANDOFF.md`

## ✔ ALWAYS VERIFY AFTER CHANGES
`cd games/mold_mission && python3 mold_mission.py --selftest`
→ must print **`selftest OK: all 5 missions win`**.
