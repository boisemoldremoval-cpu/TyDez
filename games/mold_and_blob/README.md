# Mold & Blob 🟢🧴

A **"A Boy and His Blob"-style puzzle-platformer** for TyDez / Boise Mold Removal,
built with Python + pygame.

You are **TyGuy**, and **Blob** is your loyal green companion. Blob can't fight
mold — but on command it *transforms* into the tool you need: a **trampoline** to
reach high ledges, a **bridge** to span pits, or a **ladder** to climb. Use Blob
to get around the level, spray every mold patch clean, then reach the exit door.

Single file, no external art (everything is drawn procedurally), optional
procedural sound.

## Run

```bash
pip install -r requirements.txt      # pygame + numpy
python3 mold_blob.py
```

## Controls

| Key | Action |
|-----|--------|
| ← → / A D | Walk |
| ↑ / W / Space | Jump — and climb **up** while on a ladder |
| ↓ / S | Climb **down** while on a ladder |
| Hold **F** | Spray mold in front of you |
| **1** | Blob → **Trampoline** |
| **2** | Blob → **Bridge** |
| **3** | Blob → **Ladder** |
| **E** / 0 | Call Blob back (follow you) |
| Enter | Start / restart · **M** sound · **Esc** quit |

## How Blob works

Blob transforms **wherever it's standing** (right where TyGuy is), and stays that
shape until you call it back with **E**. Only one form at a time — just like the
one blob in the original game.

- **Trampoline (1)** — a bouncy pad. *Jump on it and fall back down* to get
  launched high enough to reach an upper ledge. (A standing jump is just a normal
  jump — you need to drop onto it for the big bounce.)
- **Bridge (2)** — a solid plank that extends in the way you're facing. Stand at
  the edge of a pit, press 2, and walk across.
- **Ladder (3)** — a climbable ladder. Stand under a ledge, press 3, then hold
  **Up** to climb onto it.

## Beating the level

1. Spray the mold on the starting ground (walk up close, hold **F**).
2. At the pit, press **2** for a bridge and cross.
3. Spray the mold on the far ground.
4. Press **3** for a ladder (or **1** for a trampoline) to reach the high ledge.
5. Spray the last mold up there — the exit door turns **green** once every patch
   is gone.
6. Walk into the open door to win. Fall in the pit and you lose a life (3 total).

## Verify without a display

The game ships with a headless smoke test that actually **plays the level to a
win** and asserts it completes — good for CI or a quick sanity check:

```bash
python3 mold_blob.py --selftest
# -> selftest OK — solved level in 257 frames (4.3s), mold cleared, restart OK
```

## Extending it

Everything is tunable at the top of `mold_blob.py` (speeds, jump/bounce heights,
palette). To add levels, edit `build_level()` — return more platforms
(`"ground"` = solid, `"oneway"` = jump/climb up through it), `Mold(x, y)`
targets, and a `door`. The blob-form placement lives in `Blob.transform()`.

This is a sibling to `../mold_buster/` (a top-down arcade version). Same brand,
different genre.
