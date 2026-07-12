# Mold Mission — Handoff / Status

Everything below lives on branch **`claude/install-repository-xlm50f`**. A fresh
session that checks out this branch has all of it on disk. Read this file first.

## What it is
A Mega Man–style run-and-gun in one file: `mold_mission.py` (pygame). You play
**Ty**, blasting mold across 5 missions to a boss each, with a HQ hub for
mission select + upgrades.

## Run it
```bash
cd games/mold_mission
pip install -r requirements.txt
python3 mold_mission.py            # play
python3 mold_mission.py --selftest # headless: bot wins all 5 (CI gate; asserts)
python3 mold_mission.py --demo     # watchable auto-playthrough of the whole game
```

## Drop-in art system (how art becomes sprites)
Transparent PNGs in `assets/` override the vector art by key. **State variants
auto-load and animate** — just drop the file, no code change:
- Player: `player`, `player_run`, `player_jump`, `player_crouch`, `player_shoot`,
  `player_aim`, `player_victory` (`player_dash`→run, `player_fall`→jump in code).
- Enemy `<kind>`: base + `<kind>_run` (moving) + `<kind>_hurt` (hit) +
  `<kind>_attack` (fires). Selected by state in `Enemy.draw`.
- Boss `<key>`: base + `<key>_hurt` (shown while weak-point/core is exposed).
- Companion: `molde`, `molde_scan` (idle/exploring), `molde_alert` (near danger).
- Turret: `turret`, `turret_attack` (firing pose).

### Oversized files
If a sprite is too big, `split_asset("assets/x.png", parts=2)` splits it into
byte-parts across `split_a/`+`split_b/` with a `x.split.json` manifest; AssetPack
reassembles it at load. `boss5` ships pre-split as a working example.

## What's DONE (has real/derived sprites + animation)
- **Ty** — full state animation (idle/run/jump/fall/dash/crouch/aim/shoot/victory).
- **MOLD-E** companion — follow / scan / alert, trails the player.
- **Mold Turret** — allied auto-defense, idle + fire-beam pose.
- **Enemies (12, animated idle/run/hurt):** `sporebot` (Mold Sprouter, real art),
  and recolor-variants `moldcrawler`, `toxicsprayer`, `steammite`, `ventswarm`,
  `moldmite`, `creeper`, `mudstalker`, `gaspod`, `cultureswarm`, `reactorspore`,
  `mycelium`.
- **Bosses:** `boss3` (Spore Queen = SporeMother) and `boss5` (final SporeMother,
  with enrage pose). 
- **HQ:** Commander Ellis + support crew (Captain Rex squad leader, Dr. Mira,
  HQ Engineer, Field Medic) + the **Purification Core** (CHR_009) as the hub
  centerpiece.
- **Dr. Sporead** (CHR_008) — the mastermind villain; looms on each
  mission-win tease screen (`assets/sporead.png`).

## What's LEFT (still vector fallback — needs real art)
- **Non-blob enemies** (recolor can't fake their shapes): `moldbat`, `sporehawk`,
  `roofleech`, `centipede`, `pipeparasite`, `sporeworm`, `sentinel`, `ventstalker`.
- **Bosses:** `boss` (Sludge King), `boss2` (Shower Beast), `boss4` (Crawlor).
- **Backgrounds/tiles:** `background`/`platform` per mission.

## Pending art to cut  →  `art_reference/pending/`  — CLEARED ✅
The queue is fully processed (see `art_reference/pending/README.md`). Three new
characters were cut and wired — Dr. Sporead (`sporead`), Captain Rex (`rex`),
and the Purification Core (`purcore`); the rest were duplicate turnarounds of
already-cut characters and were removed (their canonical art lives in
`art_reference/`).

Cutting recipe used throughout (for future sheets): crop the pose region →
flood-fill the solid background from the edges (green or white) → keep the
largest connected component (protects enclosed green logos/eyes) → light
despill → autocrop. Layout is consistent: a 360° turnaround row up top and an
"ANIMATION POSES" row around the vertical middle; cut from those.

## Verify after any change
`python3 mold_mission.py --selftest` must print `selftest OK: all 5 missions win`.
