#!/usr/bin/env python3
"""Record a labelled showcase of every TyGuy move, zoomed, companions hidden."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/allmoves.mp4"
pygame.init()
screen = pygame.display.set_mode((M.WIDTH, M.HEIGHT))
snd = M.Sound()
g = M.Game(screen, snd)
g.mission = 1
g.state = M.STATE_PLAY
g.reset()
p = g.player
p.maxhp = 99999; p.hp = 99999
font = pygame.font.Font(None, 34)
w = imageio.get_writer(OUT, fps=30, codec="libx264", quality=8, macro_block_size=8)


class K(dict):
    def __missing__(self, k):
        return False


CW, CH = 470, 350
frame = 0


def grab(label):
    global frame
    g.molde_x = -999; g.molde_y = -999; g.mira.x = -999
    g.draw(frame / 60.0)
    arr = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
    cx = int(p.x - g.cam + p.w / 2); cy = 360
    x0 = max(0, min(M.WIDTH - CW, cx - CW // 2))
    y0 = max(0, min(M.HEIGHT - CH, cy - CH // 2))
    crop = np.ascontiguousarray(arr[y0:y0 + CH, x0:x0 + CW])
    big = pygame.transform.scale(
        pygame.surfarray.make_surface(np.transpose(crop, (1, 0, 2))), (900, 670))
    surf = pygame.Surface((900, 672)); surf.blit(big, (0, 0))
    t = font.render(label, True, (255, 240, 120))
    surf.blit(t, (18, 16))
    if frame % 2 == 0:
        w.append_data(np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2)))
    frame += 1


def play(label, n, keyfn, setup=None):
    if setup:
        setup()
    for i in range(n):
        g.update(1 / 60.0, keyfn(i))
        grab(label)


def keys(**kw):
    def f(i):
        k = K()
        for name, val in kw.items():
            code = getattr(pygame, "K_" + name)
            k[code] = val(i) if callable(val) else val
        return k
    return f


# reset Ty to a clear spot on the flat opening ground
def place(x):
    def s():
        p.x = x; p.y = M.GROUND_Y - p.h; p.vx = 0; p.vy = 0
        p.on_ground = True; p.carrying = None
    return s


play("IDLE", 30, keys(), place(240))
play("WALK", 46, keys(RIGHT=True), )
play("RUN", 60, keys(RIGHT=True), )
play("JUMP  (jump / fall / land)", 60,
     keys(RIGHT=True, SPACE=lambda i: i < 16))
play("DASH", 34, keys(RIGHT=True, l=lambda i: i < 3), place(250))
play("SHOOT  (tap)", 40, keys(RIGHT=lambda i: i > 20, j=lambda i: (i % 8) < 2),
     place(250))
play("CHARGE + RELEASE  (hold, grows, fires)", 90,
     keys(j=lambda i: i < 66), place(250))
play("RUN + SHOOT", 70, keys(RIGHT=True, j=lambda i: (i % 6) < 3), place(230))
play("RUN + SHOOT DOWN  (hold Down)", 70,
     keys(RIGHT=True, DOWN=True, j=lambda i: (i % 6) < 3), place(230))
play("CROUCH  (C button)", 34, keys(c=True), place(300))
play("CROUCH-WALK", 50, keys(c=True, RIGHT=True), place(260))
play("CROUCH + SHOOT", 60, keys(c=True, j=lambda i: (i % 6) < 3), place(300))
play("JUMP + SHOOT", 60,
     keys(RIGHT=True, SPACE=lambda i: i < 16, j=lambda i: (i % 5) < 3),
     place(230))

# wall-slide / grapple: seat Ty on the M1 wall at x~980 (spans 980-1006, y260-400)
def wall_setup():
    p.x = 980 - p.w - 1; p.y = 280; p.vx = 140; p.vy = 60; p.on_ground = False
play("WALL-SLIDE / GRAPPLE", 40,
     keys(RIGHT=True, SPACE=lambda i: i in (20, 21)), wall_setup)

# pick up / carry / throw a crate (M1 crate at x=560)
def crate_setup():
    p.x = g.crates[0].x - 6; p.y = M.GROUND_Y - p.h; p.vx = 0; p.vy = 0
    p.on_ground = True; p.interact_prev = False; p.carrying = None
    g.crates[0].x = 560; g.crates[0].y = M.GROUND_Y - g.crates[0].h
    g.crates[0].carried = False; g.crates[0].thrown = False
play("PICK UP ITEM  (E)", 22, keys(e=lambda i: i == 2), crate_setup)
play("CARRY ITEM", 40, keys(RIGHT=True))
play("THROW ITEM  (J)", 46, keys(j=lambda i: i == 2))

# use an interactive object (M1 has prop_generator at 1180)
def use_setup():
    pr = [q for q in g.props if not q.used]
    tx = pr[0].x if pr else 1180
    p.x = tx - 6; p.y = M.GROUND_Y - p.h; p.vx = 0; p.vy = 0
    p.on_ground = True; p.interact_prev = False
play("USE OBJECT  (E)", 40, keys(e=lambda i: i == 2), use_setup)

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB ~%.1fs" % (frame / 2 / 30))
