# Mold Mission 🧪🎯

A **Mega Man-style run-and-gun** for TyDez / Boise Mold Removal. You're the Mold
Technician: run, jump, and blast mold with your **Disinfect Blaster** — *hold
fire to charge a big shot*, just like Mega Man's buster — clear the stage of
Spore Bots, Mold Crawlers and Toxic Sprayers, then defeat the end boss
**MOLDTIUS, the Source of Contamination**.

Built with pygame. Single file. **Drop-in art** (see below) — currently ships
with your 3D TyGuy for the player and clean vector placeholders for everything
else.

## Run

```bash
pip install -r requirements.txt
python3 mold_mission.py
```

## Controls

| Key | Action |
|-----|--------|
| ← → / A D | Move |
| ↑ / W / Space | Jump — press again in the air for a **double jump** |
| ↓ / S | Crouch |
| (into a wall, airborne) | **Wall slide**; jump to **wall-jump** off it |
| **J** (tap) | Fire a shot |
| **J** (hold, release) | **Charge shot** — bigger, more damage |
| **L / Shift** | HEPA Vac Dash (quick dash, briefly invulnerable) |
| Enter | Start / restart · **M** sound · **Esc** quit |

## What's in the prototype

- Scrolling stage with platforms, a health bar, charge meter, score & spore
  count.
- **Charge shot** (3 levels: tap / mid / full).
- Enemies: **Spore Bot** (patrols), **Mold Crawler** (chases), **Toxic Sprayer**
  (shoots toxic clouds). Each has HP and takes damage from your shots.
- **Boss fight** vs MOLDTIUS with a boss health bar and a two-phase attack
  pattern (fires faster/more when below half health).
- T-coin collectibles, particle effects (muzzle, sparks, mold splat, smoke),
  i-frames on hit.

Headless smoke test that plays the stage to a boss kill:

```bash
python3 mold_mission.py --selftest   # -> selftest: state=win ...
```

## Drop-in art

Put transparent PNGs in **`assets/`** and they replace the vector art. Missing
names fall back automatically. Recognized names:

`player` (idle) and optional state frames `player_run`, `player_jump`,
`player_fall`, `player_dash`, `player_crouch`, `player_shoot`, `player_hurt`;
`sporebot`, `moldcrawler`, `toxicsprayer`, `boss`, `shot`, `shot_charged`,
`toxic`, `coin`, `background`, `platform`.

The art direction is the **Mold Mission design sheet** in `art_reference/`.
See the game's tuning constants at the top of `mold_mission.py`.
