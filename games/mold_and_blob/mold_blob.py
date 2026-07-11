#!/usr/bin/env python3
"""Mold & Blob — a "A Boy and His Blob"-style puzzle-platformer (TyDez / Boise
Mold Removal).

You are TyGuy, and Blob is your loyal green companion. Blob can't fight mold,
but on command it transforms into the tool you need — a **trampoline** to reach
high ledges, a **bridge** to span pits, or a **ladder** to climb. Use Blob to
get around the level, spray every mold patch clean, then reach the exit door.

Controls
    Left / Right  (or A / D) ... walk
    Up / W / Space ............. jump  (and climb up while on a ladder)
    Down / S ................... climb down while on a ladder
    Hold F .................... spray mold in front of you
    1 ......................... Blob -> Trampoline (bounce up)
    2 ......................... Blob -> Bridge (cross gaps)
    3 ......................... Blob -> Ladder (climb)
    E / 0 ..................... call Blob back (follow you)
    Enter ..................... start / restart
    M ......................... toggle sound
    G ......................... toggle high-quality effects (bloom/grain)
    Esc ...................... quit

The graphics are all generated in code (no image files): the scene is rendered
at 2x and downsampled for smooth edges, with bloom, numpy-noise textures, rim
lighting, drifting mist + dust, and a film-grade/grain pass.

Run
    pip install pygame numpy
    python3 mold_blob.py

Headless smoke test (no window):
    python3 mold_blob.py --selftest
"""

import math
import os
import random
import sys

import pygame

try:
    import pygame.gfxdraw as _gfx
    _HAS_GFX = True
except Exception:
    _HAS_GFX = False

try:
    import numpy as np
    _HAS_NP = True
except Exception:
    _HAS_NP = False

# --------------------------------------------------------------------------- #
# Config / palette
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 960, 640
SS = 2                     # supersample factor (render at 2x, downscale)
SW, SH = WIDTH * SS, HEIGHT * SS
FPS = 60

C_SKY_TOP = (44, 60, 74)
C_SKY_BOT = (16, 23, 30)
C_HILL_FAR = (32, 47, 57)
C_HILL_NEAR = (24, 37, 46)
C_BRAND = (86, 214, 165)
C_BRAND_DK = (40, 140, 104)
C_BLOB = (104, 214, 170)
C_BLOB_DK = (46, 148, 114)
C_MOLD = (126, 172, 82)
C_MOLD_DK = (72, 106, 46)
C_MOSS = (92, 138, 70)
C_SPRAY = (190, 238, 250)
C_SKIN = (234, 200, 168)
C_TEXT = (236, 242, 245)
C_TEXT_DIM = (150, 164, 172)
C_DOOR = (210, 176, 96)
C_DOOR_OPEN = (120, 224, 150)
C_DANGER = (226, 96, 88)
OUTLINE = (16, 24, 22)

GRAVITY = 2200.0
MOVE_SPEED = 275.0
JUMP_V = 760.0
TRAMPOLINE_V = 1180.0
CLIMB_SPEED = 210.0

STATE_MENU, STATE_PLAY, STATE_WIN, STATE_OVER = "menu", "play", "win", "over"
FOLLOW, TRAMPOLINE, BRIDGE, LADDER = "follow", "trampoline", "bridge", "ladder"


def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


# --------------------------------------------------------------------------- #
# Low-level anti-aliased primitives (draw straight onto a surface, raw pixels)
# --------------------------------------------------------------------------- #
def fcircle(s, cx, cy, r, color):
    cx, cy, r = int(cx), int(cy), int(r)
    if r < 1:
        return
    if _HAS_GFX:
        _gfx.filled_circle(s, cx, cy, r, color)
        _gfx.aacircle(s, cx, cy, r, color)
    else:
        pygame.draw.circle(s, color[:3], (cx, cy), r)


def fellipse(s, x, y, w, h, color):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w < 1 or h < 1:
        return
    if _HAS_GFX:
        rx, ry = max(1, w // 2), max(1, h // 2)
        _gfx.filled_ellipse(s, x + rx, y + ry, rx, ry, color)
        _gfx.aaellipse(s, x + rx, y + ry, rx, ry, color)
    else:
        pygame.draw.ellipse(s, color[:3], (x, y, w, h))


def _lerp(a, b, f):
    return [int(a[i] + (b[i] - a[i]) * f) for i in range(3)]


def vgrad(w, h, top, bot, radius=0):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for yy in range(h):
        pygame.draw.line(surf, _lerp(top, bot, yy / max(1, h - 1)),
                         (0, yy), (w, yy))
    if radius:
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h),
                         border_radius=radius)
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def noise_surf(w, h, cell, seed, lo, hi):
    """Smooth value-noise as a grayscale surface (for texture overlays)."""
    if not _HAS_NP:
        s = pygame.Surface((w, h))
        s.fill((255, 255, 255))
        return s
    rng = np.random.default_rng(seed)
    gw, gh = max(2, w // cell), max(2, h // cell)
    g = rng.integers(lo, hi, (gw, gh)).astype("uint8")
    small = pygame.surfarray.make_surface(np.repeat(g[:, :, None], 3, axis=2))
    return pygame.transform.smoothscale(small, (w, h))


# --------------------------------------------------------------------------- #
# Asset pack — optional PNG art dropped into ./assets replaces the vector art
# --------------------------------------------------------------------------- #
# Drop transparent PNGs named after any of these into an "assets" folder next
# to this script and they are used throughout the game (menu + gameplay). Any
# missing name falls back to the built-in vector drawing.
ASSET_NAMES = ("tyguy", "blob", "mold", "trampoline", "bridge", "ladder",
               "door_open", "door_closed", "background", "platform")


class AssetPack:
    def __init__(self, folder):
        self.imgs = {}
        self.scaled = {}
        self.folder = folder
        for name in ASSET_NAMES:
            p = os.path.join(folder, name + ".png")
            if os.path.isfile(p):
                try:
                    self.imgs[name] = pygame.image.load(p).convert_alpha()
                except Exception:
                    pass

    def scaled_get(self, name, dw, dh, flip):
        key = (name, dw, dh, flip)
        s = self.scaled.get(key)
        if s is None:
            s = pygame.transform.smoothscale(self.imgs[name], (dw, dh))
            if flip:
                s = pygame.transform.flip(s, True, False)
            self.scaled[key] = s
        return s


# --------------------------------------------------------------------------- #
# Canvas — scales logical coordinates up to the 2x render surface
# --------------------------------------------------------------------------- #
class Canvas:
    def __init__(self, surf, k, assets=None):
        self.s = surf
        self.k = k
        self.assets = assets

    def has(self, name):
        return self.assets is not None and name in self.assets.imgs

    def image(self, name, cx, cy, h, flip=False):
        """Blit asset centered at (cx, cy) with logical height h (aspect kept)."""
        img = self.assets.imgs[name]
        aw, ah = img.get_size()
        wlog = h * aw / ah
        dw, dh = max(1, int(wlog * self.k)), max(1, int(h * self.k))
        s = self.assets.scaled_get(name, dw, dh, flip)
        self.s.blit(s, (int((cx - wlog / 2) * self.k), int((cy - h / 2) * self.k)))

    def image_rect(self, name, rect, flip=False):
        """Fit asset inside rect (aspect kept), centered."""
        x, y, w, h = rect
        img = self.assets.imgs[name]
        aw, ah = img.get_size()
        sc = min(w / aw, h / ah)
        wlog, hlog = aw * sc, ah * sc
        dw, dh = max(1, int(wlog * self.k)), max(1, int(hlog * self.k))
        s = self.assets.scaled_get(name, dw, dh, flip)
        self.s.blit(s, (int((x + w / 2 - wlog / 2) * self.k),
                        int((y + h / 2 - hlog / 2) * self.k)))

    def circle(self, cx, cy, r, color):
        fcircle(self.s, cx * self.k, cy * self.k, r * self.k, color)

    def ocircle(self, cx, cy, r, color, ol=2):
        k = self.k
        fcircle(self.s, cx * k, cy * k, (r + ol) * k, OUTLINE)
        fcircle(self.s, cx * k, cy * k, r * k, color)

    def rect(self, rect, color, radius=0):
        k = self.k
        x, y, w, h = rect
        pygame.draw.rect(self.s, color, (int(x * k), int(y * k),
                         int(w * k), int(h * k)), border_radius=int(radius * k))

    def orrect(self, rect, color, radius=4, ol=2):
        k = self.k
        x, y, w, h = rect
        pygame.draw.rect(self.s, OUTLINE, (int((x - ol) * k), int((y - ol) * k),
                         int((w + 2 * ol) * k), int((h + 2 * ol) * k)),
                         border_radius=int((radius + ol) * k))
        pygame.draw.rect(self.s, color, (int(x * k), int(y * k),
                         int(w * k), int(h * k)), border_radius=int(radius * k))

    def line(self, color, p1, p2, w=1):
        k = self.k
        pygame.draw.line(self.s, color, (p1[0] * k, p1[1] * k),
                         (p2[0] * k, p2[1] * k), max(1, int(w * k)))

    def ellipse_rect(self, rect, color):
        k = self.k
        x, y, w, h = rect
        pygame.draw.ellipse(self.s, color,
                            (int(x * k), int(y * k), int(w * k), int(h * k)))

    def oellipse(self, cx, cy, rx, ry, color, ol=2):
        k = self.k
        pygame.draw.ellipse(self.s, OUTLINE,
                            (int((cx - rx - ol) * k), int((cy - ry - ol) * k),
                             int(2 * (rx + ol) * k), int(2 * (ry + ol) * k)))
        pygame.draw.ellipse(self.s, color,
                            (int((cx - rx) * k), int((cy - ry) * k),
                             int(2 * rx * k), int(2 * ry * k)))

    def arc(self, color, rect, a0, a1, w=1):
        k = self.k
        x, y, w0, h = rect
        pygame.draw.arc(self.s, color, (int(x * k), int(y * k),
                        int(w0 * k), int(h * k)), a0, a1, max(1, int(w * k)))

    def glow(self, cx, cy, r, color, strength=110):
        k = self.k
        R = int(r * k)
        for i in range(R, 0, -3):
            a = int(strength * (1 - i / R) ** 2)
            fcircle(self.s, cx * k, cy * k, i,
                    (color[0], color[1], color[2], a))

    def shadow(self, cx, cy, w, h):
        k = self.k
        for i in (0, 2, 4):
            fellipse(self.s, (cx - w / 2 + i) * k, (cy - h / 2 + i) * k,
                     (w - 2 * i) * k, (h - 2 * i) * k, (0, 0, 0, 42))


# --------------------------------------------------------------------------- #
# Character illustrations
# --------------------------------------------------------------------------- #
def draw_blob(c, cx, cy, r, wobble, t):
    if c.has("blob"):
        bob = math.sin(wobble) * 1.5
        c.shadow(cx, cy + r, r * 2.4, 9)
        c.image("blob", cx, cy + bob, r * 3.0)
        return
    sq = math.sin(wobble) * 0.12
    rx, ry = r * (1 + sq), r * (1 - sq)
    c.shadow(cx, cy + ry, rx * 2.4, 9)
    c.glow(cx, cy, r * 1.7, C_BLOB, 55)
    c.oellipse(cx, cy, rx, ry, C_BLOB)
    c.circle(cx, cy - ry * 0.32, rx * 0.72, (150, 236, 202, 55))
    c.circle(cx - rx * 0.16, cy - ry * 0.52, rx * 0.55, (215, 255, 235, 34))  # rim
    c.circle(cx - rx * 0.34, cy - ry * 0.42, r * 0.28, (224, 250, 236, 175))
    blink = (t * 0.9 % 3.0) < 0.13
    for side in (-1, 1):
        exx, eyy = cx + side * r * 0.34, cy - 2
        if blink:
            c.line((20, 30, 28), (exx - 3, eyy), (exx + 3, eyy), 2)
        else:
            c.circle(exx, eyy, r * 0.26, (250, 252, 250))
            c.circle(exx + 1, eyy + 0.5, r * 0.12, (26, 34, 30))
    if not blink:
        c.arc((26, 60, 48), (cx - 5, cy + 1, 10, 7), 3.7, 5.7, 2)


def draw_tyguy(c, x, y, w, h, facing, moving, on_ground, anim, spraying, t):
    cx = x + w / 2
    feet = y + h
    fc = 1 if facing >= 0 else -1
    walk = math.sin(anim * 0.045) if (moving and on_ground) else 0.0

    if c.has("tyguy"):
        if on_ground:
            c.shadow(cx, feet, w * 1.9, 9)
        bob = abs(math.sin(anim * 0.045)) * 1.2 if (moving and on_ground) else 0.0
        H = h * 1.72
        c.image("tyguy", cx, y + h * 0.5 - bob, H, flip=(fc < 0))
        return

    if on_ground:
        c.shadow(cx, feet, w * 1.9, 9)

    c.orrect((cx - fc * 13 - 5, y + 9, 11, 20), C_BRAND_DK, radius=5)
    c.circle(cx - fc * 13, y + 8, 3, (30, 46, 40))

    hip = (cx, y + 29)
    sw = 5 * walk
    for foot in ((cx - 4 + sw, feet), (cx + 4 - sw, feet)):
        c.line(OUTLINE, hip, foot, 9)
        c.line((52, 66, 60), hip, foot, 6)
        c.ocircle(foot[0], foot[1] - 2, 3.5, (40, 52, 48), ol=1)

    c.orrect((x + 2, y + 12, w - 4, 19), C_BRAND_DK, radius=6)
    c.rect((x + 4, y + 13, w - 8, 8), C_BRAND, radius=5)
    c.circle(x + 6, y + 14, 3, (190, 245, 220, 60))            # torso rim
    c.circle(cx, y + 22, 5, (22, 42, 34))
    c.line((210, 245, 228), (cx - 3, y + 20), (cx + 3, y + 20), 2)
    c.line((210, 245, 228), (cx, y + 20), (cx, y + 25), 2)

    shoulder = (cx + fc * 5, y + 17)
    gun = (cx + fc * (w / 2 + 7), y + 17 - (5 if spraying else 0))
    c.line(OUTLINE, shoulder, gun, 8)
    c.line(C_SKIN, shoulder, gun, 5)
    c.orrect((gun[0] - 4, gun[1] - 4, 8, 8), (70, 80, 76), radius=2)

    hx, hy = cx, y + 7
    c.ocircle(hx, hy, 8, C_SKIN)
    c.circle(hx - 3, hy - 3, 3, (255, 240, 215, 60))          # head rim light
    for side in (-1, 1):
        c.circle(hx + fc * 2 + side * 3, hy - 1, 1.5, (30, 32, 30))
    c.arc((150, 90, 70), (hx - 4, hy + 1, 8, 6), 3.7, 5.7, 2)
    c.ellipse_rect((hx - 11, hy - 14, 22, 15), OUTLINE)
    c.ellipse_rect((hx - 9, hy - 13, 18, 12), C_BRAND)
    c.circle(hx - 4, hy - 9, 2.5, (200, 250, 225, 70))
    c.orrect((hx - 12, hy - 4, 24, 4), C_BRAND, radius=2)

    if spraying:
        gxx = gun[0] + fc * 8
        for _ in range(6):
            c.circle(gxx + random.uniform(0, fc * 20),
                     gun[1] + random.uniform(-8, 8),
                     random.uniform(1, 3), (*C_SPRAY, 180))


# --------------------------------------------------------------------------- #
# Sound (procedural; degrades gracefully with no audio device)
# --------------------------------------------------------------------------- #
class Sound:
    def __init__(self):
        self.ok = False
        self.on = True
        self._cache = {}
        try:
            if not _HAS_NP:
                raise RuntimeError
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.ok = True
        except Exception:
            self.ok = False

    def _tone(self, freq, ms, vol=0.3, shape="sine"):
        n = int(44100 * ms / 1000)
        t = np.linspace(0, ms / 1000, n, endpoint=False)
        wave = np.sign(np.sin(2 * math.pi * freq * t)) if shape == "square" \
            else np.sin(2 * math.pi * freq * t)
        env = np.minimum(1.0, np.linspace(1.0, 0.0, n) * 3)
        data = (wave * env * vol * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.ascontiguousarray(data))

    def play(self, name):
        if not (self.ok and self.on):
            return
        try:
            if name not in self._cache:
                specs = {"jump": (520, 90), "bounce": (300, 160, "square"),
                         "clear": (680, 110), "morph": (240, 120, "square"),
                         "win": (720, 400), "die": (120, 380, "square")}
                self._cache[name] = self._tone(*specs.get(name, (440, 60)))
            self._cache[name].play()
        except Exception:
            self.ok = False


# --------------------------------------------------------------------------- #
# Particles
# --------------------------------------------------------------------------- #
class Particles:
    def __init__(self):
        self.items = []

    def _add(self, x, y, vx, vy, life, r, color, grav=0.0):
        self.items.append([x, y, vx, vy, life, life, r, color, grav])

    def spray(self, x, y, facing):
        for _ in range(3):
            a = random.uniform(-0.35, 0.35)
            sp = random.uniform(220, 380)
            self._add(x, y, facing * sp * math.cos(a), sp * math.sin(a) - 40,
                      random.uniform(0.25, 0.45), random.uniform(2, 4),
                      C_SPRAY, 700)

    def burst(self, x, y, color=C_MOLD):
        for _ in range(16):
            a = random.uniform(0, 6.283)
            sp = random.uniform(60, 200)
            self._add(x, y, math.cos(a) * sp, math.sin(a) * sp - 60,
                      random.uniform(0.4, 0.8), random.uniform(2, 5), color, 500)

    def dust(self, x, y):
        for _ in range(10):
            self._add(x + random.uniform(-8, 8), y, random.uniform(-95, 95),
                      random.uniform(-70, -10), random.uniform(0.3, 0.55),
                      random.uniform(2, 4), (150, 132, 112), 380)

    def bounce(self, x, y):
        for _ in range(18):
            a = random.uniform(3.6, 5.8)
            sp = random.uniform(90, 220)
            self._add(x + random.uniform(-20, 20), y, math.cos(a) * sp,
                      abs(math.sin(a)) * sp * 0.3, random.uniform(0.3, 0.6),
                      random.uniform(2, 5), C_BLOB, 300)

    def sparkle(self, x, y):
        self._add(x + random.uniform(-16, 16), y + random.uniform(-20, 20),
                  random.uniform(-20, 20), random.uniform(-45, -10),
                  random.uniform(0.4, 0.9), random.uniform(1, 3), C_DOOR_OPEN, 0)

    def mote(self):
        self._add(random.uniform(0, WIDTH), random.uniform(120, HEIGHT),
                  random.uniform(-12, 12), random.uniform(-22, -6),
                  random.uniform(2.5, 5.0), random.uniform(1, 2.4),
                  (180, 210, 200), 0)

    def update(self, dt):
        alive = []
        for p in self.items:
            p[4] -= dt
            if p[4] <= 0:
                continue
            p[3] += p[8] * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            alive.append(p)
        self.items = alive

    def draw(self, c):
        for x, y, vx, vy, life, maxlife, r, color, grav in self.items:
            a = max(0, min(255, int(255 * life / maxlife)))
            c.circle(x, y, r, (color[0], color[1], color[2], a))


# --------------------------------------------------------------------------- #
# Blob companion
# --------------------------------------------------------------------------- #
class Blob:
    def __init__(self):
        self.form = FOLLOW
        self.x, self.y = 120.0, 520.0
        self.rect = None
        self.wobble = 0.0

    def solid_rect(self):
        if self.form in (TRAMPOLINE, BRIDGE):
            return self.rect
        return None

    def ladder_rect(self):
        return self.rect if self.form == LADDER else None

    def transform(self, form, player):
        self.form = form
        feet = player.y + player.h
        cx = player.x + player.w / 2
        if form == TRAMPOLINE:
            self.rect = (cx - 42, feet - 4, 84, 20)
        elif form == BRIDGE:
            if player.facing >= 0:
                self.rect = (cx - 24, feet - 2, 250, 18)
            else:
                self.rect = (cx + 24 - 250, feet - 2, 250, 18)
        elif form == LADDER:
            self.rect = (cx - 16, feet - 250, 32, 250)

    def follow(self):
        self.form = FOLLOW
        self.rect = None

    def update(self, dt, player):
        self.wobble += dt * 6
        if self.form == FOLLOW:
            tx = player.x + player.w / 2 - player.facing * 34
            ty = player.y + player.h / 2 - 6
            self.x += (tx - self.x) * min(1.0, dt * 7)
            self.y += (ty - self.y) * min(1.0, dt * 7)

    def draw(self, c, t):
        if self.form == FOLLOW:
            draw_blob(c, self.x, self.y, 15, self.wobble, t)
            return
        x, y, w, h = self.rect
        if self.form == TRAMPOLINE:
            if c.has("trampoline"):
                c.image_rect("trampoline", (x, y - 8, w, h + 8))
                return
            c.orrect((x, y + 9, w, h - 9), C_BLOB_DK, radius=7)
            for i in range(4):
                sx = x + 12 + i * (w - 24) / 3
                c.line(C_BLOB_DK, (sx, y + 9), (sx, y + h - 2), 3)
            c.orrect((x, y - 2, w, 12), C_BLOB, radius=6)
            c.rect((x + 3, y - 1, w - 6, 3), (170, 240, 210, 90), radius=2)
            for ex in (x + 13, x + w - 13):
                c.circle(ex, y + 3, 3, (250, 252, 250))
                c.circle(ex, y + 3, 1.4, (26, 34, 30))
        elif self.form == BRIDGE:
            if c.has("bridge"):
                c.image_rect("bridge", (x, y - 4, w, h + 8))
                return
            c.orrect((x, y, w, h), C_BLOB_DK, radius=7)
            c.rect((x + 2, y + 2, w - 4, 5), C_BLOB, radius=4)
            for i in range(1, int(w // 26)):
                px = x + i * 26
                c.line(C_BLOB_DK, (px, y + 3), (px, y + h - 3), 2)
            for ex in (x + 14, x + 25):
                c.circle(ex, y + 9, 3, (250, 252, 250))
                c.circle(ex, y + 9, 1.4, (26, 34, 30))
        elif self.form == LADDER:
            if c.has("ladder"):
                c.image_rect("ladder", (x - 4, y, w + 8, h))
                return
            c.orrect((x, y, 5, h), C_BLOB_DK, radius=3)
            c.orrect((x + w - 5, y, 5, h), C_BLOB_DK, radius=3)
            for i in range(int(h // 26) + 1):
                ry = y + 12 + i * 26
                c.line(OUTLINE, (x, ry), (x + w, ry), 7)
                c.line(C_BLOB, (x, ry), (x + w, ry), 4)


# --------------------------------------------------------------------------- #
# Player
# --------------------------------------------------------------------------- #
class Player:
    def __init__(self, spawn):
        self.spawn = spawn
        self.w, self.h = 26, 42
        self.reset()

    def reset(self):
        self.x, self.y = float(self.spawn[0]), float(self.spawn[1])
        self.vx = self.vy = 0.0
        self.facing = 1
        self.on_ground = False
        self.on_ladder = False
        self.spraying = False
        self.anim = 0.0
        self.landed = False
        self.bounced = False
        self.bounce_pt = None

    def spray_rect(self):
        if self.facing >= 0:
            return (self.x + self.w, self.y + 6, 56, 30)
        return (self.x - 56, self.y + 6, 56, 30)

    # -- physics ------------------------------------------------------------- #
    def update(self, dt, keys, solids, ladder, snd):
        self.landed = False
        self.bounced = False

        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]

        self.vx = (right - left) * MOVE_SPEED
        if right:
            self.facing = 1
        elif left:
            self.facing = -1

        on_ladder = ladder is not None and overlap(
            self.x, self.y, self.w, self.h, *ladder)
        self.on_ladder = on_ladder
        if on_ladder and (up or down):
            self.vy = (down - up) * CLIMB_SPEED
        else:
            self.vy += GRAVITY * dt
            if on_ladder and not (up or down):
                self.vy = min(self.vy, 40)

        if up and self.on_ground and not on_ladder:
            self.vy = -JUMP_V
            self.on_ground = False
            snd.play("jump")

        prev_bottom = self.y + self.h

        self.x += self.vx * dt
        for (sx, sy, sw, sh, kind) in solids:
            if kind != "ground":
                continue
            if overlap(self.x, self.y, self.w, self.h, sx, sy, sw, sh):
                if self.vx > 0:
                    self.x = sx - self.w
                elif self.vx < 0:
                    self.x = sx + sw
        self.x = max(0, min(WIDTH - self.w, self.x))

        self.y += self.vy * dt
        self.on_ground = False
        for (sx, sy, sw, sh, kind) in solids:
            if not overlap(self.x, self.y, self.w, self.h, sx, sy, sw, sh):
                continue
            if kind == "ground":
                if self.vy > 0:
                    pv = self.vy
                    self.y = sy - self.h
                    self.on_ground = True
                    self.vy = 0
                    if pv > 300:
                        self.landed = True
                elif self.vy < 0:
                    self.y = sy + sh
                    self.vy = 0
            else:
                if self.vy > 0 and prev_bottom <= sy + 6:
                    landing_v = self.vy
                    self.y = sy - self.h
                    self.on_ground = True
                    if kind == TRAMPOLINE and landing_v > 240:
                        self.vy = -TRAMPOLINE_V
                        self.on_ground = False
                        self.bounced = True
                        self.bounce_pt = (self.x + self.w / 2, sy)
                        snd.play("bounce")
                    else:
                        self.vy = 0
                        if landing_v > 300:
                            self.landed = True

        self.spraying = keys[pygame.K_f]
        self.anim += abs(self.vx) * dt

    def draw(self, c, t):
        draw_tyguy(c, self.x, self.y, self.w, self.h, self.facing,
                   abs(self.vx) > 1, self.on_ground, self.anim, self.spraying, t)


# --------------------------------------------------------------------------- #
# Mold target
# --------------------------------------------------------------------------- #
class Mold:
    def __init__(self, x, y):
        self.x, self.y, self.r = float(x), float(y), 20.0
        rng = random.Random(int(x) * 131 + int(y))
        self.blobs = [(rng.uniform(-1, 1), rng.uniform(-1, 1),
                       rng.uniform(0.45, 0.8)) for _ in range(5)]
        self.spores = [(rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7))
                       for _ in range(6)]
        self.phase = rng.uniform(0, 6.283)

    def draw(self, c, t):
        r = self.r
        if c.has("mold"):
            side = r * 3.2
            c.image_rect("mold", (self.x - side / 2, self.y - side / 2, side, side))
            return
        c.glow(self.x, self.y, r * 1.4, C_MOLD_DK, 45)
        for dx, dy, rr in self.blobs:
            c.circle(self.x + dx * r * 0.55, self.y + dy * r * 0.55,
                     r * rr, (C_MOLD_DK[0], C_MOLD_DK[1], C_MOLD_DK[2], 210))
        c.ocircle(self.x, self.y, r, C_MOLD, ol=2)
        c.circle(self.x - r * 0.3, self.y - r * 0.35, r * 0.3, (168, 208, 120, 150))
        for sx, sy in self.spores:
            c.circle(self.x + sx * r, self.y + sy * r, max(1, r * 0.09), C_MOLD_DK)
        for k in range(3):
            ang = t * 1.1 + self.phase + k * 2.1
            px = self.x + math.cos(ang) * (r + 6)
            py = self.y + math.sin(ang * 1.3) * (r + 4) - 2
            c.circle(px, py, 1.6, (150, 190, 110, 150))


# --------------------------------------------------------------------------- #
# Level
# --------------------------------------------------------------------------- #
def build_level():
    solids = [
        (0, 560, 380, 80, "ground"),
        (560, 560, 400, 80, "ground"),
        (620, 340, 340, 24, "oneway"),
        (300, 452, 90, 20, "oneway"),
    ]
    molds = [Mold(190, 540), Mold(690, 540), Mold(770, 320)]
    door = (904, 300, 34, 40)
    spawn = (60, 500)
    return solids, molds, door, spawn


# --------------------------------------------------------------------------- #
# Game
# --------------------------------------------------------------------------- #
class Game:
    def __init__(self, screen, snd):
        self.screen = screen
        self.snd = snd
        self.big = pygame.font.SysFont("arialblack,arial", 62, bold=True)
        self.mid = pygame.font.SysFont("arial", 26, bold=True)
        self.small = pygame.font.SysFont("arial", 19)
        self.tiny = pygame.font.SysFont("arial", 15, bold=True)
        self.scene = pygame.Surface((SW, SH)).convert()
        here = os.path.dirname(os.path.abspath(__file__))
        self.assets = AssetPack(os.path.join(here, "assets"))
        self.cv = Canvas(self.scene, SS, self.assets)
        self.hq = True
        self.grain = self._make_grain()
        self.particles = Particles()
        self.reset()
        self.bg = self._make_bg()
        self.plat = self._make_platforms()
        self.state = STATE_MENU

    # -- pre-rendered assets ------------------------------------------------- #
    def _make_grain(self):
        if not _HAS_NP:
            return []
        out = []
        rng = np.random.default_rng(7)
        for _ in range(6):
            n = rng.integers(0, 15, (WIDTH, HEIGHT, 1)).repeat(3, 2).astype("uint8")
            out.append(pygame.surfarray.make_surface(n).convert())
        return out

    def _vignette(self):
        v = pygame.Surface((80, 80), pygame.SRCALPHA)
        md = math.hypot(40, 40)
        for yy in range(80):
            for xx in range(80):
                d = math.hypot(xx - 40, yy - 40) / md
                a = int(max(0.0, (d - 0.5) / 0.5) ** 1.5 * 150)
                v.set_at((xx, yy), (0, 0, 0, a))
        return pygame.transform.smoothscale(v, (SW, SH))

    def _make_bg(self):
        if "background" in self.assets.imgs:
            return pygame.transform.smoothscale(
                self.assets.imgs["background"], (SW, SH)).convert()
        bg = vgrad(SW, SH, C_SKY_TOP, C_SKY_BOT).convert()
        # soft clouds from noise
        clouds = noise_surf(SW, SH // 2, 120 * SS, 11, 150, 220)
        clouds.set_alpha(26)
        bg.blit(clouds, (0, 0))
        # top light bloom source
        gl = pygame.Surface((SW, SH), pygame.SRCALPHA)
        fcircle(gl, SW // 2, -120 * SS, 360 * SS, (94, 150, 150, 55))
        bg.blit(gl, (0, 0))
        # parallax hills
        for col, amp, base, freq, ph in (
                (C_HILL_FAR, 40, 300, 0.006, 0.0),
                (C_HILL_NEAR, 62, 384, 0.009, 1.3)):
            pts = [(0, SH)]
            for x in range(0, WIDTH + 1, 8):
                yy = base + math.sin(x * freq + ph) * amp \
                    + math.sin(x * freq * 2.3 + ph) * amp * 0.3
                pts.append((x * SS, yy * SS))
            pts.append((SW, SH))
            pygame.draw.polygon(bg, col, pts)
        bg.blit(self._vignette(), (0, 0))
        return bg

    def _make_platforms(self):
        surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        c = Canvas(surf, SS)
        plat_img = self.assets.imgs.get("platform")
        dirt = noise_surf(SW, SH, 6 * SS, 21, 200, 256)
        st = random.getstate()
        for (x, y, w, h, kind) in self.solids:
            sh = pygame.Surface(((w + 26) * SS, (h + 26) * SS), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 70), (0, 0, (w + 26) * SS,
                             (h + 26) * SS), border_radius=16 * SS)
            surf.blit(sh, ((x - 13) * SS, (y - 4) * SS))
            if plat_img is not None:
                surf.blit(pygame.transform.smoothscale(
                    plat_img, (int(w * SS), int(h * SS))), (int(x * SS), int(y * SS)))
                continue
            rad = 9 if kind == "oneway" else 4
            body = vgrad(w * SS, h * SS, (100, 76, 60), (42, 31, 25),
                         radius=rad * SS)
            # apply dirt texture
            tex = dirt.subsurface((x * SS, y * SS, w * SS, h * SS)).copy()
            body.blit(tex, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(body, (x * SS, y * SS))
            c.rect((x, y, w, 7), C_MOSS, radius=rad)
            c.rect((x, y, w, 3), (108, 152, 80), radius=rad)
            random.seed(int(x * 7 + y))
            for _ in range(max(2, w // 55)):
                dxp = x + random.randint(6, max(7, w - 6))
                dl = random.randint(4, 13)
                c.line(C_MOSS, (dxp, y + 5), (dxp, y + 5 + dl), 2)
        random.setstate(st)
        return surf

    def reset(self):
        self.solids, self.molds, self.door, self.spawn = build_level()
        self.player = Player(self.spawn)
        self.blob = Blob()
        self.lives = 3

    def all_solids(self):
        s = list(self.solids)
        bs = self.blob.solid_rect()
        if bs:
            s.append((bs[0], bs[1], bs[2], bs[3], self.blob.form))
        return s

    def cleared(self):
        return len(self.molds) == 0

    # -- update -------------------------------------------------------------- #
    def update(self, dt, keys):
        if self.state != STATE_PLAY:
            return
        self.blob.update(dt, self.player)
        p = self.player
        p.update(dt, keys, self.all_solids(), self.blob.ladder_rect(), self.snd)

        if p.landed:
            self.particles.dust(p.x + p.w / 2, p.y + p.h)
        if p.bounced and p.bounce_pt:
            self.particles.bounce(*p.bounce_pt)
        if random.random() < 0.16:
            self.particles.mote()

        if p.y > HEIGHT + 60:
            self.lives -= 1
            self.snd.play("die")
            if self.lives <= 0:
                self.state = STATE_OVER
                return
            p.reset()
            self.blob.follow()

        if p.spraying:
            sr = p.spray_rect()
            ox = sr[0] if p.facing >= 0 else sr[0] + sr[2]
            self.particles.spray(ox, sr[1] + sr[3] / 2, p.facing)
            for m in list(self.molds):
                if overlap(*sr, m.x - m.r, m.y - m.r, m.r * 2, m.r * 2):
                    m.r -= 95 * dt
                    if m.r <= 3:
                        self.molds.remove(m)
                        self.particles.burst(m.x, m.y)
                        self.snd.play("clear")

        if self.cleared():
            dx, dy, dw, dh = self.door
            if overlap(p.x, p.y, p.w, p.h, dx, dy, dw, dh):
                self.state = STATE_WIN
                self.snd.play("win")

        self.particles.update(dt)

    # -- post-processing (numpy-free: all C-level surface blends) ------------ #
    def _present(self, t):
        # supersample downscale (the AA pass)
        frame = pygame.transform.smoothscale(self.scene, (WIDTH, HEIGHT))
        if self.hq:
            # bloom: keep only bright pixels (subtract threshold), blur, add back
            s = pygame.transform.smoothscale(frame, (WIDTH // 6, HEIGHT // 6))
            s.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_SUB)
            s = pygame.transform.smoothscale(s, (WIDTH // 16, HEIGHT // 16))
            s = pygame.transform.smoothscale(s, (WIDTH, HEIGHT))
            frame.blit(s, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            # cool cinematic tint (also offsets the grain's slight brightening)
            frame.fill((236, 246, 242), special_flags=pygame.BLEND_RGB_MULT)
            # film grain
            if self.grain:
                frame.blit(self.grain[int(t * 24) % len(self.grain)], (0, 0),
                           special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(frame, (0, 0))

    def _mist(self, c, t):
        for i, (by, sp, al) in enumerate(((548, 0.4, 26), (600, 0.7, 34))):
            off = math.sin(t * sp + i) * 40
            fellipse(self.scene, (-120 + off) * SS, (by - 24) * SS,
                     (WIDTH + 240) * SS, 60 * SS, (150, 170, 175, al))

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        scene = self.scene
        c = self.cv
        scene.blit(self.bg, (0, 0))

        if self.state == STATE_MENU:
            draw_blob(c, WIDTH // 2 - 46, HEIGHT // 2 + 172, 26, t * 3, t)
            draw_tyguy(c, WIDTH // 2 + 8, HEIGHT // 2 + 140, 26, 42, -1,
                       False, True, 0, True, t)
            self.particles.draw(c)
            self._present(t)
            self._title("MOLD & BLOB", HEIGHT // 2 - 150)
            self._cc(self.mid, "TyGuy + Blob vs. the mold", HEIGHT // 2 - 92, C_TEXT)
            lines = [
                "Move: Arrows / A D      Jump & climb: Up / W / Space",
                "Spray mold: hold F",
                "Transform Blob:  1 Trampoline   2 Bridge   3 Ladder   E call back",
                "Clear every mold patch, then reach the exit door.",
            ]
            for i, ln in enumerate(lines):
                self._cc(self.small, ln, HEIGHT // 2 - 36 + i * 27, C_TEXT_DIM)
            self._cc(self.mid, "Press Enter to start", HEIGHT // 2 + 96, C_BRAND)
            return

        scene.blit(self.plat, (0, 0))
        self._mist(c, t)

        dx, dy, dw, dh = self.door
        open_ = self.cleared()
        if open_:
            pulse = 0.55 + 0.45 * math.sin(t * 4)
            c.glow(dx + dw / 2, dy + dh / 2, 46, C_DOOR_OPEN, int(130 * pulse))
            if random.random() < 0.3:
                self.particles.sparkle(dx + dw / 2, dy + dh / 2)
        dname = "door_open" if open_ else "door_closed"
        if c.has(dname):
            c.image_rect(dname, (dx - 4, dy - 4, dw + 8, dh + 8))
        else:
            c.orrect((dx, dy, dw, dh), C_DOOR_OPEN if open_ else C_DOOR, radius=6)
            c.orrect((dx + 5, dy + 7, dw - 10, dh - 7), (26, 36, 32), radius=4)
            c.circle(dx + dw - 9, dy + dh / 2, 2.5, (250, 240, 180))

        for m in self.molds:
            m.draw(c, t)
        self.blob.draw(c, t)
        self.player.draw(c, t)
        self.particles.draw(c)

        self._present(t)

        # HUD (native resolution, crisp text)
        if open_:
            self._t(self.tiny, "EXIT", (dx - 6, dy - 20), C_DOOR_OPEN)
        panel = pygame.Surface((252, 76), pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 18, 22, 150), (0, 0, 252, 76),
                         border_radius=12)
        self.screen.blit(panel, (12, 10))
        self._t(self.mid, f"Mold left: {len(self.molds)}", (24, 16), C_TEXT)
        self._t(self.small, f"Blob: {self.blob.form}", (24, 48), C_BRAND)
        for i in range(3):
            col = C_BLOB if i < self.lives else (58, 70, 66)
            fcircle(self.screen, WIDTH - 30 - i * 32, 30, 11, OUTLINE)
            fcircle(self.screen, WIDTH - 30 - i * 32, 30, 9, col)
        self._t(self.tiny, "1 tramp  2 bridge  3 ladder  E call  F spray",
                (WIDTH - 356, 52), C_TEXT_DIM)

        if self.state in (STATE_WIN, STATE_OVER):
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((10, 14, 18, 190))
            self.screen.blit(veil, (0, 0))
            if self.state == STATE_WIN:
                self._title("MOLD-FREE!", HEIGHT // 2 - 60, C_BRAND)
                self._cc(self.mid, "TyGuy & Blob cleaned the whole level.",
                         HEIGHT // 2 + 12, C_TEXT)
            else:
                self._title("WIPED OUT", HEIGHT // 2 - 60, C_DANGER)
                self._cc(self.mid, "Blob will miss you. Try again?",
                         HEIGHT // 2 + 12, C_TEXT)
            self._cc(self.mid, "Press Enter", HEIGHT // 2 + 72, C_BRAND)

    # -- text (native res) --------------------------------------------------- #
    def _t(self, font, msg, pos, col):
        self.screen.blit(font.render(msg, True, col), pos)

    def _cc(self, font, msg, y, col):
        img = font.render(msg, True, col)
        self.screen.blit(img, img.get_rect(center=(WIDTH // 2, y)))

    def _title(self, msg, y, col=C_BRAND):
        shadow = self.big.render(msg, True, (10, 16, 14))
        self.screen.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 3, y + 3)))
        img = self.big.render(msg, True, col)
        self.screen.blit(img, img.get_rect(center=(WIDTH // 2, y)))

    # -- input --------------------------------------------------------------- #
    def on_key(self, key):
        if key == pygame.K_RETURN:
            if self.state in (STATE_MENU, STATE_WIN, STATE_OVER):
                self.reset()
                self.state = STATE_PLAY
            return
        if key == pygame.K_g:
            self.hq = not self.hq
            return
        if self.state != STATE_PLAY:
            return
        if key == pygame.K_m:
            self.snd.on = not self.snd.on
        elif key == pygame.K_1:
            self.blob.transform(TRAMPOLINE, self.player); self.snd.play("morph")
        elif key == pygame.K_2:
            self.blob.transform(BRIDGE, self.player); self.snd.play("morph")
        elif key == pygame.K_3:
            self.blob.transform(LADDER, self.player); self.snd.play("morph")
        elif key in (pygame.K_e, pygame.K_0):
            self.blob.follow()


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def run(selftest=False):
    if selftest:
        import os
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TyDez — Mold & Blob")
    clock = pygame.time.Clock()
    snd = Sound()
    game = Game(screen, snd)

    if selftest:
        class _Keys(dict):
            def __missing__(self, _):
                return False

        game.on_key(pygame.K_RETURN)

        def ahead_mold(p):
            best = None
            for m in game.molds:
                if p.x < m.x < p.x + 160 and abs(m.y - (p.y + 20)) < 48:
                    if best is None or m.x < best.x:
                        best = m
            return best

        bridged = laddered = False
        for i in range(3000):
            p = game.player
            keys = _Keys()
            keys[pygame.K_f] = True
            m = ahead_mold(p)
            if p.on_ladder and not (p.on_ground and p.y < 400):
                keys[pygame.K_UP] = True
            elif m is not None and (m.x - (p.x + p.w)) <= 44:
                pass
            else:
                keys[pygame.K_RIGHT] = True
            if not bridged and 344 <= p.x <= 366:
                game.on_key(pygame.K_2); bridged = True
            if bridged and not laddered and p.x >= 735 and p.y > 480:
                game.on_key(pygame.K_3); laddered = True
            game.update(1 / FPS, keys)
            game.draw(i / FPS)
            if game.state == STATE_WIN:
                break

        assert game.state == STATE_WIN, \
            "level not completed (state=%s mold_left=%d)" % (game.state, len(game.molds))
        game.on_key(pygame.K_RETURN)
        pygame.quit()
        print("selftest OK — solved level in %d frames (%.1fs), mold cleared, restart OK"
              % (i, i / FPS))
        return

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.on_key(e.key)
        game.update(dt, pygame.key.get_pressed())
        game.draw(pygame.time.get_ticks() / 1000.0)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    run(selftest="--selftest" in sys.argv)
