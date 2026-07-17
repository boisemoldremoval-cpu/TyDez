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

### 🕹 Mega Man feel (moves · levels · buttons)
- **Moves:** variable-height jump (hold higher / tap hop) + double jump; the
  Mega Man **slide** (↓+Jump); a full crouch move-set (sneak-walk, ducked
  fire/aim, slide, melee); hold-to-**charge** buster; ladder **climbing**;
  dash. Buttons: A/D move · Space/W/Z jump · J fire · K vacuum · ↑↓ climb ·
  L dash · ↓+Jump slide.
- **Levels:** each stage is a Mega Man platforming run — **pits** (a fall is
  instant death), **spike** strips to leap, **ladders** up to bonus platforms
  with pickups, floating platforms, and a solid boss approach.
- **Consistent sizing:** every character is drawn at one size across all its
  poses/screens, scaled to its collision box and planted at the feet
  (`blit_char` + `CHAR_H`/`BOSS_H`) — no more pose-to-pose size popping.

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
