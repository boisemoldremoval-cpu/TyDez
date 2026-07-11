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

---

# Volume 1, Chapter 2 — Elite Mold Technician (Player Character)

**Codename:** Ty (working name) · **Role:** Elite DesilPower Mold Technician ·
**Mission:** eliminate intelligent mold infestations while restoring buildings ·
**Personality:** courageous, optimistic, calm under pressure, problem solver.

**Starting equipment:** HEPA Backpack Unit, Digital Mold Scanner, Utility Belt,
Inspection Flashlight, Sample Cassette Holder, Protective Visor & Respirator.

**Player abilities:** run, jump, crouch, interact, climb ladders, wall slide,
dash *(unlock)*, double jump *(unlock)*, use remediation tools, deploy drones,
collect Sample Cassettes, scan hidden mold colonies.

**Upgrade path:** L1 HEPA Vacuum → L2 Disinfect Blaster → L3 Seal Foam Cannon →
L4 Air Scrubber Drone → L5 UV Pulse Emitter.

**Animation checklist:** Idle, Walk, Run, Sprint, Jump, Fall, Land, Crouch,
Ladder Climb, Dash, Hurt, Victory, Scan, Vacuum, Spray, Deploy Drone, Boss
Introduction, Game Over.

**Asset IDs:** PLY-001 Main Character, PLY-002 HEPA Backpack, PLY-003 Scanner,
PLY-004 Utility Belt, PLY-005 Helmet, PLY-006 Visor, PLY-007 Gloves,
PLY-008 Boots.

**Implemented in prototype:** run, jump, **double jump**, **crouch**, **wall
slide + wall jump**, dash, charged blaster, Sample Cassette pickups. State-based
player sprites are supported via drop-in art (`player_run`, `player_jump`,
`player_fall`, `player_dash`, `player_crouch`, `player_shoot`, `player_hurt`;
`player` is the idle fallback). Not yet: ladder climb, scan, drones, and the
full weapon upgrade tree.

---

# Volume 1, Chapter 3 — DesilPower Headquarters

Central hub between missions: upgrade equipment, accept missions, train, customize
cosmetics, review lore, save. **Areas:** Mission Command, Research Lab (tool
upgrades), Engineering Bay (movement upgrades), Training Simulator, Locker Room,
Archives, Garage. **NPCs:** Commander Ellis (briefings), Engineer Nova (builds
gear), Dr. Mira (lore/biology), Quartermaster Jax (sells upgrades for Sample
Cassettes). **Systems:** manual save, fast travel, achievement wall, collectible
cases, hidden practice room after Level 3.

**Implemented:** an HQ hub screen (the title screen) — Deploy Mission plus
Research Lab (Armor → +HP) and Engineering Bay (Battery → +Energy, Speed Module)
upgrades bought with banked Sample Cassettes; Commander Ellis flavor. Not yet:
the fully explorable 2D HQ, other NPCs, cosmetics, archives.

# Volume 1, Chapter 4 — Player Systems & Controls

Move / Jump / Interact / Primary Tool / Tool Wheel / Pause. Base run medium-fast,
responsive accel, jump clears one story. **Dash unlocks after L1, Double Jump
after L3, Wall Slide** enables wall jumps. **Health 100 HP**; Health Packs +25.
**Weapon Energy** powers advanced tools, refilled by **Energy Cells** from enemies.
**Checkpoints** save + refill + set respawn. **Upgrade tree:** Armor Mk I–V,
Battery Capacity I–V, Tool Efficiency, Movement Module. Dev note: prioritize
responsiveness — input buffering + **coyote time**, data-driven values.

**Implemented:** 100 HP, Weapon Energy meter + regen, coyote-time jumps,
enemy-dropped Health/Energy pickups, and the Armor/Battery/Speed upgrade tree via
HQ. Not yet: tool wheel, pause/inventory, checkpoints, Tool Efficiency.

# Volume 2, Chapter 2 — Boss: Sludge King

First Mold General; teaches pattern-recognition and weak-point play. A towering
humanoid of mud/fungal growth/pipes with a **cracked chest water-valve weak
point**. Arena: flooded basement with moving platforms and hazards. **Phase 1:**
punches, spore projectiles, ground slams. **Phase 2 (70% HP):** flood rises,
pipes burst. **Phase 3 (30% HP):** enrages, faster, **summons Mold Slimes**. The
chest valve opens briefly after heavy attacks. Rewards: HEPA Vacuum + Dash + 500
Sample Cassettes + Basement Restoration Badge.

**Implemented:** the Sludge King replaces the Basement boss — 3 HP-based phases,
a chest weak-point that opens after each attack (2× damage), spore-spread + ground
slam attacks, and Mold Slime summons in Phase 3. Reward text + 500-cassette bank
on victory. Not yet: the reactive flooding arena, moving platforms, cutscene.

# Volume 2, Chapter 3 — HEPA Vacuum Module

First permanent tool — clean rather than destroy. Removes spore clouds, vacuums
weakened small enemies, reveals hidden vents/cassettes, opens HEPA vents, clears
fungal blockages. **Tap:** suction burst · **Hold:** continuous beam · **Charge:**
vortex. Mk I–V upgrades (range, heavy pull, energy regen, air barrier). Blue/white
canister, hose, turbine, airflow particles.

**Implemented:** hold **K** for a suction beam that pulls enemies in, instantly
vacuums weakened enemies, and absorbs hostile spore projectiles (small energy
refund) — drains Weapon Energy. Not yet: vent/puzzle interactions, charge vortex,
the Mk I–V upgrade line.

# Volume 2, Chapter 5 — Enemy Pack 1

- **Spore Slime** — basic melee; short hop → body slam; weak to HEPA Vacuum after
  a stun; drops Cassettes/Health.
- **Mold Bat** — flying harassment; circles the player then dives; weak to the
  Blaster or a timed jump; drops Energy Cells.
- **Toxic Drip** — ceiling hazard; drips acidic mold on a timer; Vacuum clears
  buildup.
Shared AI: Idle → Patrol → Detect → Attack → Recover → Stunned → Defeated (data-driven).

**Implemented:** the **Mold Bat** flying enemy (circles + dives, drops energy).
The existing Spore Bot stands in for the Spore Slime. Not yet: hop/slam + stun
combo, Toxic Drip ceiling hazard, data-driven AI-state machine.

# Volume 2, Chapter 6 — Level 1 World Layout

A single-family home's flooded basement. **Rooms:** 01 Exterior Entry (movement
tutorial) · 02 Stairwell (first Spore Slime) · 03 Utility (scan tutorial) · 04
Laundry (water hazards, Mold Bat) · 05 Storage Maze (crate puzzle, secret room) ·
06 Mechanical (checkpoint + rising water) · 07 Boss Arena. Collectibles: 50 Bronze
/ 10 Silver / 1 Gold cassette + 1 hidden Blueprint (wall-slide challenge).
Environmental storytelling: family boxes, toys, water-stained drywall, restoration
tape.

# Volume 2, Chapter 7 — Level 1 Room-by-Room

Per-room beats (scan tutorial gating, melee avoidance, crate puzzle, checkpoint,
rising-water pre-boss, auto boss-intro cutscene). Accessibility: disable-able
tutorial prompts, colorblind-safe hazard indicators, optional aim assist. Target
first-run time 12–18 min.

**Implemented (V2C6/7):** the current single scrolling stage is the compressed
Basement (enemies → boss). Not yet: discrete rooms, scanner tutorial, crate
puzzle, checkpoints, rising-water event, secret/collectible tiers.

# Volume 2, Chapter 8 — Cutscenes & Dialogue

Opening briefing (Commander Ellis), environmental storytelling, **boss intro**
("THIS HOME... IS MINE!"), victory cutscene, and an **HQ debrief** teasing
**Moldius Prime**. Voice direction per character. Cinematics skippable; story
replayable from HQ Archives.

**Implemented:** Ellis briefing flavor at HQ, an in-fight **boss-intro banner**
("THIS HOME... IS MINE!"), and a **victory tease** ("...Moldius Prime..."). Not
yet: full scripted cutscenes, voice, Archives replay.

# Volume 3, Chapter 1 — Level 2: Bathroom (planned)

Persistent humidity/leaks let mold spread through bathroom walls & vents. Teaches
Dash, steam hazards, and strategic HEPA use. Vertical level. New hazards: steam
jets (visibility), slippery tile, electrified puddles, toxic vent bursts.
Enemies: Steam Mite, Mold Leech, Mold Bat Mk II, Vent Spore Swarm. Puzzle: restore
the exhaust fan via 3 breakers. **End boss: Shower Beast** → unlocks the Disinfect
Blaster. Rewards: Bathroom Badge, 750 Cassettes, Level 3 access.

**Status: BUILT.** Level 2 (Bathroom) is playable — selectable from HQ Mission
Command after clearing Mission 1, with the blue-tile stage, steam-vent hazards,
the new enemy roster, and the Shower Beast boss.

# Volume 3, Chapter 2 — Enemy Pack 2: Bathroom Infestation

Level 2 roster; emphasizes positioning + combining movement, HEPA Vacuum, and
Dash (not swarms).

- **ENM-101 Steam Mite** — small, hides in steam clouds, ambushes when visibility
  is low; fast, low HP; weak to HEPA suction after exposure.
- **ENM-102 Mold Leech** — clings to walls/ceilings, drops onto the player, deals
  **damage-over-time** until shaken off by **dashing** or the HEPA Vacuum.
- **ENM-103 Vent Spore Swarm** — floating spore cluster patrolling vents; **splits
  into smaller spores when damaged** unless finished with a **charged vacuum**.
- **ENM-104 Mold Bat Mk II** — faster Basement bat; **chained dive attacks**,
  retreats into ceiling vents between strikes.

Shared AI: Idle → Patrol → Investigate Sound → Detect → Attack → Retreat →
Stunned → Defeated (data-driven). Audio/FX: steam hiss, dripping, ventilation
hum, spore bursts, wet footsteps, enclosed-room echo.

**Status: mostly BUILT.** Steam Mite, Mold Bat Mk II, and Vent Spore Swarm (splits
unless killed with a charged shot) are in Level 2. Mold Leech (wall-cling + DoT /
shake-off) is still planned.

# Volume 3, Chapter 4 — Disinfect Blaster

Second permanent tool (Bathroom reward). **Primary:** continuous short-range
spray. **Charged:** penetrating burst vs hardened mold. **Alt mode:** wide mist
that clears airborne spores (extra energy). Puzzle uses: clean biofilm switches,
sterilize vents, purify valves. **Upgrades Mk I–V:** range, energy cost,
Corrosion Breaker (armored enemies), Purification Pulse (area cleanse).
Balancing: 100 energy; spray 1/s, charged 15, Energy Cell +25.

**Implemented:** the blaster is the game's default weapon (tap + 3-level charge).
Not yet: alt mist mode, puzzle interactions, Mk I–V tree.

# Volume 3, Chapter 5 — Bathroom World Map

Looping, upward-then-down route. Rooms: 01 Hallway (briefing) · 02 Vanity
(mirror puzzle) · 03 Shower (steam tutorial) · 04 Linen Closet (secret) · 05
Ceiling Vent Network (vertical) · 06 Maintenance Crawlspace (breaker puzzle) ·
07 Master Bath Arena. Checkpoints A (Vanity exit) + B (before final door).
Hidden: Gold cassette above the mirror, lore/cosmetic behind the tub. Puzzle:
3 breakers restore the exhaust fan → steam clears → boss route opens.

# Volume 3, Chapter 6 — Bathroom Room-by-Room

Per-room beats: dash reminder, HEPA mirror-clean keypad puzzle (Steam Mites),
timed steam vents + Mold Leeches, optional Linen Closet, vent-shaft dash
platforming (Vent Swarms), breaker room, boss arena. Accessibility: puzzle hints,
reduced steam opacity, colorblind-safe indicators. Target 15–20 min.

**Implemented (V3C5/6):** the compressed single scrolling Bathroom with steam-vent
hazards, the new roster, and the Shower Beast. Not yet: discrete rooms, mirror/
breaker puzzles, checkpoints, secret tiers.

# Volume 3, Chapter 7 — Bathroom Cutscenes & Dialogue

Ellis briefing ("...the infestation has spread upward... Clear the bathroom
before it reaches the attic"), mid-level Dr. Mira (restore the exhaust fan), boss
intro (**"YOU CANNOT WASH AWAY PERFECTION."**), victory (installs the Disinfect
Blaster), HQ debrief ("The attic is next"; every General links to **Moldius
Prime**).

**Implemented:** the boss-intro banner uses the canonical Shower Beast line;
briefing + victory tease reflect this dialogue. Not yet: full scripted scenes.

# Volume 3, Chapter 8 — Bathroom Technical Spec & QA

60 FPS target, dynamic steam scaling, <5s load. Reusable enemy state machines
(configurable detection/cooldown/retreat); deterministic boss phases with small
randomized attack selection. Accessibility: hints, steam opacity, remap,
subtitles, colorblind indicators, camera-shake slider. QA: collectibles
obtainable, no soft-locks after breaker puzzle, checkpoint state, boss
transitions, skippable cutscenes, hidden-area completion. Hooks: moisture spread
to the attic → Level 3.

# Volume 4, Chapter 2 — Enemy Pack 3: Attic Infestation (Level 3)

Emphasize vertical movement + combining all tools; more flyers in coordinated
patterns. **Insulation Creeper** (burrows, ambushes; weak to Blaster after
surfacing). **Spore Hawk** (rides air currents, circles then dives; interrupt
with a charged HEPA pull). **Mold Mite Cluster** (weak singly, dangerous in
groups; area attacks disperse). **Roof Leech** (drips corrosive mold; clear roof
leaks to stop spawns). Enemies react to restored ventilation.

**Status:** documented; ships with Level 3 (Attic), not yet built.

# Volume 4, Chapter 3 — Boss: Spore Queen (Level 3)

Third Mold General; controls airborne spores + wind. Regal fungal creature with
spore-membrane wings, tendrils, amber eyes, a truss-and-mold crown; hovers,
shedding spores. Arena: attic under a broken roof — rotating fans change wind,
rafters are platforms, sections collapse. **P1:** guided spore projectiles +
Mold Mite Clusters. **P2 (70%):** wind manipulation moves platforms, spawns
Spore Hawks. **P3 (30%):** breaks the roof for updrafts + rapid aerial attacks.
**Weak point:** the fungal core under the crown, exposed after a wind channel —
disrupt the wind with the **HEPA Vacuum**, then hit with the **Disinfect
Blaster**. Rewards: **Seal Foam Cannon**, Attic Badge, 1000 cassettes, Level 4.

**Status:** documented; the third boss for the upcoming Level 3 (Attic).

---

## Reference images

- `art_reference/mold_mission_designsheet.png` — the full design sheet.
- `art_reference/player_character_concept.png` — main player character concept.
