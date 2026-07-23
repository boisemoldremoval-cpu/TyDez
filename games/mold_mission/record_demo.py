#!/usr/bin/env python3
"""Record a headless gameplay clip of Mold Mission to an mp4.

Drives Ty with the same world-aware auto-player the selftest uses, and layers
in a few scripted interact presses (E) so the clip also shows the new mechanic:
using the Batch 6 interactive objects, and picking up / carrying / throwing a
supply crate. Frames are captured straight off the draw surface (no window
needed) and encoded with imageio-ffmpeg.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import numpy as np
import pygame
import imageio
import mold_mission as M

OUT = "/tmp/claude-0/-home-user-TyDez/bd9207a8-f98b-5cb2-b956-cc56d2cddccc/scratchpad/mold_mission_gameplay.mp4"
MISSIONS = [1, 3]          # basement + attic (different worlds, both to the boss)
SRC_FPS = M.FPS            # sim runs at 60
OUT_FPS = 30               # capture every 2nd frame -> smooth, real-time speed


def demo_keys(game, st, ds, i):
    """Auto-player keys + scripted interact presses to showcase items/objects."""
    K = M._bot_keys(game, st, i)
    p = game.player
    pcx = p.x + p.w / 2
    press_e = False
    if p.on_ground and not ds["e_prev"]:
        if p.carrying is None:
            # USE the nearest unused interactive object as Ty passes it
            for idx, pr in enumerate(game.props):
                if not pr.used and abs(pr.x - pcx) < 38 and idx not in ds["props"]:
                    press_e = True
                    ds["props"].add(idx)
                    break
            # grab a crate (once) to demo carry + throw
            if not press_e:
                for cr in game.crates:
                    if (not cr.carried and not cr.thrown
                            and abs((cr.x + cr.w / 2) - pcx) < 38
                            and id(cr) not in ds["picked"]):
                        press_e = True
                        ds["picked"].add(id(cr))
                        ds["carry_hold"] = 34     # carry a beat before throwing
                        break
    K[pygame.K_e] = press_e
    ds["e_prev"] = press_e
    # hold the crate visibly for a moment, then let the bot's fire toss it
    if ds["carry_hold"] > 0 and p.carrying is not None:
        ds["carry_hold"] -= 1
        K[pygame.K_j] = False
        K[pygame.K_RIGHT] = True                  # walk while carrying
    return K


def main():
    pygame.init()
    screen = pygame.display.set_mode((M.WIDTH, M.HEIGHT))
    snd = M.Sound()
    game = M.Game(screen, snd)
    writer = imageio.get_writer(OUT, fps=OUT_FPS, codec="libx264",
                                quality=8, macro_block_size=8)
    frame = 0

    def grab():
        arr = pygame.surfarray.array3d(screen)      # (W, H, 3)
        writer.append_data(np.transpose(arr, (1, 0, 2)))

    for m in MISSIONS:
        game.mission = m
        game.unlocked = max(game.unlocked, m)
        game.reset()
        game.state = M.STATE_PLAY
        st = {}
        ds = {"e_prev": False, "props": set(), "picked": set(), "carry_hold": 0}
        for i in range(9000):
            keys = demo_keys(game, st, ds, i)
            game.update(1 / SRC_FPS, keys)
            game.draw(frame / SRC_FPS)
            if frame % 2 == 0:
                grab()
            frame += 1
            if game.state in (M.STATE_WIN, M.STATE_OVER):
                break
        for j in range(int(SRC_FPS * 2.0)):          # linger on the win screen
            game.draw((frame) / SRC_FPS)
            if j % 2 == 0:
                grab()
            frame += 1
        print("mission %d done at frame %d (state=%s)" % (m, frame, game.state))

    writer.close()
    pygame.quit()
    sz = os.path.getsize(OUT)
    print("wrote %s (%.1f MB, %d src frames)" % (OUT, sz / 1e6, frame))


if __name__ == "__main__":
    main()
