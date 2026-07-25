#!/usr/bin/env python3
"""Zoomed showcase of the new SPORE MOLD elite and its full move-set."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/sporemold_showcase.mp4"
pygame.init()
screen = pygame.display.set_mode((M.WIDTH, M.HEIGHT))
snd = M.Sound()
g = M.Game(screen, snd)
g.mission = 3
g.unlocked = 3
g.reset()
g.state = M.STATE_PLAY
p = g.player
p.maxhp = 99999; p.hp = 99999
font = pygame.font.Font(None, 34)
w = imageio.get_writer(OUT, fps=24, codec="libx264", quality=8, macro_block_size=8)


class K(dict):
    def __missing__(self, k):
        return False


CW, CH = 520, 380
frame = 0


def focus_on(e):
    """Camera + crop centred on enemy e; label the creature's current pose."""
    global frame
    g.molde_x = -999; g.molde_y = -999; g.mira.x = -999
    g.draw(frame / 60.0)
    arr = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
    cx = int(e.x - g.cam + e.w / 2); cy = int(e.y)
    x0 = max(0, min(M.WIDTH - CW, cx - CW // 2))
    y0 = max(0, min(M.HEIGHT - CH, cy - CH // 2))
    crop = np.ascontiguousarray(arr[y0:y0 + CH, x0:x0 + CW])
    big = pygame.transform.scale(
        pygame.surfarray.make_surface(np.transpose(crop, (1, 0, 2))), (900, 658))
    surf = pygame.Surface((900, 660)); surf.blit(big, (0, 0))
    # read the pose the enemy is showing right now
    pose = "IDLE"
    if e.stun_t > 0:
        pose = "STUNNED"
    elif e.ceiling:
        pose = "CEILING HANG"
    elif e.dropping:
        pose = "DROP"
    elif e.lunging > 0:
        pose = "DASH ATTACK"
    elif e.windup > 0:
        pose = "CHARGE (wind-up)"
    elif e.splitting > 0:
        pose = "SPLIT / SPAWN"
    elif e.atk_anim > 0:
        pose = "BIG SPORE SHOT"
    elif getattr(e, "enraged", False):
        pose = "ENRAGED"
    elif abs(e.vx) > 8:
        pose = "RUN"
    t = font.render("SPORE MOLD  —  " + pose, True, (255, 240, 120))
    surf.blit(t, (18, 16))
    w.append_data(np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2)))
    frame += 1


# grab the ground Spore Mold in M3 (placed at x=600) and stage Ty in front of it
mold = next(e for e in g.enemies if e.kind == "sporemold" and not e.ceiling)
ceil_mold = next(e for e in g.enemies if e.kind == "sporemold" and e.ceiling)


def step(keys, n, target):
    for j in range(n):
        g.update(1 / 60.0, keys)
        if j % 2 == 0:            # sample every 2nd sim step -> 30fps-ish source
            focus_on(target)


# 1) approach from range so it lobs a BIG SPORE SHOT, then RUN/stalk
p.x = 980; p.y = M.GROUND_Y - p.h; p.on_ground = True
step(K(), 120, mold)
# 2) get close so it DASH ATTACKS (charge -> dash)
p.x = mold.x + 150; p.y = M.GROUND_Y - p.h; p.on_ground = True
step(K(), 150, mold)
# 3) shoot it to wound -> ENRAGE + corrode trail, and finally SPLIT on death
for _ in range(9):
    mold.hurt(1, g.parts)
step(K(RIGHT=True), 120, mold)
# 4) the ceiling hanger: stand Ty underneath so it DROPS + splats on impact
p.x = ceil_mold.x + 6; p.y = M.GROUND_Y - p.h; p.on_ground = True
step(K(), 110, ceil_mold)

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB", frame, "frames")
