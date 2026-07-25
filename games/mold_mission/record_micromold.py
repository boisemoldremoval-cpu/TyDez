#!/usr/bin/env python3
"""Zoomed in-game clip of the Micro Mold swarm using its video animations."""
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
font = pygame.font.Font(None, 32)
w = imageio.get_writer(OUT, fps=24, codec="libx264", quality=8, macro_block_size=8)

CW, CH = 560, 360
frame = 0


def grab(label, target_x):
    global frame
    g.molde_x = -999; g.molde_y = -999; g.mira.x = -999
    g.draw(frame / 60.0)
    arr = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
    cx = int(target_x - g.cam); cy = 380
    x0 = max(0, min(M.WIDTH - CW, cx - CW // 2))
    y0 = max(0, min(M.HEIGHT - CH, cy - CH // 2))
    crop = np.ascontiguousarray(arr[y0:y0 + CH, x0:x0 + CW])
    big = pygame.transform.scale(
        pygame.surfarray.make_surface(np.transpose(crop, (1, 0, 2))), (896, 576))
    surf = pygame.Surface((896, 576)); surf.blit(big, (0, 0))
    t = font.render(label, True, (255, 240, 120))
    surf.blit(t, (16, 14))
    w.append_data(np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2)))
    frame += 1


class K(dict):
    def __missing__(self, k):
        return False


# a micromold swarm sits around x=630 in M1 — stage Ty just to its right so the
# swarm walks toward him (WALK cycle), then he shoots (HURT), and it spore-bursts
mm = [e for e in g.enemies if e.kind == "micromold"]
tx = mm[0].x + 40
p.x = tx + 120; p.y = M.GROUND_Y - p.h; p.on_ground = True; p.facing = -1


def step(keys, n):
    for j in range(n):
        g.update(1 / 60.0, keys)
        alive = [e for e in g.enemies if e.kind == "micromold"]
        focus = alive[0].x if alive else tx
        if j % 2 == 0:
            grab("MICRO MOLD  —  swarm (video animations)", focus)


# 1) let the swarm crawl toward Ty — WALK cycle
step(K(), 90)
# 2) Ty opens fire — HURT recoils + kills ripple through the swarm
step(K(LEFT=lambda i: False, j=lambda i: (i % 5) < 2), 150)

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB", frame, "frames")
