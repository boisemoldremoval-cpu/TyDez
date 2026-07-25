#!/usr/bin/env python3
"""Show the Micro Mold MOVING across a clean stage — walking, running in,
hopping, and turning around — driven by its real Enemy AI (a moving target
steers it). Fixed camera so you watch it travel."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import mold_mission as M
import imageio

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/micromold_moving.mp4"
W, H = 860, 460
GROUND = 372
pygame.init()
screen = pygame.display.set_mode((W, H))
snd = M.Sound()
g = M.Game(screen, snd)            # builds AssetPack
A = g.assets
small = pygame.font.Font(None, 30)
big = pygame.font.Font(None, 40)
w = imageio.get_writer(OUT, fps=24, codec="libx264", quality=9, macro_block_size=8)

# scale the character up for the showcase (draw height), overriding CHAR_H usage
DRAW_H = 150


class FakeP:                       # minimal 'player' the enemy AI steers toward
    def __init__(self):
        self.x = 700.0; self.y = GROUND - 60.0; self.w = 30; self.h = 60
        self.dead = False


p = FakeP()
mob = M.Enemy("micromold", 120.0, 0.0)
mob.h = 40                          # a touch bigger box so it reads at this scale
mob.home_y = GROUND - mob.h
mob.y = mob.home_y
mob.sprite_aspect = 1.0


def stage():
    surf = pygame.Surface((W, H))
    for y in range(H):
        f = y / H
        surf.fill((int(30 + 12 * f), int(36 + 14 * f), int(44 + 12 * f)), (0, y, W, 1))
    pygame.draw.rect(surf, (46, 52, 46), (0, GROUND, W, H - GROUND))
    pygame.draw.line(surf, (90, 120, 80), (0, GROUND), (W, GROUND), 3)
    for gx in range(0, W, 60):      # ground texture ticks so motion is obvious
        pygame.draw.line(surf, (38, 44, 40), (gx, GROUND + 8), (gx, H), 2)
    return surf


ST = stage()


def label_for():
    if mob.mm_air and mob.vy < -25:
        return "JUMP"
    if mob.mm_air and mob.vy > 25:
        return "FALL"
    if mob.mm_air:
        return "HOP"
    if mob.land_t > 0:
        return "LAND"
    if mob.turn_t > 0:
        return "TURN AROUND"
    if abs(mob.vx) > 150:
        return "RUN"
    if abs(mob.vx) > 8:
        return "WALK"
    return "IDLE"


def draw_frame():
    surf = ST.copy()
    # shadow scales with hop height
    lift = max(0.0, (mob.home_y - mob.y))
    sw = max(30, 96 - lift * 0.6)
    sh = pygame.Surface((int(sw), 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, int(sw), 18))
    surf.blit(sh, (int(mob.x + mob.w / 2 - sw / 2), GROUND - 10))
    # the character, drawn via the same state machine the game uses
    st = _pick_state()
    seq = A.anims.get(st) or A.anims.get("micromold")
    suf = st[len("micromold"):].lstrip("_")
    fps = M.ANIM_STATE_FPS.get(suf, 8)
    frame = seq[int(mob.t * fps) % len(seq)]
    feet = mob.y + mob.h
    squash = 1.0
    if st.endswith("_walk") or st.endswith("_run"):
        u = (mob.t * fps / len(seq) * 2.0) % 1.0
        b = abs(np.sin(np.pi * u))
        feet -= DRAW_H * 0.06 * b
        squash = 1.0 + 0.05 * (b - 0.5)
    A.blit_char(surf, frame, mob.x + mob.w / 2, feet, DRAW_H,
                flip=mob.vx < 0, squash=squash, ref_h=A.enemy_ref["micromold"])
    surf.blit(small.render("MICRO MOLD", True, (150, 210, 120)), (24, 22))
    surf.blit(big.render(label_for(), True, (255, 240, 120)), (24, 46))
    arr = np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2))
    w.append_data(arr)


def _pick_state():
    k = "micromold"
    if mob.mm_air and mob.vy < -25 and A.anims.get(k + "_jump"):
        return k + "_jump"
    if mob.mm_air and mob.vy > 25 and A.anims.get(k + "_fall"):
        return k + "_fall"
    if mob.mm_air and A.anims.get(k + "_hop"):
        return k + "_hop"
    if mob.land_t > 0 and A.anims.get(k + "_land"):
        return k + "_land"
    if mob.turn_t > 0 and A.anims.get(k + "_turn"):
        return k + "_turn"
    if abs(mob.vx) > 150 and A.anims.get(k + "_run"):
        return k + "_run"
    if abs(mob.vx) > 8:
        return k + "_walk"
    return k


def move_to(target_x, frames):
    p.x = target_x
    for _ in range(frames):
        mob.update(1 / 60.0, p, [], g.parts, g.acids)
        # keep it inside the visible stage
        mob.x = max(60.0, min(W - 100.0, mob.x))
        draw_frame()


# run in from the left, hop across, reach the right, turn, come back
move_to(760, 150)     # far target -> RUN in, hopping
move_to(620, 120)     # close target -> WALK + HOP
move_to(90, 170)      # target now on the LEFT -> TURN AROUND, run/walk back
move_to(300, 90)      # settle

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB")
