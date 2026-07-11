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
import sys

import pygame

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 960, 640
FPS = 60

C_SKY_TOP = (36, 46, 54)
C_SKY_BOT = (22, 29, 35)
C_GROUND = (58, 46, 40)
C_GROUND_TOP = (86, 66, 54)
C_BRAND = (86, 214, 165)
C_BRAND_DK = (44, 150, 112)
C_BLOB = (96, 210, 168)
C_BLOB_DK = (52, 150, 116)
C_MOLD = (120, 168, 78)
C_MOLD_DK = (74, 110, 48)
C_SPRAY = (188, 236, 250)
C_TEXT = (236, 242, 245)
C_TEXT_DIM = (150, 164, 172)
C_DOOR = (210, 176, 96)
C_DOOR_OPEN = (120, 224, 150)
C_DANGER = (226, 96, 88)

GRAVITY = 2200.0
MOVE_SPEED = 275.0
JUMP_V = 760.0
TRAMPOLINE_V = 1180.0
CLIMB_SPEED = 210.0

STATE_MENU, STATE_PLAY, STATE_WIN, STATE_OVER = "menu", "play", "win", "over"

FOLLOW, TRAMPOLINE, BRIDGE, LADDER = "follow", "trampoline", "bridge", "ladder"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


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
# Blob companion — the heart of the game
# --------------------------------------------------------------------------- #
class Blob:
    """Follows TyGuy, or transforms into a placed tool at a fixed spot."""

    def __init__(self):
        self.form = FOLLOW
        self.x, self.y = 120.0, 520.0     # center while following
        self.rect = None                   # solid/climb region when transformed
        self.wobble = 0.0

    def solid_rect(self):
        """Return (x, y, w, h) if Blob is a solid the player stands on."""
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

    def draw(self, s):
        if self.form == FOLLOW:
            r = 15 + math.sin(self.wobble) * 1.5
            cx, cy = int(self.x), int(self.y)
            pygame.draw.circle(s, C_BLOB_DK, (cx, cy + 2), int(r) + 2)
            pygame.draw.circle(s, C_BLOB, (cx, cy), int(r))
            for ex in (-5, 5):
                pygame.draw.circle(s, (245, 250, 250), (cx + ex, cy - 3), 4)
                pygame.draw.circle(s, (20, 30, 28), (cx + ex, cy - 3), 2)
            return
        x, y, w, h = self.rect
        if self.form == TRAMPOLINE:
            pygame.draw.rect(s, C_BLOB_DK, (x, y + 8, w, h - 8), border_radius=6)
            pygame.draw.rect(s, C_BLOB, (x, y, w, 10), border_radius=5)
            for i in range(4):
                sx = x + 12 + i * (w - 24) / 3
                pygame.draw.line(s, C_BLOB_DK, (sx, y + 8), (sx, y + h), 3)
        elif self.form == BRIDGE:
            pygame.draw.rect(s, C_BLOB_DK, (x, y, w, h), border_radius=6)
            pygame.draw.rect(s, C_BLOB, (x, y, w, 6), border_radius=4)
            pygame.draw.circle(s, (245, 250, 250), (int(x + 14), int(y + 9)), 3)
            pygame.draw.circle(s, (245, 250, 250), (int(x + 26), int(y + 9)), 3)
        elif self.form == LADDER:
            pygame.draw.rect(s, C_BLOB_DK, (x, y, 5, h))
            pygame.draw.rect(s, C_BLOB_DK, (x + w - 5, y, 5, h))
            n = int(h // 26)
            for i in range(n + 1):
                ry = int(y + 12 + i * 26)
                pygame.draw.line(s, C_BLOB, (x, ry), (x + w, ry), 5)


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

    def spray_rect(self):
        if self.facing >= 0:
            return (self.x + self.w, self.y + 6, 56, 30)
        return (self.x - 56, self.y + 6, 56, 30)

    # -- physics ------------------------------------------------------------- #
    def update(self, dt, keys, solids, ladder, snd):
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
                    self.y = sy - self.h
                    self.on_ground = True
                    self.vy = 0
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
                        snd.play("bounce")
                    else:
                        self.vy = 0

        self.spraying = keys[pygame.K_f]

    def draw(self, s, font):
        x, y, w, h = int(self.x), int(self.y), self.w, self.h
        # legs
        pygame.draw.rect(s, (40, 60, 52), (x + 4, y + 28, 7, 14))
        pygame.draw.rect(s, (40, 60, 52), (x + w - 11, y + 28, 7, 14))
        # body
        pygame.draw.rect(s, C_BRAND_DK, (x, y + 12, w, 18), border_radius=4)
        pygame.draw.rect(s, C_BRAND, (x + 2, y + 12, w - 4, 8), border_radius=3)
        # head + hard hat
        hx, hy = x + w // 2, y + 6
        pygame.draw.circle(s, (232, 200, 170), (hx, hy), 8)
        pygame.draw.rect(s, C_BRAND, (hx - 10, hy - 8, 20, 6), border_radius=3)
        glyph = font.render("T", True, (18, 40, 32))
        s.blit(glyph, glyph.get_rect(center=(hx, y + 20)))
        # sprayer nozzle
        nx = x + w + 4 if self.facing >= 0 else x - 4
        pygame.draw.circle(s, C_SPRAY, (nx, y + 18), 3)
        if self.spraying:
            rx, ry, rw, rh = self.spray_rect()
            for i in range(12):
                import random as _r
                px = rx + _r.uniform(0, rw)
                py = ry + _r.uniform(0, rh)
                pygame.draw.circle(s, C_SPRAY, (int(px), int(py)), _r.randint(2, 4))


# --------------------------------------------------------------------------- #
# Mold target
# --------------------------------------------------------------------------- #
class Mold:
    def __init__(self, x, y):
        self.x, self.y, self.r = float(x), float(y), 20.0

    def draw(self, s):
        for dx, dy, rr in ((-8, 2, 0.7), (9, 4, 0.6), (0, -7, 0.65), (5, 8, 0.5)):
            pygame.draw.circle(s, C_MOLD_DK, (int(self.x + dx), int(self.y + dy)),
                               max(2, int(self.r * rr)))
        pygame.draw.circle(s, C_MOLD, (int(self.x), int(self.y)), int(self.r))


# --------------------------------------------------------------------------- #
# Level
# --------------------------------------------------------------------------- #
def build_level():
    # solids: (x, y, w, h, kind)
    solids = [
        (0, 560, 380, 80, "ground"),      # left ground
        (560, 560, 400, 80, "ground"),    # right ground (pit between 380..560)
        (620, 340, 340, 24, "oneway"),    # upper-right ledge (jump/climb up onto)
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
        self.big = pygame.font.SysFont("arialblack,arial", 60, bold=True)
        self.mid = pygame.font.SysFont("arial", 28, bold=True)
        self.small = pygame.font.SysFont("arial", 19)
        self.tiny = pygame.font.SysFont("arial", 16, bold=True)
        self.bg = self._make_bg()
        self.reset()
        self.state = STATE_MENU

    def _make_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            f = y / HEIGHT
            col = [int(a + (b - a) * f) for a, b in zip(C_SKY_TOP, C_SKY_BOT)]
            pygame.draw.line(bg, col, (0, y), (WIDTH, y))
        return bg

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
        self.player.update(dt, keys, self.all_solids(),
                           self.blob.ladder_rect(), self.snd)

        # fell into a pit / off the world
        if self.player.y > HEIGHT + 60:
            self.lives -= 1
            self.snd.play("die")
            if self.lives <= 0:
                self.state = STATE_OVER
                return
            self.player.reset()
            self.blob.follow()

        # spraying mold
        if self.player.spraying:
            sr = self.player.spray_rect()
            for m in list(self.molds):
                if overlap(*sr, m.x - m.r, m.y - m.r, m.r * 2, m.r * 2):
                    m.r -= 95 * dt
                    if m.r <= 3:
                        self.molds.remove(m)
                        self.snd.play("clear")

        # reaching the (open) exit
        if self.cleared():
            dx, dy, dw, dh = self.door
            if overlap(self.player.x, self.player.y, self.player.w,
                       self.player.h, dx, dy, dw, dh):
                self.state = STATE_WIN
                self.snd.play("win")

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        s = self.screen
        s.blit(self.bg, (0, 0))

        if self.state == STATE_MENU:
            self._c(self.big, "MOLD & BLOB", HEIGHT // 2 - 120, C_BRAND)
            self._c(self.mid, "TyGuy + Blob vs. the mold", HEIGHT // 2 - 62, C_TEXT)
            lines = [
                "Move: Arrows / A D      Jump & climb: Up / W / Space",
                "Spray mold: hold F",
                "Transform Blob:  1 Trampoline   2 Bridge   3 Ladder   E call back",
                "Clear every mold patch, then reach the exit door.",
            ]
            for i, ln in enumerate(lines):
                self._c(self.small, ln, HEIGHT // 2 - 6 + i * 28, C_TEXT_DIM)
            self._c(self.mid, "Press Enter to start", HEIGHT // 2 + 130, C_BRAND)
            return

        # platforms
        for (x, y, w, h, kind) in self.solids:
            pygame.draw.rect(s, C_GROUND, (x, y, w, h))
            pygame.draw.rect(s, C_GROUND_TOP, (x, y, w, 6))

        # exit door (glows green once mold is cleared)
        dx, dy, dw, dh = self.door
        open_ = self.cleared()
        pygame.draw.rect(s, C_DOOR_OPEN if open_ else C_DOOR, (dx, dy, dw, dh),
                         border_radius=4)
        pygame.draw.rect(s, (30, 40, 36), (dx + 5, dy + 6, dw - 10, dh - 6),
                         border_radius=3)
        if open_:
            self._t(self.tiny, "EXIT", (dx - 6, dy - 20), C_DOOR_OPEN)

        for m in self.molds:
            m.draw(s)
        self.blob.draw(s)
        self.player.draw(s, self.mid)

        # HUD
        self._t(self.mid, f"Mold left: {len(self.molds)}", (18, 12), C_TEXT)
        self._t(self.small, f"Blob: {self.blob.form}", (18, 46), C_BRAND)
        for i in range(3):
            col = C_BRAND if i < self.lives else (70, 82, 90)
            pygame.draw.circle(s, col, (WIDTH - 28 - i * 30, 26), 9)
        self._t(self.tiny, "1 tramp  2 bridge  3 ladder  E call  F spray",
                (WIDTH - 360, 48), C_TEXT_DIM)

        if self.state in (STATE_WIN, STATE_OVER):
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((10, 14, 18, 185))
            s.blit(veil, (0, 0))
            if self.state == STATE_WIN:
                self._c(self.big, "MOLD-FREE!", HEIGHT // 2 - 40, C_BRAND)
                self._c(self.mid, "TyGuy & Blob cleaned the whole level.",
                        HEIGHT // 2 + 20, C_TEXT)
            else:
                self._c(self.big, "WIPED OUT", HEIGHT // 2 - 40, C_DANGER)
                self._c(self.mid, "Blob will miss you. Try again?",
                        HEIGHT // 2 + 20, C_TEXT)
            self._c(self.mid, "Press Enter", HEIGHT // 2 + 80, C_BRAND)

    def _t(self, font, msg, pos, col):
        self.screen.blit(font.render(msg, True, col), pos)

    def _c(self, font, msg, y, col):
        img = font.render(msg, True, col)
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

        # Actually play the level to a win: walk right, bridge the pit,
        # spray each mold from close range, ladder up, reach the exit.
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
                pass                                   # stand and spray
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
        game.on_key(pygame.K_RETURN)                   # win -> restart
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
