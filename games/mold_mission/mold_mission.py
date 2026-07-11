#!/usr/bin/env python3
"""Mold Mission — a Mega Man-style run-and-gun (TyDez / Boise Mold Removal).

You are the Mold Technician. Run, jump, and blast mold with your Disinfect
Blaster. Hold fire to CHARGE a bigger shot (like Mega Man's buster). Clear the
Basement of Spore Bots, Mold Crawlers and Toxic Sprayers, then defeat the end
boss MOLDTIUS, the Source of Contamination.

Controls
    Left / Right  (A / D) ..... move
    Up / W / Space ............ jump
    J  (hold to charge) ....... fire Disinfect Blaster  (tap = pew, hold = charge shot)
    L / Left-Shift ............ HEPA Vac Dash (quick dash, briefly invulnerable)
    Enter ..................... start / restart      M sound      Esc quit

All art is drop-in: put transparent PNGs in ./assets (player, sporebot,
moldcrawler, toxicsprayer, boss, shot, shot_charged, toxic, coin, background,
platform). Missing ones fall back to built-in vector art.

Run
    pip install pygame numpy
    python3 mold_mission.py

Headless smoke test (no window):
    python3 mold_mission.py --selftest
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

# --------------------------------------------------------------------------- #
# Config / palette
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 960, 600
FPS = 60
GROUND_Y = 500
LEVEL_W = 3200
BOSS_TRIGGER = 2500
CAM_BOSS = LEVEL_W - WIDTH

C_TEAL = (32, 196, 150)
C_TEAL_DK = (18, 120, 96)
C_TEAL_LT = (120, 236, 200)
C_SHOT = (150, 224, 255)
C_SHOT_DK = (70, 150, 220)
C_CHARGE = (200, 245, 255)
C_MOLD = (120, 176, 70)
C_MOLD_DK = (60, 92, 40)
C_TOXIC = (150, 210, 90)
C_CRAWLER = (40, 46, 40)
C_BOSS = (70, 84, 52)
C_BOSS_DK = (40, 50, 32)
C_COIN = (236, 196, 80)
C_TEXT = (238, 244, 246)
C_DIM = (150, 164, 172)
C_DANGER = (232, 96, 92)
C_HP = (96, 224, 130)
OUTLINE = (14, 20, 20)

GRAVITY = 2400.0
MOVE_SPEED = 250.0
JUMP_V = 760.0
DASH_SPEED = 620.0
DASH_TIME = 0.22
DASH_CD = 0.55

PLAYER_HP = 100
IFRAMES = 1.0
MAX_ENERGY = 100
HP_PACK = 25
ENERGY_CELL = 30
COYOTE = 0.10
SLUDGE_HP = 220

STATE_HQ, STATE_PLAY, STATE_WIN, STATE_OVER = "hq", "play", "win", "over"
STATE_MENU = STATE_HQ  # menu screen is the DesilPower HQ hub


def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


# --------------------------------------------------------------------------- #
# Draw helpers
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


def orrect(s, rect, color, radius=4, ol=2):
    x, y, w, h = [int(v) for v in rect]
    pygame.draw.rect(s, OUTLINE, (x - ol, y - ol, w + 2 * ol, h + 2 * ol),
                     border_radius=radius + ol)
    pygame.draw.rect(s, color, (x, y, w, h), border_radius=radius)


def glow(s, cx, cy, r, color, strength=120):
    surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for i in range(int(r), 0, -2):
        a = int(strength * (1 - i / r) ** 2)
        fcircle(surf, r, r, i, (color[0], color[1], color[2], a))
    s.blit(surf, (cx - r, cy - r))


# --------------------------------------------------------------------------- #
# Assets (drop-in PNGs override the vector art)
# --------------------------------------------------------------------------- #
ASSET_NAMES = ("player", "player_run", "player_jump", "player_fall",
               "player_dash", "player_crouch", "player_shoot", "player_hurt",
               "sporebot", "moldcrawler", "toxicsprayer", "moldbat", "boss",
               "shot", "shot_charged", "toxic", "coin", "background", "platform")


class AssetPack:
    def __init__(self, folder):
        self.imgs = {}
        self._scaled = {}
        for name in ASSET_NAMES:
            p = os.path.join(folder, name + ".png")
            if os.path.isfile(p):
                try:
                    self.imgs[name] = pygame.image.load(p).convert_alpha()
                except Exception:
                    pass

    def has(self, name):
        return name in self.imgs

    def blit_fit(self, s, name, cx, cy, w, h, flip=False):
        """Blit asset fit inside (w,h) box centered at (cx,cy), aspect kept."""
        img = self.imgs[name]
        aw, ah = img.get_size()
        sc = min(w / aw, h / ah)
        dw, dh = max(1, int(aw * sc)), max(1, int(ah * sc))
        key = (name, dw, dh, flip)
        sp = self._scaled.get(key)
        if sp is None:
            sp = pygame.transform.smoothscale(img, (dw, dh))
            if flip:
                sp = pygame.transform.flip(sp, True, False)
            self._scaled[key] = sp
        s.blit(sp, (int(cx - dw / 2), int(cy - dh / 2)))


# --------------------------------------------------------------------------- #
# Particles
# --------------------------------------------------------------------------- #
class Particles:
    def __init__(self):
        self.items = []

    def _add(self, x, y, vx, vy, life, r, color, grav=0.0):
        self.items.append([x, y, vx, vy, life, life, r, color, grav])

    def spark(self, x, y, color=C_SHOT, n=8, spd=260):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            v = random.uniform(spd * 0.3, spd)
            self._add(x, y, math.cos(a) * v, math.sin(a) * v,
                      random.uniform(0.2, 0.45), random.uniform(2, 4), color, 200)

    def splat(self, x, y, color=C_MOLD, n=16):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            v = random.uniform(60, 260)
            self._add(x, y, math.cos(a) * v, math.sin(a) * v - 60,
                      random.uniform(0.4, 0.9), random.uniform(2, 6), color, 600)

    def smoke(self, x, y, n=8):
        for _ in range(n):
            self._add(x + random.uniform(-6, 6), y, random.uniform(-40, 40),
                      random.uniform(-70, -20), random.uniform(0.5, 1.0),
                      random.uniform(4, 9), (150, 155, 150), -40)

    def muzzle(self, x, y, facing):
        for _ in range(6):
            self._add(x, y, facing * random.uniform(120, 340),
                      random.uniform(-60, 60), random.uniform(0.1, 0.25),
                      random.uniform(2, 4), C_CHARGE, 0)

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

    def draw(self, s, cam):
        for x, y, vx, vy, life, maxlife, r, color, grav in self.items:
            a = max(0, min(255, int(255 * life / maxlife)))
            fcircle(s, x - cam, y, r, (color[0], color[1], color[2], a))


# --------------------------------------------------------------------------- #
# Projectiles
# --------------------------------------------------------------------------- #
class Shot:
    def __init__(self, x, y, vx, dmg, level, hostile=False):
        self.x, self.y, self.vx = x, y, vx
        self.dmg = dmg
        self.level = level          # 0 normal, 1 mid, 2 full (player); -1 toxic
        self.hostile = hostile
        self.r = 6 + level * 5 if level >= 0 else 10
        self.dead = False

    def rect(self):
        return (self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < -40 or self.x > LEVEL_W + 40:
            self.dead = True

    def draw(self, s, cam, assets):
        sx = self.x - cam
        if self.hostile:
            if assets.has("toxic"):
                assets.blit_fit(s, "toxic", sx, self.y, self.r * 3, self.r * 3)
            else:
                glow(s, sx, self.y, self.r + 6, C_TOXIC, 120)
                fcircle(s, sx, self.y, self.r, C_TOXIC)
                fcircle(s, sx, self.y, self.r * 0.6, C_MOLD_DK)
            return
        name = "shot_charged" if self.level >= 1 else "shot"
        if assets.has(name):
            assets.blit_fit(s, name, sx, self.y, self.r * 3, self.r * 3,
                            flip=self.vx < 0)
        else:
            glow(s, sx, self.y, self.r + 7, C_SHOT, 130)
            fcircle(s, sx, self.y, self.r, C_SHOT)
            fcircle(s, sx, self.y, self.r * 0.55, (245, 252, 255))


# --------------------------------------------------------------------------- #
# Enemies
# --------------------------------------------------------------------------- #
class Enemy:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.vx = 0.0
        self.hit = 0.0
        self.shoot_t = random.uniform(0.8, 2.0)
        self.dead = False
        self.t = random.uniform(0, 6.28)
        self.home_y = float(y)
        self.dive_t = random.uniform(1.5, 3.0)
        self.diving = 0.0
        if kind == "sporebot":
            self.w, self.h, self.hp = 40, 40, 4
            self.vx = -70
            self.dmg = 4
        elif kind == "moldcrawler":
            self.w, self.h, self.hp = 46, 34, 9
            self.dmg = 4
        elif kind == "moldbat":       # flying harassment enemy (V2C5)
            self.w, self.h, self.hp = 36, 26, 3
            self.dmg = 4
        else:  # toxicsprayer
            self.w, self.h, self.hp = 40, 48, 6
            self.dmg = 4

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def update(self, dt, player, shots, parts):
        self.hit = max(0.0, self.hit - dt)
        self.t += dt
        if self.kind == "sporebot":
            self.x += self.vx * dt
            # patrol turn-around on level edges / simple bounds
            if self.x < 60 or self.x > LEVEL_W - 100:
                self.vx *= -1
        elif self.kind == "moldcrawler":
            d = player.x - self.x
            self.x += (30 if d > 0 else -30) * dt
        elif self.kind == "moldbat":
            # circle the player, then dive (V2C5 Mold Bat)
            d = player.x - self.x
            self.x += (1 if d > 0 else -1) * 80 * dt
            self.dive_t -= dt
            if self.dive_t <= 0 and abs(d) < 320 and self.diving <= 0:
                self.diving = 0.6
                self.dive_t = random.uniform(2.0, 3.5)
            if self.diving > 0:
                self.diving -= dt
                self.y += (player.y - self.y) * min(1.0, dt * 4)
            else:
                self.y += (self.home_y + math.sin(self.t * 3) * 26 - self.y) \
                    * min(1.0, dt * 3)
        else:  # toxicsprayer shoots
            self.shoot_t -= dt
            if self.shoot_t <= 0 and abs(player.x - self.x) < 520:
                self.shoot_t = random.uniform(1.6, 2.6)
                face = 1 if player.x > self.x else -1
                shots.append(Shot(self.x + self.w / 2, self.y + 16,
                                  face * 240, 4, -1, hostile=True))

    def hurt(self, dmg, parts):
        self.hp -= dmg
        self.hit = 0.12
        parts.spark(self.x + self.w / 2, self.y + self.h / 2, C_TEAL_LT, 6, 200)
        if self.hp <= 0:
            self.dead = True
            parts.splat(self.x + self.w / 2, self.y + self.h / 2, C_MOLD, 18)
            return True
        return False

    def draw(self, s, cam, assets):
        x, y = self.x - cam, self.y
        cx, cy = x + self.w / 2, y + self.h / 2
        asset = {"sporebot": "sporebot", "moldcrawler": "moldcrawler",
                 "toxicsprayer": "toxicsprayer", "moldbat": "moldbat"}[self.kind]
        if assets.has(asset):
            assets.blit_fit(s, asset, cx, cy, self.w * 1.5, self.h * 1.5)
        elif self.kind == "moldbat":
            flap = math.sin(self.t * 16) * 6
            for wdir in (-1, 1):
                pygame.draw.polygon(s, C_CRAWLER, [
                    (cx, cy), (cx + wdir * 20, cy - 6 - flap),
                    (cx + wdir * 16, cy + 8)])
            fcircle(s, cx, cy, self.h * 0.5, C_MOLD_DK)
            fcircle(s, cx - 5, cy - 2, 3, (200, 255, 160))
            fcircle(s, cx + 5, cy - 2, 3, (200, 255, 160))
            fcircle(s, cx - 5, cy - 2, 1.5, (20, 30, 20))
            fcircle(s, cx + 5, cy - 2, 1.5, (20, 30, 20))
        elif self.kind == "sporebot":
            for a in range(8):
                ang = a / 8 * 6.283
                fcircle(s, cx + math.cos(ang) * self.w * 0.5,
                        cy + math.sin(ang) * self.w * 0.5, 4, C_MOLD_DK)
            fcircle(s, cx, cy, self.w * 0.44, C_MOLD)
            fcircle(s, cx - 6, cy - 4, 4, (250, 250, 250))
            fcircle(s, cx + 6, cy - 4, 4, (250, 250, 250))
            fcircle(s, cx - 6, cy - 4, 2, (20, 20, 20))
            fcircle(s, cx + 6, cy - 4, 2, (20, 20, 20))
        elif self.kind == "moldcrawler":
            pygame.draw.ellipse(s, C_CRAWLER,
                                (int(x), int(y + 6), self.w, self.h))
            fcircle(s, cx - 7, cy, 4, (230, 240, 230))
            fcircle(s, cx + 7, cy, 4, (230, 240, 230))
        else:
            orrect(s, (x + 6, y + 10, self.w - 12, self.h - 10), C_TEAL_DK, 5)
            fcircle(s, cx, y + 10, self.w * 0.4, C_CRAWLER)
            fcircle(s, cx, y + 10, self.w * 0.22, (120, 200, 120))
        if self.hit > 0:
            fl = pygame.Surface((self.w * 2, self.h * 2), pygame.SRCALPHA)
            fcircle(fl, self.w, self.h, self.w * 0.7, (255, 255, 255, 120))
            s.blit(fl, (cx - self.w, cy - self.h))


# --------------------------------------------------------------------------- #
# Boss — MOLDTIUS
# --------------------------------------------------------------------------- #
class Boss:
    """The Sludge King — first Mold General. 3 phases, chest-valve weak point."""
    NAME = "SLUDGE KING"

    def __init__(self):
        self.w, self.h = 260, 300
        self.x = LEVEL_W - self.w - 40
        self.y = GROUND_Y - self.h
        self.hp = self.maxhp = SLUDGE_HP
        self.hit = 0.0
        self.t = 0.0
        self.attack_t = 1.6
        self.weak_open = 0.0     # chest valve open window
        self.summon_t = 4.0
        self.slam = 0.0
        self.mode = 0
        self.dead = False
        self.bob = 0.0

    def phase(self):
        f = self.hp / self.maxhp
        return 3 if f <= 0.3 else (2 if f <= 0.7 else 1)

    def rect(self):
        return (self.x + 30, self.y + 40 + self.bob, self.w - 60, self.h - 70)

    def weak_rect(self):
        return (self.x + self.w * 0.34, self.y + self.h * 0.42 + self.bob,
                self.w * 0.30, self.h * 0.20)

    def update(self, dt, player, shots, parts, enemies):
        self.t += dt
        self.hit = max(0.0, self.hit - dt)
        self.weak_open = max(0.0, self.weak_open - dt)
        self.slam = max(0.0, self.slam - dt)
        ph = self.phase()
        self.bob = math.sin(self.t * (1.3 + 0.35 * ph)) * 12
        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = 0.9 if ph == 3 else (1.3 if ph == 2 else 1.7)
            self.mode ^= 1
            mx, my = self.x + 50, self.y + self.h * 0.42 + self.bob
            if self.mode == 0:                      # spore spread
                n = 3 if ph >= 2 else 2
                for i in range(n):
                    ang = math.atan2((player.y + 20) - my, player.x - mx)
                    ang += (i - (n - 1) / 2) * 0.30
                    sp = 300 + ph * 20
                    sh = Shot(mx, my, math.cos(ang) * sp, 4, -1, hostile=True)
                    sh.vy = math.sin(ang) * sp
                    shots.append(sh)
            else:                                   # ground slam
                self.slam = 0.3
                parts.splat(self.x + 40, GROUND_Y, C_MOLD, 22)
                for d in (-1, 1):
                    sh = Shot(self.x + self.w * 0.4, GROUND_Y - 14, d * 260,
                              4, -1, hostile=True)
                    sh.vy = 0
                    shots.append(sh)
            self.weak_open = 1.8                     # valve opens after each attack
        if ph == 3:                                  # enrage: summon Mold Slimes
            self.summon_t -= dt
            live = len([e for e in enemies if not e.dead])
            if self.summon_t <= 0 and live < 6:
                self.summon_t = 3.0
                sx = max(CAM_BOSS + 40, min(LEVEL_W - 90,
                         player.x + random.choice([-170, 170])))
                enemies.append(Enemy("sporebot", sx, GROUND_Y - 40))
        if self.weak_open > 0:
            parts.spark(self.x + self.w * 0.5, self.y + self.h * 0.52 + self.bob,
                        C_TEAL_LT, 1, 50)

    def hurt(self, dmg, parts):
        self.hp -= dmg
        self.hit = 0.1
        parts.spark(self.x + self.w * 0.5, self.y + self.h * 0.5, C_TEAL_LT, 8, 240)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def draw(self, s, cam, assets):
        x, y = self.x - cam, self.y + self.bob
        cx, cy = x + self.w / 2, y + self.h / 2
        glow(s, cx, cy, self.w * 0.6, (60, 90, 40), 70)
        if self.slam > 0:
            pygame.draw.rect(s, (180, 220, 120), (0, GROUND_Y - 4, WIDTH, 4))
        if assets.has("boss"):
            assets.blit_fit(s, "boss", cx, cy, self.w * 1.15, self.h * 1.15,
                            flip=True)
        else:
            pygame.draw.ellipse(s, C_BOSS_DK, (int(x), int(y + 20), self.w, self.h - 20))
            pygame.draw.ellipse(s, C_BOSS, (int(x + 16), int(y + 30),
                                self.w - 32, self.h - 60))
            random.seed(1)
            for i in range(14):
                bx = x + 30 + random.random() * (self.w - 60)
                by = y + 40 + random.random() * (self.h - 90)
                fcircle(s, bx, by, random.randint(10, 22), C_BOSS_DK)
                fcircle(s, bx, by, 5, (40, 60, 30))
            for ex in (cx - 40, cx + 40):
                fcircle(s, ex, cy - 40, 16, (180, 255, 140))
                fcircle(s, ex, cy - 40, 8, (20, 40, 20))
        # chest valve weak point
        wx, wy, ww, wh = self.weak_rect()
        wx -= cam
        if self.weak_open > 0:
            glow(s, wx + ww / 2, wy + wh / 2, ww * 0.9, (120, 255, 160), 160)
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.4, (150, 255, 180))
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.22, (40, 90, 50))
        else:
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.36, (60, 50, 40))
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.2, (30, 26, 22))
        if self.hit > 0:
            fl = pygame.Surface((self.w * 2, self.h * 2), pygame.SRCALPHA)
            fcircle(fl, self.w, self.h, self.w * 0.55, (255, 255, 255, 90))
            s.blit(fl, (cx - self.w, cy - self.h))


# --------------------------------------------------------------------------- #
# Coin
# --------------------------------------------------------------------------- #
class Coin:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.got = False
        self.t = random.uniform(0, 6.28)

    def draw(self, s, cam, assets, t):
        sx = self.x - cam
        yy = self.y + math.sin(t * 3 + self.t) * 4
        if assets.has("coin"):
            assets.blit_fit(s, "coin", sx, yy, 26, 26)
        else:
            wob = abs(math.cos(t * 3 + self.t))
            orrect(s, (sx - 11 * wob, yy - 11, 22 * wob, 22), C_COIN, radius=11)
            f = pygame.font.SysFont("arial", 14, bold=True)
            if wob > 0.4:
                g = f.render("T", True, (120, 80, 20))
                s.blit(g, g.get_rect(center=(sx, yy)))


class Pickup:
    """Dropped by enemies: 'health' restores HP, 'energy' refills weapon energy."""
    def __init__(self, x, y, kind):
        self.x, self.y, self.kind = float(x), float(y), kind
        self.got = False
        self.t = random.uniform(0, 6.28)

    def draw(self, s, cam, t):
        sx = self.x - cam
        yy = self.y + math.sin(t * 4 + self.t) * 3
        if self.kind == "health":
            col = (232, 96, 92)
            pygame.draw.circle(s, col, (int(sx - 5), int(yy - 2)), 6)
            pygame.draw.circle(s, col, (int(sx + 5), int(yy - 2)), 6)
            pygame.draw.polygon(s, col, [(sx - 11, yy), (sx + 11, yy), (sx, yy + 12)])
        else:
            orrect(s, (sx - 8, yy - 9, 16, 18), (110, 180, 240), radius=3)
            pygame.draw.rect(s, (210, 240, 255), (int(sx - 3), int(yy - 12), 6, 4))


# --------------------------------------------------------------------------- #
# Player
# --------------------------------------------------------------------------- #
class Player:
    def __init__(self):
        self.w, self.h = 34, 54
        self.reset()

    def reset(self):
        self.x, self.y = 80.0, GROUND_Y - self.h
        self.vx = self.vy = 0.0
        self.facing = 1
        self.on_ground = False
        self.maxhp = getattr(self, "maxhp", PLAYER_HP)
        self.maxenergy = getattr(self, "maxenergy", MAX_ENERGY)
        self.speed_mult = getattr(self, "speed_mult", 1.0)
        self.hp = self.maxhp
        self.energy = self.maxenergy
        self.coyote = 0.0
        self.vacuuming = False
        self.iframe = 0.0
        self.fire_prev = False
        self.charge = 0.0
        self.charging = False
        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.anim = 0.0
        self.dead = False
        self.jump_prev = False
        self.jumps = 2          # ground jump + one air (double) jump
        self.wall = 0           # -1 wall on left, 1 wall on right, 0 none
        self.wj_lock = 0.0      # wall-jump horizontal lockout
        self.wj_dir = 0
        self.crouching = False
        self.sliding = False

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def vacuum_rect(self):
        reach = 200
        if self.facing >= 0:
            return (self.x + self.w, self.y - 12, reach, self.h + 24)
        return (self.x - reach, self.y - 12, reach, self.h + 24)

    def hurt(self, dmg, parts):
        if self.iframe > 0 or self.dash_t > 0:
            return
        self.hp -= dmg
        self.iframe = IFRAMES
        parts.spark(self.x + self.w / 2, self.y + self.h / 2, C_DANGER, 10, 260)
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    def update(self, dt, keys, plats, shots, parts, snd):
        self.iframe = max(0.0, self.iframe - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        self.wj_lock = max(0.0, self.wj_lock - dt)

        # dash
        if (keys[pygame.K_l] or keys[pygame.K_LSHIFT]) and self.dash_cd <= 0 \
                and self.dash_t <= 0:
            self.dash_t = DASH_TIME
            self.dash_cd = DASH_CD
            snd.play("dash")

        self.crouching = down and self.on_ground and self.dash_t <= 0
        if self.dash_t > 0:
            self.dash_t -= dt
            self.vx = self.facing * DASH_SPEED
        elif self.wj_lock > 0:
            self.vx = self.wj_dir * MOVE_SPEED * self.speed_mult
        elif self.crouching:
            self.vx = 0.0
        else:
            self.vx = (right - left) * MOVE_SPEED * self.speed_mult
            if right:
                self.facing = 1
            elif left:
                self.facing = -1

        # -- horizontal move + resolve (records wall contact) --
        self.wall = 0
        self.x += self.vx * dt
        self.x = max(0, min(LEVEL_W - self.w, self.x))
        for (px, py, pw, ph) in plats:
            if overlap(self.x, self.y, self.w, self.h, px, py, pw, ph):
                if self.vx > 0:
                    self.x = px - self.w
                    self.wall = 1
                elif self.vx < 0:
                    self.x = px + pw
                    self.wall = -1

        self.vy += GRAVITY * dt
        # wall slide: cling and fall slowly when pressing into a wall
        self.sliding = (not self.on_ground and self.wall != 0 and self.vy > 0
                        and ((right and self.wall == 1) or (left and self.wall == -1)))
        if self.sliding:
            self.vy = min(self.vy, 130)

        # jump: edge-triggered — ground (with coyote time), wall, or air jump
        jump_edge = up and not self.jump_prev
        self.jump_prev = up
        if jump_edge and self.dash_t <= 0:
            if self.on_ground or self.coyote > 0:
                self.vy = -JUMP_V
                self.jumps = 1
                self.coyote = 0.0
                snd.play("jump")
            elif self.wall != 0:
                self.vy = -JUMP_V
                self.wj_dir = -self.wall
                self.wj_lock = 0.18
                self.facing = -self.wall
                self.jumps = 1
                snd.play("jump")
            elif self.jumps > 0:
                self.vy = -JUMP_V * 0.92
                self.jumps -= 1
                snd.play("jump")

        # -- vertical move + resolve --
        self.y += self.vy * dt
        self.on_ground = False
        for (px, py, pw, ph) in plats:
            if overlap(self.x, self.y, self.w, self.h, px, py, pw, ph):
                if self.vy > 0:
                    self.y = py - self.h
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0:
                    self.y = py + ph
                    self.vy = 0
        if self.on_ground:
            self.jumps = 2
            self.coyote = COYOTE
        else:
            self.coyote = max(0.0, self.coyote - dt)
        if abs(self.vx) > 1 and self.on_ground:
            self.anim += dt

        # HEPA Vacuum (hold K) — drains energy; Game applies the suction.
        self.vacuuming = (keys[pygame.K_k] and self.energy > 0
                          and self.dash_t <= 0)
        if self.vacuuming:
            self.energy = max(0.0, self.energy - 26 * dt)
        else:
            self.energy = min(self.maxenergy, self.energy + 9 * dt)

        # shooting (edge-triggered; hold to charge)
        fire = keys[pygame.K_j] or keys[pygame.K_x]
        muzx = self.x + (self.w if self.facing > 0 else 0)
        muzy = self.y + 24
        if fire and not self.fire_prev:
            shots.append(Shot(muzx, muzy, self.facing * 620, 2, 0))
            parts.muzzle(muzx, muzy, self.facing)
            snd.play("shot")
            self.charging = True
            self.charge = 0.0
        if fire and self.charging:
            self.charge += dt
        if not fire and self.fire_prev and self.charging:
            if self.charge >= 0.9:
                shots.append(Shot(muzx, muzy, self.facing * 680, 6, 2))
                parts.muzzle(muzx, muzy, self.facing)
                snd.play("charge")
            elif self.charge >= 0.4:
                shots.append(Shot(muzx, muzy, self.facing * 650, 4, 1))
                parts.muzzle(muzx, muzy, self.facing)
                snd.play("shot")
            self.charging = False
            self.charge = 0.0
        self.fire_prev = fire

    def draw(self, s, cam, assets, t):
        x, y = self.x - cam, self.y
        cx = x + self.w / 2
        # HEPA vacuum suction cone
        if self.vacuuming:
            vx, vy, vw, vh = self.vacuum_rect()
            vx -= cam
            cone = pygame.Surface((int(vw), int(vh)), pygame.SRCALPHA)
            tip = (0 if self.facing > 0 else vw)
            far = (vw if self.facing > 0 else 0)
            pygame.draw.polygon(cone, (150, 220, 255, 60),
                                [(tip, vh / 2), (far, 0), (far, vh)])
            s.blit(cone, (int(vx), int(vy)))
            for _ in range(4):
                px = vx + random.uniform(0, vw)
                py = vy + random.uniform(0, vh)
                fcircle(s, px, py, random.uniform(1, 3), (200, 240, 255, 160))
        blink = self.iframe > 0 and int(self.iframe * 20) % 2 == 0
        if not blink:
            if self.charging and self.charge > 0.4:
                cr = 10 + self.charge * 12
                glow(s, x + (self.w if self.facing > 0 else 0),
                     y + 24, cr, C_CHARGE, 150)
            if self.dash_t > 0:
                for k in range(3):
                    fcircle(s, cx - self.facing * k * 12, y + self.h / 2,
                            8 - k * 2, (*C_TEAL_LT, 90))
            if assets.has("player"):
                # pick an animation sprite by state, fall back to 'player'
                if self.iframe > 0:
                    want = "player_hurt"
                elif self.dash_t > 0:
                    want = "player_dash"
                elif self.crouching:
                    want = "player_crouch"
                elif not self.on_ground:
                    want = "player_fall" if self.vy > 0 else "player_jump"
                elif self.charging or self.fire_prev:
                    want = "player_shoot"
                elif abs(self.vx) > 1:
                    want = "player_run"
                else:
                    want = "player"
                name = want if assets.has(want) else "player"
                assets.blit_fit(s, name, cx, y + self.h / 2,
                                self.w * 2.1, self.h * 1.25, flip=self.facing < 0)
            else:
                bob = abs(math.sin(self.anim * 9)) * 3 if self.on_ground else 0
                orrect(s, (x + 4, y + 14 - bob, self.w - 8, 26), C_TEAL_DK, 6)
                orrect(s, (x + 6, y + 15 - bob, self.w - 12, 8), C_TEAL, 4)
                fcircle(s, cx, y + 9 - bob, 10, (232, 200, 168))
                orrect(s, (cx - 11, y + 1 - bob, 22, 6), C_TEAL, 3)
                gx = x + (self.w if self.facing > 0 else 0)
                pygame.draw.line(s, (60, 70, 66),
                                 (cx, y + 24 - bob), (gx + self.facing * 14, y + 24 - bob), 6)
                legs = math.sin(self.anim * 9) * 5 if self.on_ground else 0
                pygame.draw.line(s, C_TEAL_DK, (cx, y + 40 - bob),
                                 (cx - 6 + legs, y + self.h), 6)
                pygame.draw.line(s, C_TEAL_DK, (cx, y + 40 - bob),
                                 (cx + 6 - legs, y + self.h), 6)


# --------------------------------------------------------------------------- #
# Sound
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

    def _tone(self, freq, ms, vol=0.25, shape="sine"):
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
                specs = {"shot": (620, 70), "charge": (300, 200, "square"),
                         "jump": (520, 90), "dash": (700, 120),
                         "hit": (160, 160, "square"), "boss": (90, 500, "square"),
                         "win": (720, 500), "coin": (900, 70)}
                self._cache[name] = self._tone(*specs.get(name, (440, 60)))
            self._cache[name].play()
        except Exception:
            self.ok = False


# --------------------------------------------------------------------------- #
# Level
# --------------------------------------------------------------------------- #
def build_level():
    plats = [(0, GROUND_Y, LEVEL_W, HEIGHT - GROUND_Y)]
    # floating platforms
    for (x, y, w) in [(360, 410, 140), (620, 340, 150), (980, 400, 160),
                      (1300, 330, 150), (1600, 410, 180), (1980, 360, 160),
                      (2260, 420, 150)]:
        plats.append((x, y, w, 24))
    enemies = [
        Enemy("sporebot", 500, GROUND_Y - 40),
        Enemy("moldcrawler", 780, GROUND_Y - 34),
        Enemy("sporebot", 1050, 400 - 40),
        Enemy("toxicsprayer", 1360, GROUND_Y - 48),
        Enemy("sporebot", 1650, GROUND_Y - 40),
        Enemy("moldcrawler", 1900, GROUND_Y - 34),
        Enemy("toxicsprayer", 2150, GROUND_Y - 48),
        Enemy("sporebot", 2350, GROUND_Y - 40),
        Enemy("moldbat", 1150, 280),
        Enemy("moldbat", 1750, 260),
        Enemy("moldbat", 2200, 280),
    ]
    coins = [Coin(x, GROUND_Y - 60) for x in range(300, 2400, 190)]
    return plats, enemies, coins


# --------------------------------------------------------------------------- #
# Game
# --------------------------------------------------------------------------- #
class Game:
    def __init__(self, screen, snd):
        self.screen = screen
        self.snd = snd
        self.big = pygame.font.SysFont("arialblack,arial", 58, bold=True)
        self.mid = pygame.font.SysFont("arial", 26, bold=True)
        self.small = pygame.font.SysFont("arial", 18)
        here = os.path.dirname(os.path.abspath(__file__))
        self.assets = AssetPack(os.path.join(here, "assets"))
        self.bg = self._make_bg()
        # persistent between missions (DesilPower HQ upgrades — Ch 3/4)
        self.armor = 0
        self.battery = 0
        self.speed = 0
        self.bank = 0            # Sample Cassettes banked at HQ
        self.cursor = 0
        self.shake = 0.0
        self.reset()
        self.state = STATE_MENU

    HQ_ITEMS = ["Deploy Mission", "Research Lab: Armor  (+20 HP)",
                "Engineering Bay: Battery  (+20 Energy)",
                "Engineering Bay: Speed Module  (+10%)"]

    def hq_cost(self, i):
        lvl = (0, self.armor, self.battery, self.speed)[i]
        return 5 + lvl * 4

    def _make_bg(self):
        if self.assets.has("background"):
            return pygame.transform.smoothscale(
                self.assets.imgs["background"], (WIDTH, HEIGHT)).convert()
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            f = y / HEIGHT
            bg_col = [int(a + (b - a) * f) for a, b in
                      zip((26, 40, 38), (12, 20, 22))]
            pygame.draw.line(bg, bg_col, (0, y), (WIDTH, y))
        return bg

    def reset(self):
        self.plats, self.enemies, self.coins = build_level()
        self.player = Player()
        # apply persistent HQ upgrades
        self.player.maxhp = PLAYER_HP + self.armor * 20
        self.player.maxenergy = MAX_ENERGY + self.battery * 20
        self.player.speed_mult = 1.0 + self.speed * 0.10
        self.player.hp = self.player.maxhp
        self.player.energy = self.player.maxenergy
        self.shots = []
        self.pickups = []
        self.parts = Particles()
        self.boss = None
        self.cam = 0.0
        self.score = 0
        self.spores = 1200
        self.cassettes = 0
        self.cassettes_total = len(self.coins)
        self.boss_intro = 0.0

    def spawn_boss(self):
        self.boss = Boss()
        self.boss_intro = 3.0
        self.snd.play("boss")

    # -- update -------------------------------------------------------------- #
    def update(self, dt, keys):
        if self.state != STATE_PLAY:
            return
        p = self.player
        p.update(dt, keys, self.plats, self.shots, self.parts, self.snd)

        # camera
        if self.boss:
            self.cam = CAM_BOSS
        else:
            self.cam = max(0, min(LEVEL_W - WIDTH, p.x + p.w / 2 - WIDTH * 0.4))
            if p.x > BOSS_TRIGGER:
                self.spawn_boss()

        for e in self.enemies:
            e.update(dt, p, self.shots, self.parts)
        if self.boss:
            self.boss.update(dt, p, self.shots, self.parts, self.enemies)

        # HEPA Vacuum (V2C3): pull enemies in, finish weakened ones, eat spores
        if p.vacuuming:
            vr = p.vacuum_rect()
            pcx = p.x + p.w / 2
            for e in self.enemies:
                if not e.dead and overlap(*vr, *e.rect()):
                    e.x += (1 if pcx > e.x else -1) * 150 * dt
                    if e.hp <= 3:
                        e.dead = True
                        self.parts.splat(e.x + e.w / 2, e.y + e.h / 2, C_TEAL_LT, 12)
                        self.score += 120
                        self._maybe_drop(e)
            for sh in self.shots:
                if sh.hostile and overlap(*vr, *sh.rect()):
                    sh.dead = True
                    p.energy = min(p.maxenergy, p.energy + 4)
                    self.parts.spark(sh.x, sh.y, C_SHOT, 4, 120)
            if random.random() < 0.6:
                self.parts.spark(pcx + p.facing * 60, p.y + 24, (200, 240, 255), 1, 60)

        # shots
        for sh in self.shots:
            sh.update(dt)
            vy = getattr(sh, "vy", None)
            if vy is not None:
                sh.y += vy * dt
            if sh.hostile:
                if overlap(*sh.rect(), *p.rect()):
                    p.hurt(4, self.parts)
                    sh.dead = True
                    self.snd.play("hit")
            else:
                for e in self.enemies:
                    if not e.dead and overlap(*sh.rect(), *e.rect()):
                        if e.hurt(sh.dmg, self.parts):
                            self.score += 100
                            self.spores = max(0, self.spores - 50)
                            self._maybe_drop(e)
                        sh.dead = True
                        break
                if not sh.dead and self.boss and overlap(*sh.rect(), *self.boss.rect()):
                    dmg = sh.dmg
                    if self.boss.weak_open > 0 and overlap(*sh.rect(), *self.boss.weak_rect()):
                        dmg *= 2
                        self.parts.spark(sh.x, sh.y, (150, 255, 180), 8, 260)
                    if self.boss.hurt(dmg, self.parts):
                        self.state = STATE_WIN
                        self.bank += self.cassettes + 500     # boss reward
                        self.snd.play("win")
                    sh.dead = True
        self.shots = [s for s in self.shots if not s.dead]

        # enemy contact damage
        for e in self.enemies:
            if not e.dead and overlap(*e.rect(), *p.rect()):
                p.hurt(e.dmg, self.parts)
                self.snd.play("hit")
        self.enemies = [e for e in self.enemies if not e.dead]
        if self.boss and overlap(*self.boss.rect(), *p.rect()):
            p.hurt(6, self.parts)

        # coins (Sample Cassettes)
        for c in self.coins:
            if not c.got and overlap(c.x - 12, c.y - 12, 24, 24, *p.rect()):
                c.got = True
                self.score += 50
                self.cassettes += 1
                self.snd.play("coin")
        self.coins = [c for c in self.coins if not c.got]

        # pickups (health / energy)
        for pk in self.pickups:
            if not pk.got and overlap(pk.x - 12, pk.y - 12, 24, 24, *p.rect()):
                pk.got = True
                if pk.kind == "health":
                    p.hp = min(p.maxhp, p.hp + HP_PACK)
                else:
                    p.energy = min(p.maxenergy, p.energy + ENERGY_CELL)
                self.snd.play("coin")
        self.pickups = [pk for pk in self.pickups if not pk.got]

        if p.dead:
            self.state = STATE_OVER
            self.bank += self.cassettes
            self.snd.play("hit")

        self.boss_intro = max(0.0, self.boss_intro - dt)
        self.parts.update(dt)

    def _maybe_drop(self, e):
        r = random.random()
        if r < 0.22:
            self.pickups.append(Pickup(e.x + e.w / 2, e.y, "health"))
        elif r < 0.44:
            self.pickups.append(Pickup(e.x + e.w / 2, e.y, "energy"))

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        s = self.screen
        s.blit(self.bg, (0, 0))
        cam = self.cam

        if self.state == STATE_MENU:
            # DesilPower HQ hub (Ch 3)
            self._center(self.big, "DESILPOWER HQ", 92, C_TEAL_LT)
            self._center(self.small,
                         "Mission Command · Research Lab · Engineering Bay",
                         132, C_DIM)
            self._center(self.mid, f"Sample Cassettes banked: {self.bank}", 172, C_COIN)
            for i, label in enumerate(self.HQ_ITEMS):
                y = 230 + i * 44
                sel = (i == self.cursor)
                if i == 0:
                    txt = label
                else:
                    lvl = (0, self.armor, self.battery, self.speed)[i]
                    txt = f"{label}   Mk{lvl} → {lvl + 1}   [{self.hq_cost(i)} cassettes]"
                col = C_TEAL_LT if sel else C_TEXT
                if sel:
                    pygame.draw.rect(s, (24, 44, 42),
                                     (WIDTH // 2 - 330, y - 16, 660, 34), border_radius=8)
                self._center(self.small if i else self.mid, txt, y, col)
            self._center(self.small, "↑/↓ select    Enter: deploy / buy    "
                         "Commander Ellis: \"Clear the Basement, technician.\"",
                         HEIGHT - 108, C_DIM)
            self._center(self.small,
                         "In-mission:  Move A/D · Jump (double) · Crouch · "
                         "J blaster (charge) · K HEPA vacuum · L dash",
                         HEIGHT - 78, C_DIM)
            self._center(self.mid, "MISSION 1 — THE BASEMENT", HEIGHT - 44, C_TOXIC)
            return

        self._draw_world(t)
        self._hud()

        # boss introduction cutscene banner (V2C8)
        if self.boss_intro > 0 and self.boss:
            band = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
            band.fill((8, 12, 14, 190))
            s.blit(band, (0, HEIGHT // 2 - 60))
            self._center(self.big, "SLUDGE KING", HEIGHT // 2 - 24, C_DANGER)
            self._center(self.mid, "\"THIS HOME... IS MINE!\"", HEIGHT // 2 + 22, C_TOXIC)

        if self.state in (STATE_WIN, STATE_OVER):
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((8, 12, 14, 190))
            s.blit(veil, (0, 0))
            if self.state == STATE_WIN:
                self._center(self.big, "BASEMENT RESTORED", HEIGHT // 2 - 92, C_TEAL_LT)
                self._center(self.mid, "SLUDGE KING defeated!", HEIGHT // 2 - 40, C_TEXT)
                self._center(self.small, "NEW TOOL UNLOCKED:  HEPA Vacuum Module  ·  "
                             "+500 Sample Cassettes  ·  Basement Restoration Badge",
                             HEIGHT // 2 - 8, C_TOXIC)
                self._center(self.small,
                             f"Score {self.score}  ·  Cassettes banked: {self.bank}",
                             HEIGHT // 2 + 18, C_TEXT)
                self._center(self.small, "Dr. Mira: \"These traces link the Sludge King "
                             "to something bigger — Moldius Prime...\"",
                             HEIGHT // 2 + 42, C_DIM)
            else:
                self._center(self.big, "TECHNICIAN DOWN", HEIGHT // 2 - 40, C_DANGER)
                self._center(self.mid, f"The mold won this time.  Score {self.score}",
                             HEIGHT // 2 + 16, C_TEXT)
            self._center(self.mid, "Press Enter — return to DesilPower HQ", HEIGHT // 2 + 66, C_TEAL_LT)

    def _draw_world(self, t):
        s, cam = self.screen, self.cam
        # platforms
        for (x, y, w, h) in self.plats:
            sx = x - cam
            if sx + w < 0 or sx > WIDTH:
                continue
            if self.assets.has("platform"):
                s.blit(pygame.transform.smoothscale(
                    self.assets.imgs["platform"], (int(w), int(h))), (int(sx), int(y)))
            else:
                pygame.draw.rect(s, (46, 40, 34), (int(sx), int(y), int(w), int(h)))
                pygame.draw.rect(s, (70, 104, 52), (int(sx), int(y), int(w), 6))
        for c in self.coins:
            c.draw(s, cam, self.assets, t)
        for pk in self.pickups:
            pk.draw(s, cam, t)
        for e in self.enemies:
            e.draw(s, cam, self.assets)
        if self.boss:
            self.boss.draw(s, cam, self.assets)
        self.player.draw(s, cam, self.assets, t)
        for sh in self.shots:
            sh.draw(s, cam, self.assets)
        self.parts.draw(s, cam)

    def _hud(self):
        s = self.screen
        p = self.player
        # health bar (0..maxhp)
        pygame.draw.rect(s, (10, 16, 16), (18, 16, 244, 20), border_radius=6)
        hf = max(0.0, p.hp / p.maxhp)
        pygame.draw.rect(s, C_HP, (21, 19, int(238 * hf), 14), border_radius=5)
        self._t(self.small, f"HP {int(p.hp)}/{p.maxhp}", (270, 15), C_DIM)
        # weapon energy bar
        pygame.draw.rect(s, (10, 16, 16), (18, 42, 244, 14), border_radius=5)
        ef = max(0.0, p.energy / p.maxenergy)
        pygame.draw.rect(s, (110, 180, 240), (21, 44, int(238 * ef), 9), border_radius=4)
        self._t(self.small, "ENERGY", (270, 40), C_DIM)
        # charge meter
        pygame.draw.rect(s, (10, 16, 16), (18, 62, 244, 10), border_radius=4)
        ch = min(1.0, p.charge / 0.9) if p.charging else 0
        pygame.draw.rect(s, C_SHOT, (20, 63, int(240 * ch), 7), border_radius=4)
        # score / spores / cassettes
        self._t(self.mid, f"SCORE {self.score}", (WIDTH - 230, 16), C_TEXT)
        self._t(self.small, f"SPORE COUNT {self.spores}", (WIDTH - 230, 48), C_TOXIC)
        self._t(self.small, f"CASSETTES {self.cassettes}/{self.cassettes_total}",
                (WIDTH - 230, 70), C_COIN)
        # boss bar
        if self.boss:
            bw = 460
            bx = WIDTH // 2 - bw // 2
            pygame.draw.rect(s, (10, 16, 16), (bx - 3, HEIGHT - 44, bw + 6, 22),
                             border_radius=6)
            frac = max(0, self.boss.hp / self.boss.maxhp)
            pygame.draw.rect(s, C_DANGER, (bx, HEIGHT - 41, int(bw * frac), 16))
            self._t(self.small, self.boss.NAME + "   (Phase %d)" % self.boss.phase(),
                    (bx, HEIGHT - 66), C_DANGER)
            if self.boss.weak_open > 0:
                self._center(self.small, "WEAK POINT OPEN — hit the chest valve!",
                             HEIGHT - 90, C_TEAL_LT)

    def _t(self, font, msg, pos, col):
        self.screen.blit(font.render(msg, True, col), pos)

    def _center(self, font, msg, y, col):
        img = font.render(msg, True, col)
        self.screen.blit(img, img.get_rect(center=(WIDTH // 2, y)))

    def on_key(self, key):
        if key == pygame.K_m:
            self.snd.on = not self.snd.on
            return
        if self.state == STATE_HQ:
            if key in (pygame.K_UP, pygame.K_w):
                self.cursor = (self.cursor - 1) % len(self.HQ_ITEMS)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.cursor = (self.cursor + 1) % len(self.HQ_ITEMS)
            elif key == pygame.K_RETURN:
                if self.cursor == 0:
                    self.reset()
                    self.state = STATE_PLAY
                else:
                    cost = self.hq_cost(self.cursor)
                    if self.bank >= cost:
                        self.bank -= cost
                        if self.cursor == 1:
                            self.armor += 1
                        elif self.cursor == 2:
                            self.battery += 1
                        elif self.cursor == 3:
                            self.speed += 1
                        self.snd.play("coin")
        elif self.state in (STATE_WIN, STATE_OVER) and key == pygame.K_RETURN:
            self.cursor = 0
            self.state = STATE_HQ


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def run(selftest=False):
    if selftest:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TyDez — Mold Mission")
    clock = pygame.time.Clock()
    snd = Sound()
    game = Game(screen, snd)

    if selftest:
        class _Keys(dict):
            def __missing__(self, _):
                return False
        game.on_key(pygame.K_RETURN)
        for i in range(9000):
            p = game.player
            keys = _Keys()
            keys[pygame.K_RIGHT] = game.boss is None
            keys[pygame.K_j] = (i % 6) < 2            # tap-fire stream
            if i % 50 == 0:
                keys[pygame.K_SPACE] = True
            game.update(1 / FPS, keys)
            game.draw(i / FPS)
            if game.state in (STATE_WIN, STATE_OVER):
                break
        print("selftest: state=%s frame=%d hp=%d bosshp=%s score=%d"
              % (game.state, i, game.player.hp,
                 game.boss.hp if game.boss else "-", game.score))
        pygame.quit()
        return game.state

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
