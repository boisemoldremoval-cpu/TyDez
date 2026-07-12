# HANDOFF → next chat (Mold Mission)

Snapshot for a **fresh session** to continue. Everything is on GitHub, branch
**`claude/install-repository-xlm50f`** (repo `boisemoldremoval-cpu/TyDez`).
Latest commit at handoff: `738b440`.

## ▶ START HERE (how to resume)
1. New Claude Code session → repo `boisemoldremoval-cpu/TyDez` → **existing**
   branch `claude/install-repository-xlm50f` (don't make a new branch).
2. First message:
   > Read HANDOFF_NEXT.md and games/mold_mission/HANDOFF.md, then do the OPEN
   > REQUESTS.
3. Always verify with: `cd games/mold_mission && python3 mold_mission.py --selftest`
   → must print `selftest OK: all 5 missions win`.

## ⚠ WHY A FRESH SESSION
This session's **image reader is exhausted** ("media rejected by API") — it
can't open any new images, even tiny ones. A fresh session resets that so the
pending art can actually be viewed and cut. (Image *processing* via PIL in a
script has no such limit; only visual reads do.)

## ✅ OPEN REQUESTS (do these)
1. **"Allow these movements"** — the user sent a movement/animation sheet,
   saved at `games/mold_mission/art_reference/pending/upload_new_8ea6eccc.png`.
   Open it, identify the character, cut its movement poses, and wire them
   (`<key>` + `<key>_run`/`_hurt`/`_attack`, or player poses). Already done in
   code: every enemy draw path (sprite AND vector) now applies a walk/idle bob,
   so characters visibly move even without dedicated art (commit `738b440`).
2. **"Make sure all words look professional and in their right place"** —
   a scripted placement audit of HQ / gameplay HUD / win / over screens found
   **no off-screen text**. Still TODO with a working reader: eyeball ALL
   screens (boss intro banner, weapon-select, upgrade menu, mission-win tease,
   pause) for overlap/alignment, and proofread every string for wording.

## STATE OF THE GAME (much bigger than early handoffs)
`games/mold_mission/mold_mission.py` (~2,900 lines), 91 sprite assets. Runs;
self-test wins all 5 missions. Beyond the basics it now has:
- **Weapon pickup system** — 5 weapons Ty finds & fires; gunfire colour matches
  the weapon; HUD shows the equipped weapon.
- **Redesigned HUD** — player-status panel, resource panel, boss bar.
- **Audio + game feel** — per-action SFX, music, screen shake, hit-stop,
  knockback.
- **Enemies** — 12 animated mold blobs + distinct attack patterns; non-blob
  enemies still vector but now bob when moving.
- **Bosses** — `boss3` Spore Queen, `boss4` Crawlor (Crawler King art), `boss5`
  final SporeMother (enrage pose). Still vector: `boss` (Sludge King), `boss2`
  (Shower Beast).
- **Characters** — Ty (full state animation), MOLD-E (follow/scan/alert), Mold
  Turret (idle/fire), HQ crew (Ellis, Rex, Dr. Mira, Engineer, Medic,
  Purification Core), Dr. Sporead villain on win-tease.
- **Systems** — drop-in auto-animating art variants; `split_asset()` +
  reassembling loader for oversized files; `--demo` playthrough; `--selftest`.

## STILL NEEDS REAL ART (recolors can't fake these shapes)
- Enemies: `moldbat`, `sporehawk`, `roofleech`, `centipede`, `pipeparasite`,
  `sporeworm`, `sentinel`, `ventstalker`.
- Bosses: `boss` (Sludge King), `boss2` (Shower Beast).
- Backgrounds/tiles per mission.

## KEY FILES
- Game: `games/mold_mission/mold_mission.py`
- Sprites in use: `games/mold_mission/assets/`
- Cut source art: `games/mold_mission/art_reference/`
- Art still to cut: `games/mold_mission/art_reference/pending/` (1 file now)
- Deeper how-it-works: `games/mold_mission/HANDOFF.md`

Nothing lives only in chat — git holds all of it. Safe to end this session.
