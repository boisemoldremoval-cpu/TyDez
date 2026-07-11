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

**Status: BUILT.** Level 3 (Attic) is playable — Insulation Creeper, Spore Hawk,
Mold Mite clusters, and Roof Leech are in the stage.

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

**Status: BUILT.** The Spore Queen is Mission 3's boss — hovering, 3 phases,
mite/hawk summons, and an exposed-core weak point after her wind channel.

# Volume 4, Chapter 4 — Seal Foam Cannon

Third permanent tool (Spore Queen / Attic reward). **Primary:** place expandable
foam on valid surfaces. **Charged:** reinforced foam that lasts longer and
supports heavy objects. **Precision:** narrow bead to seal cracks / trigger
objectives. **Combat:** trap charging enemies, interrupt spore vents, block
projectile lanes, expose boss weak points by redirecting airflow. **Puzzle:**
bridge gaps, seal roof leaks, redirect water, stabilize platforms, isolate
chambers. **Upgrades Mk I–V:** cure time, size, heat-resistant, smart auto-seal.
Balance: 8 energy/shot, 20 charged; max 3 active structures (grid-snapped,
deterministic, dissolve on timer/replace).

**Status:** documented; unlocks after the Spore Queen. Foam-platform placement is
a natural fit for the existing platform engine when Level 3 is built.

# Volume 4, Chapter 5 — Attic World Map

Looping multi-level, vertical-exploration attic. Rooms: 01 Access Hatch · 02
Storage Loft · 03 Insulation Field · 04 HVAC Junction · 05 Broken Skylight · 06
Roof Vent Network · 07 Queen's Nest. Checkpoints A (after Storage Loft) + B
(before the Nest). Secrets: rafter-tunnel Gold cassette, chimney cosmetic, seal
all roof leaks for a lore entry. Puzzle: seal roof leaks (Foam Cannon), restore
ventilation, redirect air with fans, clear spores (HEPA) before opening the Nest.

# Volume 4, Chapter 6 — Attic Room-by-Room

Access Hatch (dust visibility + dash across joists) → Storage Loft (foam
platforms to shelving) → Insulation Field (Creepers, slow footing) → HVAC
Junction (rotate duct valves; ventilation weakens flyers) → Broken Skylight (wind
alters jumps; Roof Leeches) → Roof Vent Network (seal leaks + Spore Hawks; Gold
cassette) → Queen's Nest (checkpoint + cinematic). Accessibility: nav markers,
reduced wind.

**Implemented (V4C5/6):** the compressed single scrolling Attic with updraft air
currents and the full roster. Not yet: discrete rooms, foam/valve/leak puzzles,
checkpoints.

# Volume 4, Chapter 7 — Attic Cutscenes & Dialogue

Ellis briefing (spores could reach neighboring homes), Dr. Mira (restore
ventilation), boss intro (**"THE SKY BELONGS TO THE HIVE."**), victory (installs
the Seal Foam Cannon), HQ debrief teasing the **Crawlspace** as the next mission
and the source of remaining contamination.

**Implemented:** boss-intro banner uses the canonical Spore Queen line.

# Volume 4, Chapter 8 — Attic Technical Spec & QA

60 FPS with dynamic wind/particles/lighting (auto-scaled). Flyers pressure
movement without unavoidable damage; Spore Queen phases escalate with clean
telegraphs. Common wind-aware deterministic state machine. Accessibility: reduced
wind/shake, subtitles, hints, remap, colorblind indicators. QA: seal all leaks,
ventilation completes, collectibles reachable, boss transitions, post-boss
shortcuts, no platforming soft-locks. Target 18–24 min. Hook: samples point
**beneath the foundation → the Crawlspace (Level 4)**.

# Volume 5, Chapter 2 — Enemy Pack: Crawlspace (Level 4)

Confined-space tension; combine every unlocked tool. Enemies use darkness, mud,
and structure.

- **Mud Stalker (ENM-301)** — ambush predator under mud; detects footstep
  vibration, bursts up; vulnerable right after surfacing.
- **Mold Centipede (ENM-302)** — segmented joist/wall crawler; **splits into
  segments if defeated incorrectly**.
- **Pipe Parasite (ENM-303)** — clings to plumbing, sprays contaminated water;
  **spreads contamination if ignored**.
- **Toxic Gas Pod (ENM-304)** — stationary; releases poison spores when
  disturbed; **best countered with the Seal Foam Cannon**.
- **Burrowing Spore Worm (ENM-305)** — fast tunneler; **telegraphs with shaking
  dirt** then erupts.

Shared AI: Idle → Patrol → Detect Vibration → Ambush → Attack → Recover →
Retreat → Defeated. Environment: standing water slows, restored ventilation
weakens gas, better lighting reduces ambushes.

**Status:** documented; the first piece of **Level 4 (Crawlspace)**. Will be
built once the Crawlspace boss + world map arrive (the level 4 hook from V4C8).

# Volume 5, Chapter 3 — Boss: Crawlor

Fourth Mold General, ruler of the crawlspace. A colossal segmented mold worm
that tunnels beneath the foundation, forcing reaction to shifting terrain.
Armored fungal worm with stone-like plates, glowing green fissures, root
tendrils, and jaws of broken foundation blocks. Arena: circular crawlspace under
the home — piers, standing water, damaged vapor barrier, mud pits, support
beams, multiple elevations. **P1:** burrows between chambers, erupts beneath the
player. **P2 (65%):** collapses beams, floods sections, **summons Pipe
Parasites**. **P3 (25%):** coils the arena, exposing weak points while launching
toxic gas bursts. **Weak point:** each body segment briefly exposes a glowing
fungal core after a charge — seal tunnels with the **Foam Cannon**, hit cores
with the **Blaster**. Rewards: **Air Scrubber Drone**, Crawlspace Badge, 1500
cassettes, Level 5 unlocked. Target 6–8 min.

**Status:** documented; the 4th boss. Level 4 (Crawlspace) will be built once its
world map / room layout arrives — I now have its enemy pack (V5C2) and boss.

# Volume 5, Chapter 4 — Air Scrubber Drone

Fourth permanent tool (Crawlor / Crawlspace reward) — an autonomous companion.
**Abilities:** auto-filters nearby airborne spores, highlights hidden
contamination, temporarily weakens flying enemies, powers purification beacons.
**Commands (radial):** Deploy, Recall, Hold, Follow, Focus Clean, Beacon Mode.
**Combat:** disrupts spore projectiles, briefly stuns airborne enemies, creates
safe zones. **Environment:** purifies sealed rooms, restores breathable air,
activates air-quality sensors, opens clean-air-threshold doors. **Upgrades Mk
I–V:** radius, battery, dual filter, adaptive-AI targeting. Battery recharges
docked; Emergency Recall before depletion. Compact quad-rotor with HEPA
canisters.

**Status:** documented; unlocks after Crawlor. A companion-drone entity fits the
engine as a follower that auto-clears nearby hostile projectiles/spores.

# Volume 5, Chapters 6–8 — Crawlspace rooms / cutscenes / QA

**Rooms:** Access Hatch → Vapor Barrier Corridor (foam repairs) → Flooded Utility
Bay (water + Pipe Parasites, checkpoint) → Foundation Tunnel (Mud Stalker
ambushes) → Pipe Junction (valve puzzle) → Fungal Hive (destroy nodes) → Crawlor
Arena. **Dialogue:** Ellis briefing (structural instability), Dr. Mira (destroy
hive nodes), boss intro (Crawlor erupts), victory (deploy Air Scrubber Drone).
**QA:** 60 FPS with mud/water/drone FX; telegraphed Crawlor emergences; modular
behavior trees; reduced-darkness mode; 20–25 min target.

**Built:** the compressed Crawlspace stage + Crawlor. Planned: discrete rooms,
foam/valve puzzles, checkpoints, hive-node objective.

# Volume 6 — Research Facility (Level 5, the finale)

**Ch1 Overview:** contamination traced to an abandoned research facility where
experimental fungal samples escaped; Moldius Prime originated from a cleanup
experiment that became a hive mind. Zones: Reception/Security, Research Labs,
Clean Rooms, Specimen Vault, Mechanical Plant, Server Core, Containment Reactor.
Hazards: containment doors, laser grids, contaminated vents, chemical spills,
sterilization cycles.
**Ch2 Enemies:** Biofilm Sentinel (armor — Blaster then Vacuum), Vent Stalker
(ceiling quadruped, retreats from the Drone), Culture Swarm (merges/splits —
Drone + Vacuum), Reactor Spore (buffs nearby enemies), Security Mycelium (locks
routes/alarms).
**Ch3 Prototype Purification Core:** final tool — pulses that empower all tools,
break elite defenses, expose weak points; Stage I–V; charges via objectives +
Purification Cells.
**Ch4/5 Map/Rooms:** 7 zones, checkpoints A/B/C, Prototype Cells + research logs,
power/quarantine/vent/reactor puzzles.
**Ch6 Moldius Prime:** the hive mind that absorbed every prior boss. 4 phases
(commands elites + reactor hazards → contamination beams + tendrils → reactor
destabilizes, use the Core → exposed-core battle). Purification-Node weak points
after major attacks; 8–10 min.
**Ch7 Ending:** Core purifies the facility; epilogues (Ty = Master Remediator);
HQ celebration; credits over restored communities; post-credits faint signal in
an unexplored region.
**Ch8 QA:** stable 60 FPS in the finale; each phase adds one mechanic; 30–40 min.

**Built:** Mission 5 (Research Facility) with the elite roster, the **Moldius
Prime** 4-phase final boss, and a campaign-complete ending. Planned: the 7
distinct zones, security/laser/reactor puzzles, the Purification Core as a
usable ability, and full scripted cinematics.

# Volume 7 — Meta Systems (post-campaign design, documented)

- **Ch1 Skill Tree:** XP-driven permanent upgrades across Movement, Scanner, each
  tool, and Restoration Mastery; each tool has a signature end-tier upgrade.
- **Ch2 Upgrade Economy:** currencies — Sample Cassettes (primary), Research
  Tokens, Restoration Badges, Purification Cells; rewards for time/coverage/
  collectibles/optional objectives, not grinding.
- **Ch3 HUD/UI:** health, energy, active tool, cassettes, objective, minimap,
  contamination meter, boss bar; a **tool wheel** (radial switch across all
  tools + scanner); consistent menus.
- **Ch4 Save/Progression:** auto-checkpoints + HQ manual slots + cloud; tracks
  missions, coverage, collectibles, ratings, unlockables; mission replay.
- **Ch5 Audio/Music:** restoration-themed; per-level identities that intensify
  with contamination; phase-evolving boss music; unique tool sound signatures;
  telegraph cues.
- **Ch6 Achievements:** campaign, restoration quality (100%/perfect/no-damage),
  tool mastery, challenges (speedrun/no-hit/limited-upgrade); cosmetic rewards.
- **Ch7 Difficulty:** Story / Standard / Expert / **Master Remediator** (post-
  campaign remix) + optional adaptive assist; same story/levels.
- **Ch8 Accessibility:** scalable UI, high-contrast, colorblind-safe, reduced
  flashing; remappable + toggle/hold + aim assist; separate audio sliders +
  subtitles; objective reminders, hints, nav markers.
- **Ch9 New Game+ / Post-Game:** carry tools/cosmetics/lore/most skills; elite
  variants + remixed encounters; Boss Rush, Time Trials, Daily Contracts,
  Challenge Missions, Free Exploration, Gallery; leaderboards.

**Status:** documented as the design target. The prototype already implements a
slice — HQ upgrades (Armor/Battery/Speed) with a Sample-Cassette economy, the
core HUD (health/energy/charge/score/cassettes/boss bar), mission select, and
per-mission unlock progression.

# Volume 8, Chapter 1 — Project Architecture

Modular architecture separating gameplay, UI, audio, AI, assets, save. **Core
modules:** Gameplay, Player Controller, Enemy AI, Tool System, Mission Manager,
Save System, UI Framework, Audio Manager, Visual Effects, Analytics, Content
Database. **Levels** own scene/lighting/encounters/collectibles/events/hazards
but share global systems. **Data-driven** config files for weapons/enemies/
upgrades/achievements/collectibles (balance without touching code). **Event
flow:** Mission Start → Exploration → Puzzle Events → Boss → Completion →
Rewards → HQ Upgrade Loop. Subsystems talk via event messaging; stream large
environments; pool effects/enemies; documented interfaces + automated tests.

**Status:** documented as the target production architecture. The single-file
prototype already mirrors much of it informally — the `Enemy` class is
kind/data-driven, `build_level(mission)` holds per-level content, `Game` is the
mission manager, and bosses/tools are modular classes. A full refactor into
separate modules + data files is the natural step toward a production build.

---

## Reference images

- `art_reference/mold_mission_designsheet.png` — the full design sheet.
- `art_reference/player_character_concept.png` — main player character concept.
