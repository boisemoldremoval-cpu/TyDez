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
| **J** (tap) | Fire the Disinfect Blaster |
| **J** (hold, release) | **Charge shot** — bigger, more damage |
| **K** (hold) | **HEPA Vacuum** — suction beam: pull enemies in, finish weakened ones, eat spore shots (uses Energy) |
| **L / Shift** | Dash (quick, briefly invulnerable) |
| Enter | HQ: select / deploy / buy · **M** sound · **Esc** quit |

At **DesilPower HQ** (title screen) use ↑/↓ to select, ◀ ▶ to change mission, and
Enter to Deploy or spend banked **Sample Cassettes** on Armor (+HP), Battery
(+Energy), or Speed upgrades — they persist across runs.

**Five missions** — the full campaign (each unlocks the next):
1. **The Basement** — Spore Bots, Mold Crawlers, Toxic Sprayers, Mold Bats; boss
   **Sludge King** (chest weak-point opens after its attacks).
2. **The Bathroom** — Steam Mites, Mold Bat Mk II, Vent Spore Swarms (split unless
   killed with a charged shot), steam-vent hazards; boss **Shower Beast** (back
   regulator opens after slams — dash behind).
3. **The Attic** — Insulation Creepers, Spore Hawks, Mold Mite clusters, Roof
   Leeches, **air-current updrafts** to ride upward; boss **Spore Queen** (hovering,
   summons mites/hawks, exposed core weak-point).
4. **The Crawlspace** — Mud Stalkers, Mold Centipedes (split), Pipe Parasites, Gas
   Pods, Burrowing Spore Worms, **standing-water slow zones**; boss **Crawlor** (a
   segmented tunneling worm — erupts, summons Pipe Parasites, exposed segment cores).
5. **Research Facility** *(finale)* — elite roster: Biofilm Sentinels, Vent Stalkers,
   Culture Swarms (split), Reactor Spores, Security Mycelium; final boss **Moldius
   Prime** (4 phases, summons elites, Purification-Node weak point) → campaign ending.

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
`toxic`, `coin`, `background`, `platform`; `ellis` (Commander Ellis at HQ); `molde` (MOLD-E companion drone that trails Ty).

The art direction is the **Mold Mission design sheet** in `art_reference/`.
See the game's tuning constants at the top of `mold_mission.py`.
