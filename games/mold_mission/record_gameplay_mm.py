#!/usr/bin/env python3
"""Normal full-view gameplay (HUD + TyGuy + level) of a mission, so the Micro
Mold swarms are seen animating / moving / attacking / dying during real play.
Driven by the same auto-player the selftest uses."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/micromold_gameplay.mp4"
pygame.init()
screen = pygame.display.set_mode((M.WIDTH, M.HEIGHT))
snd = M.Sound()
g = M.Game(screen, snd)
g.mission = 1
g.unlocked = 1
g.reset()
g.state = M.STATE_PLAY
w = imageio.get_writer(OUT, fps=30, codec="libx264", quality=8, macro_block_size=8)

st = {}
frame = 0
# play until the boss is reached (keeps the clip to the level run where the
# Micro Mold swarms live), capped so it never runs away.
for i in range(2600):
    keys = M._bot_keys(g, st, i)
    g.update(1 / M.FPS, keys)
    g.draw(i / M.FPS)
    if i % 2 == 0:                     # 60fps sim -> 30fps capture
        arr = pygame.surfarray.array3d(screen)
        w.append_data(np.transpose(arr, (1, 0, 2)))
        frame += 1
    if g.boss is not None:             # stop once the level is cleared to the boss
        break

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB", frame, "frames")
