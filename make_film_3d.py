#!/usr/bin/env python3
"""
Render the 3D TyGuy film "The Kindness Choice" to a PNG sequence.

Per frame the scene is rebuilt from scratch (reset -> environment ->
characters posed for time t -> camera for the active shot -> render). This
keeps memory clean and lets the pose system drive walking / waving / faces
without a rig.

Usage:
    python3 make_film_3d.py stills            # a few key-beat stills -> /tmp
    python3 make_film_3d.py range 0 48        # render frames [0,48)
    python3 make_film_3d.py all               # full sequence -> /tmp/seq3d
Captions/speech/hearts are added later by encode_film.py (they share TIMELINE).
"""

import sys
import math
import time
import os
import bpy
from mathutils import Vector
import tyguy3d as T

FPS = 24
RES = (800, 450)
SAMPLES = 16   # denoiser cleans the flat materials well at low samples
SEQ_DIR = "/tmp/seq3d"

T.SUBSURF_RENDER = 1   # lighter subdivision for faster film frames

GROUND_GREEN = (0.34, 0.55, 0.27)


# --------------------------------------------------------------------------- #
# timeline  (start, dur, name)   total ~31s
# --------------------------------------------------------------------------- #
BEATS = [
    ("establish", 5.0),
    ("ignore", 5.0),
    ("enter", 5.0),
    ("approach", 6.0),
    ("cheer", 5.5),
    ("friends", 4.5),
]
START = {}
_a = 0.0
for _n, _d in BEATS:
    START[_n] = _a
    _a += _d
DURATION = _a

# caption + speech text shared with the encoder
TIMELINE = {
    "establish": {"cap": "Mia was the new kid. She didn't know anyone."},
    "ignore":    {"cap": "The other kids hurried past without saying hi."},
    "enter":     {"cap": "But TyGuy noticed her standing all alone."},
    "approach":  {"cap": "He chose to walk over and say hello.",
                  "speech": ("Hi! I'm Ty — want to hang out with us?", 2.0, 3.6)},
    "cheer":     {"cap": "One kind hello made her whole day brighter!",
                  "hearts": (1.5, 5.5)},
    "friends":   {"cap": "Kindness turns a stranger into a friend."},
}


def beat_at(t):
    for name, dur in BEATS:
        if START[name] <= t < START[name] + dur:
            return name, t - START[name], dur
    return BEATS[-1][0], BEATS[-1][1], BEATS[-1][1]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def eo(t):
    return 1 - (1 - clamp(t)) ** 3


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(len(a)))


# --------------------------------------------------------------------------- #
# environment
# --------------------------------------------------------------------------- #
def tree(x, y, h=2.6):
    trunk = T.mat("trunk", (0.40, 0.27, 0.16), rough=0.9)
    leaf = T.mat("leaf", (0.27, 0.5, 0.22), rough=0.85)
    T._capsule((x, y, 0), (x, y, h), 0.16, trunk, subsurf=1)
    T._ball((x, y, h + 0.3), 0.85, leaf, scale=(1, 1, 0.9))
    T._ball((x - 0.5, y + 0.2, h + 0.0), 0.6, leaf)
    T._ball((x + 0.5, y - 0.1, h + 0.1), 0.6, leaf)


def bench(x, y):
    wood = T.mat("bench", (0.55, 0.38, 0.22), rough=0.8)
    metal = T.mat("benchleg", (0.25, 0.25, 0.28), rough=0.5)
    T._box((x, y, 0.55), (1.6, 0.5, 0.08), wood)            # seat
    T._box((x, y + 0.24, 0.85), (1.6, 0.08, 0.5), wood)     # back
    for sx in (x - 0.7, x + 0.7):
        T._box((sx, y, 0.27), (0.08, 0.45, 0.55), metal)


def building(x, y):
    wall = T.mat("wall", (0.86, 0.78, 0.62), rough=0.9)
    win = T.mat("win", (0.45, 0.62, 0.78), rough=0.3)
    roof = T.mat("roof", (0.5, 0.3, 0.26), rough=0.8)
    T._box((x, y, 2.4), (7.0, 0.4, 4.8), wall)
    T._box((x, y - 0.1, 5.0), (7.4, 0.6, 0.5), roof)
    for wx in (x - 2.2, x, x + 2.2):
        for wz in (2.0, 3.6):
            T._box((wx, y - 0.25, wz), (1.1, 0.1, 1.0), win)


def clouds():
    c = T.mat("cloud", (0.97, 0.98, 1.0), rough=1.0)
    for (cx, cz) in [(-6, 6.5), (5, 7.2), (0.5, 8.0)]:
        T._ball((cx, 14, cz), 1.1, c, scale=(1.6, 1, 0.8))
        T._ball((cx + 1.2, 14, cz - 0.1), 0.8, c, scale=(1.4, 1, 0.8))
        T._ball((cx - 1.1, 14, cz + 0.05), 0.7, c, scale=(1.3, 1, 0.8))


def build_environment():
    T.set_world((0.40, 0.62, 0.92), 0.5)
    # sky-blue ground? no: grass
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    g = bpy.context.active_object
    g.data.materials.append(T.mat("grass", GROUND_GREEN, rough=0.95))
    # path strip
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0.01))
    p = bpy.context.active_object
    p.scale = (1.4, 12, 1)
    p.data.materials.append(T.mat("path", (0.70, 0.66, 0.58), rough=0.95))
    building(0, 9.5)
    tree(-6.5, 4, 2.8)
    tree(6.2, 3.2, 2.6)
    tree(8.0, 6, 3.0)
    bench(3.4, 2.2)
    clouds()
    # lights
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    so = bpy.data.objects.new("Sun", sun)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(52), math.radians(12), math.radians(35))
    fill = bpy.data.lights.new("Fill", "AREA")
    fill.energy = 250
    fill.size = 10
    fo = bpy.data.objects.new("Fill", fill)
    bpy.context.scene.collection.objects.link(fo)
    fo.location = (-6, -7, 5)
    fo.rotation_euler = (1.0, -0.2, -0.5)


# --------------------------------------------------------------------------- #
# character blocking
# --------------------------------------------------------------------------- #
def walk_pose(t, base=None, speed=2.2, swing=22, amp=0.06):
    """Arm-swing + returns (pose, bob_z)."""
    pose = dict(base or {})
    s = math.sin(t * speed * math.pi)
    pose["arm_l"] = 14 + s * swing
    pose["arm_r"] = 14 - s * swing
    pose["fwd_l"] = 6 - s * 14
    pose["fwd_r"] = 6 + s * 14
    bob = abs(math.sin(t * speed * math.pi)) * amp
    return pose, bob


def place(t):
    """Return list of (palette, x, y, z, pose) for all characters at time t."""
    name, lt, dur = beat_at(t)
    chars = []
    mia_x = 3.4   # by the bench
    mia_y = 1.4

    if name == "establish":
        # Mia alone (sad), two kids chatting at left
        chars.append((T.MIA, mia_x, mia_y, 0, {"mouth": "sad", "arm_l": 8, "arm_r": 8, "lean": 3}))
        chars.append((T.KID_A, -2.4, 1.6, 0, {"mouth": "smile", "rotz": 25, "arm_r": 30, "fwd_r": 20}))
        chars.append((T.KID_B, -3.4, 1.8, 0, {"mouth": "smile", "rotz": -20, "arm_l": 28, "fwd_l": 18}))

    elif name == "ignore":
        chars.append((T.MIA, mia_x, mia_y, 0, {"mouth": "sad", "lean": 5, "arm_l": 7, "arm_r": 7}))
        # kids walk off to the left and exit
        p = eo(lt / (dur - 0.5))
        kx1 = lerp(-2.4, -9.0, p)
        kx2 = lerp(-3.4, -10.2, p)
        po1, b1 = walk_pose(lt, {"mouth": "smile", "rotz": -90})
        po2, b2 = walk_pose(lt + 0.3, {"mouth": "smile", "rotz": -90})
        chars.append((T.KID_A, kx1, 1.6, b1, po1))
        chars.append((T.KID_B, kx2, 1.9, b2, po2))

    elif name == "enter":
        chars.append((T.MIA, mia_x, mia_y, 0, {"mouth": "sad", "lean": 4, "arm_l": 7, "arm_r": 7}))
        # TyGuy walks in from left to center, then turns to notice Mia
        move = dur * 0.6
        if lt < move:
            tx = lerp(-7.0, -0.5, eo(lt / move))
            po, bz = walk_pose(lt, {"mouth": "smile"})
        else:
            tx = -0.5
            turn = smooth((lt - move) / (dur - move))
            po = {"mouth": "open", "rotz": 40 * turn, "arm_l": 12, "arm_r": 12}
            bz = 0
        chars.append((T.TYGUY, tx, 1.5, bz, po))

    elif name == "approach":
        # TyGuy walks from -0.5 to next to Mia, then waves
        move = dur * 0.5
        if lt < move:
            tx = lerp(-0.5, 1.7, eo(lt / move))
            po, bz = walk_pose(lt, {"mouth": "smile", "rotz": 20})
        else:
            tx = 1.7
            wv = math.sin((lt - move) * 7)
            po = {"mouth": "open", "rotz": 35, "arm_r": 60 + wv * 18,
                  "fwd_r": 70, "arm_l": 12}
            bz = 0
        chars.append((T.TYGUY, tx, 1.5, bz, po))
        # Mia turns from sad toward neutral
        mm = "neutral" if lt > move else "sad"
        chars.append((T.MIA, mia_x, mia_y, 0, {"mouth": mm, "rotz": -20, "arm_l": 7, "arm_r": 7}))

    elif name == "cheer":
        wv = math.sin(lt * 6)
        chars.append((T.TYGUY, 1.7, 1.5, 0, {"mouth": "smile", "rotz": 30,
                      "arm_r": 55 + wv * 12, "fwd_r": 55, "arm_l": 14}))
        # Mia waves back, happy
        chars.append((T.MIA, mia_x, mia_y, 0, {"mouth": "smile", "rotz": -25,
                      "arm_l": 50 + wv * 12, "fwd_l": 45, "arm_r": 12}))

    else:  # friends
        bob = math.sin(lt * 3) * 0.03
        chars.append((T.TYGUY, 1.6, 1.5, bob, {"mouth": "smile", "rotz": 10,
                      "arm_r": 40, "fwd_r": 25, "arm_l": 14}))
        chars.append((T.MIA, 2.9, 1.5, bob, {"mouth": "smile", "rotz": -10,
                      "arm_l": 40, "fwd_l": 25, "arm_r": 12}))
    return chars


# --------------------------------------------------------------------------- #
# camera per shot (with gentle in-shot motion)
# --------------------------------------------------------------------------- #
def camera_at(t):
    name, lt, dur = beat_at(t)
    p = lt / dur
    if name == "establish":
        loc = vlerp((-1.5, -10.5, 3.2), (-0.5, -9.5, 3.0), smooth(p))
        look = (1.0, 1.5, 1.3)
        lens = 36
    elif name == "ignore":
        loc = vlerp((0.5, -7.5, 2.4), (1.2, -7.0, 2.2), smooth(p))
        look = (2.8, 1.4, 1.3)
        lens = 44
    elif name == "enter":
        loc = vlerp((-3.0, -7.5, 2.2), (-0.5, -7.2, 2.2), smooth(p))
        look = (-0.2, 1.5, 1.4)
        lens = 42
    elif name == "approach":
        loc = vlerp((0.0, -6.8, 2.2), (1.0, -6.4, 2.1), smooth(p))
        look = (1.8, 1.4, 1.4)
        lens = 44
    elif name == "cheer":
        loc = (1.6, -6.0, 2.1)
        look = (2.4, 1.4, 1.45)
        lens = 46
    else:  # friends
        loc = vlerp((2.2, -6.4, 2.2), (2.2, -8.4, 2.7), smooth(p))
        look = (2.2, 1.4, 1.4)
        lens = 44
    return loc, look, lens


# --------------------------------------------------------------------------- #
# render one frame
# --------------------------------------------------------------------------- #
def render_frame(t, path):
    T.reset_scene()
    build_environment()
    for pal, x, y, z, pose in place(t):
        root = T.build_character(pal, x=x, y=y, facing=-1, pose=pose)
        root.location.z = z
    loc, look, lens = camera_at(t)
    T.add_camera(loc, look, lens=lens)
    sc = T.setup_render(res=RES, samples=SAMPLES, fps=FPS)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    n_total = int(DURATION * FPS)

    if mode == "stills":
        os.makedirs("/tmp/stills", exist_ok=True)
        for name, _d in BEATS:
            t = START[name] + _d * 0.7
            f = f"/tmp/stills/{name}.png"
            t0 = time.time()
            render_frame(t, f)
            print(f"{name:10s} t={t:5.1f}  {time.time()-t0:5.1f}s -> {f}")
        return

    os.makedirs(SEQ_DIR, exist_ok=True)
    if mode == "range":
        a, b = int(sys.argv[2]), int(sys.argv[3])
    else:
        a, b = 0, n_total
    print(f"Total {n_total} frames; rendering [{a},{b}) -> {SEQ_DIR}")
    t0 = time.time()
    for i in range(a, b):
        render_frame(i / FPS, f"{SEQ_DIR}/{i:05d}.png")
        if (i - a) % 10 == 0:
            el = time.time() - t0
            done = i - a + 1
            eta = el / done * (b - a - done)
            print(f"  frame {i:4d}/{b}  {el/done:4.1f}s/frame  ETA {eta/60:5.1f}min")
    print(f"Done [{a},{b}) in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
