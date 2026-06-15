"""
3D cartoon dog — a self-contained numpy raytracer.

Blender isn't required: the puppy is assembled from shaded ellipsoids (the same
"made of balls" idea as `tyguy3d.py`'s `_ball` primitives), then ray-traced with
Lambert + specular shading, a ground plane and a soft cast shadow. Outputs a PNG.

    python3 dog3d.py            # -> dog3d.png
    python3 dog3d.py pup.png    # custom output path
"""

import sys
import numpy as np
from PIL import Image


# --------------------------------------------------------------------------- #
# palette (linear 0..1)
# --------------------------------------------------------------------------- #
def _c(r, g, b):
    return np.array([r / 255, g / 255, b / 255], float)


FUR      = _c(214, 158, 96)
FUR_DARK = _c(176, 122, 66)
BELLY    = _c(244, 226, 198)
NOSE     = _c(46, 38, 36)
EYEW     = _c(250, 250, 250)
EYE      = _c(28, 22, 20)
TONGUE   = _c(232, 120, 120)
COLLAR   = _c(58, 150, 118)   # TyDez green
TAG      = _c(245, 205, 80)
GROUND   = _c(223, 235, 230)


# --------------------------------------------------------------------------- #
# the dog: a list of ellipsoids (center, scale, color, shininess)
# axes: x right, y up, z toward camera
# --------------------------------------------------------------------------- #
def build_dog():
    P = []

    def ball(c, s, col, shine=0.25):
        P.append((np.array(c, float), np.array(s, float), col, shine))

    # body / haunch (sitting)
    ball((0.0, -0.55, -0.05), (0.82, 0.78, 0.78), FUR)
    ball((0.0, -0.62, 0.55), (0.44, 0.52, 0.40), BELLY)        # chest blaze
    # front legs + paws
    for sx in (-0.30, 0.30):
        ball((sx, -1.05, 0.45), (0.20, 0.42, 0.22), FUR)
        ball((sx, -1.40, 0.58), (0.24, 0.15, 0.28), BELLY)
    # tail
    ball((0.86, -0.45, -0.35), (0.18, 0.30, 0.20), FUR_DARK)

    # head (big and expressive)
    ball((0.0, 0.62, 0.20), (0.94, 0.88, 0.90), FUR)
    # floppy ears
    for sx in (-0.84, 0.84):
        ball((sx, 0.58, 0.00), (0.24, 0.52, 0.30), FUR_DARK)
    # muzzle
    ball((0.0, 0.36, 0.82), (0.56, 0.44, 0.52), BELLY)
    # nose
    ball((0.0, 0.44, 1.22), (0.15, 0.13, 0.14), NOSE, shine=0.6)
    # eyes
    for sx in (-0.31, 0.31):
        ball((sx, 0.86, 0.80), (0.23, 0.27, 0.18), EYEW, shine=0.2)
        ball((sx, 0.84, 0.98), (0.135, 0.145, 0.11), EYE, shine=0.7)
    # eyebrows
    for sx in (-0.31, 0.31):
        ball((sx, 1.07, 0.74), (0.20, 0.07, 0.12), FUR_DARK)
    # tongue
    ball((0.0, 0.06, 0.94), (0.11, 0.16, 0.10), TONGUE)

    # collar band + tag
    ball((0.0, 0.02, 0.30), (0.70, 0.10, 0.62), COLLAR, shine=0.4)
    ball((0.0, -0.14, 0.92), (0.11, 0.11, 0.10), TAG, shine=0.6)
    return P


# --------------------------------------------------------------------------- #
# raytracer
# --------------------------------------------------------------------------- #
def _normalize(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, 1.0, n)


def intersect(orig, dirs, center, scale):
    """Ray/ellipsoid hit. orig (3,), dirs (H,W,3). Returns (t, normal)."""
    o = (orig - center) / scale                       # (3,)
    d = dirs / scale                                  # (H,W,3)
    a = np.einsum("...i,...i->...", d, d)
    b = 2.0 * np.einsum("...i,...i->...", d, o)
    c = np.dot(o, o) - 1.0
    disc = b * b - 4 * a * c
    hit = disc > 0
    sq = np.sqrt(np.where(hit, disc, 0.0))
    t = (-b - sq) / (2 * a)
    t = np.where(hit & (t > 1e-3), t, np.inf)
    P = orig + t[..., None] * dirs
    n = _normalize((P - center) / (scale ** 2))
    return t, n, P


def shade(P, N, base, shine, light, eye):
    L = _normalize(light - P)
    V = _normalize(eye - P)
    diff = np.clip(np.einsum("...i,...i->...", N, L), 0, 1)
    R = 2 * np.einsum("...i,...i->...", N, L)[..., None] * N - L
    spec = np.clip(np.einsum("...i,...i->...", R, V), 0, 1) ** 40
    amb = 0.32
    col = base * (amb + 0.85 * diff)[..., None] + (shine * spec)[..., None]
    # subtle rim light for that toon pop
    rim = (1 - np.clip(np.einsum("...i,...i->...", N, V), 0, 1)) ** 3
    col += (0.18 * rim)[..., None] * np.array([1.0, 0.97, 0.9])
    return col


def render(out="dog3d.png", W=820, H=820):
    objs = build_dog()
    eye = np.array([0.0, 0.20, 6.4])
    target = np.array([0.0, -0.05, 0.0])
    up = np.array([0.0, 1.0, 0.0])
    fwd = _normalize(target - eye)
    right = _normalize(np.cross(fwd, up))
    tup = np.cross(right, fwd)
    fov = np.radians(40)
    sc = np.tan(fov / 2)

    px = (np.arange(W) + 0.5) / W * 2 - 1
    py = 1 - (np.arange(H) + 0.5) / H * 2
    gx, gy = np.meshgrid(px, py)
    dirs = _normalize(fwd + (gx * sc)[..., None] * right + (gy * sc)[..., None] * tup)

    light = np.array([4.0, 6.0, 5.0])

    best_t = np.full((H, W), np.inf)
    color = np.zeros((H, W, 3))
    hit_any = np.zeros((H, W), bool)

    # objects
    for center, scale, base, shine in objs:
        t, n, P = intersect(eye, dirs, center, scale)
        closer = t < best_t
        if closer.any():
            shaded = shade(P, n, base, shine, light, eye)
            color = np.where(closer[..., None], shaded, color)
            best_t = np.where(closer, t, best_t)
            hit_any |= closer & np.isfinite(t)

    # ground plane y = -1.45 with a soft cast shadow
    gy_plane = -1.45
    tg = (gy_plane - eye[1]) / dirs[..., 1]
    ghit = (tg > 1e-3) & (tg < best_t)
    Pg = eye + tg[..., None] * dirs
    # occlusion toward the light = shadow
    shadow = np.zeros((H, W))
    Ldir = _normalize(light - Pg)
    for center, scale, _, _ in objs:
        ts, _, _ = intersect_pts(Pg, Ldir, center, scale)
        shadow = np.maximum(shadow, (ts < np.inf).astype(float))
    # radial vignette on the floor so it reads as a soft studio sweep
    rad = np.clip(1 - (Pg[..., 0] ** 2 + (Pg[..., 2] + 0.2) ** 2) / 12.0, 0, 1)
    gcol = GROUND * (0.55 + 0.45 * rad)[..., None]
    gcol = gcol * (1 - 0.55 * shadow)[..., None]
    color = np.where((ghit & ~hit_any)[..., None], gcol, color)
    hit_any |= ghit

    # soft gradient background where nothing was hit
    bg_top = np.array([0.93, 0.96, 0.99])
    bg_bot = np.array([0.82, 0.89, 0.95])
    grad = (gy[..., None] * 0.5 + 0.5)
    bg = bg_bot * (1 - grad) + bg_top * grad
    color = np.where(hit_any[..., None], color, bg)

    img = np.clip(color, 0, 1) ** (1 / 2.2)           # gamma
    Image.fromarray((img * 255).astype(np.uint8)).save(out)
    print(f"wrote {out}")


def intersect_pts(orig, dirs, center, scale):
    """Like intersect but orig is per-pixel (H,W,3) — used for shadow rays."""
    o = (orig - center) / scale
    d = dirs / scale
    a = np.einsum("...i,...i->...", d, d)
    b = 2.0 * np.einsum("...i,...i->...", d, o)
    c = np.einsum("...i,...i->...", o, o) - 1.0
    disc = b * b - 4 * a * c
    hit = disc > 0
    sq = np.sqrt(np.where(hit, disc, 0.0))
    t = (-b - sq) / (2 * a)
    t = np.where(hit & (t > 1e-2), t, np.inf)
    return t, None, None


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "dog3d.png")
