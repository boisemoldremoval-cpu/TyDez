#!/usr/bin/env python3
"""Zoomed, labelled showcase of the Micro Mold and its full video move-set.
Camera is locked on the creature and Ty is kept out of the tight frame."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/micromold_showcase.mp4"
pygame.init()
screen = pygame.display.set_mode((M.WIDTH, M.HEIGHT))
snd = M.Sound()
g = M.Game(screen, snd)
g.mission = 1
g.reset()
g.state = M.STATE_PLAY
p = g.player
p.maxhp = 99999; p.hp = 99999
font = pygame.font.Font(None, 34)
w = imageio.get_writer(OUT, fps=22, codec="libx264", quality=8, macro_block_size=8)

CW, CH = 150, 132
frame = 0

star = next(e for e in g.enemies if e.kind == "micromold")
star.x = 900.0; star.y = M.GROUND_Y - star.h; star.home_y = star.y
for e in g.enemies:                       # clear everything else out of frame
    if e is not star:
        e.x = -4000


def pose_of(e):
    if e.death_t > 0 or g.death_fx:
        return "DEATH SPLAT"
    if e.stun_t > 0:
        return "STUNNED"
    if e.hit > 0:
        return "HURT"
    if e.mm_air and e.vy < -25:
        return "JUMP"
    if e.mm_air and e.vy > 25:
        return "FALL"
    if e.mm_air:
        return "HOP"
    if e.land_t > 0:
        return "LAND"
    if e.turn_t > 0:
        return "TURN AROUND"
    if e.atk_anim > 0:
        return "SPORE BURST"
    if abs(e.vx) > 150:
        return "RUN (rushing in)"
    if abs(e.vx) > 8:
        return "WALK"
    return "IDLE"


def grab(label=None):
    global frame
    g.cam = max(0.0, min(M.LEVEL_W - M.WIDTH, star.x + star.w / 2 - M.WIDTH / 2))
    g.molde_x = -999; g.molde_y = -999; g.mira.x = -999
    g._draw_scene(frame / 60.0)             # world only — no HUD banner clutter
    arr = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
    cx = int(star.x - g.cam + star.w / 2)
    cy = int(star.y + star.h * 0.35)        # frame the body, not the feet
    x0 = max(0, min(M.WIDTH - CW, cx - CW // 2))
    y0 = max(0, min(M.HEIGHT - CH, cy - CH // 2))
    crop = np.ascontiguousarray(arr[y0:y0 + CH, x0:x0 + CW])
    big = pygame.transform.scale(
        pygame.surfarray.make_surface(np.transpose(crop, (1, 0, 2))), (896, 788))
    surf = pygame.Surface((896, 790)); surf.blit(big, (0, 0))
    t = font.render("MICRO MOLD  —  " + (label or pose_of(star)), True, (255, 240, 120))
    surf.blit(t, (18, 16))
    w.append_data(np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2)))
    frame += 1


class K(dict):
    def __missing__(self, k):
        return False


def run(n, ty_at=None, keys=None, label=None):
    if ty_at is not None:
        p.x = star.x + ty_at; p.y = M.GROUND_Y - p.h; p.on_ground = True
    for j in range(n):
        if ty_at is not None:                 # hold Ty put so he steers the mold
            p.x = star.x + ty_at; p.vx = 0
        g.update(1 / 60.0, keys or K())
        if j % 2 == 0:
            grab(label)


# 0) Ty stands FAR to the right -> the mold RUNS in (speed lines), then walks
run(150, ty_at=760)
# 1) Ty closer on the RIGHT -> the mold WALKS toward him, HOPS along the way
run(150, ty_at=300)
# 2) Ty jumps to the mold's LEFT -> it swings a TURN-AROUND, then walks left
run(150, ty_at=-520)
# 3) Ty steps into mid-range -> the mold coughs a SPORE BURST
run(150, ty_at=200)
# 4) finish it: HURT recoil, then the DEATH SPLAT plays where it drops
for _ in range(8):
    star.hit = 0.12
    grab("HURT")
g._maybe_drop(star)            # spawn the death splat FX at its position
g.enemies = []                 # remove the live sprite so only the splat shows
for _ in range(30):
    for fx in g.death_fx:
        fx[4] += 1 / 60.0
    g.death_fx = [f for f in g.death_fx if f[4] < 0.42]
    g.parts.update(1 / 60.0)
    grab("DEATH SPLAT")

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB", frame, "frames")
