# TyDez Mold Buster 🍄🚿

A small arcade game built with **Python + pygame**, themed for
Boise Mold Removal. You play **TyGuy**, the mold-removal pro: green mold keeps
blooming on the wall — move around and blast it with your sprayer before any
patch grows big enough to spread. Let three patches spread and the job's lost.

Single file, no external assets (all graphics are drawn procedurally), optional
procedural sound.

## Run

```bash
pip install -r requirements.txt      # pygame + numpy
python3 mold_buster.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move TyGuy |
| Space (hold) | Spray in the direction you're facing |
| Enter | Start / restart |
| M | Toggle sound |
| Esc | Quit |

## How it plays

- Mold patches spawn at random and **grow over time**. Spawns get faster the
  longer you survive.
- Holding **Space** emits a spray cloud just in front of TyGuy; overlap a patch
  to shrink it. Clear a patch for **+10 points**.
- If a patch reaches full size it **spreads** — it spawns two new patches and
  costs you a strike (the red dots, top-right).
- **3 strikes = game over.** Score and survival time are shown on the end
  screen.

## Verify without a display

The game includes a headless smoke test that cycles through every state
(menu → play → game over → restart) and exits non-zero on any crash:

```bash
python3 mold_buster.py --selftest
# -> selftest OK — states cycled, ...
```

## Structure

The code follows the game-loop / state-machine pattern from
`../../claude-code-game-development/docs/02-core-game-concepts/`:

- `Sound` — procedural tones via `pygame.sndarray`, degrades gracefully with no
  audio device.
- `Mold` / `Player` — entities with `update(dt)` + `draw(surf)`.
- `Game` — owns state (`menu` / `play` / `over`), spawning, collision, scoring,
  and HUD.
- `run()` — fixed-timestep-ish main loop (delta clamped after stalls).

Tweak the constants at the top of `mold_buster.py` (speeds, sizes, spawn rate,
palette) to rebalance the game.
