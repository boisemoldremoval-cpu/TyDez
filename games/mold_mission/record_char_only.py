#!/usr/bin/env python3
"""Show JUST the Micro Mold character — its animation clips on a clean stage,
no level, cycling through every state at its real playback rate."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/micromold_character.mp4"
pygame.init()
screen = pygame.display.set_mode((720, 720))
snd = M.Sound()
g = M.Game(screen, snd)          # builds the AssetPack
A = g.assets
K = "micromold"
ref = A.enemy_ref[K]
big = pygame.font.Font(None, 46)
small = pygame.font.Font(None, 30)
w = imageio.get_writer(OUT, fps=24, codec="libx264", quality=9, macro_block_size=8)

# (label, state-suffix, seconds to show). "" = bare idle clip.
SEQUENCE = [
    ("IDLE", "", 1.6),
    ("WALK", "_walk", 2.0),
    ("RUN", "_run", 2.0),
    ("JUMP", "_jump", 1.1),
    ("FALL", "_fall", 1.1),
    ("LAND", "_land", 1.1),
    ("TURN AROUND", "_turn", 1.3),
    ("HOP", "_hop", 1.3),
    ("BIG SPORE SHOT (attack)", "_attack", 1.8),
    ("HURT", "_hurt", 1.3),
    ("STUNNED", "_stun", 1.6),
    ("ENRAGED (rare)", "_enraged", 2.0),
    ("DEATH SPLAT", "_splat", 1.4),
    ("DEATH FADE", "_fade", 1.4),
]

DRAW_H = 340          # on-stage height of the character
GROUND_Y = 560
t = 0.0


def bg():
    surf = pygame.Surface((720, 720))
    for y in range(720):                       # soft vertical gradient stage
        f = y / 720
        surf.fill((int(34 + 14 * f), int(40 + 16 * f), int(48 + 14 * f)),
                  (0, y, 720, 1))
    pygame.draw.ellipse(surf, (20, 24, 28), (200, GROUND_Y - 18, 320, 60))  # shadow pad
    return surf


STAGE = bg()

for label, suf, secs in SEQUENCE:
    seq = A.anims.get(K + suf) or A.anims.get(K)
    fps = M.ANIM_STATE_FPS.get(suf.lstrip("_"), 8)
    nframes = int(secs * 24)
    for i in range(nframes):
        tt = i / 24.0
        surf = STAGE.copy()
        # play the clip
        idx = int(tt * fps) % len(seq)
        frame = seq[idx]
        # a gentle bounce for the ground-locomotion clips so it reads lively
        feet = GROUND_Y
        squash = 1.0
        if suf in ("_walk", "_run"):
            u = (tt * fps / len(seq) * 2.0) % 1.0
            lift = abs(np.sin(np.pi * u))
            feet -= DRAW_H * 0.08 * lift
            squash = 1.0 + 0.06 * (lift - 0.5)
        A.blit_char(surf, frame, 360, feet, DRAW_H, ref_h=ref, squash=squash)
        # captions
        surf.blit(small.render("MICRO MOLD", True, (150, 210, 120)), (28, 26))
        lab = big.render(label, True, (255, 240, 120))
        surf.blit(lab, (28, 56))
        arr = np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2))
        w.append_data(arr)

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB")
