#!/usr/bin/env python3
"""TyDez Mold Buster — a small arcade game (Boise Mold Removal).

You are TyGuy, the mold-removal pro. Green mold keeps blooming on the wall.
Move around and blast it with your sprayer before any patch grows big enough
to spread. Let three patches spread and the job's lost.

Controls
    Arrow keys / WASD ... move TyGuy
    Space (hold) ........ spray in the direction you're facing
    Enter ............... start / restart
    M ................... toggle sound
    Esc ................. quit

Run
    pip install pygame numpy
    python3 mold_buster.py

Headless smoke test (no window):
    python3 mold_buster.py --selftest
"""

import math
import random
import sys

import pygame

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 900, 620
FPS = 60

# Brand palette (Boise Mold Removal / TyDez).
C_BG_TOP = (30, 38, 46)
C_BG_BOT = (18, 24, 30)
C_BRAND = (86, 214, 165)      # TyDez green
C_BRAND_DK = (44, 150, 112)
C_MOLD = (108, 156, 72)       # sickly mold green
C_MOLD_DK = (70, 104, 46)
C_SPRAY = (176, 230, 250)
C_TEXT = (236, 242, 245)
C_TEXT_DIM = (150, 164, 172)
C_DANGER = (226, 96, 88)

PLAYER_SPEED = 320.0          # px / second
PLAYER_R = 16
SPRAY_R = 34
SPRAY_REACH = 46              # how far in front the spray cloud sits
SPRAY_POWER = 46.0            # mold radius removed per second of contact

MOLD_START_R = 8
MOLD_MAX_R = 40               # patch spreads once it reaches this
MOLD_GROWTH = 3.2             # radius px / second
SPAWN_EVERY_START = 2.2       # seconds between spawns at the start
SPAWN_EVERY_MIN = 0.65
MAX_STRIKES = 3

STATE_MENU, STATE_PLAY, STATE_OVER = "menu", "play", "over"


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

    def _tone(self, freq, ms, vol=0.35, shape="sine"):
        import numpy as np
        n = int(44100 * ms / 1000)
        t = np.linspace(0, ms / 1000, n, endpoint=False)
        if shape == "square":
            wave = np.sign(np.sin(2 * math.pi * freq * t))
        else:
            wave = np.sin(2 * math.pi * freq * t)
        env = np.minimum(1.0, np.linspace(1.0, 0.0, n) * 3)  # quick decay
        data = (wave * env * vol * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.ascontiguousarray(data))

    def play(self, name):
        if not (self.ok and self.on):
            return
        try:
            if name not in self._cache:
                if name == "clear":
                    self._cache[name] = self._tone(660, 90)
                elif name == "spread":
                    self._cache[name] = self._tone(150, 220, shape="square")
                elif name == "over":
                    self._cache[name] = self._tone(110, 500, shape="square")
                else:
                    self._cache[name] = self._tone(440, 60)
            self._cache[name].play()
        except Exception:
            self.ok = False


# --------------------------------------------------------------------------- #
# Entities
# --------------------------------------------------------------------------- #
class Mold:
    """A growing mold patch. Blobs are baked once for a crusty look."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.r = float(MOLD_START_R)
        rng = random.Random((int(x) << 16) ^ int(y))
        self.blobs = [
            (rng.uniform(0, 2 * math.pi), rng.uniform(0.35, 0.9), rng.uniform(0.3, 0.6))
            for _ in range(6)
        ]

    def update(self, dt):
        self.r += MOLD_GROWTH * dt

    def draw(self, surf):
        for ang, dist, size in self.blobs:
            bx = self.x + math.cos(ang) * self.r * dist
            by = self.y + math.sin(ang) * self.r * dist
            pygame.draw.circle(surf, C_MOLD_DK, (int(bx), int(by)), max(2, int(self.r * size)))
        pygame.draw.circle(surf, C_MOLD, (int(self.x), int(self.y)), int(self.r))
        # danger ring when close to spreading
        if self.r > MOLD_MAX_R * 0.7:
            pygame.draw.circle(surf, C_DANGER, (int(self.x), int(self.y)), int(self.r) + 3, 2)


class Player:
    def __init__(self):
        self.x, self.y = WIDTH / 2, HEIGHT / 2
        self.dx, self.dy = 0.0, 1.0   # facing direction
        self.spraying = False

    def update(self, dt, keys):
        mx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        my = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if mx or my:
            length = math.hypot(mx, my)
            self.dx, self.dy = mx / length, my / length
            self.x += self.dx * PLAYER_SPEED * dt
            self.y += self.dy * PLAYER_SPEED * dt
        self.x = max(PLAYER_R, min(WIDTH - PLAYER_R, self.x))
        self.y = max(PLAYER_R, min(HEIGHT - PLAYER_R, self.y))
        self.spraying = keys[pygame.K_SPACE]

    def spray_point(self):
        return (self.x + self.dx * SPRAY_REACH, self.y + self.dy * SPRAY_REACH)

    def draw(self, surf, t):
        if self.spraying:
            sx, sy = self.spray_point()
            for i in range(10):
                jx = sx + random.uniform(-SPRAY_R, SPRAY_R) * 0.7
                jy = sy + random.uniform(-SPRAY_R, SPRAY_R) * 0.7
                pygame.draw.circle(surf, C_SPRAY, (int(jx), int(jy)),
                                   random.randint(2, 5))
            pygame.draw.circle(surf, (120, 200, 235), (int(sx), int(sy)), SPRAY_R, 1)
        # TyGuy: green body + "T" cap
        pygame.draw.circle(surf, C_BRAND_DK, (int(self.x), int(self.y)), PLAYER_R + 2)
        pygame.draw.circle(surf, C_BRAND, (int(self.x), int(self.y)), PLAYER_R)
        f = pygame.font.SysFont("arialblack,arial", 18, bold=True)
        glyph = f.render("T", True, (18, 40, 32))
        surf.blit(glyph, glyph.get_rect(center=(int(self.x), int(self.y))))
        # nozzle showing facing
        nx, ny = self.x + self.dx * (PLAYER_R + 6), self.y + self.dy * (PLAYER_R + 6)
        pygame.draw.circle(surf, C_SPRAY, (int(nx), int(ny)), 4)


# --------------------------------------------------------------------------- #
# Game
# --------------------------------------------------------------------------- #
class Game:
    def __init__(self, screen, snd):
        self.screen = screen
        self.snd = snd
        self.big = pygame.font.SysFont("arialblack,arial", 64, bold=True)
        self.mid = pygame.font.SysFont("arial", 30, bold=True)
        self.small = pygame.font.SysFont("arial", 20)
        self.bg = self._make_bg()
        self.reset()
        self.state = STATE_MENU

    def _make_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            f = y / HEIGHT
            col = [int(a + (b - a) * f) for a, b in zip(C_BG_TOP, C_BG_BOT)]
            pygame.draw.line(bg, col, (0, y), (WIDTH, y))
        return bg

    def reset(self):
        self.player = Player()
        self.molds = []
        self.score = 0
        self.strikes = 0
        self.elapsed = 0.0
        self.spawn_timer = 1.0

    def spawn_interval(self):
        # ramps from SPAWN_EVERY_START down to SPAWN_EVERY_MIN over ~90s
        k = min(1.0, self.elapsed / 90.0)
        return SPAWN_EVERY_START + (SPAWN_EVERY_MIN - SPAWN_EVERY_START) * k

    def spawn_mold(self, x=None, y=None):
        if x is None:
            x = random.uniform(60, WIDTH - 60)
            y = random.uniform(60, HEIGHT - 60)
        self.molds.append(Mold(x, y))

    # -- update -------------------------------------------------------------- #
    def update(self, dt, keys):
        if self.state != STATE_PLAY:
            return
        self.elapsed += dt
        self.player.update(dt, keys)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_mold()
            self.spawn_timer = self.spawn_interval()

        sx, sy = self.player.spray_point()
        survivors = []
        for m in self.molds:
            m.update(dt)
            if self.player.spraying:
                d = math.hypot(m.x - sx, m.y - sy)
                if d < SPRAY_R + m.r:
                    m.r -= SPRAY_POWER * dt
            if m.r <= 3:
                self.score += 10
                self.snd.play("clear")
                continue
            if m.r >= MOLD_MAX_R:
                # it spreads: two smaller children nearby, costs a strike
                self.snd.play("spread")
                self.strikes += 1
                for _ in range(2):
                    ang = random.uniform(0, 2 * math.pi)
                    nx = max(40, min(WIDTH - 40, m.x + math.cos(ang) * 70))
                    ny = max(40, min(HEIGHT - 40, m.y + math.sin(ang) * 70))
                    survivors.append(Mold(nx, ny))
                continue
            survivors.append(m)
        self.molds = survivors

        if self.strikes >= MAX_STRIKES:
            self.state = STATE_OVER
            self.snd.play("over")

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        s = self.screen
        s.blit(self.bg, (0, 0))

        if self.state == STATE_MENU:
            self._center(self.big, "MOLD BUSTER", HEIGHT // 2 - 90, C_BRAND)
            self._center(self.mid, "Boise Mold Removal — you're TyGuy", HEIGHT // 2 - 30, C_TEXT)
            self._center(self.small, "Move: Arrows / WASD    Spray: hold Space", HEIGHT // 2 + 20, C_TEXT_DIM)
            self._center(self.small, "Clear mold for points. 3 patches spread = game over.", HEIGHT // 2 + 48, C_TEXT_DIM)
            self._center(self.mid, "Press Enter to start", HEIGHT // 2 + 110, C_BRAND)
            return

        for m in self.molds:
            m.draw(s)
        self.player.draw(s, t)

        self._text(self.mid, f"Score {self.score}", (20, 14), C_TEXT)
        # strikes as dots
        for i in range(MAX_STRIKES):
            col = C_DANGER if i < self.strikes else (70, 82, 90)
            pygame.draw.circle(s, col, (WIDTH - 30 - i * 34, 30), 11)
        self._text(self.small, "spreads", (WIDTH - 132, 48), C_TEXT_DIM)

        if self.state == STATE_OVER:
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((10, 14, 18, 180))
            s.blit(veil, (0, 0))
            self._center(self.big, "JOB'S LOST", HEIGHT // 2 - 70, C_DANGER)
            self._center(self.mid, f"Mold cleared — score {self.score}", HEIGHT // 2, C_TEXT)
            self._center(self.small, f"You lasted {int(self.elapsed)}s", HEIGHT // 2 + 40, C_TEXT_DIM)
            self._center(self.mid, "Press Enter to try again", HEIGHT // 2 + 95, C_BRAND)

    # -- text helpers -------------------------------------------------------- #
    def _text(self, font, msg, pos, col):
        self.screen.blit(font.render(msg, True, col), pos)

    def _center(self, font, msg, y, col):
        img = font.render(msg, True, col)
        self.screen.blit(img, img.get_rect(center=(WIDTH // 2, y)))

    # -- input --------------------------------------------------------------- #
    def on_key(self, key):
        if key == pygame.K_RETURN:
            if self.state in (STATE_MENU, STATE_OVER):
                self.reset()
                self.state = STATE_PLAY
        elif key == pygame.K_m:
            self.snd.on = not self.snd.on


# --------------------------------------------------------------------------- #
# Main loop / entry
# --------------------------------------------------------------------------- #
def run(selftest=False):
    if selftest:
        import os
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TyDez Mold Buster")
    clock = pygame.time.Clock()
    snd = Sound()
    game = Game(screen, snd)

    if selftest:
        # Drive a few hundred frames through every state, then exit clean.
        game.on_key(pygame.K_RETURN)          # menu -> play

        class _Keys(dict):
            def __missing__(self, _):
                return False

        for i in range(400):
            keys = _Keys()
            keys[pygame.K_SPACE] = True
            keys[pygame.K_RIGHT] = (i % 120) < 60
            keys[pygame.K_UP] = (i % 90) < 45
            game.update(1 / FPS, keys)
            game.draw(i / FPS)
        game.state = STATE_OVER
        game.draw(0)
        game.on_key(pygame.K_RETURN)          # over -> play
        pygame.quit()
        print("selftest OK — states cycled, score=%d strikes=%d molds=%d"
              % (game.score, game.strikes, len(game.molds)))
        return

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)  # clamp after stalls
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
