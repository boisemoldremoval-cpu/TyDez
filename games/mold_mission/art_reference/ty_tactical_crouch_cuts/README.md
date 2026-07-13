# Ty crouch cuts — OFF-MODEL, preserved (not shipped)

These two sprites were cut cleanly (transparent background, largest-component
protected, de-spilled, autocropped) from the pending movement sheet
`../pending/upload_new_8ea6eccc.png` ("TY — CROUCHING ANIMATIONS"), which is
OPEN REQUEST #1 in `START_HERE.md` ("Allow these movements").

- `player_crouch.png` — pose 1, Crouch Idle (gun ready)
- `player_crouch_shoot.png` — pose 5, Crouch Fire (muzzle flash)

## Why they are here and not in `assets/`

The sheet is **off-model**. Ty's official design — the art bible pages
`CHR_001_Ty*` / `PLR_001_Ty` and *every* shipped player sprite
(`assets/player*.png`) — is the bright **blue-and-white armored kid** with a
green-cross chest emblem. This sheet is a different, **darker tactical**
character (charcoal armor, lime accents, older face, no green cross).

Dropping these into `assets/` would make the player visibly change identity the
moment he crouches — the opposite of OPEN REQUEST #2 ("make sure everything
looks professional"). So the cuts are preserved here instead.

## How to ship them (if you DO want the tactical look for crouch)

    cp ty_tactical_crouch_cuts/player_crouch.png       ../assets/player_crouch.png
    cp ty_tactical_crouch_cuts/player_crouch_shoot.png ../assets/player_crouch_shoot.png
    python3 mold_mission.py --selftest

The game is already wired for both keys: `player_crouch` shows while ducking,
and `player_crouch_shoot` (already in `ASSET_NAMES`) shows when firing while
crouched instead of popping Ty up to the standing shoot pose. With no
`player_crouch_shoot.png` present, the crouch simply keeps its idle pose — the
code change is inert and safe.

Regenerate the cuts anytime with `python3 cut_crouch.py`.
