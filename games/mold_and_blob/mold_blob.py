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
    M ......................... toggle sound      Esc ... quit

Run
    pip install pygame numpy
    python3 mold_blob.py

Headless smoke test (no window):
    python3 mold_blob.py --selftest
"""

import math
import random
import sys

import pygame

try:
    import pygame.gfxdraw as _gfx
    _HAS_GFX = True
except Exception:
    _HAS_GFX = False

# --------------------------------------------------------------------------- #
# Config / palette
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 960, 640
FPS = 60

C_SKY_TOP = (40, 54, 66)
C_SKY_BOT = (17, 24, 31)
C_HILL_FAR = (30, 44, 53)
C_HILL_NEAR = (23, 35, 43)
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


# --------------------------------------------------------------------------- #
# Drawing helpers (anti-aliased shapes, outlines, gradients, glows)
# --------------------------------------------------------------------------- #
def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def fcircle(s, cx, cy, r, color):
    cx, cy, r = int(cx), int(cy), int(r)
    if r < 1:
        return
    if _HAS_GFX:
        _gfx.filled_circle(s, cx, cy, r, color)
        _gfx.aacircle(s, cx, cy, r, color)
    else:
        pygame.draw.circle(s, color, (cx, cy), r)


def ocircle(s, cx, cy, r, color, ol=2):
    fcircle(s, cx, cy, r + ol, OUTLINE)
    fcircle(s, cx, cy, r, color)


def orrect(s, rect, color, radius=4, ol=2):
    x, y, w, h = [int(v) for v in rect]
    pygame.draw.rect(s, OUTLINE, (x - ol, y - ol, w + 2 * ol, h + 2 * ol),
                     border_radius=radius + ol)
    pygame.draw.rect(s, color, (x, y, w, h), border_radius=radius)


def ellipse_o(s, cx, cy, rx, ry, color, ol=2):
    pygame.draw.ellipse(s, OUTLINE,
                        (int(cx - rx - ol), int(cy - ry - ol),
                         int(2 * (rx + ol)), int(2 * (ry + ol))))
    pygame.draw.ellipse(s, color,
                        (int(cx - rx), int(cy - ry), int(2 * rx), int(2 * ry)))


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


_cache = {}


def glow(r, color, strength=110):
    key = ("g", r, color, strength)
    g = _cache.get(key)
    if g is None:
        g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -2):
            a = int(strength * (1 - i / r) ** 2)
            fcircle(g, r, r, i, (color[0], color[1], color[2], a))
        _cache[key] = g
    return g


def soft_shadow(w, h):
    key = ("s", w, h)
    g = _cache.get(key)
    if g is None:
        g = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in (0, 2, 4):
            pygame.draw.ellipse(g, (0, 0, 0, 42),
                                (i, i, max(1, w - 2 * i), max(1, h - 2 * i)))
        _cache[key] = g
    return g


# --------------------------------------------------------------------------- #
# Character illustrations (shared so the menu can show them too)
# --------------------------------------------------------------------------- #
def draw_blob(s, cx, cy, r, wobble, t):
    sq = math.sin(wobble) * 0.12
    rx, ry = r * (1 + sq), r * (1 - sq)
    sh = soft_shadow(int(rx * 2.4), 9)
    s.blit(sh, (cx - sh.get_width() / 2, cy + ry - 3))
    gl = glow(int(r * 1.7), C_BLOB, 55)
    s.blit(gl, (cx - gl.get_width() / 2, cy - gl.get_height() / 2))
    ellipse_o(s, cx, cy, rx, ry, C_BLOB)
    fcircle(s, cx, cy - ry * 0.32, rx * 0.72, (150, 236, 202, 55))
    fcircle(s, cx - rx * 0.34, cy - ry * 0.42, r * 0.28, (224, 250, 236, 165))
    blink = (t * 0.9 % 3.0) < 0.13
    for side in (-1, 1):
        exx, eyy = cx + side * r * 0.34, cy - 2
        if blink:
            pygame.draw.line(s, (20, 30, 28), (exx - 3, eyy), (exx + 3, eyy), 2)
        else:
            fcircle(s, exx, eyy, r * 0.26, (250, 252, 250))
            fcircle(s, exx + 1, eyy + 0.5, r * 0.12, (26, 34, 30))
    if not blink:
        pygame.draw.arc(s, (26, 60, 48),
                        (int(cx - 5), int(cy + 1), 10, 7), 3.7, 5.7, 2)


def draw_tyguy(s, x, y, w, h, facing, moving, on_ground, anim, spraying, t):
    cx = x + w / 2
    feet = y + h
    fc = 1 if facing >= 0 else -1
    walk = math.sin(anim * 0.045) if (moving and on_ground) else 0.0

    if on_ground:
        sh = soft_shadow(int(w * 1.9), 9)
        s.blit(sh, (cx - sh.get_width() / 2, feet - 4))

    # backpack tank
    orrect(s, (cx - fc * 13 - 5, y + 9, 11, 20), C_BRAND_DK, radius=5)
    fcircle(s, cx - fc * 13, y + 8, 3, (30, 46, 40))

    # legs (walk cycle)
    hip = (cx, y + 29)
    sw = 5 * walk
    for foot in ((cx - 4 + sw, feet), (cx + 4 - sw, feet)):
        pygame.draw.line(s, OUTLINE, hip, foot, 9)
        pygame.draw.line(s, (52, 66, 60), hip, foot, 6)
        ocircle(s, foot[0], foot[1] - 2, 3.5, (40, 52, 48), ol=1)

    # torso
    orrect(s, (x + 2, y + 12, w - 4, 19), C_BRAND_DK, radius=6)
    pygame.draw.rect(s, C_BRAND, (int(x + 4), int(y + 13), int(w - 8), 8),
                     border_radius=5)
    # chest "T" emblem
    fcircle(s, cx, y + 22, 5, (22, 42, 34))
    pygame.draw.line(s, (210, 245, 228), (cx - 3, y + 20), (cx + 3, y + 20), 2)
    pygame.draw.line(s, (210, 245, 228), (cx, y + 20), (cx, y + 25), 2)

    # arm + spray gun (raised while spraying)
    shoulder = (cx + fc * 5, y + 17)
    gun = (cx + fc * (w / 2 + 7), y + 17 - (5 if spraying else 0))
    pygame.draw.line(s, OUTLINE, shoulder, gun, 8)
    pygame.draw.line(s, C_SKIN, shoulder, gun, 5)
    orrect(s, (gun[0] - 4, gun[1] - 4, 8, 8), (70, 80, 76), radius=2)

    # head + face
    hx, hy = cx, y + 7
    ocircle(s, hx, hy, 8, C_SKIN)
    for side in (-1, 1):
        fcircle(s, hx + fc * 2 + side * 3, hy - 1, 1.5, (30, 32, 30))
    pygame.draw.arc(s, (150, 90, 70), (int(hx - 4), int(hy + 1), 8, 6), 3.7, 5.7, 2)
    # hard hat
    pygame.draw.ellipse(s, OUTLINE, (int(hx - 11), int(hy - 14), 22, 15))
    pygame.draw.ellipse(s, C_BRAND, (int(hx - 9), int(hy - 13), 18, 12))
    orrect(s, (hx - 12, hy - 4, 24, 4), C_BRAND, radius=2)

    if spraying:
        gx = gun[0] + fc * 8
        for _ in range(6):
            fcircle(s, gx + random.uniform(0, fc * 20),
                    gun[1] + random.uniform(-8, 8), random.uniform(1, 3),
                    (*C_SPRAY, 180))


# --------------------------------------------------------------------------- #
# Sound (procedural; degrades gracefully with no audio device)
# --------------------------------------------------------------------------- #
class Sound:
    def __init__(self):
        self.ok = False
        self.on = True
        self._cache = {}
        try:
            import numpy  # noqa: F401
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.ok = True
        except Exception:
            self.ok = False

    def _tone(self, freq, ms, vol=0.3, shape="sine"):
        import numpy as np
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

    def draw(self, s):
        for x, y, vx, vy, life, maxlife, r, color, grav in self.items:
            a = max(0, min(255, int(255 * life / maxlife)))
            fcircle(s, x, y, r, (color[0], color[1], color[2], a))


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

    def draw(self, s, t):
        if self.form == FOLLOW:
            draw_blob(s, self.x, self.y, 15, self.wobble, t)
            return
        x, y, w, h = self.rect
        if self.form == TRAMPOLINE:
            orrect(s, (x, y + 9, w, h - 9), C_BLOB_DK, radius=7)
            for i in range(4):
                sx = x + 12 + i * (w - 24) / 3
                pygame.draw.line(s, C_BLOB_DK, (sx, y + 9), (sx, y + h - 2), 3)
            orrect(s, (x, y - 2, w, 12), C_BLOB, radius=6)
            for ex in (x + 13, x + w - 13):
                fcircle(s, ex, y + 3, 3, (250, 252, 250))
                fcircle(s, ex, y + 3, 1.4, (26, 34, 30))
        elif self.form == BRIDGE:
            orrect(s, (x, y, w, h), C_BLOB_DK, radius=7)
            pygame.draw.rect(s, C_BLOB, (int(x + 2), int(y + 2), int(w - 4), 5),
                             border_radius=4)
            for i in range(1, int(w // 26)):
                px = x + i * 26
                pygame.draw.line(s, C_BLOB_DK, (px, y + 3), (px, y + h - 3), 2)
            for ex in (x + 14, x + 25):
                fcircle(s, ex, y + 9, 3, (250, 252, 250))
                fcircle(s, ex, y + 9, 1.4, (26, 34, 30))
        elif self.form == LADDER:
            orrect(s, (x, y, 5, h), C_BLOB_DK, radius=3)
            orrect(s, (x + w - 5, y, 5, h), C_BLOB_DK, radius=3)
            for i in range(int(h // 26) + 1):
                ry = int(y + 12 + i * 26)
                pygame.draw.line(s, OUTLINE, (x, ry), (x + w, ry), 7)
                pygame.draw.line(s, C_BLOB, (x, ry), (x + w, ry), 4)


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

        # ladder climbing overrides gravity
        on_ladder = ladder is not None and overlap(
            self.x, self.y, self.w, self.h, *ladder)
        self.on_ladder = on_ladder
        if on_ladder and (up or down):
            self.vy = (down - up) * CLIMB_SPEED
        else:
            self.vy += GRAVITY * dt
            if on_ladder and not (up or down):
                self.vy = min(self.vy, 40)  # cling gently

        # jump
        if up and self.on_ground and not on_ladder:
            self.vy = -JUMP_V
            self.on_ground = False
            snd.play("jump")

        prev_bottom = self.y + self.h

        # -- horizontal move + resolve (only full 'ground' blocks sideways)
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

        # -- vertical move + resolve
        self.y += self.vy * dt
        self.on_ground = False
        for (sx, sy, sw, sh, kind) in solids:
            if not overlap(self.x, self.y, self.w, self.h, sx, sy, sw, sh):
                continue
            if kind == "ground":                     # solid on every side
                if self.vy > 0:
                    pv = self.vy
                    self.y = sy - self.h
                    self.on_ground = True
                    self.vy = 0
                    if pv > 300:
                        self.landed = True
                elif self.vy < 0:                    # rising: bonk head
                    self.y = sy + sh
                    self.vy = 0
            else:                                    # one-way: land from above
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

    def draw(self, s, t):
        draw_tyguy(s, self.x, self.y, self.w, self.h, self.facing,
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

    def draw(self, s, t):
        r = self.r
        for dx, dy, rr in self.blobs:
            fcircle(s, self.x + dx * r * 0.55, self.y + dy * r * 0.55,
                    r * rr, (C_MOLD_DK[0], C_MOLD_DK[1], C_MOLD_DK[2], 210))
        ocircle(s, self.x, self.y, r, C_MOLD, ol=2)
        fcircle(s, self.x - r * 0.3, self.y - r * 0.35, r * 0.3, (168, 208, 120, 150))
        for sx, sy in self.spores:
            fcircle(s, self.x + sx * r, self.y + sy * r, max(1, r * 0.09), C_MOLD_DK)
        # drifting spores
        for k in range(3):
            ang = t * 1.1 + self.phase + k * 2.1
            px = self.x + math.cos(ang) * (r + 6)
            py = self.y + math.sin(ang * 1.3) * (r + 4) - 2
            fcircle(s, px, py, 1.6, (150, 190, 110, 150))


# --------------------------------------------------------------------------- #
# Level
# --------------------------------------------------------------------------- #
def build_level():
    solids = [
        (0, 560, 380, 80, "ground"),      # left ground
        (560, 560, 400, 80, "ground"),    # right ground (pit between 380..560)
        (620, 340, 340, 24, "oneway"),    # upper-right ledge
        (300, 452, 90, 20, "oneway"),     # little floating step
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
        self.bg = self._make_bg()
        self.particles = Particles()
        self.reset()
        self.plat = self._make_platforms()
        self.state = STATE_MENU

    def _vignette(self):
        v = pygame.Surface((80, 80), pygame.SRCALPHA)
        md = math.hypot(40, 40)
        for yy in range(80):
            for xx in range(80):
                d = math.hypot(xx - 40, yy - 40) / md
                a = int(max(0.0, (d - 0.5) / 0.5) ** 1.5 * 150)
                v.set_at((xx, yy), (0, 0, 0, a))
        return pygame.transform.smoothscale(v, (WIDTH, HEIGHT))

    def _make_bg(self):
        bg = vgrad(WIDTH, HEIGHT, C_SKY_TOP, C_SKY_BOT).convert()
        gl = glow(360, (94, 150, 150), 55)
        bg.blit(gl, (WIDTH // 2 - 360, -250))
        for col, amp, base, freq, ph in (
                (C_HILL_FAR, 40, 300, 0.006, 0.0),
                (C_HILL_NEAR, 62, 384, 0.009, 1.3)):
            pts = [(0, HEIGHT)]
            for x in range(0, WIDTH + 1, 10):
                yy = base + math.sin(x * freq + ph) * amp \
                    + math.sin(x * freq * 2.3 + ph) * amp * 0.3
                pts.append((x, yy))
            pts.append((WIDTH, HEIGHT))
            pygame.draw.polygon(bg, col, pts)
        bg.blit(self._vignette(), (0, 0))
        return bg

    def _make_platforms(self):
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        st = random.getstate()
        for (x, y, w, h, kind) in self.solids:
            sh = pygame.Surface((w + 26, h + 26), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 70), (0, 0, w + 26, h + 26),
                             border_radius=16)
            surf.blit(sh, (x - 13, y - 4))
            rad = 9 if kind == "oneway" else 4
            surf.blit(vgrad(w, h, (98, 74, 58), (44, 32, 26), radius=rad), (x, y))
            pygame.draw.rect(surf, C_MOSS, (x, y, w, 7), border_radius=rad)
            pygame.draw.rect(surf, (108, 152, 80), (x, y, w, 3), border_radius=rad)
            random.seed(int(x * 7 + y))
            for _ in range(max(2, w // 55)):
                dxp = x + random.randint(6, max(7, w - 6))
                dl = random.randint(4, 13)
                pygame.draw.line(surf, C_MOSS, (dxp, y + 5), (dxp, y + 5 + dl), 2)
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

        # fell into a pit / off the world
        if p.y > HEIGHT + 60:
            self.lives -= 1
            self.snd.play("die")
            if self.lives <= 0:
                self.state = STATE_OVER
                return
            p.reset()
            self.blob.follow()

        # spraying mold
        if p.spraying:
            sr = p.spray_rect()
            origin = (sr[0] if p.facing >= 0 else sr[0] + sr[2], sr[1] + sr[3] / 2)
            self.particles.spray(origin[0], origin[1], p.facing)
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

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        s = self.screen
        s.blit(self.bg, (0, 0))

        if self.state == STATE_MENU:
            self._title("MOLD & BLOB", HEIGHT // 2 - 150)
            self._c(self.mid, "TyGuy + Blob vs. the mold", HEIGHT // 2 - 92, C_TEXT)
            lines = [
                "Move: Arrows / A D      Jump & climb: Up / W / Space",
                "Spray mold: hold F",
                "Transform Blob:  1 Trampoline   2 Bridge   3 Ladder   E call back",
                "Clear every mold patch, then reach the exit door.",
            ]
            for i, ln in enumerate(lines):
                self._c(self.small, ln, HEIGHT // 2 - 36 + i * 27, C_TEXT_DIM)
            self._c(self.mid, "Press Enter to start", HEIGHT // 2 + 96, C_BRAND)
            draw_blob(s, WIDTH // 2 - 46, HEIGHT // 2 + 172, 26, t * 3, t)
            draw_tyguy(s, WIDTH // 2 + 8, HEIGHT // 2 + 140, 26, 42, -1,
                       False, True, 0, True, t)
            return

        s.blit(self.plat, (0, 0))

        # exit door (glows + sparkles once mold is cleared)
        dx, dy, dw, dh = self.door
        open_ = self.cleared()
        if open_:
            pulse = 0.55 + 0.45 * math.sin(t * 4)
            gl = glow(46, C_DOOR_OPEN, int(130 * pulse))
            s.blit(gl, (dx + dw / 2 - 46, dy + dh / 2 - 46))
            if random.random() < 0.3:
                self.particles.sparkle(dx + dw / 2, dy + dh / 2)
        orrect(s, (dx, dy, dw, dh), C_DOOR_OPEN if open_ else C_DOOR, radius=6)
        orrect(s, (dx + 5, dy + 7, dw - 10, dh - 7), (26, 36, 32), radius=4)
        fcircle(s, dx + dw - 9, dy + dh / 2, 2.5, (250, 240, 180))
        if open_:
            self._t(self.tiny, "EXIT", (dx - 6, dy - 20), C_DOOR_OPEN)

        for m in self.molds:
            m.draw(s, t)
        self.blob.draw(s, t)
        self.player.draw(s, t)
        self.particles.draw(s)

        # HUD panel
        panel = pygame.Surface((252, 76), pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 18, 22, 150), (0, 0, 252, 76),
                         border_radius=12)
        s.blit(panel, (12, 10))
        self._t(self.mid, f"Mold left: {len(self.molds)}", (24, 16), C_TEXT)
        self._t(self.small, f"Blob: {self.blob.form}", (24, 48), C_BRAND)
        for i in range(3):
            col = C_BLOB if i < self.lives else (58, 70, 66)
            ocircle(s, WIDTH - 30 - i * 32, 30, 9, col)
        self._t(self.tiny, "1 tramp  2 bridge  3 ladder  E call  F spray",
                (WIDTH - 356, 52), C_TEXT_DIM)

        if self.state in (STATE_WIN, STATE_OVER):
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((10, 14, 18, 190))
            s.blit(veil, (0, 0))
            if self.state == STATE_WIN:
                self._title("MOLD-FREE!", HEIGHT // 2 - 60, C_BRAND)
                self._c(self.mid, "TyGuy & Blob cleaned the whole level.",
                        HEIGHT // 2 + 12, C_TEXT)
            else:
                self._title("WIPED OUT", HEIGHT // 2 - 60, C_DANGER)
                self._c(self.mid, "Blob will miss you. Try again?",
                        HEIGHT // 2 + 12, C_TEXT)
            self._c(self.mid, "Press Enter", HEIGHT // 2 + 72, C_BRAND)

    def _t(self, font, msg, pos, col):
        self.screen.blit(font.render(msg, True, col), pos)

    def _c(self, font, msg, y, col):
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

        game.on_key(pygame.K_RETURN)                   # menu -> play

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
