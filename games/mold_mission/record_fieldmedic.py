#!/usr/bin/env python3
"""Show the FIELD MEDIC (Dr. Mira) — her video-cut animation clips on a clean
stage, then a live gameplay beat where she trails Ty and heal-beams him."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/fieldmedic_showcase.mp4"
pygame.init()
screen = pygame.display.set_mode((720, 720))
g = M.Game(screen, M.Sound())
A = g.assets
K = "fieldmedic"
ref = A.enemy_ref[K]
big = pygame.font.Font(None, 46)
small = pygame.font.Font(None, 30)
w = imageio.get_writer(OUT, fps=24, codec="libx264", quality=9, macro_block_size=8)

SEQUENCE = [
    ("LOOPABLE IDLE", "", 1.8),
    ("RUN", "_run", 2.0),
    ("DASH / SPRINT", "_dash", 1.6),
    ("SLIDE", "_slide", 1.4),
    ("SHOOT", "_shoot", 1.6),
    ("RELOAD", "_reload", 1.6),
    ("HEAL BEAM (ALLY)", "_heal", 1.8),
    ("HEAL BURST (AREA)", "_burst", 1.8),
    ("PROTECT BARRIER", "_barrier", 1.8),
    ("HAPPY", "_happy", 1.6),
]
DRAW_H = 360
GROUND_Y = 590
STAGE = pygame.Surface((720, 720))
for y in range(720):
    f = y / 720
    STAGE.fill((int(30 + 16 * f), int(38 + 18 * f), int(46 + 14 * f)), (0, y, 720, 1))
pygame.draw.ellipse(STAGE, (18, 22, 26), (210, GROUND_Y - 16, 300, 54))

for label, suf, secs in SEQUENCE:
    seq = A.anims.get(K + suf) or A.anims.get(K)
    fps = M.ANIM_STATE_FPS.get(suf.lstrip("_"), 8)
    for i in range(int(secs * 24)):
        tt = i / 24.0
        surf = STAGE.copy()
        frame = seq[int(tt * fps) % len(seq)]
        feet = GROUND_Y
        squash = 1.0
        if suf in ("_run", "_dash"):
            u = (tt * fps / len(seq) * 2.0) % 1.0
            lift = abs(np.sin(np.pi * u))
            feet -= DRAW_H * 0.07 * lift
            squash = 1.0 + 0.05 * (lift - 0.5)
        A.blit_char(surf, frame, 360, feet, DRAW_H, ref_h=ref, squash=squash)
        surf.blit(small.render("FIELD MEDIC  ·  Dr. Mira", True, (150, 230, 150)), (26, 24))
        surf.blit(big.render(label, True, (200, 255, 190)), (26, 52))
        w.append_data(np.transpose(pygame.surfarray.array3d(surf), (1, 0, 2)))

# ---- live gameplay beat: Ty + the Field Medic trailing / healing ----
g.mission = 1; g.unlocked = 1; g.reset(); g.state = M.STATE_PLAY
p = g.player
st = {}
for i in range(900):
    keys = M._bot_keys(g, st, i)
    # bleed Ty's HP down on a cycle so the medic's HEAL BEAM keeps firing on-camera
    if i % 150 == 60:
        p.hp = max(12, p.hp - 40)
    g.update(1 / 60.0, keys)
    g.cam = max(0.0, min(M.LEVEL_W - M.WIDTH, p.x + p.w / 2 - M.WIDTH / 2))
    g.draw(i / 60.0)
    if i % 2 == 0:
        arr = np.transpose(pygame.surfarray.array3d(screen), (1, 0, 2))
        big2 = pygame.transform.scale(pygame.surfarray.make_surface(
            np.transpose(arr, (1, 0, 2))), (720, 450))
        out = pygame.Surface((720, 720)); out.fill((12, 14, 18))
        out.blit(big2, (0, 135))
        out.blit(small.render("FIELD MEDIC in play — trails Ty, heal-beams him", True,
                              (150, 230, 150)), (24, 96))
        w.append_data(np.transpose(pygame.surfarray.array3d(out), (1, 0, 2)))
    if g.state != M.STATE_PLAY:
        break

w.close()
pygame.quit()
print("wrote", OUT, os.path.getsize(OUT) // 1000, "KB")
