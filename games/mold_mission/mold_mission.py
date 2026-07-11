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

PLAYER_HP = 28
IFRAMES = 1.0
BOSS_HP = 140

STATE_MENU, STATE_PLAY, STATE_WIN, STATE_OVER = "menu", "play", "win", "over"


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
ASSET_NAMES = ("player", "player_shoot", "sporebot", "moldcrawler",
               "toxicsprayer", "boss", "shot", "shot_charged", "toxic",
               "coin", "background", "platform")


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
        if kind == "sporebot":
            self.w, self.h, self.hp = 40, 40, 4
            self.vx = -70
            self.dmg = 4
        elif kind == "moldcrawler":
            self.w, self.h, self.hp = 46, 34, 9
            self.dmg = 4
        else:  # toxicsprayer
            self.w, self.h, self.hp = 40, 48, 6
            self.dmg = 4

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def update(self, dt, player, shots, parts):
        self.hit = max(0.0, self.hit - dt)
        if self.kind == "sporebot":
            self.x += self.vx * dt
            # patrol turn-around on level edges / simple bounds
            if self.x < 60 or self.x > LEVEL_W - 100:
                self.vx *= -1
        elif self.kind == "moldcrawler":
            d = player.x - self.x
            self.x += (30 if d > 0 else -30) * dt
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
                 "toxicsprayer": "toxicsprayer"}[self.kind]
        if assets.has(asset):
            assets.blit_fit(s, asset, cx, cy, self.w * 1.5, self.h * 1.5)
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
    def __init__(self):
        self.w, self.h = 260, 300
        self.x = LEVEL_W - self.w - 40
        self.y = GROUND_Y - self.h
        self.hp = BOSS_HP
        self.maxhp = BOSS_HP
        self.hit = 0.0
        self.t = 0.0
        self.shoot_t = 1.5
        self.dead = False
        self.bob = 0.0

    def rect(self):
        return (self.x + 30, self.y + 40, self.w - 60, self.h - 60)

    def update(self, dt, player, shots, parts):
        self.t += dt
        self.hit = max(0.0, self.hit - dt)
        self.bob = math.sin(self.t * 1.4) * 14
        self.shoot_t -= dt
        if self.shoot_t <= 0:
            phase2 = self.hp < self.maxhp * 0.5
            self.shoot_t = 1.1 if phase2 else 1.7
            n = 3 if phase2 else 2
            mx, my = self.x + 40, self.y + self.h * 0.4 + self.bob
            for i in range(n):
                ang = math.atan2((player.y + 20) - my, (player.x) - mx)
                ang += (i - (n - 1) / 2) * 0.28
                sp = 300
                sh = Shot(mx, my, math.cos(ang) * sp, 4, -1, hostile=True)
                sh.vy = math.sin(ang) * sp
                shots.append(sh)
        parts.spark(self.x + 40, self.y + self.h * 0.4 + self.bob, C_TOXIC, 1, 60)

    def hurt(self, dmg, parts):
        self.hp -= dmg
        self.hit = 0.1
        parts.spark(self.x + 50, self.y + self.h * 0.4, C_TEAL_LT, 8, 240)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def draw(self, s, cam, assets):
        x, y = self.x - cam, self.y + self.bob
        cx, cy = x + self.w / 2, y + self.h / 2
        glow(s, cx, cy, self.w * 0.6, (60, 90, 40), 70)
        if assets.has("boss"):
            assets.blit_fit(s, "boss", cx, cy, self.w * 1.15, self.h * 1.15)
        else:
            pygame.draw.ellipse(s, C_BOSS_DK, (int(x), int(y + 20),
                                self.w, self.h - 20))
            pygame.draw.ellipse(s, C_BOSS, (int(x + 16), int(y + 30),
                                self.w - 32, self.h - 60))
            for _ in range(0):
                pass
            random.seed(1)
            for i in range(14):
                bx = x + 30 + random.random() * (self.w - 60)
                by = y + 40 + random.random() * (self.h - 90)
                fcircle(s, bx, by, random.randint(10, 22), C_BOSS_DK)
                fcircle(s, bx, by, 5, (40, 60, 30))
            # eyes
            for ex in (cx - 40, cx + 40):
                fcircle(s, ex, cy - 20, 16, (180, 255, 140))
                fcircle(s, ex, cy - 20, 8, (20, 40, 20))
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
        self.hp = PLAYER_HP
        self.iframe = 0.0
        self.fire_prev = False
        self.charge = 0.0
        self.charging = False
        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.anim = 0.0
        self.dead = False

    def rect(self):
        return (self.x, self.y, self.w, self.h)

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

        # dash
        if (keys[pygame.K_l] or keys[pygame.K_LSHIFT]) and self.dash_cd <= 0 \
                and self.dash_t <= 0:
            self.dash_t = DASH_TIME
            self.dash_cd = DASH_CD
            snd.play("dash")
        if self.dash_t > 0:
            self.dash_t -= dt
            self.vx = self.facing * DASH_SPEED
        else:
            self.vx = (right - left) * MOVE_SPEED
            if right:
                self.facing = 1
            elif left:
                self.facing = -1

        self.vy += GRAVITY * dt
        if up and self.on_ground and self.dash_t <= 0:
            self.vy = -JUMP_V
            self.on_ground = False
            snd.play("jump")

        # move + collide
        self.x += self.vx * dt
        self.x = max(0, min(LEVEL_W - self.w, self.x))
        for (px, py, pw, ph) in plats:
            if overlap(self.x, self.y, self.w, self.h, px, py, pw, ph):
                if self.vx > 0:
                    self.x = px - self.w
                elif self.vx < 0:
                    self.x = px + pw
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
        if abs(self.vx) > 1 and self.on_ground:
            self.anim += dt

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
                assets.blit_fit(s, "player", cx, y + self.h / 2,
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
        self.reset()
        self.state = STATE_MENU

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
        self.shots = []
        self.parts = Particles()
        self.boss = None
        self.cam = 0.0
        self.score = 0
        self.spores = 1200
        self.cassettes = 0
        self.cassettes_total = len(self.coins)

    def spawn_boss(self):
        self.boss = Boss()
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
            self.boss.update(dt, p, self.shots, self.parts)

        # shots
        for sh in self.shots:
            sh.x += getattr(sh, "vy", 0.0) * 0 + 0  # keep attr access cheap
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
                        sh.dead = True
                        break
                if not sh.dead and self.boss and overlap(*sh.rect(), *self.boss.rect()):
                    if self.boss.hurt(sh.dmg, self.parts):
                        self.state = STATE_WIN
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

        # coins
        for c in self.coins:
            if not c.got and overlap(c.x - 12, c.y - 12, 24, 24, *p.rect()):
                c.got = True
                self.score += 50
                self.cassettes += 1
                self.snd.play("coin")
        self.coins = [c for c in self.coins if not c.got]

        if p.dead:
            self.state = STATE_OVER
            self.snd.play("hit")

        self.parts.update(dt)

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        s = self.screen
        s.blit(self.bg, (0, 0))
        cam = self.cam

        if self.state == STATE_MENU:
            self._draw_world(t)
            self._center(self.big, "MOLD MISSION", HEIGHT // 2 - 150, C_TEAL_LT)
            self._center(self.mid, "Clean it. Seal it. Protect it.",
                         HEIGHT // 2 - 100, C_TEXT)
            # mission briefing
            self._center(self.small, "MISSION 1  —  THE BASEMENT", HEIGHT // 2 - 60, C_TOXIC)
            for i, ln in enumerate([
                    "Damp, dark, and full of spores. Clear the contamination,",
                    "collect Sample Cassettes, and shut down MOLDTIUS at the source."]):
                self._center(self.small, ln, HEIGHT // 2 - 34 + i * 22, C_DIM)
            for i, ln in enumerate([
                    "Move: Arrows / A D      Jump: Up / W / Space",
                    "Fire blaster: J  (hold to CHARGE)      Dash: L / Shift"]):
                self._center(self.small, ln, HEIGHT // 2 + 20 + i * 24, C_DIM)
            self._center(self.mid, "Press Enter to deploy", HEIGHT // 2 + 96, C_TEAL_LT)
            return

        self._draw_world(t)
        self._hud()

        if self.state in (STATE_WIN, STATE_OVER):
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((8, 12, 14, 190))
            s.blit(veil, (0, 0))
            if self.state == STATE_WIN:
                self._center(self.big, "CONTAINMENT COMPLETE", HEIGHT // 2 - 80, C_TEAL_LT)
                self._center(self.mid, "NEW TOOL UNLOCKED:  HEPA Vac Dash",
                             HEIGHT // 2 - 26, C_TOXIC)
                self._center(self.small,
                             f"MOLDTIUS defeated  ·  Score {self.score}  ·  "
                             f"Cassettes {self.cassettes}/{self.cassettes_total}",
                             HEIGHT // 2 + 14, C_TEXT)
                self._center(self.small, "Return to DesilPower HQ to upgrade, then on to the Attic.",
                             HEIGHT // 2 + 40, C_DIM)
            else:
                self._center(self.big, "TECHNICIAN DOWN", HEIGHT // 2 - 40, C_DANGER)
                self._center(self.mid, f"The mold won this time.  Score {self.score}",
                             HEIGHT // 2 + 16, C_TEXT)
            self._center(self.mid, "Press Enter to retry", HEIGHT // 2 + 70, C_TEAL_LT)

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
        # health bar
        pygame.draw.rect(s, (10, 16, 16), (18, 16, 224, 26), border_radius=6)
        seg = 200 / PLAYER_HP
        for i in range(self.player.hp):
            pygame.draw.rect(s, C_HP, (24 + i * seg, 22, max(2, seg - 1), 14))
        self._t(self.small, "HEALTH", (26, 44), C_DIM)
        # charge meter
        pygame.draw.rect(s, (10, 16, 16), (18, 66, 224, 14), border_radius=4)
        ch = min(1.0, self.player.charge / 0.9) if self.player.charging else 0
        pygame.draw.rect(s, C_SHOT, (20, 68, int(220 * ch), 10), border_radius=4)
        # score / spores
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
            self._t(self.small, "MOLDTIUS", (bx, HEIGHT - 66), C_DANGER)

    def _t(self, font, msg, pos, col):
        self.screen.blit(font.render(msg, True, col), pos)

    def _center(self, font, msg, y, col):
        img = font.render(msg, True, col)
        self.screen.blit(img, img.get_rect(center=(WIDTH // 2, y)))

    def on_key(self, key):
        if key == pygame.K_RETURN and self.state in (STATE_MENU, STATE_WIN, STATE_OVER):
            self.reset()
            self.state = STATE_PLAY
        elif key == pygame.K_m:
            self.snd.on = not self.snd.on


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
