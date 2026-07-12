# HANDOFF — Mold Mission (read me first)

This is the pick-up-where-we-left-off guide. Everything we built is safe on
GitHub, branch **`claude/install-repository-xlm50f`** (repo
`boisemoldremoval-cpu/TyDez`). A new session on that branch has all of it.

---

## ▶ HOW TO RESUME IN A FRESH SESSION
1. Open Claude Code where you normally chat with me (web app / phone / desktop).
2. Start a **New session** (the “+” / “New session” / “New task” button).
3. Pick the repo **`boisemoldremoval-cpu/TyDez`**.
4. Pick the **existing** branch **`claude/install-repository-xlm50f`** (do NOT
   create a new branch — choose this one so all the work loads).
5. Send this message:
   > Read `HANDOFF.md` and `games/mold_mission/HANDOFF.md`, then finish cutting
   > the art in `games/mold_mission/art_reference/pending/`.

That’s it. The fresh session has a working image reader again and continues
exactly where we stopped. **Nothing is lost** — git is the memory.

---

## WHERE THINGS ARE
- **The game:** `games/mold_mission/mold_mission.py` (single file, pygame).
- **Sprites the game uses:** `games/mold_mission/assets/`
- **Source art already cut:** `games/mold_mission/art_reference/`
- **Art still to cut:** `games/mold_mission/art_reference/pending/` (14 sheets)
- **Full technical detail:** `games/mold_mission/HANDOFF.md`

## RUN / CHECK THE GAME
```bash
cd games/mold_mission
pip install -r requirements.txt
python3 mold_mission.py            # play
python3 mold_mission.py --demo     # watch a full auto-playthrough
python3 mold_mission.py --selftest # must print: selftest OK: all 5 missions win
```

## WHAT'S DONE
- **Ty** (player) — fully animated: idle/run/jump/fall/dash/crouch/aim/shoot/victory.
- **MOLD-E** drone — follows Ty, scans, alerts near danger.
- **Mold Turret** — allied auto-defense with a firing pose.
- **12 mold enemies** — animated (idle/run/hurt): sporebot, moldcrawler,
  toxicsprayer, steammite, ventswarm, moldmite, creeper, mudstalker, gaspod,
  cultureswarm, reactorspore, mycelium.
- **2 bosses** — Spore Queen (`boss3`) and the final SporeMother (`boss5`, with
  an enrage pose).
- **HQ** — Commander Ellis + Dr. Mira, HQ Engineer, Field Medic.
- Systems: drop-in art with auto-animating state variants, a split-file loader
  for oversized art, and `--demo` / `--selftest`.

## WHAT'S LEFT (needs real art — recolors can't fake these shapes)
- Enemies: `moldbat`, `sporehawk`, `roofleech`, `centipede`, `pipeparasite`,
  `sporeworm`, `sentinel`, `ventstalker`.
- Bosses: `boss` (Sludge King), `boss2` (Shower Beast), `boss4` (Crawlor).
- Backgrounds/tiles per mission.
- The sheets in `art_reference/pending/` — cut each into its sprite keys.

## HOW NEW ART BECOMES ANIMATED SPRITES (for the next session)
Drop transparent PNGs in `assets/` named by key; they override vector art and
animate automatically:
- Enemy `<kind>`: `<kind>` + `<kind>_run` + `<kind>_hurt` + `<kind>_attack`.
- Boss `<key>`: `<key>` + `<key>_hurt` (shown while the weak point is exposed).
- If a file is too big: `split_asset("assets/x.png")` splits it across folders;
  the game reassembles it (see `games/mold_mission/HANDOFF.md`).

After any change, `--selftest` must still print **all 5 missions win**.
