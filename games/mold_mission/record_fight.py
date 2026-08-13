#!/usr/bin/env python3
"""Zoomed gameplay clip of TyGuy fighting a Micro Mold swarm: molds hop/rush in
and spore-attack, TyGuy blasts them (hurt -> death splat -> fade). Full HUD kept."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/tyguy_vs_micromold.mp4"
pygame.init()
screen = pygame.display.set_mode((M.WIDTH, M.HEIGHT))
snd = M.Sound()
g = M.Game(screen, snd)
g.mission = 1
g.unlocked = 1
g.reset()
g.state = M.STATE_PLAY
p = g.player
p.maxhp = 99999; p.hp = 99999          # keep Ty up so the fight plays out
w = imageio.get_writer(OUT, fps=30, codec="libx264", quality=8, macro_block_size=8)

# clear the level to a controlled arena: just Ty + waves of Micro Molds on the
# opening flat ground, so the clip is purely the Ty-vs-Micro-Mold fight.
for e in g.enemies:
    e.x = -5000
g.boss = None
CW, CH = 520, 300
frame = 0


def spawn_wave(cx, n):
    for k in range(n):
        e = M.Enemy("micromold", cx + k * 46, M.GROUND_Y - 26)
        e.home_y = e.y
        e.sprite_aspect = (g.assets.imgs[g.assets.anims["micromold"][0]].get_width()
                           / g.assets.imgs[g.assets.anims["micromold"][0]].get_height())
        g.enemies.append(e)


def grab():
    global frame
    g.cam = max(0.0, min(M.LEVEL_W - M.WIDTH, p.x + p.w / 2 - M.WIDTH / 2))
    g.molde_x = -999; g.molde_y = -999; g.mira.x = -999
    g.draw(frame / 60.0)                # full scene incl. HUD
    arr = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
    cx = int(p.x - g.cam + p.w / 2); cy = M.GROUND_Y - 78
    x0 = max(0, min(M.WIDTH - CW, cx - CW // 2))
    y0 = max(0, min(M.HEIGHT - CH, cy - CH // 2))
    crop = np.ascontiguousarray(arr[y0:y0 + CH, x0:x0 + CW])
    big = pygame.transform.scale(
        pygame.surfarray.make_surface(np.transpose(crop, (1, 0, 2))), (900, 519))
    out = pygame.Surface((900, 520)); out.blit(big, (0, 0))
    w.append_data(np.transpose(pygame.surfarray.array3d(out), (1, 0, 2)))
    frame += 1


class K(dict):
    def __missing__(self, k):
        return False


# stage Ty on the flat opening ground, facing right
p.x = 360.0; p.y = M.GROUND_Y - p.h; p.on_ground = True; p.facing = 1
spawn_wave(760, 4)


def run(keys, n):
    for j in range(n):
        g.update(1 / 60.0, keys)
        if j % 2 == 0:
            grab()
        # keep the fight fed: respawn a wave when the field is nearly clear
        if len([e for e in g.enemies if e.kind == "micromold" and not e.dead
                and e.x > 0]) <= 1 and j % 2 == 0:
            spawn_wave(p.x + 460, 4)


# Ty holds his ground and fires right as the molds hop/rush in and get shredded;
# a couple of short steps toward them keeps the swarm on-screen
run(K(RIGHT=lambda i: (i % 90) < 12, j=lambda i: (i % 4) < 2), 360)

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB", frame, "frames")
