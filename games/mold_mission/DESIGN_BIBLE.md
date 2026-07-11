# Mold Mission — Game Design Bible (Volume 1, Chapter 1)

*Transcribed from `art_reference/Mold_Mission_Design_Bible_Vol1_Ch1.pdf`. This is
the canonical design reference for the game; the prototype in `mold_mission.py`
implements a slice of it.*

## Game Vision

Players become an elite mold remediation technician who restores contaminated
buildings, defeats intelligent mold creatures, and **unlocks new remediation
tools after every boss**. The game combines fast-paced platforming with
exploration and environmental storytelling.

## Core Gameplay Loop

> Mission Briefing → Explore → Fight Mold Creatures → **Collect Sample
> Cassettes** → Solve Puzzles → Defeat Boss → **Unlock New Tool** → Return to
> DesilPower HQ → Upgrade Equipment → Next Mission.

## Pillars (from the design sheet)

- **Player:** the Mold Technician ("DESIL POWER"), equipped with advanced
  remediation tools.
- **Tools / Weapons:** Disinfect Blaster (chargeable), HEPA Vac Dash (dash +
  vacuum), Sealant Shot (seal cracks so mold can't return). New tools unlock
  after each boss.
- **Enemies:** Spore Bot (spreads spores when destroyed), Mold Crawler (sticks
  to walls, slow), Toxic Sprayer (shoots toxic clouds).
- **End Boss:** MOLDTIUS — "The Source of Contamination," a massive mold colony.
- **Stages:** 1. Basement · 2. Attic · 3. Bathroom · 4. Crawlspace.
- **Power-ups:** Heal Pack, HEPA Filter, Protect Shield, Speed Boost.
- **Collectibles:** Sample Cassettes (+ T tokens).
- **HUD:** Health, Weapon Energy, Spore Count.

## Chapter 2 (planned)

Will fully define the player character: equipment, animation list, weapons,
statistics, hitboxes, upgrade tree, and labeled concept images.

## Prototype status (this repo)

Implemented in `mold_mission.py`: side-scrolling run-and-gun, chargeable
blaster, HEPA Vac Dash, the three enemy types, the MOLDTIUS boss with a
two-phase pattern, Sample Cassette pickups, a mission-briefing intro, and a
"tool unlocked" beat on boss defeat.

Not yet built: the 4 separate stages + stage select, puzzles, the DesilPower HQ
upgrade tree, power-up pickups, and Sealant Shot / weapon switching. See the
game's `README.md` for the drop-in art asset names.

## Reference images

- `art_reference/mold_mission_designsheet.png` — the full design sheet.
- `art_reference/player_character_concept.png` — main player character concept.
