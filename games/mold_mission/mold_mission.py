#!/usr/bin/env python3
"""Mold Mission — a Mega Man-style run-and-gun (TyDez / Boise Mold Removal).

You are the Mold Technician. Run, jump, and blast mold with your Disinfect
Blaster. Hold fire to CHARGE a bigger shot (like Mega Man's buster). Clear the
Basement of Spore Bots, Mold Crawlers and Toxic Sprayers, then defeat the end
boss MOLDTIUS, the Source of Contamination.

Controls (Mega Man style)
    Left / Right  (A / D) ..... move / walk
    Space / W / Z ............. jump — hold for a higher jump, tap for a short
                               hop (variable height); press again for a double jump
    Down / S .................. crouch (duck under shots); hold + Left/Right to
                               sneak-walk low. Ty stays ducked to fire & aim.
    Down + Jump .............. SLIDE (Mega Man slide — scoot under things, low profile)
    Up / Down (on a ladder) .. climb ladders
    J  (hold to charge) ....... fire Disinfect Blaster  (tap = pew, hold = charge) · X also fires
    K  (hold) ................. HEPA Vacuum — suction beam (pull/finish enemies, eat spores)
    L / Left-Shift ............ dash (quick, briefly invulnerable). While crouched:
                               L + direction = low SLIDE, L standing still = MELEE swing.
    Enter ..................... start / restart      M sound      Esc quit

    Levels are Mega Man style: jump the PITS (a fall is death), leap the SPIKES,
    and climb LADDERS to reach the upper platforms and their pickups. Get hit and
    Ty is knocked back with a brief stagger, Mega Man style. Every fire — shots
    and muzzle flash — leaves the tip of the blaster.

All art is drop-in: put transparent PNGs in ./assets (player, sporebot,
moldcrawler, toxicsprayer, boss, shot, shot_charged, toxic, coin, background,
platform). Missing ones fall back to built-in vector art.

Run
    pip install pygame numpy
    python3 mold_mission.py

Headless smoke test (no window):
    python3 mold_mission.py --selftest
"""

import glob
import io
import json
import math
import os
import random
import re
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
CROUCH_MULT = 0.45      # crouch-walk speed as a fraction of MOVE_SPEED
MELEE_TIME = 0.30       # crouch-melee swing duration
CHARGE_MAX = 1.1        # seconds to reach a full charge — caps the bolt growth
MELEE_DMG = 5           # crouch-melee damage
SLIDE_TIME = 0.30       # Mega Man slide (Down + Jump) duration
JUMP_CUT = 300.0        # release jump early -> rise is capped here (variable height)
CLIMB_SPEED = 160.0     # ladder climb speed (Mega Man)
MIRA_HEAL_RATE = 9.0    # HP/sec Dr. Mira's heal beam restores to Ty
# Consistent character sizing: every character sprite is drawn at
# (collision height x CHAR_H), anchored at the feet, so one character keeps the
# same on-screen size across all poses/screens and sizes track collision boxes.
CHAR_H = 1.42
# frames-per-second for Ty's video animation sequences (per state; default 12)
ANIM_FPS = {"player": 6, "player_walk": 11, "player_run": 15, "player_dash": 18,
            "player_shoot": 20, "player_aim": 8, "player_reload": 10,
            "player_crouch": 6, "player_crouch_walk": 11, "player_roll": 16,
            "player_jump": 12, "player_peak": 8, "player_fall": 10,
            "player_land": 14, "player_wallslide": 8, "player_use": 12,
            "player_crouch_run": 15, "player_pickup": 12, "player_carry": 11,
            "player_throw": 16, "player_place": 12,
            "player_jumpfire": 12, "player_fallfire": 10, "player_peakfire": 8,
            "player_crouchfire": 10, "player_crouchshoot": 12,
            "player_runfire": 15, "player_walkfire": 11,
            "player_rundownfire": 15, "player_walkdownfire": 11,
            "player_dashfire": 18}
DUCK_RATIO = 0.74       # a ducked pose renders this fraction of standing height
BOSS_H = 1.34           # boss sprite height as a multiple of its collision height

PLAYER_HP = 100
IFRAMES = 1.0
MAX_ENERGY = 100
HP_PACK = 25
ENERGY_CELL = 30
COYOTE = 0.10
SLUDGE_HP = 220
BEAST_HP = 260
QUEEN_HP = 280
CRAWLOR_HP = 320
PRIME_HP = 420

# Bathroom (Level 2) palette
C_TILE = (74, 120, 138)
C_TILE_DK = (34, 58, 70)
C_STEAM = (210, 224, 230)
C_WATER = (90, 150, 190)
# Attic (Level 3) palette
C_WOOD = (120, 86, 54)
C_WOOD_DK = (72, 50, 32)
C_SUN = (250, 226, 150)
# Crawlspace (Level 4) palette
C_MUD = (86, 66, 48)
C_MUD_DK = (44, 34, 26)
C_GAS = (150, 200, 90)
# Research Facility (Level 5) palette
C_LAB = (70, 90, 110)
C_LAB_DK = (32, 44, 58)
C_PRIME = (150, 90, 180)
C_PRIME_DK = (70, 40, 90)

MISSIONS = {
    1: {"name": "THE BASEMENT", "boss": "SLUDGE KING",
        "briefing": "Damp, dark, and full of spores.",
        "reward": "HEPA Vacuum Module"},
    2: {"name": "THE BATHROOM", "boss": "SHOWER BEAST",
        "briefing": "The infestation spread upward — clear it before it reaches the attic.",
        "reward": "Disinfect Blaster"},
    3: {"name": "THE ATTIC", "boss": "SPORE QUEEN",
        "briefing": "Ride the air currents to the Queen's nest and end the outbreak.",
        "reward": "Seal Foam Cannon"},
    4: {"name": "THE CRAWLSPACE", "boss": "CRAWLOR",
        "briefing": "Beneath the foundation — mud, flood water, and the hive's source.",
        "reward": "Air Scrubber Drone"},
    5: {"name": "RESEARCH FACILITY", "boss": "MOLDIUS PRIME",
        "briefing": "The source of it all. End Moldius Prime and finish the mission.",
        "reward": "Prototype Purification Core"},
}

STATE_HQ, STATE_PLAY, STATE_WIN, STATE_OVER = "hq", "play", "win", "over"
STATE_MENU = STATE_HQ  # menu screen is the DesilPower HQ hub

# Pick-up weapons (Batch 4). Ty carries one at a time; each recolours/retunes
# his shot and swaps his hold/fire sprite (ty_<id> / ty_<id>_fire).
WEAPONS = {
    "disinfect": {"name": "DISINFECT BLASTER", "color": (150, 224, 255),
                  "dmg": 3, "spd": 720, "cd": 0.14},
    "uvcannon":  {"name": "UV PURIFIER CANNON", "color": (196, 120, 255),
                  "dmg": 5, "spd": 780, "cd": 0.26},
    "fogger":    {"name": "THERMAL FOGGER", "color": (255, 176, 84),
                  "dmg": 2, "spd": 560, "cd": 0.08},
    "sealant":   {"name": "SEALANT APPLICATOR", "color": (120, 236, 180),
                  "dmg": 4, "spd": 620, "cd": 0.18},
    "grenade":   {"name": "PURIFICATION GRENADE", "color": (150, 240, 90),
                  "dmg": 6, "spd": 470, "cd": 0.32},
}
WEAPON_ORDER = ["disinfect", "uvcannon", "fogger", "sealant", "grenade"]


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


_glow_cache = {}


def glow(s, cx, cy, r, color, strength=120):
    r = int(r)
    if r < 1:
        return
    key = (r, color, strength)
    surf = _glow_cache.get(key)
    if surf is None:
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -2):
            a = int(strength * (1 - i / r) ** 2)
            fcircle(surf, r, r, i, (color[0], color[1], color[2], a))
        _glow_cache[key] = surf
    s.blit(surf, (cx - r, cy - r))


# --------------------------------------------------------------------------- #
# Assets (drop-in PNGs override the vector art)
# --------------------------------------------------------------------------- #
ASSET_NAMES = ("player", "player_run", "player_jump", "player_fall",
               "player_dash", "player_shoot", "player_hurt", "player_wallslide",
               "player_walk", "player_peak", "player_land",
               "player_aim", "player_victory", "player_reload", "player_climb",
               # Ty crouch move-set (15-pose sheet)
               "player_crouch", "player_crouch_walk", "player_crouch_aim",
               "player_crouch_aim_ds", "player_crouch_shoot",
               "player_crouch_reload", "player_crouch_melee",
               "player_crouch_hurt", "player_crouch_low", "player_crouch_roll",
               "player_crouch_slide", "player_crouch_cover",
               "player_crouch_interact", "player_crouch_item",
               "player_crouch_jump",
               "micromold", "sporedrifter",
               "sporedrifter_charge", "sporedrifter_enraged",
               "toxicslime", "toxicslime_enraged",
               "moldcrawler_enraged",
               "fungusbrute", "fungusbrute_enraged",
               "sporeturret", "corruptcyst",
               "sporebot", "moldcrawler", "toxicsprayer", "moldbat",
               "steammite", "ventswarm", "sporehawk", "roofleech", "moldmite",
               "creeper", "mudstalker", "centipede", "pipeparasite", "gaspod",
               "sporeworm", "sentinel", "ventstalker", "cultureswarm",
               "reactorspore", "mycelium", "boss", "boss2", "boss3", "boss4",
               "boss5", "shot", "shot_charged", "toxic", "coin",
               "background", "background2", "background3", "background4",
               "background5", "platform", "platform2", "platform3",
               "platform4", "platform5", "ellis", "molde", "turret",
               "mira", "mira_run", "mira_heal",
               "engineer", "medic", "molde_alert", "molde_scan",
               "rex", "rex_2", "purcore", "sporead", "sporead_gloat",
               "ty_disinfect", "ty_disinfect_fire", "ty_uvcannon",
               "ty_uvcannon_fire", "ty_fogger", "ty_fogger_fire",
               "ty_sealant", "ty_sealant_fire", "ty_grenade",
               "ty_grenade_fire",
               "wpn_disinfect", "wpn_uvcannon", "wpn_fogger",
               "wpn_sealant", "wpn_grenade",
               "prop_generator", "prop_station", "prop_vent", "prop_fusebox",
               "prop_panel", "prop_bench")


def split_asset(path, parts=2, dest_dirs=None):
    """Split a too-big asset file into byte-parts stored across DIFFERENT
    folders, plus a <name>.split.json manifest, then remove the original.
    AssetPack reassembles it transparently, so the app still sees one file."""
    data = open(path, "rb").read()
    folder = os.path.dirname(path)
    name = os.path.splitext(os.path.basename(path))[0]
    if dest_dirs is None:
        dest_dirs = [os.path.join(folder, "split_a"),
                     os.path.join(folder, "split_b")]
    chunk = math.ceil(len(data) / parts)
    rel = []
    for i in range(parts):
        d = dest_dirs[i % len(dest_dirs)]
        os.makedirs(d, exist_ok=True)
        pth = os.path.join(d, "%s.p%d" % (name, i))
        with open(pth, "wb") as fh:
            fh.write(data[i * chunk:(i + 1) * chunk])
        rel.append(os.path.relpath(pth, folder))
    with open(os.path.join(folder, name + ".split.json"), "w") as fh:
        json.dump({"parts": rel, "orig": os.path.basename(path)}, fh)
    os.remove(path)
    return rel


class AssetPack:
    def __init__(self, folder):
        self.imgs = {}
        self._scaled = {}
        self.folder = folder
        for name in ASSET_NAMES:
            # base sprite + optional state variants (enemy/boss animations):
            # <name>_run / _hurt / _attack drop in and animate automatically
            for key in (name, name + "_run", name + "_hurt", name + "_attack"):
                surf = self._load(key)
                if surf is not None:
                    self.imgs[key] = surf
        # multi-frame player animations: player_<state>_0.png .. _N.png become a
        # frame SEQUENCE (self.anims[state] -> [keys]) so the draw can cycle them
        self.anims = {}
        for p in sorted(glob.glob(os.path.join(folder, "player_*.png"))):
            key = os.path.basename(p)[:-4]
            mo = re.match(r"(player(?:_[a-z_]+)?)_(\d+)$", key)
            if not mo:
                continue
            try:
                surf = pygame.image.load(p).convert_alpha()
            except Exception:
                continue
            self.imgs[key] = surf
            self.anims.setdefault(mo.group(1), []).append((int(mo.group(2)), key))
        for k in self.anims:
            self.anims[k] = [key for _, key in sorted(self.anims[k])]
        # one shared reference height for ALL of Ty's clips (his idle canvas),
        # so blit_char scales every animation by a single constant factor and he
        # never pops bigger/smaller between states (see blit_char ref_h).
        self.anim_ref = None
        idle = self.anims.get("player")
        if idle:
            self.anim_ref = self.imgs[idle[0]].get_height()

    def _load(self, key):
        """Load <key>.png, or transparently reassemble it from byte-parts
        spread across other folders when it was split (see <key>.split.json)."""
        p = os.path.join(self.folder, key + ".png")
        if os.path.isfile(p):
            try:
                return pygame.image.load(p).convert_alpha()
            except Exception:
                return None
        mani = os.path.join(self.folder, key + ".split.json")
        if os.path.isfile(mani):
            try:
                parts = json.load(open(mani))["parts"]
                data = b"".join(
                    open(pp if os.path.isabs(pp)
                         else os.path.join(self.folder, pp), "rb").read()
                    for pp in parts)
                return pygame.image.load(io.BytesIO(data),
                                         key + ".png").convert_alpha()
            except Exception:
                return None
        return None

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

    def blit_char(self, s, name, feet_x, feet_y, draw_h, flip=False, squash=1.0,
                  ref_h=None):
        """Draw a CHARACTER sprite at a consistent size: scaled uniformly so its
        rendered height == draw_h, and anchored at the feet (bottom-centre at
        feet_x/feet_y). Unlike blit_fit this never lets a wide effect pose (a
        muzzle flash, a slide's dust) shrink the figure — height is the anchor,
        so a character keeps the same on-screen size across every pose/screen.
        `squash` <1 flattens+widens (landing splat), >1 stretches+narrows
        (a jump / a breath) while roughly preserving volume — the juice.

        `ref_h` overrides the height the scale is measured against. Multi-frame
        clips are cut onto per-clip canvases with different headroom (arms-up in
        a jump, tucked in a landing), so normalizing each canvas to draw_h would
        make the BODY pop bigger/smaller every state change. Passing a single
        shared reference (the idle canvas height) applies ONE constant scale to
        every clip — feet stay planted and limbs are free to extend past the
        canvas, so Ty holds a steady size across his whole move-set."""
        img = self.imgs[name]
        aw, ah = img.get_size()
        sc = draw_h / (ref_h or ah)
        dw = max(1, int(aw * sc / squash))
        dh = max(1, int(ah * sc * squash))
        key = ("C", name, dw, dh, flip)
        sp = self._scaled.get(key)
        if sp is None:
            sp = pygame.transform.smoothscale(img, (dw, dh))
            if flip:
                sp = pygame.transform.flip(sp, True, False)
            self._scaled[key] = sp
        s.blit(sp, (int(feet_x - dw / 2), int(feet_y - dh)))


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

    def muzzle(self, x, y, facing, color=C_CHARGE):
        for _ in range(6):
            self._add(x, y, facing * random.uniform(120, 340),
                      random.uniform(-60, 60), random.uniform(0.1, 0.25),
                      random.uniform(2, 4), color, 0)

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
    def __init__(self, x, y, vx, dmg, level, hostile=False, color=None, low=False):
        self.x, self.y, self.vx = x, y, vx
        self.dmg = dmg
        self.level = level          # 0 normal, 1 mid, 2 full (player); -1 toxic
        self.hostile = hostile
        self.color = color          # weapon tint (None = default blaster blue)
        self.low = low              # fired from a crouch — can hit crouch_only mold
        self.r = 6 + level * 5 if level >= 0 else 10
        self.dead = False

    def rect(self):
        return (self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def update(self, dt):
        self.x += self.vx * dt
        # cull off-screen on BOTH axes: an aimed shot can travel near-vertically
        # (never crossing an x bound), so without a y bound it would fly off and
        # its coordinate would overflow the draw layer
        if (self.x < -40 or self.x > LEVEL_W + 40
                or self.y < -400 or self.y > HEIGHT + 400):
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
        col = self.color or C_SHOT
        name = "shot_charged" if self.level >= 1 else "shot"
        if self.color is None and assets.has(name):
            assets.blit_fit(s, name, sx, self.y, self.r * 3, self.r * 3,
                            flip=self.vx < 0)
        else:
            glow(s, sx, self.y, self.r + 7, col, 130)
            fcircle(s, sx, self.y, self.r, col)
            fcircle(s, sx, self.y, self.r * 0.55, (245, 252, 255))


# --------------------------------------------------------------------------- #
# Enemies
# --------------------------------------------------------------------------- #
# kind -> the base idle sprite key (variants <key>_run/_hurt/_attack/... load
# alongside). Used both to draw and to size the hitbox to the drawn art.
ENEMY_ASSET = {
    "sporebot": "sporebot", "moldcrawler": "moldcrawler",
    "toxicsprayer": "toxicsprayer", "moldbat": "moldbat", "moldbat2": "moldbat",
    "steammite": "steammite", "ventswarm": "ventswarm", "sporehawk": "sporehawk",
    "roofleech": "roofleech", "moldmite": "moldmite", "creeper": "creeper",
    "mudstalker": "mudstalker", "centipede": "centipede",
    "pipeparasite": "pipeparasite", "gaspod": "gaspod", "sporeworm": "sporeworm",
    "sentinel": "sentinel", "ventstalker": "ventstalker",
    "cultureswarm": "cultureswarm", "reactorspore": "reactorspore",
    "mycelium": "mycelium", "micromold": "micromold",
    "sporedrifter": "sporedrifter", "toxicslime": "toxicslime",
    "fungusbrute": "fungusbrute", "sporeturret": "sporeturret",
    "corruptcyst": "corruptcyst",
}

# Ground-hugging crawlers that are armoured on top: standing fire pings off, you
# must CROUCH to shoot them out. Kept to single-placed low enemies (never the
# tiny swarms) so the pacing stays fair.
CROUCH_ONLY = {"moldcrawler", "mudstalker"}

# Grappler walls per mission — (x, y_top, w, h) tall faces seated on a platform.
# Placed on platforms with a big AHEAD-clearance so the ground-running
# auto-player never jumps into them (it can't wall-climb) — --selftest stays green.
WALLS_BY = {
    1: [(980, 260, 26, 140), (2260, 280, 26, 140)],
    2: [(1520, 210, 26, 140), (300, 260, 26, 140)],
    3: [(300, 270, 24, 140), (1600, 220, 24, 140)],
    # M4 (Crawlspace) has a low ceiling and no gap wide enough to seat a wall
    # clear of the auto-player's jumps, so it keeps its flatter layout.
    5: [(1180, 160, 26, 140), (340, 260, 26, 140)],
}


class Enemy:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.vx = 0.0
        self.hit = 0.0
        self.atk_anim = 0.0        # brief attack-pose window after firing
        self.shoot_t = random.uniform(0.8, 2.0)
        self.crouch_only = kind in CROUCH_ONLY  # armoured up top — needs a crouch shot
        self.dead = False
        self.t = random.uniform(0, 6.28)
        self.home_y = float(y)
        self.dive_t = random.uniform(1.5, 3.0)
        self.diving = 0.0
        # melee lunge/pounce state (telegraph -> launch)
        self.lunge_cd = random.uniform(1.0, 2.4)
        self.windup = 0.0
        self.lunging = 0.0
        self.lunge_vx = 0.0
        self.gen = 0                  # ventswarm split generation
        self.bat_speed = 80
        self.spore_wind = 0.0         # Spore Drifter: attack wind-up timer
        self.enraged = False          # Spore Drifter: low-HP enraged state
        self.sprite_aspect = None     # drawn-sprite width/height (set on load)
        self.turret_face = 1          # Spore Turret: aim direction
        if kind == "sporebot":
            self.w, self.h, self.hp = 40, 40, 4
            self.vx = -70
            self.dmg = 4
        elif kind == "moldcrawler":   # Mold Crawler — fast skittering clawer
            self.w, self.h, self.hp = 46, 34, 6
            self.dmg = 4
        elif kind in ("moldbat", "moldbat2"):   # flying harassment (V2C5 / V3C2)
            self.w, self.h, self.hp = 36, 26, 3
            self.dmg = 4
            if kind == "moldbat2":
                self.bat_speed = 150
                self.hp = 4
        elif kind == "steammite":     # V3C2 — small, fast ground ambusher
            self.w, self.h, self.hp = 26, 22, 2
            self.dmg = 3
        elif kind == "ventswarm":     # V3C2 — floats, splits unless charged
            self.w, self.h, self.hp = 44, 44, 5
            self.dmg = 4
        elif kind == "sporehawk":     # V4C2 — big attic flyer, dives
            self.w, self.h, self.hp = 56, 40, 6
            self.dmg = 5
            self.bat_speed = 120
        elif kind == "roofleech":     # V4C2 — ceiling, drips down
            self.w, self.h, self.hp = 34, 30, 4
            self.dmg = 4
        elif kind == "micromold":     # Micro Mold — common swarm unit (spore burst)
            self.w, self.h, self.hp = 28, 26, 2
            self.dmg = 3
        elif kind == "sporedrifter":  # Spore Drifter — floating spore-shooter
            self.w, self.h, self.hp = 40, 40, 4
            self.dmg = 3
        elif kind == "toxicslime":    # Toxic Slime — slow corrosive ground blob
            self.w, self.h, self.hp = 46, 34, 6
            self.dmg = 3
        elif kind == "fungusbrute":   # Fungus Brute — large heavy elite (club)
            self.w, self.h, self.hp = 58, 54, 14
            self.dmg = 5
        elif kind == "sporeturret":   # Spore Turret — stationary platform cannon
            self.w, self.h, self.hp = 40, 42, 5
            self.dmg = 4
        elif kind == "corruptcyst":   # Corrupt Cyst — slow blob, bursts on death
            self.w, self.h, self.hp = 42, 38, 5
            self.dmg = 4
        elif kind == "moldmite":      # V4C2 — tiny swarm unit
            self.w, self.h, self.hp = 20, 18, 1
            self.dmg = 2
        elif kind == "creeper":       # V4C2 — insulation ambusher, slow
            self.w, self.h, self.hp = 42, 28, 6
            self.dmg = 4
        elif kind == "mudstalker":    # V5C2 — mud ambusher
            self.w, self.h, self.hp = 40, 30, 4
            self.dmg = 4
        elif kind == "centipede":     # V5C2 — segmented, splits
            self.w, self.h, self.hp = 48, 24, 6
            self.dmg = 4
        elif kind == "pipeparasite":  # V5C2 — clings, sprays water
            self.w, self.h, self.hp = 32, 40, 5
            self.dmg = 4
        elif kind == "gaspod":        # V5C2 — stationary gas hazard
            self.w, self.h, self.hp = 34, 40, 4
            self.dmg = 5
        elif kind == "sporeworm":     # V5C2 — fast burrower
            self.w, self.h, self.hp = 38, 24, 3
            self.dmg = 4
        elif kind == "sentinel":      # V6C2 — armored construct
            self.w, self.h, self.hp = 44, 52, 12
            self.dmg = 5
        elif kind == "ventstalker":   # V6C2 — fast ceiling attacker
            self.w, self.h, self.hp = 40, 30, 5
            self.dmg = 5
            self.bat_speed = 165
        elif kind == "cultureswarm":  # V6C2 — floats, merges/splits
            self.w, self.h, self.hp = 46, 46, 5
            self.dmg = 4
        elif kind == "reactorspore":  # V6C2 — stationary energy pulser
            self.w, self.h, self.hp = 40, 44, 7
            self.dmg = 5
        elif kind == "mycelium":      # V6C2 — security growth shooter
            self.w, self.h, self.hp = 36, 46, 8
            self.dmg = 4
        else:  # toxicsprayer
            self.w, self.h, self.hp = 40, 48, 6
            self.dmg = 4

    def rect(self):
        # Sprite enemies are drawn height-normalised to self.h*CHAR_H and
        # feet-anchored, so their art is bigger than the raw (w,h). Return a
        # collision box that matches the DRAWN sprite (with a small inset for
        # fairness) so shots and contacts land where the animation actually is.
        asp = self.sprite_aspect
        if not asp:
            return (self.x, self.y, self.w, self.h)
        dh = self.h * CHAR_H * 0.90
        dw = dh * asp * 0.86
        cx = self.x + self.w / 2
        feet = self.y + self.h
        return (cx - dw / 2, feet - dh, dw, dh)

    def update(self, dt, player, shots, parts, acids=None):
        self.hit = max(0.0, self.hit - dt)
        self.atk_anim = max(0.0, self.atk_anim - dt)
        self.t += dt
        if self.kind == "sporebot":
            self.x += self.vx * dt
            # patrol turn-around on level edges / simple bounds
            if self.x < 60 or self.x > LEVEL_W - 100:
                self.vx *= -1
        elif self.kind in ("moldbat", "moldbat2", "ventstalker"):
            # circle the player, then dive-bomb (Mk II / Vent Stalker dive faster)
            d = player.x - self.x
            self.x += (1 if d > 0 else -1) * self.bat_speed * dt
            self.dive_t -= dt
            gap = 1.2 if self.kind != "moldbat" else 2.0
            if self.dive_t <= 0 and abs(d) < 340 and self.diving <= 0:
                self.diving = 0.6
                self.dive_t = random.uniform(gap, gap + 1.4)
            if self.diving > 0:
                self.diving -= dt
                self.atk_anim = 0.3            # dive is the attack
                self.y += (player.y - self.y) * min(1.0, dt * (5 if self.kind == "moldbat2" else 4))
            else:
                self.y += (self.home_y + math.sin(self.t * 3) * 26 - self.y) \
                    * min(1.0, dt * 3)
        elif self.kind in ("moldcrawler", "steammite", "moldmite", "mudstalker",
                            "centipede", "sporeworm", "sentinel", "creeper",
                            "micromold"):
            # ground stalkers: chase, telegraph (rear back), then pounce
            d = player.x - self.x
            face = 1 if d > 0 else -1
            sp = {"moldcrawler": 105, "steammite": 165, "moldmite": 190,
                  "mudstalker": 90, "centipede": 85, "sporeworm": 155,
                  "sentinel": 55, "creeper": 45, "micromold": 120}[self.kind]
            # the Mold Crawler is a fast skitterer that goes INFECTED (enraged,
            # even quicker) once wounded
            if self.kind == "moldcrawler":
                self.enraged = self.hp <= 2
                if self.enraged:
                    sp = 150
            self.lunge_cd = max(0.0, self.lunge_cd - dt)
            if self.windup > 0:                        # telegraph the pounce
                self.windup -= dt
                self.x -= face * 46 * dt
                self.vx = 0
                if self.windup <= 0:
                    self.lunge_vx = face * (360 if self.kind == "sentinel" else 520)
                    self.lunging = 0.30
                    self.atk_anim = 0.45
            elif self.lunging > 0:                      # the pounce itself
                self.lunging -= dt
                self.x += self.lunge_vx * dt
                self.vx = self.lunge_vx
            elif self.kind == "creeper":                # slime lobs acid, no pounce
                self.x += face * sp * dt
                self.vx = face * sp
                self.shoot_t -= dt
                if self.shoot_t <= 0 and 100 < abs(d) < 360:
                    self.shoot_t = random.uniform(2.0, 3.4)
                    self.atk_anim = 0.4
                    blob = Shot(self.x + self.w / 2, self.y, face * 150, 4, -1,
                                hostile=True)
                    blob.vy = -300
                    blob.grav = 900
                    shots.append(blob)
            elif self.kind == "micromold":              # common swarm: steady crawl,
                self.x += face * sp * dt                 # no pounce (a lunge could leap
                self.vx = face * sp                      # into a spike lane and shove Ty)
            elif self.lunge_cd <= 0 and abs(d) < 150:   # in range -> wind up
                self.windup = 0.30
                self.lunge_cd = random.uniform(2.2, 3.6)
                self.vx = 0
            else:                                        # normal chase
                self.x += face * sp * dt
                self.vx = face * sp
        elif self.kind in ("gaspod", "reactorspore"):
            # stationary emplacements: gaspod puffs upward gas, reactorspore
            # detonates a radial energy burst
            self.shoot_t -= dt
            rng = 340 if self.kind == "reactorspore" else 260
            if self.shoot_t <= 0 and abs(player.x - self.x) < rng:
                self.shoot_t = random.uniform(1.8, 2.8)
                self.atk_anim = 0.4
                cx, cy = self.x + self.w / 2, self.y + self.h / 2
                if self.kind == "reactorspore":
                    for ang in range(0, 360, 60):       # 6-way radial burst
                        a = math.radians(ang)
                        sh = Shot(cx, cy, math.cos(a) * 210, 4, -1, hostile=True)
                        sh.vy = math.sin(a) * 210
                        shots.append(sh)
                else:
                    for dvx in (-100, 0, 100):          # gas puff spread up
                        sh = Shot(cx, self.y, dvx, 4, -1, hostile=True)
                        sh.vy = -70
                        shots.append(sh)
        elif self.kind == "corruptcyst":
            # Corrupt Cyst: a slow pulsating blob. Rolls toward Ty and lobs an
            # arcing acid glob; when killed it BURSTS (handled in Game._split) —
            # a radial spore spatter, so finishing it point-blank is risky.
            d = player.x - self.x
            face = 1 if d > 0 else -1
            self.x += face * 40 * dt
            self.vx = face * 40
            self.shoot_t -= dt
            if self.shoot_t <= 0 and 70 < abs(d) < 340:
                self.shoot_t = random.uniform(2.2, 3.4)
                self.atk_anim = 0.4
                cx = self.x + self.w / 2 + face * self.w * 0.4
                glob = Shot(cx, self.y + 8, face * 165, 4, -1, hostile=True)
                glob.vy = -250
                glob.grav = 780
                shots.append(glob)
        elif self.kind == "sporeturret":
            # Spore Turret: a STATIONARY platform-mounted cannon. It never moves
            # (mounted on the level's platforms/ledges); it rotates to track Ty
            # and fires an aimed spore shot, so it can pepper him from above.
            self.vx = 0
            d = player.x - self.x
            self.turret_face = 1 if d > 0 else -1
            self.shoot_t -= dt
            if self.shoot_t <= 0 and abs(d) < 360:
                self.shoot_t = random.uniform(1.6, 2.6)
                self.atk_anim = 0.4
                cx = self.x + self.w / 2 + self.turret_face * self.w * 0.4
                cy = self.y + self.h * 0.4
                tx = player.x + player.w / 2 - cx
                ty = player.y + player.h / 2 - cy
                dist = max(1.0, math.hypot(tx, ty))
                spd = 230
                sh = Shot(cx, cy, tx / dist * spd, 4, -1, hostile=True)
                sh.vy = ty / dist * spd
                shots.append(sh)
        elif self.kind == "fungusbrute":
            # Fungus Brute: a large, heavy elite. Lumbers toward Ty (its club
            # deals heavy contact damage) and hurls arcing toxic spores; when
            # wounded it ENRAGES — faster, with a spore-burst spread.
            self.enraged = self.hp <= 5
            d = player.x - self.x
            face = 1 if d > 0 else -1
            sp = 80 if self.enraged else 48
            self.x += face * sp * dt
            self.vx = face * sp
            self.shoot_t -= dt
            if self.shoot_t <= 0 and 90 < abs(d) < 430:
                self.shoot_t = random.uniform(1.6, 2.4) if self.enraged \
                    else random.uniform(2.6, 3.8)
                self.atk_anim = 0.4
                cx, cy = self.x + self.w / 2 + face * self.w * 0.4, self.y + 12
                glob = Shot(cx, cy, face * 175, 5, -1, hostile=True)
                glob.vy = -240
                glob.grav = 760
                shots.append(glob)
                if self.enraged:                    # spore burst spread
                    for dvx in (face * 90, face * 275):
                        g2 = Shot(cx, cy, dvx, 5, -1, hostile=True)
                        g2.vy = -300
                        g2.grav = 760
                        shots.append(g2)
        elif self.kind == "toxicslime":
            # Toxic Slime: a slow corrosive blob. Crawls toward Ty, spits an
            # arcing acid glob at him, and leaves short-lived ACID POOLS in its
            # wake (its signature — they damage anything that stands in them).
            # Once wounded it ENRAGES: faster, and its spit becomes a spread.
            self.enraged = self.hp <= 2
            d = player.x - self.x
            face = 1 if d > 0 else -1
            sp = 48 if self.enraged else 28
            self.x += face * sp * dt
            self.vx = face * sp
            self.drip_t = getattr(self, "drip_t", 1.0) - dt
            if self.drip_t <= 0 and acids is not None:
                self.drip_t = random.uniform(0.8, 1.4)
                acids.append([self.x + self.w / 2, self.y + self.h - 2,
                              19, 2.6, 2.6])
            self.shoot_t -= dt
            if self.shoot_t <= 0 and 60 < abs(d) < 300:
                self.shoot_t = random.uniform(1.3, 2.0) if self.enraged \
                    else random.uniform(2.2, 3.4)
                self.atk_anim = 0.4
                mx = self.x + self.w / 2 + face * self.w * 0.5   # from the mouth
                my = self.y + 8
                glob = Shot(mx, my, face * 150, 3, -1, hostile=True)
                glob.vy = -260
                glob.grav = 820
                shots.append(glob)
                if self.enraged:                    # corrosive spread when enraged
                    for dvx in (face * 60, face * 240):
                        g2 = Shot(mx, my, dvx, 3, -1, hostile=True)
                        g2.vy = -300
                        g2.grav = 820
                        shots.append(g2)
        elif self.kind == "sporedrifter":
            # Spore Drifter: floats through the air toward Ty, hovering on a
            # gentle bob, and fires a spore shot aimed at him (the attack that
            # damages Ty). It telegraphs each shot with a brief CHARGE wind-up,
            # and once wounded it ENRAGES — drifting/firing faster and loosing a
            # 3-way spore spread instead of a single bolt.
            self.enraged = self.hp <= 2
            drift = 66 if self.enraged else 42
            d = player.x - self.x
            face = 1 if d > 0 else -1
            if abs(d) > 150:                       # drift in, but hover once close
                self.x += face * drift * dt
                self.vx = face * drift
            else:
                self.vx = 0
            # slow vertical float toward Ty's level (uses float-up / float-down)
            aim_y = min(GROUND_Y - 120, player.y - 40)
            self.home_y += (aim_y - self.home_y) * min(1.0, dt * 0.5)
            self.y = self.home_y + math.sin(self.t * (3.0 if self.enraged else 2.2)) * 22
            if self.spore_wind > 0:                # winding up (charge pose)
                self.spore_wind -= dt
                self.vx = 0
                if self.spore_wind <= 0:           # release the spore(s)
                    self.atk_anim = 0.35
                    cx, cy = self.x + self.w / 2, self.y + self.h / 2
                    tx = player.x + player.w / 2 - cx
                    ty = player.y + player.h / 2 - cy
                    dist = max(1.0, math.hypot(tx, ty))
                    spd = 210
                    ux, uy = tx / dist, ty / dist
                    ex, ey = cx + ux * self.w * 0.45, cy + uy * self.h * 0.4
                    spread = (-0.30, 0.0, 0.30) if self.enraged else (0.0,)
                    for a in spread:               # rotate the aim vector by a
                        rx = ux * math.cos(a) - uy * math.sin(a)
                        ry = ux * math.sin(a) + uy * math.cos(a)
                        sh = Shot(ex, ey, rx * spd, 3, -1, hostile=True)
                        sh.vy = ry * spd
                        shots.append(sh)
            else:
                self.shoot_t -= dt
                if self.shoot_t <= 0 and abs(d) < 320:
                    self.shoot_t = random.uniform(1.4, 2.2) if self.enraged \
                        else random.uniform(2.0, 3.2)
                    self.spore_wind = 0.32         # telegraph before firing
        elif self.kind in ("ventswarm", "cultureswarm"):
            d = player.x - self.x
            self.x += (1 if d > 0 else -1) * 55 * dt
            self.y = self.home_y + math.sin(self.t * 2) * 30
        elif self.kind == "sporehawk":
            d = player.x - self.x
            self.x += (1 if d > 0 else -1) * self.bat_speed * dt
            self.dive_t -= dt
            if self.dive_t <= 0 and abs(d) < 380 and self.diving <= 0:
                self.diving = 0.7
                self.dive_t = random.uniform(2.2, 3.6)
            if self.diving > 0:
                self.diving -= dt
                self.y += (player.y - self.y) * min(1.0, dt * 4)
            else:
                self.y += (self.home_y + math.sin(self.t * 2) * 40 - self.y) \
                    * min(1.0, dt * 3)
        elif self.kind == "roofleech":
            self.shoot_t -= dt
            if self.shoot_t <= 0 and abs(player.x - self.x) < 240:
                self.shoot_t = random.uniform(1.4, 2.4)
                sh = Shot(self.x + self.w / 2, self.y + self.h, 0, 4, -1, hostile=True)
                sh.vy = 300
                shots.append(sh)
        elif self.kind == "mycelium":                     # ground-level shooter
            self.shoot_t -= dt
            if self.shoot_t <= 0 and abs(player.x - self.x) < 480:
                self.shoot_t = random.uniform(1.5, 2.5)
                self.atk_anim = 0.4
                face = 1 if player.x > self.x else -1
                shots.append(Shot(self.x + self.w / 2, self.y + 18, face * 270,
                                  4, -1, hostile=True))
        elif self.kind == "pipeparasite":   # clings high, sprays water DOWN at Ty
            self.shoot_t -= dt
            if self.shoot_t <= 0 and abs(player.x - self.x) < 460:
                self.shoot_t = random.uniform(1.5, 2.5)
                self.atk_anim = 0.4
                # aim the spray at Ty so it actually reaches the ground lane,
                # instead of a flat shot that flies over his head
                cx, cy = self.x + self.w / 2, self.y + self.h
                tx = player.x + player.w / 2 - cx
                ty = player.y + player.h / 2 - cy
                dist = max(1.0, math.hypot(tx, ty))
                spd = 250
                sh = Shot(cx, cy, tx / dist * spd, 4, -1, hostile=True)
                sh.vy = ty / dist * spd
                shots.append(sh)
        else:  # toxicsprayer shoots
            self.shoot_t -= dt
            if self.shoot_t <= 0 and abs(player.x - self.x) < 520:
                self.shoot_t = random.uniform(1.6, 2.6)
                self.atk_anim = 0.4
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
        asset = ENEMY_ASSET[self.kind]
        # state-based pose: hurt > charge > attack > walk-cycle > idle (variants
        # auto-load). The Spore Drifter swaps its idle/drift base for an ENRAGED
        # look once wounded, and shows a CHARGE pose while winding up a shot.
        base = asset
        if self.kind in ("sporedrifter", "toxicslime", "moldcrawler",
                         "fungusbrute") \
                and getattr(self, "enraged", False) \
                and assets.has(asset + "_enraged"):
            base = asset + "_enraged"
        want = base
        bob = 0.0
        if self.hit > 0 and assets.has(asset + "_hurt"):
            want = asset + "_hurt"
        elif getattr(self, "spore_wind", 0.0) > 0 and assets.has(asset + "_charge"):
            want = asset + "_charge"
        elif getattr(self, "atk_anim", 0.0) > 0 and assets.has(asset + "_attack"):
            want = asset + "_attack"
        elif abs(self.vx) > 8:
            # animate the walk: alternate the move pose with the idle pose on a
            # timer + a little step-bob, so movement reads as motion not a slide
            if int(self.t * 9) % 2 == 0 and assets.has(asset + "_run"):
                want = asset + "_run"
            else:
                want = base
            bob = -abs(math.sin(self.t * 9)) * 3.0
        else:
            bob = math.sin(self.t * 3) * 1.5      # gentle idle breathing
        # apply the motion bob to EVERY draw path (sprite or vector) so a moving
        # character always reads as moving, even without dedicated animation art
        y += bob
        cy += bob
        if assets.has(want):
            # idle breathing pulse + a quick squash on hit, so every enemy is
            # visibly alive even between its keyframes
            breath = 1.0 + 0.045 * math.sin(self.t * 3.2 + self.x * 0.01)
            if self.hit > 0:
                breath *= 0.9
            flip = (self.turret_face < 0 if self.kind == "sporeturret"
                    else self.vx < 0)
            assets.blit_char(s, want, cx, y + self.h, self.h * CHAR_H,
                             flip=flip, squash=breath)
        elif self.kind == "sentinel":
            orrect(s, (x + 4, y + 8, self.w - 8, self.h - 8), C_LAB_DK, 6)
            orrect(s, (x + 8, y + 12, self.w - 16, 12), C_LAB, 4)
            fcircle(s, cx, y + 8, 9, (90, 110, 130))
            fcircle(s, cx, y + 8, 4, (150, 240, 160))
        elif self.kind in ("ventstalker",):
            flap = math.sin(self.t * 14) * 6
            for wdir in (-1, 1):
                pygame.draw.polygon(s, C_LAB_DK, [
                    (cx, cy), (cx + wdir * 22, cy - 8 - flap), (cx + wdir * 18, cy + 8)])
            fcircle(s, cx, cy, self.h * 0.42, (80, 100, 120))
            fcircle(s, cx - 5, cy - 2, 3, (170, 255, 180))
            fcircle(s, cx + 5, cy - 2, 3, (170, 255, 180))
        elif self.kind == "cultureswarm":
            for k in range(8):
                ang = self.t * 2 + k * 0.8
                rr = self.w * (0.18 + 0.16 * (k % 3))
                fcircle(s, cx + math.cos(ang) * rr, cy + math.sin(ang) * rr, 6,
                        C_PRIME if k % 2 else (120, 200, 140))
            fcircle(s, cx, cy, 7, C_PRIME_DK)
        elif self.kind == "reactorspore":
            glow(s, cx, cy, self.w * 0.9, (150, 120, 200), 70)
            fcircle(s, cx, cy, self.w * 0.4, C_PRIME_DK)
            fcircle(s, cx, cy, self.w * 0.24, C_PRIME)
        elif self.kind == "mycelium":
            orrect(s, (x + 6, y, self.w - 12, self.h), C_LAB_DK, 4)
            for k in range(3):
                fcircle(s, cx, y + 8 + k * 14, 6, (120, 200, 150))
        elif self.kind in ("mudstalker", "sporeworm"):
            pygame.draw.ellipse(s, C_MUD_DK, (int(x), int(y + 6), self.w, self.h))
            fcircle(s, cx, cy + 4, self.h * 0.34, (100, 130, 70))
            fcircle(s, cx - 6, cy, 3, (230, 240, 190))
            fcircle(s, cx + 6, cy, 3, (230, 240, 190))
        elif self.kind == "centipede":
            for k in range(5):
                sx2 = x + 6 + k * (self.w - 12) / 4
                fcircle(s, sx2, cy, 8, C_MUD_DK)
                fcircle(s, sx2, cy, 5, (120, 150, 80))
            fcircle(s, x + self.w, cy - 2, 3, (240, 240, 190))
        elif self.kind == "pipeparasite":
            pygame.draw.rect(s, (90, 96, 100), (int(cx - 4), int(y), 8, self.h))
            fcircle(s, cx, cy, self.w * 0.42, C_MOLD_DK)
            fcircle(s, cx, cy, self.w * 0.24, (120, 170, 200))
        elif self.kind == "gaspod":
            glow(s, cx, cy, self.w * 0.9, C_GAS, 60)
            pygame.draw.ellipse(s, C_MUD_DK, (int(x), int(y), self.w, self.h))
            fcircle(s, cx, cy, self.w * 0.3, C_GAS)
        elif self.kind == "sporehawk":
            flap = math.sin(self.t * 12) * 10
            for wdir in (-1, 1):
                pygame.draw.polygon(s, C_WOOD_DK, [
                    (cx, cy), (cx + wdir * 32, cy - 10 - flap), (cx + wdir * 26, cy + 12)])
            fcircle(s, cx, cy, self.h * 0.42, (110, 90, 60))
            fcircle(s, cx - 7, cy - 3, 4, (250, 210, 120))
            fcircle(s, cx + 7, cy - 3, 4, (250, 210, 120))
        elif self.kind == "roofleech":
            pygame.draw.ellipse(s, C_MOLD_DK, (int(x), int(y), self.w, self.h))
            fcircle(s, cx, y + self.h, 5, C_MOLD)
            fcircle(s, cx - 5, cy, 3, (200, 240, 160))
            fcircle(s, cx + 5, cy, 3, (200, 240, 160))
        elif self.kind == "moldmite":
            fcircle(s, cx, cy, self.h * 0.5, C_MOLD_DK)
            fcircle(s, cx, cy, self.h * 0.3, (140, 190, 90))
        elif self.kind == "corruptcyst":             # pulsating eyeball blob
            pulse = 1.0 + 0.06 * math.sin(self.t * 4)
            fcircle(s, cx, cy, self.h * 0.5 * pulse, (96, 74, 110))
            fcircle(s, cx, cy, self.h * 0.34 * pulse, (120, 90, 60))
            fcircle(s, cx, cy, self.h * 0.2, C_TOXIC)
            fcircle(s, cx, cy, self.h * 0.09, (30, 40, 20))
        elif self.kind == "sporeturret":             # stationary platform cannon
            pygame.draw.rect(s, (60, 66, 58), (int(x + 4), int(y + self.h * 0.6),
                                               self.w - 8, int(self.h * 0.4)))
            fcircle(s, cx, cy, self.h * 0.34, (70, 80, 66))
            fcircle(s, cx + self.turret_face * 5, cy, self.h * 0.2, C_TOXIC)
            for k in range(3):                       # mushroom caps
                fcircle(s, x + 8 + k * (self.w - 16) / 2, y + 4, 4, (150, 90, 150))
        elif self.kind == "fungusbrute":             # large club-wielding ogre
            pygame.draw.ellipse(s, (86, 104, 54),
                                (int(x), int(y + self.h * 0.2),
                                 self.w, int(self.h * 0.8)))
            fcircle(s, cx, cy - 4, self.w * 0.3, (110, 130, 66))
            for k in range(3):                       # mushroom caps
                fcircle(s, x + 12 + k * (self.w - 24) / 2, y + 6, 6, (150, 90, 150))
            fcircle(s, cx - 8, cy, 4, (210, 240, 120))
            fcircle(s, cx + 8, cy, 4, (210, 240, 120))
        elif self.kind == "toxicslime":              # corrosive ground blob
            glow(s, cx, y + self.h, self.w * 0.7, C_TOXIC, 55)
            pygame.draw.ellipse(s, (120, 150, 40),
                                (int(x), int(y + self.h * 0.3),
                                 self.w, int(self.h * 0.8)))
            fcircle(s, cx, cy, self.h * 0.32, (150, 190, 70))
            fcircle(s, cx - 6, cy - 2, 3, (40, 60, 20))
            fcircle(s, cx + 6, cy - 2, 3, (40, 60, 20))
        elif self.kind == "sporedrifter":            # floating spore jelly
            glow(s, cx, cy, self.w * 0.8, (150, 210, 90), 55)
            fcircle(s, cx, cy - 2, self.h * 0.4, (96, 70, 130))
            for k in range(5):                       # dangling tentacles
                tx = x + 6 + k * (self.w - 12) / 4
                pygame.draw.line(s, (70, 50, 100), (tx, cy),
                                 (tx, y + self.h + math.sin(self.t * 5 + k) * 4), 3)
            fcircle(s, cx - 6, cy - 2, 4, (180, 240, 120))
            fcircle(s, cx + 6, cy - 2, 4, (180, 240, 120))
        elif self.kind == "creeper":
            pygame.draw.ellipse(s, C_WOOD_DK, (int(x), int(y + 4), self.w, self.h))
            for k in range(4):
                fcircle(s, x + 8 + k * 9, y + 4, 5, (130, 160, 90))
            fcircle(s, cx - 7, cy, 3, (240, 240, 200))
            fcircle(s, cx + 7, cy, 3, (240, 240, 200))
        elif self.kind == "steammite":
            col = (150, 200, 150)
            fcircle(s, cx, cy, self.h * 0.5, C_MOLD_DK)
            fcircle(s, cx, cy, self.h * 0.32, col)
            for lx in (-1, 1):
                pygame.draw.line(s, (20, 30, 20), (cx, cy),
                                 (cx + lx * 12, cy + 8), 2)
            fcircle(s, cx - 3, cy - 2, 2, (240, 255, 240))
            fcircle(s, cx + 3, cy - 2, 2, (240, 255, 240))
        elif self.kind == "ventswarm":
            for k in range(7):
                ang = self.t * 2 + k * 0.9
                r = self.w * (0.2 + 0.16 * (k % 3))
                fcircle(s, cx + math.cos(ang) * r, cy + math.sin(ang) * r,
                        6, C_MOLD if k % 2 else C_TOXIC)
            fcircle(s, cx, cy, 7, C_MOLD_DK)
        elif self.kind in ("moldbat", "moldbat2"):
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
        bkey = "boss"
        if self.slam > 0 and assets.has("boss_attack"):
            bkey = "boss_attack"   # ground-pound stomp pose during a slam
        elif self.weak_open > 0 and assets.has("boss_hurt"):
            bkey = "boss_hurt"     # rears/enrages while the chest valve is open
        if assets.has(bkey):
            assets.blit_char(s, bkey, cx, cy + self.h / 2, self.h * BOSS_H,
                             flip=True,
                             squash=1.0 + 0.03 * math.sin(self.t * 2.4))
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
# Boss — SHOWER BEAST (Level 2, V3C3)
# --------------------------------------------------------------------------- #
class ShowerBeast:
    """Second Mold General. Water blasts, steam+swarms at 65%, charges at 25%.
    Back-mounted pressure-regulator weak point opens after slam attacks."""
    NAME = "SHOWER BEAST"

    def __init__(self):
        self.w, self.h = 250, 300
        self.home_x = LEVEL_W - self.w - 60
        self.x = self.home_x
        self.y = GROUND_Y - self.h
        self.hp = self.maxhp = BEAST_HP
        self.hit = 0.0
        self.t = 0.0
        self.attack_t = 1.4
        self.weak_open = 0.0
        self.summon_t = 3.5
        self.slam = 0.0
        self.charge_t = 0.0
        self.dead = False
        self.bob = 0.0

    def phase(self):
        f = self.hp / self.maxhp
        return 3 if f <= 0.25 else (2 if f <= 0.65 else 1)

    def rect(self):
        return (self.x + 24, self.y + 40 + self.bob, self.w - 48, self.h - 70)

    def weak_rect(self):
        # pressure regulator on the back (right side)
        return (self.x + self.w * 0.6, self.y + self.h * 0.3 + self.bob,
                self.w * 0.3, self.h * 0.22)

    def update(self, dt, player, shots, parts, enemies):
        self.t += dt
        self.hit = max(0.0, self.hit - dt)
        self.weak_open = max(0.0, self.weak_open - dt)
        self.slam = max(0.0, self.slam - dt)
        ph = self.phase()
        self.bob = math.sin(self.t * 2.0) * 8

        if self.charge_t > 0:                        # P3 charge across the room
            self.charge_t -= dt
            self.x += (1 if player.x > self.x else -1) * 340 * dt
            self.x = max(CAM_BOSS + 20, min(LEVEL_W - self.w, self.x))
        else:
            self.x += (self.home_x - self.x) * min(1.0, dt * 2)

        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = 0.8 if ph == 3 else (1.2 if ph == 2 else 1.5)
            mode = int(self.t) % 2
            mx, my = self.x + 30, self.y + self.h * 0.4 + self.bob
            if mode == 0:                            # high-pressure water blast
                for dy in (-40, 0, 40):
                    sh = Shot(mx, my, -360, 4, -1, hostile=True)
                    sh.vy = dy
                    shots.append(sh)
            else:                                    # pipe slam → opens weak point
                self.slam = 0.3
                parts.splat(self.x + 30, GROUND_Y, C_WATER, 22)
                self.weak_open = 1.9
            if ph == 3 and self.charge_t <= 0 and random.random() < 0.5:
                self.charge_t = 0.8                  # lunge
        if ph >= 2:                                  # steam phase — vent swarms
            self.summon_t -= dt
            if self.summon_t <= 0 and len([e for e in enemies if not e.dead]) < 5:
                self.summon_t = 4.0
                sx = max(CAM_BOSS + 40, player.x + random.choice([-160, 160]))
                sw = Enemy("ventswarm", sx, GROUND_Y - 180)
                sw.home_y = GROUND_Y - 180
                enemies.append(sw)

    def hurt(self, dmg, parts):
        self.hp -= dmg
        self.hit = 0.1
        parts.spark(self.x + self.w * 0.6, self.y + self.h * 0.4, C_SHOT, 8, 240)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def draw(self, s, cam, assets):
        x, y = self.x - cam, self.y + self.bob
        cx, cy = x + self.w / 2, y + self.h / 2
        glow(s, cx, cy, self.w * 0.6, (90, 130, 150), 70)
        if self.slam > 0:
            pygame.draw.rect(s, C_WATER, (0, GROUND_Y - 4, WIDTH, 4))
        bkey = "boss2"
        if self.weak_open > 0 and assets.has("boss2_hurt"):
            bkey = "boss2_hurt"    # phase-shift glow while the core is exposed
        if assets.has(bkey):
            assets.blit_char(s, bkey, cx, cy + self.h / 2, self.h * BOSS_H,
                             squash=1.0 + 0.03 * math.sin(self.t * 2.4))
        else:
            # bathtub/tile creature
            pygame.draw.ellipse(s, C_TILE_DK, (int(x), int(y + 30), self.w, self.h - 30))
            pygame.draw.ellipse(s, C_TILE, (int(x + 18), int(y + 44),
                                self.w - 36, self.h - 80))
            random.seed(2)
            for i in range(12):
                bx = x + 30 + random.random() * (self.w - 60)
                by = y + 50 + random.random() * (self.h - 100)
                fcircle(s, bx, by, random.randint(8, 18), C_TILE_DK)
                fcircle(s, bx, by, 4, (120, 200, 120))
            for ex in (cx - 34, cx + 34):
                fcircle(s, ex, cy - 40, 15, (170, 240, 255))
                fcircle(s, ex, cy - 40, 7, (20, 40, 50))
            # venting steam
            for k in range(4):
                sx2 = cx + (k - 1.5) * 40
                fcircle(s, sx2, y + 20 - (self.t * 40 + k * 20) % 40,
                        10, (*C_STEAM, 60))
        # back weak point (pressure regulator)
        wx, wy, ww, wh = self.weak_rect()
        wx -= cam
        if self.weak_open > 0:
            glow(s, wx + ww / 2, wy + wh / 2, ww * 0.9, (160, 230, 255), 160)
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.4, (180, 240, 255))
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.2, (40, 80, 100))
        else:
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.34, (60, 70, 74))
        if self.hit > 0:
            fl = pygame.Surface((self.w * 2, self.h * 2), pygame.SRCALPHA)
            fcircle(fl, self.w, self.h, self.w * 0.55, (255, 255, 255, 90))
            s.blit(fl, (cx - self.w, cy - self.h))


# --------------------------------------------------------------------------- #
# Boss — SPORE QUEEN (Level 3, V4C3)
# --------------------------------------------------------------------------- #
class SporeQueen:
    """Third Mold General. Hovers, controls spores + wind. Core weak point under
    the crown opens after a wind channel. Summons Mold Mites / Spore Hawks."""
    NAME = "SPORE QUEEN"

    def __init__(self):
        self.w, self.h = 210, 210
        self.home_x = LEVEL_W - self.w - 120
        self.x = self.home_x
        self.y = 310.0
        self.hp = self.maxhp = QUEEN_HP
        self.hit = 0.0
        self.t = 0.0
        self.attack_t = 1.3
        self.weak_open = 0.0
        self.summon_t = 3.0
        self.slam = 0.0
        self.dead = False
        self.bob = 0.0

    def phase(self):
        f = self.hp / self.maxhp
        return 3 if f <= 0.3 else (2 if f <= 0.7 else 1)

    def rect(self):
        return (self.x + 20, self.y + 30 + self.bob, self.w - 40, self.h - 40)

    def weak_rect(self):
        return (self.x + self.w * 0.36, self.y + self.h * 0.45 + self.bob,
                self.w * 0.28, self.h * 0.24)

    def update(self, dt, player, shots, parts, enemies):
        self.t += dt
        self.hit = max(0.0, self.hit - dt)
        self.weak_open = max(0.0, self.weak_open - dt)
        ph = self.phase()
        self.bob = math.sin(self.t * 1.8) * 16
        self.x += (self.home_x - self.x) * min(1.0, dt * 1.5)

        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = 0.8 if ph == 3 else (1.1 if ph == 2 else 1.5)
            mx, my = self.x + self.w * 0.4, self.y + self.h * 0.5 + self.bob
            n = 2 + ph
            for i in range(n):
                ang = math.atan2((player.y + 20) - my, player.x - mx)
                ang += (i - (n - 1) / 2) * 0.26
                sp = 280 + ph * 25
                sh = Shot(mx, my, math.cos(ang) * sp, 4, -1, hostile=True)
                sh.vy = math.sin(ang) * sp
                shots.append(sh)
            self.weak_open = 1.8                    # wind channel exposes the core
            parts.spark(mx, my, C_TOXIC, 6, 120)
        # summons: mites (P1+), hawks (P2+)
        self.summon_t -= dt
        if self.summon_t <= 0 and len([e for e in enemies if not e.dead]) < 7:
            self.summon_t = 3.0 if ph == 1 else 2.2
            sx = max(CAM_BOSS + 40, min(LEVEL_W - 90,
                     player.x + random.choice([-180, 180])))
            if ph >= 2 and random.random() < 0.5:
                hk = Enemy("sporehawk", sx, 220)
                hk.home_y = 220
                enemies.append(hk)
            else:
                for k in range(3):
                    enemies.append(Enemy("moldmite", sx + k * 22, GROUND_Y - 18))

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
        glow(s, cx, cy, self.w * 0.6, (150, 130, 60), 70)
        bkey = "boss3"
        if self.weak_open > 0 and assets.has("boss3_hurt"):
            bkey = "boss3_hurt"
        if assets.has(bkey):
            assets.blit_char(s, bkey, cx, cy + self.h / 2, self.h * BOSS_H,
                             squash=1.0 + 0.03 * math.sin(self.t * 2.4))
        else:
            # spore-membrane wings
            for wdir in (-1, 1):
                pygame.draw.polygon(s, (90, 74, 46), [
                    (cx, cy), (cx + wdir * 120, cy - 60), (cx + wdir * 96, cy + 60)])
            pygame.draw.ellipse(s, C_WOOD_DK, (int(x + 40), int(y + 20),
                                self.w - 80, self.h - 30))
            # crown of trusses
            for k in range(5):
                kx = cx + (k - 2) * 20
                pygame.draw.line(s, C_WOOD, (kx, y + 30), (kx, y - 4), 4)
            for ex in (cx - 26, cx + 26):
                fcircle(s, ex, cy - 20, 12, (250, 200, 90))
                fcircle(s, ex, cy - 20, 6, (60, 30, 10))
            # shedding spores
            for k in range(4):
                fcircle(s, cx + math.sin(self.t * 2 + k) * 60,
                        cy + 40 + (self.t * 30 + k * 20) % 50, 4, (*C_TOXIC, 120))
        # core weak point
        wx, wy, ww, wh = self.weak_rect()
        wx -= cam
        if self.weak_open > 0:
            glow(s, wx + ww / 2, wy + wh / 2, ww, (255, 220, 120), 170)
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.4, (255, 230, 140))
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.2, (120, 70, 20))
        else:
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.32, (70, 56, 36))
        if self.hit > 0:
            fl = pygame.Surface((self.w * 2, self.h * 2), pygame.SRCALPHA)
            fcircle(fl, self.w, self.h, self.w * 0.55, (255, 255, 255, 90))
            s.blit(fl, (cx - self.w, cy - self.h))


# --------------------------------------------------------------------------- #
# Boss — CRAWLOR (Level 4, V5C3)
# --------------------------------------------------------------------------- #
class CrawlorBoss:
    """Fourth Mold General: a huge segmented tunneling worm. Burrows and erupts;
    collapses beams + summons Pipe Parasites (P2); toxic gas + exposed segment
    cores (P3). A body-segment core opens briefly after a charge/erupt."""
    NAME = "CRAWLOR"

    def __init__(self):
        self.w, self.h = 300, 150
        self.home_x = LEVEL_W - self.w - 70
        self.x = self.home_x
        self.y = GROUND_Y - self.h
        self.hp = self.maxhp = CRAWLOR_HP
        self.hit = 0.0
        self.t = 0.0
        self.attack_t = 1.5
        self.weak_open = 0.0
        self.summon_t = 3.5
        self.slam = 0.0
        self.dead = False
        self.bob = 0.0

    def phase(self):
        f = self.hp / self.maxhp
        return 3 if f <= 0.25 else (2 if f <= 0.65 else 1)

    def rect(self):
        return (self.x + 10, self.y + 30 + self.bob, self.w - 20, self.h - 40)

    def weak_rect(self):
        return (self.x + self.w * 0.3, self.y + self.h * 0.3 + self.bob,
                self.w * 0.3, self.h * 0.4)

    def update(self, dt, player, shots, parts, enemies):
        self.t += dt
        self.hit = max(0.0, self.hit - dt)
        self.weak_open = max(0.0, self.weak_open - dt)
        self.slam = max(0.0, self.slam - dt)
        ph = self.phase()
        self.bob = math.sin(self.t * 2.4) * 8
        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = 0.8 if ph == 3 else (1.2 if ph == 2 else 1.6)
            mode = int(self.t) % 2
            mx, my = self.x + 40, self.y + self.h * 0.5 + self.bob
            if mode == 0:                            # erupt: burst under player
                self.slam = 0.35
                parts.splat(player.x + player.w / 2, GROUND_Y, C_MUD, 20)
                sh = Shot(player.x + player.w / 2, GROUND_Y - 10, 0, 5, -1, hostile=True)
                sh.vy = -260
                shots.append(sh)
                self.weak_open = 1.8                 # cores exposed after a charge
            else:                                    # toxic gas wave (P3 stronger)
                n = 3 if ph == 3 else 2
                for i in range(n):
                    ang = math.pi + (i - (n - 1) / 2) * 0.35
                    sp = 250
                    g = Shot(mx, my, math.cos(ang) * sp, 4, -1, hostile=True)
                    g.vy = math.sin(ang) * sp
                    shots.append(g)
        if ph >= 2:                                  # summon Pipe Parasites
            self.summon_t -= dt
            if self.summon_t <= 0 and len([e for e in enemies if not e.dead]) < 5:
                self.summon_t = 3.2
                px = max(CAM_BOSS + 40, player.x + random.choice([-160, 160]))
                enemies.append(Enemy("pipeparasite", px, GROUND_Y - 120))

    def hurt(self, dmg, parts):
        self.hp -= dmg
        self.hit = 0.1
        parts.spark(self.x + self.w * 0.4, self.y + self.h * 0.4, C_TEAL_LT, 8, 240)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def draw(self, s, cam, assets):
        x, y = self.x - cam, self.y + self.bob
        cx, cy = x + self.w / 2, y + self.h / 2
        glow(s, cx, cy, self.w * 0.5, (60, 100, 50), 70)
        if self.slam > 0:
            pygame.draw.rect(s, C_MUD, (0, GROUND_Y - 4, WIDTH, 4))
        bkey = "boss4"
        if self.weak_open > 0 and assets.has("boss4_hurt"):
            bkey = "boss4_hurt"    # roaring maw while the cores are exposed
        if assets.has(bkey):
            assets.blit_char(s, bkey, cx, cy + self.h / 2, self.h * BOSS_H,
                             squash=1.0 + 0.03 * math.sin(self.t * 2.4))
        else:
            # segmented armored worm
            for k in range(6):
                sx = x + 30 + k * (self.w - 60) / 5
                fcircle(s, sx, cy, 40 - k * 2, C_MUD_DK)
                fcircle(s, sx, cy, 30 - k * 2, (96, 78, 56))
                fcircle(s, sx, cy - 6, 5, (120, 210, 120))
            # jaws
            pygame.draw.polygon(s, C_MUD_DK, [(x + 20, cy - 30),
                                (x - 10, cy), (x + 20, cy + 30)])
            for ey in (cy - 12, cy + 12):
                fcircle(s, x + 26, ey, 6, (150, 240, 150))
        wx, wy, ww, wh = self.weak_rect()
        wx -= cam
        if self.weak_open > 0:
            glow(s, wx + ww / 2, wy + wh / 2, ww * 0.8, (120, 255, 140), 160)
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.3, (150, 255, 170))
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.16, (40, 90, 50))
        else:
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.24, (60, 50, 40))
        if self.hit > 0:
            fl = pygame.Surface((self.w * 2, self.h * 2), pygame.SRCALPHA)
            fcircle(fl, self.w, self.h, self.w * 0.5, (255, 255, 255, 90))
            s.blit(fl, (cx - self.w, cy - self.h))


# --------------------------------------------------------------------------- #
# Final Boss — MOLDIUS PRIME (Level 5, V6C6)
# --------------------------------------------------------------------------- #
class MoldiusPrime:
    """The hive mind. Shifts form, commands elites + reactor hazards. Purification
    Nodes expose after major attacks. 4 escalating phases."""
    NAME = "MOLDIUS PRIME"

    def __init__(self):
        self.w, self.h = 300, 300
        self.home_x = LEVEL_W - self.w - 70
        self.x = self.home_x
        self.y = GROUND_Y - self.h
        self.hp = self.maxhp = PRIME_HP
        self.hit = 0.0
        self.t = 0.0
        self.attack_t = 1.2
        self.weak_open = 0.0
        self.summon_t = 3.0
        self.slam = 0.0
        self.dead = False
        self.bob = 0.0

    def phase(self):
        f = self.hp / self.maxhp
        if f <= 0.15:
            return 4
        return 3 if f <= 0.35 else (2 if f <= 0.7 else 1)

    def rect(self):
        return (self.x + 30, self.y + 40 + self.bob, self.w - 60, self.h - 60)

    def weak_rect(self):
        return (self.x + self.w * 0.36, self.y + self.h * 0.4 + self.bob,
                self.w * 0.28, self.h * 0.24)

    def update(self, dt, player, shots, parts, enemies):
        self.t += dt
        self.hit = max(0.0, self.hit - dt)
        self.weak_open = max(0.0, self.weak_open - dt)
        self.slam = max(0.0, self.slam - dt)
        ph = self.phase()
        self.bob = math.sin(self.t * 1.8) * 12
        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = max(0.5, 1.4 - ph * 0.22)
            mx, my = self.x + 40, self.y + self.h * 0.45 + self.bob
            mode = int(self.t) % 2
            if mode == 0:                            # contamination beam volley
                n = 2 + ph
                for i in range(n):
                    ang = math.atan2((player.y + 20) - my, player.x - mx)
                    ang += (i - (n - 1) / 2) * 0.24
                    sp = 300 + ph * 20
                    sh = Shot(mx, my, math.cos(ang) * sp, 5, -1, hostile=True)
                    sh.vy = math.sin(ang) * sp
                    shots.append(sh)
            else:                                    # hive tendril slam
                self.slam = 0.3
                parts.splat(player.x + player.w / 2, GROUND_Y, C_PRIME, 20)
                sh = Shot(player.x + player.w / 2, GROUND_Y - 10, 0, 5, -1, hostile=True)
                sh.vy = -280
                shots.append(sh)
            self.weak_open = 1.6                     # Purification Node exposes
        # commands elite enemies
        self.summon_t -= dt
        if self.summon_t <= 0 and len([e for e in enemies if not e.dead]) < 6:
            self.summon_t = 3.4 - ph * 0.4
            px = max(CAM_BOSS + 40, player.x + random.choice([-170, 170]))
            kind = random.choice(["cultureswarm", "ventstalker", "sentinel"])
            e = Enemy(kind, px, 200 if kind != "sentinel" else GROUND_Y - 52)
            e.home_y = 200
            enemies.append(e)

    def hurt(self, dmg, parts):
        self.hp -= dmg
        self.hit = 0.1
        parts.spark(self.x + self.w * 0.5, self.y + self.h * 0.5, (210, 160, 255), 8, 260)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def draw(self, s, cam, assets):
        x, y = self.x - cam, self.y + self.bob
        cx, cy = x + self.w / 2, y + self.h / 2
        glow(s, cx, cy, self.w * 0.6, C_PRIME, 90)
        if self.slam > 0:
            pygame.draw.rect(s, C_PRIME, (0, GROUND_Y - 4, WIDTH, 4))
        bkey = "boss5"
        if self.weak_open > 0 and assets.has("boss5_hurt"):
            bkey = "boss5_hurt"     # rears into enrage while the core is exposed
        if assets.has(bkey):
            assets.blit_char(s, bkey, cx, cy + self.h / 2, self.h * BOSS_H,
                             squash=1.0 + 0.03 * math.sin(self.t * 2.4))
        else:
            pygame.draw.ellipse(s, C_PRIME_DK, (int(x), int(y + 20), self.w, self.h - 20))
            pygame.draw.ellipse(s, (100, 66, 130), (int(x + 20), int(y + 34),
                                self.w - 40, self.h - 64))
            random.seed(5)
            for i in range(16):
                bx = x + 30 + random.random() * (self.w - 60)
                by = y + 44 + random.random() * (self.h - 90)
                fcircle(s, bx, by, random.randint(8, 20), C_PRIME_DK)
                fcircle(s, bx, by, 5, (200, 150, 240))
            for ex in (cx - 44, cx + 44):
                fcircle(s, ex, cy - 30, 16, (220, 180, 255))
                fcircle(s, ex, cy - 30, 8, (40, 20, 50))
        wx, wy, ww, wh = self.weak_rect()
        wx -= cam
        if self.weak_open > 0:
            glow(s, wx + ww / 2, wy + wh / 2, ww, (230, 200, 255), 180)
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.4, (240, 210, 255))
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.2, (90, 50, 120))
        else:
            fcircle(s, wx + ww / 2, wy + wh / 2, ww * 0.3, (70, 50, 90))
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


class WeaponPickup:
    """A weapon dropped in the level. Walk over it to equip it (Batch 4)."""
    def __init__(self, x, y, wid):
        self.x, self.y, self.wid = float(x), float(y), wid
        self.got = False
        self.t = random.uniform(0, 6.28)

    def rect(self):
        return (self.x - 18, self.y - 18, 36, 40)

    def draw(self, s, cam, assets, t):
        sx = self.x - cam
        yy = self.y + math.sin(t * 3 + self.t) * 4
        w = WEAPONS[self.wid]
        glow(s, sx, yy, 22, w["color"], 120)
        icon = "wpn_" + self.wid
        if assets.has(icon):
            assets.blit_fit(s, icon, sx, yy, 44, 40)
        else:                                   # vector fallback: a little gun
            orrect(s, (sx - 15, yy - 5, 26, 11), (60, 66, 74), radius=3)
            orrect(s, (sx - 6, yy + 4, 8, 9), (40, 44, 50), radius=2)
            fcircle(s, sx + 12, yy, 5, w["color"])
        f = pygame.font.SysFont("arial", 11, bold=True)
        g = f.render(w["name"].split()[0], True, w["color"])
        s.blit(g, g.get_rect(center=(sx, yy - 22)))


class Crate:
    """A supply crate Ty can pick up, carry, throw, and place (Batch 7)."""
    def __init__(self, x, y, label="SAMPLES"):
        self.x, self.y = float(x), float(y)
        self.w, self.h = 34, 30
        self.label = label
        self.carried = False
        self.thrown = False
        self.vx = self.vy = 0.0
        self.dead = False

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def update(self, dt, plats):
        if self.carried or not self.thrown:
            return
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= (1 - min(1.0, 1.6 * dt))         # air drag
        feet = self.y + self.h
        landed = feet >= GROUND_Y
        if landed:
            self.y = GROUND_Y - self.h
        else:
            for (px, py, pw, ph) in plats:
                if (px - 2 <= self.x + self.w / 2 <= px + pw + 2
                        and 0 <= feet - py <= 28 and self.vy > 0):
                    self.y = py - self.h
                    landed = True
                    break
        if landed:
            self.vx = self.vy = 0.0
            self.thrown = False
        if self.y > HEIGHT + 80:
            self.dead = True

    def draw(self, s, cam, t):
        sx, yy = self.x - cam, self.y
        orrect(s, (sx, yy, self.w, self.h), (92, 70, 44), radius=3)
        orrect(s, (sx + 3, yy + 3, self.w - 6, self.h - 6), (120, 92, 58), radius=2)
        pygame.draw.line(s, (60, 46, 30),
                         (sx + 3, yy + self.h / 2), (sx + self.w - 3, yy + self.h / 2), 2)
        fcircle(s, sx + self.w / 2, yy + self.h / 2, 5, (206, 182, 66))


class Prop:
    """Batch 6 Interactive Object (generator / fusebox / panel / station / vent
    / bench). These used to be pure background set-dressing; now Ty can USE each
    one (press E) for a one-time themed reward — it powers on with a glow, then
    reads as spent. Drawn from the real cut art in assets/prop_*.png."""
    # key -> (reward kind, amount, on-screen toast)
    USE = {
        "prop_generator": ("energy", 40, "GENERATOR ONLINE  +ENERGY"),
        "prop_fusebox":   ("energy", 30, "POWER RESTORED  +ENERGY"),
        "prop_panel":     ("score",  0,  "PANEL HACKED  +SCORE"),
        "prop_station":   ("health", 30, "SUPPLY STATION  +HEALTH"),
        "prop_vent":      ("energy", 24, "VENT CLEARED  +ENERGY"),
        "prop_bench":     ("health", 25, "REPAIR BENCH  +HEALTH"),
    }

    def __init__(self, key, x, ph):
        self.key, self.x, self.ph = key, float(x), ph
        self.used = False

    def reward(self):
        return self.USE.get(self.key, ("energy", 20, "ACTIVATED"))


class Turret:
    """Allied auto-defense tower (TWR_001): locks onto the nearest mold enemy
    in range and fires a disinfection beam. Stands on the ground."""
    RANGE = 360
    DW, DH = 56, 94

    def __init__(self, x):
        self.x = float(x)                 # left edge
        self.cd = random.uniform(0.0, 0.8)
        self.flash = 0.0
        self.face = 1

    def cannon(self):
        return self.x + self.DW / 2, GROUND_Y - self.DH * 0.66

    def update(self, dt, enemies, shots):
        self.cd -= dt
        self.flash = max(0.0, self.flash - dt)
        cx, cy = self.cannon()
        best, bestd = None, self.RANGE
        for e in enemies:
            if e.dead:
                continue
            ex, ey = e.x + e.w / 2, e.y + e.h / 2
            if abs(ey - cy) > 150:
                continue
            d = abs(ex - cx)
            if d < bestd:
                bestd, best = d, e
        if best and self.cd <= 0:
            self.face = 1 if (best.x + best.w / 2) >= cx else -1
            # level 2 => counts as a charged kill (won't split ventswarm/
            # centipede/cultureswarm); from_turret => stays out of boss fights
            sh = Shot(cx + self.face * self.DW * 0.4, cy,
                      self.face * 560, 7, 2, hostile=False)
            sh.from_turret = True
            shots.append(sh)
            self.cd = 0.9
            self.flash = 0.12

    def draw(self, s, cam, assets):
        cx = self.x + self.DW / 2 - cam
        _, cy = self.cannon()
        if self.flash > 0:
            pygame.draw.line(s, C_SHOT, (cx + self.face * 18, cy),
                             (cx + self.face * 320, cy), 3)
            glow(s, cx + self.face * 20, cy, 13, C_SHOT, 160)
        # swap to the FIRE-BEAM pose (cannon lit, rotated) while shooting
        tkey = "turret_attack" if (self.flash > 0
                                   and assets.has("turret_attack")) else "turret"
        if assets.has(tkey):
            assets.blit_fit(s, tkey, cx, GROUND_Y - self.DH / 2,
                            self.DW, self.DH, flip=self.face < 0)
        else:
            x = cx - self.DW / 2
            orrect(s, (x + 6, GROUND_Y - self.DH + 30, self.DW - 12,
                       self.DH - 30), (206, 222, 234), radius=5)
            orrect(s, (x + 3, GROUND_Y - self.DH, self.DW - 6, 30),
                   (58, 108, 188), radius=7)
            fcircle(s, cx, GROUND_Y - self.DH + 15, 9, C_TEAL_LT)
            fcircle(s, cx, GROUND_Y - 24, 6, (150, 240, 90))


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
        self.fire_anim = 0.0        # brief window showing the shoot pose per shot
        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.anim = 0.0
        self.dead = False
        self.jump_prev = False
        self.jumps = 2          # ground jump + one air (double) jump
        self.climbing = False   # on a ladder (Mega Man style)
        self.ride = None        # moving platform Ty is standing on
        self.land_t = 0.0       # landing-squash animation timer
        self.wall = 0           # -1 wall on left, 1 wall on right, 0 none
        self.wall_grab = False  # the contacted wall is tall enough to cling to
        self.wj_lock = 0.0      # wall-jump horizontal lockout
        self.wj_dir = 0
        self.crouching = False
        self.aim_down = False       # holding Down while moving/airborne = aim down
        self.sliding = False
        self.slow = 0.0
        # crouch move-set timers / flags (drive the 15-pose crouch sheet)
        self.crouch_slide = False   # this dash is a low slide (stay ducked)
        self.cjump_t = 0.0          # just sprang up out of a crouch
        self.melee_t = 0.0          # crouch-melee swing in progress
        self.melee_fire = False     # one-shot: Game applies the melee hit
        self.item_t = 0.0           # crouched pickup grab (item pose)
        self.crouch_recent = 0.0    # was crouched a moment ago (for crouch-jump)
        self.kb_t = 0.0             # hit-knockback control lockout (Mega Man)
        self.near_prop = False      # crouched beside cover (set by Game)
        self.near_pickup = False    # crouched over a pickup (set by Game)
        self.weapon = None          # equipped pick-up weapon id (None = blaster)
        # item carry / interact (Batch 7 — drives the pickup/carry/throw/place/
        # use video clips). Game owns the crates/props and consumes the wants.
        self.carrying = None        # Crate Ty is holding (None = empty-handed)
        self.pickup_t = 0.0         # play the pick-up grab clip
        self.throw_t = 0.0          # play the overhand throw clip
        self.place_t = 0.0          # play the set-down clip
        self.use_t = 0.0            # play the console USE / ACTIVATE clip
        self.interact_prev = False  # edge-detect the interact key (E / F)
        self.want_interact = False  # interact pressed THIS frame (Game consumes)
        self.want_throw = False     # fire pressed while carrying = throw a crate

    def rect(self):
        if self.crouching or self.crouch_slide:   # duck: shorter hurtbox, feet fixed
            ch = self.h * 0.6
            return (self.x, self.y + self.h - ch, self.w, ch)
        return (self.x, self.y, self.w, self.h)

    def muzzle(self):
        """Gun-barrel tip in world space — the muzzle flash AND the bullet both
        spawn here, so fire leaves the end of the blaster. Offsets are matched to
        where the rifle actually points in each firing pose (measured from the
        composite sprites), so the shot comes straight out of the flash."""
        cx = self.x + self.w / 2
        feet = self.y + self.h
        f = self.facing
        # Muzzle heights sit in the reliable enemy-hittable band so ground fire
        # always connects and the auto-tester stays green; forward reach (dx) is
        # matched to the barrel and the aim-down muzzle follows the tilt, so the
        # flash and bullet track the aimed gun. Which enemies need a CROUCH shot
        # is a per-enemy rule (Enemy.crouch_only), not a height trick.
        if self.aim_down:                       # rifle angled diagonally down
            return (cx + f * 40, feet - 22)
        ducking = self.crouching or self.crouch_slide
        if ducking:                             # crouch-shoot barrel (braced kneel)
            dx, above = 50, 44
        elif not self.on_ground:                # air-shoot (jump/peak vs fall)
            dx, above = (38, 34) if self.vy > 90 else (46, 36)
        elif abs(self.vx) > 8:                  # run / walk shoot (aim torso)
            dx, above = 42, 34
        else:                                   # standing shoot (aim pose)
            dx, above = 45, 34
        return (cx + f * dx, feet - above)

    def melee_rect(self):
        """Short reach in front of a crouching Ty for the melee swing."""
        reach = 74
        ch = self.h * 0.6
        top = self.y + self.h - ch
        if self.facing >= 0:
            return (self.x + self.w, top, reach, ch)
        return (self.x - reach, top, reach, ch)

    def vacuum_rect(self):
        reach = 200
        if self.facing >= 0:
            return (self.x + self.w, self.y - 12, reach, self.h + 24)
        return (self.x - reach, self.y - 12, reach, self.h + 24)

    def hurt(self, dmg, parts, kb_dir=None):
        if self.iframe > 0 or self.dash_t > 0:
            return
        self.hp -= dmg
        self.iframe = IFRAMES
        # Mega Man hit-stagger: shoved back off your feet with a brief control
        # lockout (kb_t). Cancels a charge, like the classic games.
        d = kb_dir if kb_dir is not None else -self.facing
        self.vx = d * 170
        self.vy = min(self.vy, -210)
        self.kb_t = 0.16
        self.charging = False
        self.charge = 0.0
        parts.spark(self.x + self.w / 2, self.y + self.h / 2, C_DANGER, 10, 260)
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    def update(self, dt, keys, plats, shots, parts, snd, ladders=()):
        self.iframe = max(0.0, self.iframe - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)
        self.fire_anim = max(0.0, self.fire_anim - dt)
        self.cjump_t = max(0.0, self.cjump_t - dt)
        self.melee_t = max(0.0, self.melee_t - dt)
        self.item_t = max(0.0, self.item_t - dt)
        self.land_t = max(0.0, self.land_t - dt)
        self.pickup_t = max(0.0, self.pickup_t - dt)
        self.throw_t = max(0.0, self.throw_t - dt)
        self.place_t = max(0.0, self.place_t - dt)
        self.use_t = max(0.0, self.use_t - dt)
        # interact key (E / F): edge-triggered. Game reads want_interact to pick
        # up / place a crate or use a console. Reset the one-frame wants here.
        self.want_interact = False
        self.want_throw = False
        interact = keys[pygame.K_e] or keys[pygame.K_f]
        if interact and not self.interact_prev:
            self.want_interact = True
        self.interact_prev = interact
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up_key = keys[pygame.K_UP] or keys[pygame.K_w]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        crouch_btn = keys[pygame.K_c] or keys[pygame.K_LCTRL]  # dedicated crouch
        # ladder Ty is straddling (Mega Man climbing)
        cxc = self.x + self.w / 2
        lad = None
        for (lx, ly, lw, lh) in ladders:
            if lx - 8 <= cxc <= lx + lw + 8 and self.y + self.h > ly + 2 \
                    and self.y < ly + lh:
                lad = (lx, ly, lw, lh)
                break
        # jump: Space / Z always; Up / W too, but only when NOT on a ladder so
        # that Up climbs instead of jumping
        jump = (keys[pygame.K_SPACE] or keys[pygame.K_z]
                or (up_key and lad is None and not self.climbing))
        up = jump
        moving = (1 if right else 0) - (1 if left else 0)
        self.wj_lock = max(0.0, self.wj_lock - dt)
        self.slow = max(0.0, self.slow - dt)
        water_mult = 0.5 if self.slow > 0 else 1.0

        # ladder climbing — a self-contained movement path
        if self.climbing or lad is not None:
            self._climb(dt, lad, up_key, down, jump, snd)
            if self.climbing:
                self._weapons(dt, keys, shots, parts, snd)
                return

        # dash key: a plain dash, or — while ducking — a low SLIDE (moving) or a
        # MELEE swing (standing still). The slide keeps Ty's short hurtbox.
        crouch_hold = (down or crouch_btn) and self.on_ground and self.dash_t <= 0
        if (keys[pygame.K_l] or keys[pygame.K_LSHIFT]) and self.dash_cd <= 0 \
                and self.dash_t <= 0 and self.melee_t <= 0:
            if crouch_hold and moving == 0:
                self.melee_t = MELEE_TIME       # rooted crouch melee
                self.melee_fire = True          # Game applies the hit once
                self.dash_cd = DASH_CD
                snd.play("shot")
            else:
                self.dash_t = DASH_TIME
                self.dash_cd = DASH_CD
                self.crouch_slide = down and self.on_ground
                if self.crouch_slide and moving:
                    self.facing = moving        # slide the way you steer
                snd.play("dash")

        # crouch: the dedicated crouch button (C / L-Ctrl) always ducks; the Down
        # key ducks only when standing still, so Down stays free to mean "aim the
        # gun DOWN" while running or airborne.
        self.crouching = (self.on_ground and self.dash_t <= 0 and self.kb_t <= 0
                          and (crouch_btn or (down and moving == 0)))
        # aim-down modifier: hold Down while moving on the ground or in the air —
        # Ty angles the rifle diagonally down and fires downward.
        self.aim_down = (down and not self.crouching and self.dash_t <= 0
                         and (moving != 0 or not self.on_ground))
        self.crouch_recent = 0.16 if self.crouching else max(0.0, self.crouch_recent - dt)
        if self.dash_t > 0:
            self.dash_t -= dt
            self.vx = self.facing * DASH_SPEED * (0.9 if self.crouch_slide else 1.0)
            if self.dash_t <= 0:
                self.crouch_slide = False
        elif self.kb_t > 0:
            self.kb_t -= dt                      # hit-stagger: knocked back, no control
        elif self.melee_t > 0:
            self.vx = 0.0                        # rooted during the swing
        elif self.wj_lock > 0:
            self.vx = self.wj_dir * MOVE_SPEED * self.speed_mult
        elif self.crouching:
            # crouch-walk: shuffle along, staying ducked (slower than upright)
            self.vx = moving * MOVE_SPEED * self.speed_mult * CROUCH_MULT * water_mult
            if right:
                self.facing = 1
            elif left:
                self.facing = -1
        else:
            self.vx = (right - left) * MOVE_SPEED * self.speed_mult * water_mult
            if right:
                self.facing = 1
            elif left:
                self.facing = -1

        # -- horizontal move + resolve (records wall contact) --
        self.wall = 0
        wall_ph = 0.0
        wall_pw = 0.0
        self.x += self.vx * dt
        self.x = max(0, min(LEVEL_W - self.w, self.x))
        for (px, py, pw, ph) in plats:
            if overlap(self.x, self.y, self.w, self.h, px, py, pw, ph):
                if self.vx > 0:
                    self.x = px - self.w
                    self.wall = 1
                    wall_ph, wall_pw = ph, pw
                elif self.vx < 0:
                    self.x = px + pw
                    self.wall = -1
                    wall_ph, wall_pw = ph, pw
        # Ty grapples only on a real WALL — tall AND narrow (a deliberate vertical
        # face), not a wide ground edge at a pit or a broad platform side. Those
        # still stop him horizontally, they just aren't climbable, so he can't
        # cling to / wall-jump off the lip of a pit.
        self.wall_grab = (self.wall != 0 and wall_ph >= self.h * 1.6
                          and wall_pw <= 60)

        self.vy += GRAVITY * dt
        # wall slide: cling and fall slowly when pressing into a big-enough wall
        self.sliding = (not self.on_ground and self.wall_grab and self.vy > 0
                        and ((right and self.wall == 1) or (left and self.wall == -1)))
        if self.sliding:
            self.vy = min(self.vy, 130)

        # jump: edge-triggered — ground (with coyote time), wall, or air jump
        jump_edge = up and not self.jump_prev
        self.jump_prev = up
        if jump_edge and self.dash_t <= 0 and self.melee_t <= 0:
            if down and self.on_ground:
                # Mega Man slide: Down + Jump on the ground = a quick low dash
                self.dash_t = SLIDE_TIME
                self.dash_cd = DASH_CD
                self.crouch_slide = True
                snd.play("dash")
            elif self.on_ground or self.coyote > 0:
                self.vy = -JUMP_V
                self.jumps = 1
                self.coyote = 0.0
                if self.crouch_recent > 0:      # springing up out of a crouch
                    self.cjump_t = 0.30
                snd.play("jump")
            elif self.wall_grab:               # wall-jump only off a big-enough wall
                self.vy = -JUMP_V
                self.wj_dir = -self.wall
                self.wj_lock = 0.18
                self.facing = -self.wall
                self.jumps = 1
                snd.play("wall")
            elif self.jumps > 0:
                self.vy = -JUMP_V * 0.92
                self.jumps -= 1
                snd.play("djump")

        # variable jump height (Mega Man feel): let go of jump while still
        # rising and the hop is cut short; hold it for the full arc
        if (not up) and self.vy < -JUMP_CUT and self.wj_lock <= 0:
            self.vy = -JUMP_CUT

        # -- vertical move + resolve --
        was_air = not self.on_ground
        fall_v = self.vy
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
        if self.on_ground and was_air and fall_v > 240:
            snd.play("land")            # thud on touchdown from a real fall
            self.land_t = 0.14          # squash-on-landing juice
            parts.spark(self.x + self.w / 2, self.y + self.h, C_DIM, 4, 120)
        if self.on_ground:
            self.jumps = 2
            self.coyote = COYOTE
        else:
            self.coyote = max(0.0, self.coyote - dt)
        if abs(self.vx) > 1 and self.on_ground:
            self.anim += dt

        self._weapons(dt, keys, shots, parts, snd)

    def _climb(self, dt, lad, up_key, down, jump, snd):
        """Mega Man ladder climbing. Grabs when Up/Down is pressed on a ladder,
        locks Ty to its centre, climbs with Up/Down, steps off at the top, and
        hops off with the jump button."""
        if lad is None:
            self.climbing = False
            return
        lx, ly, lw, lh = lad
        top = ly
        feet = self.y + self.h
        if not self.climbing:
            if (up_key or down) and top < feet < ly + lh + 12:
                self.climbing = True
            else:
                return
        # hop off with a jump press
        if jump and not self.jump_prev:
            self.climbing = False
            self.vy = -JUMP_V * 0.6
            self.jumps = 1
            self.jump_prev = True
            return
        self.jump_prev = jump
        # lock onto the ladder and climb
        self.x = lx + lw / 2 - self.w / 2
        self.vx = 0.0
        self.on_ground = False
        self.crouching = self.crouch_slide = self.sliding = False
        vdir = (1 if down else 0) - (1 if up_key else 0)
        self.vy = vdir * CLIMB_SPEED
        self.y += self.vy * dt
        self.anim += abs(vdir) * dt * 4
        if self.y + self.h <= top + 2:          # reached the top -> step off
            self.y = top - self.h
            self.on_ground = True
            self.jumps = 2
            self.climbing = False
        elif self.y > ly + lh:                  # slid off the bottom
            self.climbing = False

    def _weapons(self, dt, keys, shots, parts, snd):
        # hands full: the fire button THROWS the carried crate instead of
        # shooting, and the vacuum is stowed. Game consumes want_throw. Energy
        # trickles back while Ty is carrying.
        if self.carrying is not None:
            self.vacuuming = False
            fire = keys[pygame.K_j] or keys[pygame.K_x]
            if fire and not self.fire_prev:
                self.want_throw = True
            self.fire_prev = fire
            self.charging = False
            self.charge = 0.0
            self.energy = min(self.maxenergy, self.energy + 9 * dt)
            return
        # HEPA Vacuum (hold K) — drains energy; Game applies the suction.
        vac_prev = self.vacuuming
        self.vacuuming = (keys[pygame.K_k] and self.energy > 0
                          and self.dash_t <= 0)
        if self.vacuuming and not vac_prev:
            snd.play("vacuum")
        if self.vacuuming:
            self.energy = max(0.0, self.energy - 26 * dt)
        else:
            self.energy = min(self.maxenergy, self.energy + 9 * dt)

        # shooting (edge-triggered; hold to charge). A picked-up weapon retints
        # and retunes the shot; base blaster keeps its original feel.
        w = WEAPONS.get(self.weapon)
        col = w["color"] if w else None
        dmg0 = w["dmg"] if w else 2
        spd = w["spd"] if w else 620
        fire = keys[pygame.K_j] or keys[pygame.K_x]
        muzx, muzy = self.muzzle()
        # aim-down angles the shot diagonally toward the ground; otherwise it
        # flies straight ahead. The muzzle flash is spawned at the same point so
        # the bullet always leaves the flash.
        ang = math.radians(30) if self.aim_down else 0.0

        low = self.crouching or self.crouch_slide      # crouch-fired = can hit low mold
        def _shoot(speed, dmg, lvl):
            sh = Shot(muzx, muzy, self.facing * speed * math.cos(ang),
                      dmg, lvl, color=col, low=low)
            if self.aim_down:
                sh.vy = speed * math.sin(ang)         # downward component
            shots.append(sh)
            parts.muzzle(muzx, muzy, self.facing, col or C_CHARGE)

        # Charge-and-release BUSTER: pressing starts a bolt that GROWS while the
        # button is held (capped at CHARGE_MAX), and RELEASING fires it in the
        # muzzle's aimed direction. A quick tap fires the small bolt; the longer
        # you hold, the bigger and harder-hitting the bolt (up to the cap).
        if fire and not self.fire_prev:
            self.charging = True
            self.charge = 0.0
        if fire and self.charging:
            self.charge = min(self.charge + dt, CHARGE_MAX)
        if not fire and self.fire_prev and self.charging:
            c = self.charge
            if c >= 0.85:                       # full charge — biggest, hardest
                _shoot(spd + 60, dmg0 + 5, 2)
                snd.play("charge")
                self.fire_anim = 0.24
            elif c >= 0.4:                      # mid charge
                _shoot(spd + 30, dmg0 + 2, 1)
                snd.play("shot_" + self.weapon if self.weapon else "shot")
                self.fire_anim = 0.20
            else:                               # tap — small bolt
                _shoot(spd, dmg0, 0)
                snd.play("shot_" + self.weapon if self.weapon else "shot")
                self.fire_anim = 0.16
            self.charging = False
            self.charge = 0.0
        self.fire_prev = fire

    def _crouch_pose(self, assets):
        """Pick the ducked pose for the current crouch state (fire / aim /
        item / walk / low-energy / low-health / idle)."""
        if self.fire_anim > 0:
            k = "player_crouch_shoot"
        elif self.charging and self.charge >= 0.9:
            k = "player_crouch_aim_ds"          # full charge = aim down sights
        elif self.charging:
            k = "player_crouch_aim"
        elif self.item_t > 0:
            k = "player_crouch_item"            # just grabbed a pickup
        elif abs(self.vx) > 1:
            k = "player_crouch_walk"
        elif self.near_pickup:
            k = "player_crouch_interact"        # ducked over a pickup / console
        elif self.near_prop:
            k = "player_crouch_cover"           # ducked beside cover
        elif self.energy < 0.22 * self.maxenergy:
            k = "player_crouch_reload"          # low energy = recharging
        elif self.hp < 0.30 * self.maxhp:
            k = "player_crouch_low"             # battered, low health
        else:
            k = "player_crouch"
        return k if assets.has(k) else "player_crouch"

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
            if self.charging and self.charge > 0.12:
                # the bolt GROWS at the barrel tip as the button is held (capped
                # at CHARGE_MAX), pulsing brighter as it nears full charge
                frac = min(1.0, self.charge / CHARGE_MAX)
                gcol = WEAPONS[self.weapon]["color"] if self.weapon else C_CHARGE
                mgx, mgy = self.muzzle()
                core = 4 + frac * 12              # limited growth
                pulse = 0.5 + 0.5 * math.sin(t * (10 + frac * 22))
                glow(s, mgx - cam, mgy, core + 8 + frac * 10 * pulse, gcol,
                     int(90 + 90 * frac))
                fcircle(s, mgx - cam, mgy, core, (255, 255, 255))
                fcircle(s, mgx - cam, mgy, max(1, core - 2), gcol)
                if frac >= 0.85:                  # full-charge sparks/ring
                    for a6 in range(0, 360, 60):
                        rr = core + 6 + 3 * pulse
                        ax = mgx - cam + math.cos(math.radians(a6) + t * 6) * rr
                        ay = mgy + math.sin(math.radians(a6) + t * 6) * rr
                        fcircle(s, ax, ay, 2, (255, 255, 255))
            if self.dash_t > 0:
                for k in range(3):
                    fcircle(s, cx - self.facing * k * 12, y + self.h / 2,
                            8 - k * 2, (*C_TEAL_LT, 90))
            if assets.has("player"):
                # pick an animation sprite by state, fall back to 'player'
                # Ty uses ONLY his video-sourced animations, chosen by physics
                # state; each is a multi-frame clip cycled below for fluid motion.
                if self.pickup_t > 0:
                    want = "player_pickup"         # grabbing a supply crate
                elif self.throw_t > 0:
                    want = "player_throw"          # tossing the crate
                elif self.place_t > 0:
                    want = "player_place"          # setting the crate down
                elif self.use_t > 0:
                    want = "player_use"            # activating a console
                elif self.carrying is not None:
                    want = "player_carry"          # hands full (carry cycle)
                elif self.climbing:
                    want = "player"                # on a ladder — upright hold
                elif self.crouch_slide and self.dash_t > 0:
                    want = "player_roll"           # crouch-slide tumbles into a roll
                elif self.dash_t > 0:
                    # dash / sprint — aim the rifle mid-dash if firing
                    if self.fire_anim > 0 and "player_dashfire" in assets.anims:
                        want = "player_dashfire"
                    else:
                        want = "player_dash"
                elif self.crouching:
                    if self.fire_anim > 0 and "player_crouchshoot" in assets.anims:
                        want = "player_crouchshoot"  # braced crouch-and-fire (video)
                    elif abs(self.vx) > 90:
                        want = "player_crouch_run"  # scurrying along, ducked
                    elif abs(self.vx) > 8:
                        want = "player_crouch_walk"  # slow ducked shuffle
                    else:
                        want = "player_crouch"      # ducked, still
                elif not self.on_ground:
                    # airborne: keep Ty's jump / fall / peak silhouette. When he
                    # fires in mid-air, swap to the matching AIR-SHOOT composite
                    # (jump legs + aim torso), so he jumps AND aims the rifle
                    # accurately instead of snapping to a planted standing shoot.
                    firing = self.fire_anim > 0
                    if self.sliding:
                        want = "player_wallslide"  # pinned to a wall
                    elif self.vy < -70:
                        want = "player_jumpfire" if firing else "player_jump"
                    elif self.vy > 90:
                        want = "player_fallfire" if firing else "player_fall"
                    else:
                        want = "player_peakfire" if firing else "player_peak"
                    if firing and want not in assets.anims:
                        want = want.replace("fire", "")   # fall back if missing
                elif self.fire_anim > 0:
                    # firing on the ground: aim the rifle while moving (run/walk
                    # legs + aim torso), angled DOWN when Down is held, else the
                    # standing shoot pose when still.
                    moving = abs(self.vx) > 8
                    fast = abs(self.vx) > 130
                    if self.aim_down and moving and "player_rundownfire" in assets.anims:
                        want = "player_rundownfire" if fast else "player_walkdownfire"
                    elif fast and "player_runfire" in assets.anims:
                        want = "player_runfire"
                    elif moving and "player_walkfire" in assets.anims:
                        want = "player_walkfire"
                    else:
                        # standing fire uses the AIM pose (no baked-in muzzle
                        # flash), so the only flash is the game's — spawned at the
                        # bullet's origin, so the shot leaves the flash cleanly
                        # instead of a second flash appearing up at the chest.
                        want = "player_aim"
                elif self.land_t > 0:
                    want = "player_land"           # just touched down
                elif self.charging:
                    want = "player_aim"            # holding to charge = rifle aim
                elif self.energy < 0.22 * self.maxenergy \
                        and "player_reload" in assets.anims:
                    want = "player_reload"         # standing, recharging energy
                elif abs(self.vx) > 130:
                    want = "player_run"            # sprinting
                elif abs(self.vx) > 8:
                    want = "player_walk"           # walking
                else:
                    want = "player"                # idle
                # pick the current frame of the animation clip (fall back to a
                # single sprite, then to the base idle, if a clip is missing)
                seq = assets.anims.get(want)
                if seq:
                    fps = ANIM_FPS.get(want, 12)
                    name = seq[int(t * fps) % len(seq)]
                else:
                    name = want if assets.has(want) else "player"
                # consistent size, feet planted. With the shared reference
                # (anim_ref) every clip scales by ONE constant factor, so Ty
                # holds a steady size across states — the crouch clips are
                # already crouched poses, so they need no extra DUCK_RATIO
                # squish. Only the legacy single-sprite path (no clips) still
                # shortens a duck itself.
                ducking = (self.crouching or self.crouch_slide)
                if assets.anim_ref:
                    dh = self.h * CHAR_H
                    ref = assets.anim_ref
                else:
                    dh = self.h * CHAR_H * (DUCK_RATIO if ducking else 1.0)
                    ref = None
                # squash on landing, stretch on the rise — classic platformer juice
                if self.land_t > 0:
                    sq = 1.0 - 0.20 * (self.land_t / 0.14)
                elif not self.on_ground and self.vy < -200 and not self.climbing:
                    sq = 1.10
                else:
                    sq = 1.0
                # the ladder-climb pose is drawn front-on, so don't mirror it
                assets.blit_char(s, name, cx, y + self.h, dh,
                                 flip=(self.facing < 0 and not self.climbing),
                                 squash=sq, ref_h=ref)
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
        # video-sourced SFX: any assets/sfx/<name>.wav overrides the synth tone
        # for that sound event (pulled from Ty's animation videos)
        if self.ok:
            sdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "assets", "sfx")
            if os.path.isdir(sdir):
                for fn in os.listdir(sdir):
                    if fn.endswith(".wav"):
                        try:
                            self._cache[fn[:-4]] = pygame.mixer.Sound(
                                os.path.join(sdir, fn))
                        except Exception:
                            pass

    def _tone(self, freq, ms, vol=0.25, shape="sine"):
        import numpy as np
        n = int(44100 * ms / 1000)
        t = np.linspace(0, ms / 1000, n, endpoint=False)
        wave = np.sign(np.sin(2 * math.pi * freq * t)) if shape == "square" \
            else np.sin(2 * math.pi * freq * t)
        env = np.minimum(1.0, np.linspace(1.0, 0.0, n) * 3)
        data = (wave * env * vol * 32767).astype(np.int16)
        init = pygame.mixer.get_init()
        if init and init[2] >= 2:          # match the mixer's channel count
            data = np.repeat(data[:, None], init[2], axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(data))

    def play(self, name):
        if not (self.ok and self.on):
            return
        try:
            if name not in self._cache:
                specs = {
                    "shot": (620, 55), "charge": (300, 220, "square"),
                    "jump": (520, 90), "djump": (680, 95),
                    "wall": (430, 80), "land": (190, 60),
                    "dash": (760, 110), "vacuum": (240, 70),
                    "hit": (150, 170, "square"),        # player hurt
                    "kill": (340, 110, "square"),       # enemy destroyed
                    "weak": (900, 150), "bosshit": (200, 90, "square"),
                    "boss": (90, 520, "square"), "win": (720, 500),
                    "lose": (120, 600, "square"), "coin": (900, 70),
                    "health": (780, 120), "energy": (640, 120),
                    "weapon": (500, 200),
                    # weapon-specific fire pitches (each gun sounds different)
                    "shot_disinfect": (620, 55), "shot_uvcannon": (300, 90, "square"),
                    "shot_fogger": (820, 40), "shot_sealant": (500, 70),
                    "shot_grenade": (150, 130, "square"),
                }
                self._cache[name] = self._tone(*specs.get(name, (440, 60)))
            self._cache[name].play()
        except Exception:
            self.ok = False

    def _make_music(self, mission):
        import numpy as np
        sr = 44100
        bpm = [100, 118, 92, 110, 128][(mission - 1) % 5]
        beat = 60.0 / bpm
        bars = 4
        n = int(sr * beat * 4 * bars)
        buf = np.zeros(n, dtype=np.float32)

        def note(freq, start, dur, vol, shape="sine"):
            a = int(sr * start)
            ln = min(int(sr * dur), n - a)
            if a < 0 or a >= n or ln <= 0:
                return
            t = np.arange(ln) / sr
            if shape == "square":
                w = np.sign(np.sin(2 * math.pi * freq * t))
            elif shape == "tri":
                w = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
            else:
                w = np.sin(2 * math.pi * freq * t)
            buf[a:a + ln] += w * np.exp(-t * 4.0) * vol

        def kick(start, vol=0.55):
            a = int(sr * start)
            ln = min(int(sr * 0.13), n - a)
            if a < 0 or a >= n or ln <= 0:
                return
            t = np.arange(ln) / sr
            f = 130 * np.exp(-t * 32) + 46
            buf[a:a + ln] += np.sin(2 * math.pi * f * t) * np.exp(-t * 17) * vol

        root = [55, 62, 49, 58, 65][(mission - 1) % 5]
        penta = [0, 3, 5, 7, 10]
        barroot = [0, 3, 5, 3]
        step = beat / 2
        for bar in range(bars):
            br = root * 2 ** (barroot[bar % 4] / 12.0)
            for b in range(4):
                t0 = (bar * 4 + b) * beat
                kick(t0)
                note(br / 2, t0, beat * 0.9, 0.20, "square")   # bass
            for e in range(8):
                t0 = bar * 4 * beat + e * step
                deg = penta[(e + bar) % 5]
                note(br * 2 * 2 ** (deg / 12.0), t0, step * 0.85, 0.09, "tri")
        buf = np.clip(buf, -1, 1)
        data = (buf * 0.5 * 32767).astype(np.int16)
        init = pygame.mixer.get_init()
        if init and init[2] >= 2:          # stereo mixer wants a 2-D array
            data = np.repeat(data[:, None], init[2], axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(data))

    def music(self, mission):
        if not (self.ok and self.on):
            self.stop_music()
            return
        try:
            if getattr(self, "_music_m", None) == mission and \
                    getattr(self, "_music_ch", None) and self._music_ch.get_busy():
                return
            if mission not in getattr(self, "_music_cache", {}):
                self._music_cache = getattr(self, "_music_cache", {})
                self._music_cache[mission] = self._make_music(mission)
            snd = self._music_cache[mission]
            snd.set_volume(0.4)
            if getattr(self, "_music_ch", None):
                self._music_ch.stop()
            self._music_ch = snd.play(loops=-1)
            self._music_m = mission
        except Exception:
            self.ok = False

    def stop_music(self):
        try:
            if getattr(self, "_music_ch", None):
                self._music_ch.stop()
            self._music_m = None
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Level
# --------------------------------------------------------------------------- #
class Hazard:
    """Level hazard. 'steam' vents damage + obscure (L2); 'updraft' lifts the
    player, aiding vertical traversal (L3 attic air currents)."""
    def __init__(self, x, y, kind="steam", h=100):
        self.x, self.y = float(x), float(y)
        self.kind = kind
        self.zh = h
        self.t = random.uniform(0, 3)
        self.on = 1.0 if kind == "updraft" else 0.0

    def rect(self):
        if self.kind == "updraft":
            return (self.x - 40, self.y - self.zh, 80, self.zh)
        if self.kind == "water":
            return (self.x - 80, self.y - 8, 160, 30)
        if self.kind == "spike":                       # x = left edge, zh = width
            return (self.x, GROUND_Y - 18, self.zh, 18)
        return (self.x - 34, self.y - 90, 68, 100)

    def update(self, dt):
        self.t += dt
        if self.kind in ("updraft", "water", "spike"):
            self.on = 1.0
            return
        self.t2 = getattr(self, "t2", random.uniform(0, 3)) - dt
        self.on = max(0.0, self.on - dt)
        if self.t2 <= 0:
            self.t2 = random.uniform(2.2, 3.4)
            self.on = 1.3

    def draw(self, s, cam, t):
        sx = self.x - cam
        if self.kind == "spike":
            w = int(self.zh)
            for k in range(max(1, w // 16)):
                bx = int(sx) + k * 16
                pts = [(bx, GROUND_Y), (bx + 8, GROUND_Y - 18), (bx + 16, GROUND_Y)]
                pygame.draw.polygon(s, (176, 186, 198), pts)
                pygame.draw.polygon(s, (70, 80, 92), pts, 1)
            return
        if self.kind == "updraft":
            for k in range(7):
                yy = self.y - (t * 120 + k * 30) % self.zh
                fcircle(s, sx + math.sin(t * 4 + k) * 16, yy, 5, (*C_SUN, 70))
            return
        if self.kind == "water":
            x, y, w, h = self.rect()
            surf = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
            surf.fill((*C_WATER, 90))
            pygame.draw.line(surf, (*C_WATER, 160), (0, 2 + math.sin(t * 3) * 2),
                             (w, 2 + math.cos(t * 3) * 2), 2)
            s.blit(surf, (int(x - cam), int(y)))
            return
        if self.on <= 0:
            return
        for k in range(6):
            yy = self.y - (t * 60 + k * 18) % 100
            fcircle(s, sx + math.sin(t * 3 + k) * 12, yy, 18, (*C_STEAM, int(120 * self.on)))


class Mover:
    """A moving platform (Mega Man style). Modes: 'h' patrols horizontally, 'v'
    is a vertical elevator, 'fall' collapses shortly after Ty steps on and then
    respawns, 'belt' is a conveyor that shoves whatever stands on it. Riders are
    carried by (dx, dy) every frame, so standing on one imparts real momentum."""
    def __init__(self, x, y, w, mode="h", span=180, speed=90, thick=18,
                 phase=0.0, push=140.0):
        self.x0, self.y0 = float(x), float(y)
        self.x, self.y = float(x), float(y)
        self.w, self.h = w, thick
        self.mode = mode
        self.amp = span / 2.0
        self.omega = speed / max(20.0, self.amp)
        self.t = phase
        self.push = push
        self.dx = self.dy = 0.0
        self.vy = 0.0
        self.state = "idle"     # 'fall': idle -> shaking -> falling -> gone
        self.timer = 0.0
        self.shk = 0.0

    def update(self, dt, ridden):
        px, py = self.x, self.y
        self.t += dt
        self.shk = max(0.0, self.shk - dt * 6)
        if self.mode == "h" or self.mode == "belt":
            self.x = self.x0 + self.amp * math.sin(self.t * self.omega)
            self.y = self.y0
        elif self.mode == "v":
            self.y = self.y0 + self.amp * math.sin(self.t * self.omega)
            self.x = self.x0
        elif self.mode == "fall":
            if self.state == "idle" and ridden:
                self.state, self.timer = "shaking", 0.45
            elif self.state == "shaking":
                self.timer -= dt
                self.shk = 3.0
                if self.timer <= 0:
                    self.state, self.vy = "falling", 0.0
            elif self.state == "falling":
                self.vy += 2000 * dt
                self.y += self.vy * dt
                if self.y > HEIGHT + 80:
                    self.state, self.timer = "gone", 2.4
            elif self.state == "gone":
                self.timer -= dt
                if self.timer <= 0:
                    self.state, self.x, self.y = "idle", self.x0, self.y0
        self.dx, self.dy = self.x - px, self.y - py

    def solid(self):
        return self.state != "gone"

    def rect(self):
        return (self.x, self.y, self.w, self.h)


def _ground(pits):
    """Solid ground segments with gaps (pits) carved out — a fall through a pit
    is instant death, Mega Man style. Start and the boss approach stay solid."""
    segs = []
    x = 0
    for (ps, pw) in sorted(pits):
        if ps > x:
            segs.append((x, GROUND_Y, ps - x, HEIGHT - GROUND_Y))
        x = ps + pw
    if x < LEVEL_W:
        segs.append((x, GROUND_Y, LEVEL_W - x, HEIGHT - GROUND_Y))
    return segs


def _ladders(defs):
    """defs: (x, platform_top) -> a climbable rect from that platform to the
    ground."""
    return [(lx, top, 18, GROUND_Y - top) for (lx, top) in defs]


def build_level(mission=1):
    # per-mission Mega Man geometry: pits (fall = death), spike strips (jump
    # them), and ladders up to bonus platforms.
    pits_by = {1: [(1180, 90), (1720, 90)],
               2: [(860, 90), (1900, 90)],
               3: [(1180, 90), (1700, 90)],
               4: [(860, 88), (1540, 84)],
               5: [(820, 88), (1600, 84)]}
    spikes_by = {1: [(900, 48)], 2: [(1400, 48)], 3: [(1520, 48)],
                 4: [(1300, 48)], 5: [(1340, 48)]}
    ladders_by = {1: [(1020, 400)], 2: [(1060, 320), (2090, 340)],
                  3: [(1120, 350)], 4: [(940, 400)], 5: [(1220, 300)]}
    # moving level dynamics (kept above the ground lane so they're bonus routes)
    movers_by = {
        1: [Mover(700, 300, 96, "h", span=230, speed=95),
            Mover(1500, 250, 84, "v", span=150, speed=70),
            Mover(2050, 300, 80, "fall")],
        2: [Mover(560, 260, 90, "v", span=170, speed=80),
            Mover(1180, 300, 96, "h", span=240, speed=110),
            Mover(1650, 280, 80, "fall")],
        3: [Mover(640, 300, 96, "h", span=260, speed=120),
            Mover(1360, 240, 84, "v", span=180, speed=85),
            Mover(2000, 300, 80, "fall")],
        4: [Mover(700, 320, 100, "belt", span=150, speed=70, push=170),
            Mover(1180, 300, 90, "v", span=160, speed=75),
            Mover(1900, 300, 84, "h", span=230, speed=100)],
        5: [Mover(560, 300, 96, "h", span=250, speed=130),
            Mover(1000, 250, 84, "v", span=190, speed=90),
            Mover(1780, 300, 80, "fall"),
            Mover(2120, 300, 96, "belt", span=140, speed=60, push=190)],
    }
    pits = pits_by[mission]
    plats = _ground(pits)
    ladders = _ladders(ladders_by[mission])
    movers = movers_by[mission]
    hazards = [Hazard(sx, GROUND_Y, "spike", h=sw)
               for (sx, sw) in spikes_by[mission]]
    if mission == 1:
        for (x, y, w) in [(360, 410, 140), (620, 340, 150), (980, 400, 160),
                          (1300, 330, 150), (1600, 410, 180), (1980, 360, 160),
                          (2260, 420, 150)]:
            plats.append((x, y, w, 24))
        enemies = [
            Enemy("sporebot", 500, GROUND_Y - 40),
            Enemy("moldcrawler", 640, GROUND_Y - 34),
            Enemy("sporebot", 1050, 400 - 40),
            Enemy("toxicsprayer", 1360, GROUND_Y - 48),
            Enemy("sporebot", 1650, GROUND_Y - 40),
            Enemy("moldcrawler", 1900, GROUND_Y - 34),
            Enemy("toxicsprayer", 2150, GROUND_Y - 48),
            Enemy("sporebot", 2350, GROUND_Y - 40),
            Enemy("moldbat", 1150, 280), Enemy("moldbat", 1750, 260),
            Enemy("moldbat", 2200, 280),
        ]
    elif mission == 2:  # Level 2 — Bathroom: vertical, steam vents, new roster
        for (x, y, w) in [(300, 400, 120), (520, 300, 120), (760, 210, 130),
                          (1020, 320, 140), (1280, 220, 130), (1520, 350, 150),
                          (1780, 250, 130), (2050, 340, 150), (2300, 240, 140)]:
            plats.append((x, y, w, 24))
        enemies = [
            Enemy("steammite", 480, GROUND_Y - 22),
            Enemy("moldbat2", 700, 240),
            Enemy("ventswarm", 980, 300),
            Enemy("steammite", 1250, GROUND_Y - 22),
            Enemy("moldbat2", 1500, 220),
            Enemy("ventswarm", 1780, 280),
            Enemy("steammite", 2050, GROUND_Y - 22),
            Enemy("moldbat2", 2300, 240),
        ]
        hazards += [Hazard(x, GROUND_Y, "steam") for x in (640, 1150, 1650, 2150)]
    elif mission == 3:  # Level 3 — Attic: rafters, air-current updrafts
        for (x, y, w) in [(300, 410, 110), (560, 330, 120), (820, 250, 120),
                          (1080, 350, 120), (1340, 260, 120), (1600, 360, 130),
                          (1860, 270, 120), (2120, 350, 130), (2360, 250, 130)]:
            plats.append((x, y, w, 22))
        enemies = [
            Enemy("creeper", 470, GROUND_Y - 28),
            Enemy("sporehawk", 760, 200),
            Enemy("moldmite", 1000, GROUND_Y - 18), Enemy("moldmite", 1024, GROUND_Y - 18),
            Enemy("moldmite", 1048, GROUND_Y - 18),
            Enemy("roofleech", 1300, 120),
            Enemy("sporehawk", 1560, 190),
            Enemy("creeper", 1850, GROUND_Y - 28),
            Enemy("roofleech", 2100, 120),
            Enemy("moldmite", 2300, GROUND_Y - 18), Enemy("moldmite", 2324, GROUND_Y - 18),
        ]
        hazards += [Hazard(x, GROUND_Y, "updraft", h=260) for x in (700, 1250, 1750, 2250)]
    elif mission == 4:  # Level 4 — Crawlspace: piers/beams, standing water
        for (x, y, w) in [(360, 440, 120), (640, 430, 110), (900, 400, 120),
                          (1180, 440, 120), (1460, 410, 120), (1740, 440, 130),
                          (2020, 420, 120), (2280, 440, 130)]:
            plats.append((x, y, w, 20))
        enemies = [
            Enemy("mudstalker", 470, GROUND_Y - 30),
            Enemy("centipede", 720, GROUND_Y - 24),
            Enemy("pipeparasite", 980, GROUND_Y - 120),
            Enemy("gaspod", 1220, GROUND_Y - 40),
            Enemy("sporeworm", 1450, GROUND_Y - 24),
            Enemy("centipede", 1700, GROUND_Y - 24),
            Enemy("pipeparasite", 1950, GROUND_Y - 120),
            Enemy("mudstalker", 2180, GROUND_Y - 30),
            Enemy("gaspod", 2360, GROUND_Y - 40),
        ]
        hazards += [Hazard(x, GROUND_Y, "water", h=30) for x in (560, 1080, 1600, 2100)]
    else:  # Level 5 — Research Facility: elite roster, lab platforms
        for (x, y, w) in [(340, 400, 130), (620, 320, 120), (900, 400, 130),
                          (1180, 300, 120), (1460, 400, 140), (1740, 320, 120),
                          (2020, 400, 140), (2300, 320, 130)]:
            plats.append((x, y, w, 22))
        enemies = [
            Enemy("sentinel", 470, GROUND_Y - 52),
            Enemy("ventstalker", 720, 220),
            Enemy("cultureswarm", 980, 300),
            Enemy("mycelium", 1120, GROUND_Y - 46),
            Enemy("reactorspore", 1500, GROUND_Y - 44),
            Enemy("sentinel", 1700, GROUND_Y - 52),
            Enemy("ventstalker", 1950, 210),
            Enemy("cultureswarm", 2180, 300),
            Enemy("reactorspore", 2360, GROUND_Y - 44),
        ]
    # Micro Mold — a common swarm enemy scattered across every level (weak alone,
    # dangerous in numbers). Spawn small clusters on clear ground away from the
    # pits/spikes and the heavier emplacements so a stretch never becomes a wall.
    # Each spot is (x, count); the final stage keeps lighter swarms since its
    # roster is already the densest.
    # spots chosen to sit in the gaps between the base roster and clear of the
    # hazard leaps, so swarms are spread across the map and never overlap a
    # neighbour (verified against every enemy's drawn hitbox).
    micro_spots = {1: [(630, 3), (1490, 3), (2000, 3)],
                   2: [(560, 3), (1000, 3), (1580, 3)],
                   3: [(600, 3), (880, 3), (1980, 3), (2180, 2)],
                   4: [(600, 3), (900, 3), (1900, 3)],
                   5: [(640, 2), (1800, 2), (2050, 2), (2280, 2)]}
    for mx, count in micro_spots[mission]:
        for k in range(count):
            enemies.append(Enemy("micromold", mx + k * 34, GROUND_Y - 26))
    # Spore Drifter — a floating spore-shooter deployed on certain (air-heavy)
    # stages only. Each spot is (x, hover_y) placed in the open air lanes, clear
    # of the spike/pit approaches so its aimed spores harass Ty without turning a
    # hazard leap into a death trap.
    drifter_spots = {3: [(300, 210), (2150, 240)],
                     5: [(480, 200), (2080, 220), (2380, 200)]}
    for dx, dy in drifter_spots.get(mission, []):
        enemies.append(Enemy("sporedrifter", dx, dy))
    # Toxic Slime — a slow corrosive ground blob deployed on certain (non-air)
    # stages. Placed in open ground clear of the spike/pit leaps: its acid spit
    # and acid-pool trail harass Ty on the flats, never over a hazard jump.
    slime_spots = {1: [340, 2500], 2: [340, 2400], 4: [340, 2500]}
    for sx in slime_spots.get(mission, []):
        enemies.append(Enemy("toxicslime", sx, GROUND_Y - 34))
    # Fungus Brute — a large, heavy ELITE dropped on a couple of stages as a
    # set-piece encounter. Placed in a wide clear stretch away from the base
    # roster and the hazard leaps (it's big, slow and hits hard).
    brute_spots = {2: [1750], 4: [1130]}
    for bx in brute_spots.get(mission, []):
        enemies.append(Enemy("fungusbrute", bx, GROUND_Y - 54))
    # Spore Turret — a stationary cannon MOUNTED ON the level's platforms (it
    # engages Ty from the environment). Each mount is (platform_cx, platform_top)
    # of a floating platform; the turret sits on top and fires down at Ty. Kept
    # on back-field ledges, clear of the hazard leaps.
    turret_mounts = {1: [(2335, 420)], 2: [(2370, 240)], 3: [(2425, 250)],
                     4: [(2345, 440)], 5: [(2090, 400)]}
    for (tcx, ptop) in turret_mounts.get(mission, []):
        enemies.append(Enemy("sporeturret", tcx - 20, ptop - 42))
    # Corrupt Cyst — a slow blob that BURSTS on death (radial spores + acid
    # pool). Placed on open ground clear of the hazard leaps so the death-burst
    # never shoves Ty into a pit or spike.
    cyst_spots = {3: [1350], 5: [980]}
    for cx0 in cyst_spots.get(mission, []):
        enemies.append(Enemy("corruptcyst", cx0, GROUND_Y - 38))
    # coins along the ground (skip any hovering over a pit) plus a few perched
    # on the ladder-reached platforms as a Mega Man style reward
    def _over_pit(cx):
        return any(ps - 14 < cx < ps + pw + 14 for (ps, pw) in pits)
    coins = [Coin(x, GROUND_Y - 60) for x in range(300, 2400, 190)
             if not _over_pit(x)]
    for (lx, top) in ladders_by[mission]:
        coins.append(Coin(lx + 9, top - 26))
    # a coin riding each moving platform, to reward using the dynamics
    for m in movers:
        coins.append(Coin(m.x0 + m.w / 2, m.y0 - 24))
    # BIG WALLS (Mega Man X): tall vertical faces Ty can wall-slide down and
    # wall-jump up — only ones tall enough engage the grapple (see wall_grab).
    # Each is seated on an elevated platform so it rises OFF the ground lane. Only
    # spots verified not to trap the ground-running auto-player are used, so the
    # run to the boss always stays clear. (x, y_top, w, h); h ~ 2.6x Ty's height.
    walls_by = WALLS_BY.get(mission, [])
    for (wx, wy, ww, wh) in walls_by:
        plats.append((wx, wy, ww, wh))
        coins.append(Coin(wx + ww / 2, wy - 22))       # a reward atop each wall
    return plats, enemies, coins, hazards, ladders, movers


# --------------------------------------------------------------------------- #
# Dr. Mira — support ally
# --------------------------------------------------------------------------- #
class Ally:
    """Dr. Mira (CHR — Field Scientist / Support Specialist). She deploys with
    Ty, trails just behind him, and fires a Bio-Cleaner HEAL BEAM whenever his
    health drops — keeping the run sustainable and the boss fights winnable.
    She's a non-combatant: enemies pass through her and she takes no damage."""
    def __init__(self, x):
        self.w, self.h = 30, 52
        self.x = float(x)
        self.y = float(GROUND_Y - self.h)
        self.facing = 1
        self.anim = 0.0
        self.moving = False
        self.heal_t = 0.0
        self.beam_cd = 0.0

    def update(self, dt, p, parts, snd):
        self.anim += dt
        self.beam_cd = max(0.0, self.beam_cd - dt)
        # trail behind Ty, easing toward a spot just behind him at his level
        tx = p.x + p.w / 2 - p.facing * 78 - self.w / 2
        ty = p.y + p.h - self.h
        self.x += (tx - self.x) * min(1.0, dt * 3.0)
        self.y += (ty - self.y) * min(1.0, dt * 4.5)
        self.moving = abs(tx - self.x) > 8
        self.facing = 1 if p.x + p.w / 2 >= self.x + self.w / 2 else -1
        # heal beam: top Ty up when he drops below ~65% health
        if self.heal_t > 0:
            self.heal_t -= dt
            p.hp = min(p.maxhp, p.hp + MIRA_HEAL_RATE * dt)
        elif not p.dead and p.hp < p.maxhp * 0.65 and self.beam_cd <= 0:
            self.heal_t = 1.5
            self.beam_cd = 4.5
            snd.play("health")

    def draw(self, s, cam, assets, t, p):
        healing = self.heal_t > 0
        if healing:                       # green heal beam from Mira's emitter to Ty
            ex = self.x - cam + self.w / 2 + self.facing * 26
            ey = self.y + 26
            tx = p.x - cam + p.w / 2
            ty = p.y + p.h * 0.45
            pulse = 150 + int(80 * math.sin(t * 22))
            pygame.draw.line(s, (*C_HP, 70), (ex, ey), (tx, ty), 7)
            pygame.draw.line(s, (150, 255, 190, pulse), (ex, ey), (tx, ty), 3)
            glow(s, tx, ty, 16, C_HP, 120)
            denom = (tx - ex) or 1.0
            for _ in range(2):
                fx = random.uniform(min(ex, tx), max(ex, tx))
                fy = ey + (ty - ey) * (fx - ex) / denom
                fcircle(s, fx, fy + random.uniform(-4, 4), 2, (190, 255, 205))
        name = ("mira_heal" if healing and assets.has("mira_heal")
                else "mira_run" if self.moving and assets.has("mira_run")
                else "mira")
        if not assets.has(name):
            name = "mira" if assets.has("mira") else None
        if name:
            breath = 1.0 + 0.05 * math.sin(t * 3.0 + self.x * 0.02)
            assets.blit_char(s, name, self.x - cam + self.w / 2, self.y + self.h,
                             self.h * CHAR_H, flip=self.facing < 0, squash=breath)


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
        self.tiny = pygame.font.SysFont("arial", 13, bold=True)
        self.name_f = pygame.font.SysFont("arialblack,arial", 22, bold=True)
        self.boss_f = pygame.font.SysFont("arialblack,arial", 24, bold=True)
        here = os.path.dirname(os.path.abspath(__file__))
        self.assets = AssetPack(os.path.join(here, "assets"))
        # persistent between missions (DesilPower HQ upgrades — Ch 3/4)
        self.armor = 0
        self.battery = 0
        self.speed = 0
        self.bank = 0            # Sample Cassettes banked at HQ
        self.cursor = 0
        self.mission = 1
        self.unlocked = 1        # highest mission unlocked
        self.cleared = set()     # missions beaten at least once (full reward)
        self.reset()
        self.state = STATE_MENU

    HQ_ITEMS = ["Deploy Mission", "Select Mission",
                "Research Lab: Armor  (+20 HP)",
                "Engineering Bay: Battery  (+20 Energy)",
                "Engineering Bay: Speed Module  (+10%)"]

    def hq_cost(self, i):
        lvl = (0, 0, self.armor, self.battery, self.speed)[i]
        return 40 + lvl * 30

    def _make_bg(self, mission):
        key = {1: "background", 2: "background2", 3: "background3",
               4: "background4", 5: "background5"}[mission]
        if self.assets.has(key):
            return pygame.transform.smoothscale(
                self.assets.imgs[key], (WIDTH, HEIGHT)).convert()
        top, bot = {1: ((26, 40, 38), (12, 20, 22)),
                    2: ((20, 34, 44), (8, 16, 22)),
                    3: ((44, 40, 34), (20, 16, 14)),
                    4: ((30, 24, 20), (10, 8, 8)),
                    5: ((30, 30, 46), (12, 12, 22))}[mission]
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            f = y / HEIGHT
            pygame.draw.line(bg, [int(a + (b - a) * f) for a, b in zip(top, bot)],
                             (0, y), (WIDTH, y))
        if mission == 2:      # faint tile grid
            for gx in range(0, WIDTH, 64):
                pygame.draw.line(bg, (30, 52, 62), (gx, 0), (gx, HEIGHT))
            for gy in range(0, HEIGHT, 64):
                pygame.draw.line(bg, (30, 52, 62), (0, gy), (WIDTH, gy))
        elif mission == 3:    # sunbeams through broken roof
            for bx in range(120, WIDTH, 240):
                beam = pygame.Surface((160, HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(beam, (*C_SUN, 22),
                                    [(40, 0), (120, 0), (160, HEIGHT), (0, HEIGHT)])
                bg.blit(beam, (bx, 0))
        return bg

    def reset(self):
        (self.plats, self.enemies, self.coins, self.hazards,
         self.ladders, self.movers) = build_level(self.mission)
        # tag each sprite enemy with its drawn-art aspect so its hitbox tracks
        # the visible sprite (see Enemy.rect)
        for e in self.enemies:
            key = ENEMY_ASSET.get(e.kind)
            if key and self.assets.has(key):
                aw, ah = self.assets.imgs[key].get_size()
                e.sprite_aspect = aw / ah
        self.bg = self._make_bg(self.mission)
        self.player = Player()
        # apply persistent HQ upgrades
        self.player.maxhp = PLAYER_HP + self.armor * 20
        self.player.maxenergy = MAX_ENERGY + self.battery * 20
        self.player.speed_mult = 1.0 + self.speed * 0.10
        self.player.hp = self.player.maxhp
        self.player.energy = self.player.maxenergy
        self.shots = []
        self.pickups = []
        self.acids = []          # Toxic Slime acid pools: [x, y, r, life, maxlife]
        self.parts = Particles()
        self.boss = None
        self.cam = 0.0
        self.score = 0
        self.spores = 1200
        self.cassettes = 0
        self.cassettes_total = len(self.coins)
        self.boss_intro = 0.0
        # MOLD-E companion drone (CHR_003) trails Ty
        self.molde_x = self.player.x - 44
        self.molde_y = self.player.y - 30
        self.molde_face = 1
        self.molde_t = 0.0
        # Dr. Mira — support ally who trails Ty and heals him
        self.mira = Ally(self.player.x - 64)
        # allied auto-defense turrets (TWR_001) stationed on clear ground
        self.turrets = [Turret(880), Turret(1850)]
        # pick-up weapons dropped through the level (Batch 4): a different one
        # partway through each mission so Ty finds new gear as he pushes on
        wid = WEAPON_ORDER[(self.mission - 1) % len(WEAPON_ORDER)]
        wid2 = WEAPON_ORDER[self.mission % len(WEAPON_ORDER)]
        self.weapons = [WeaponPickup(680, GROUND_Y - 60, wid),
                        WeaponPickup(1780, GROUND_Y - 60, wid2)]
        self.weapon_msg = ""
        self.weapon_msg_t = 0.0
        self.shake = 0.0            # screen-shake magnitude (decays)
        self.hitstop = 0.0          # brief freeze on big impacts (juice)
        # non-interactive background props (Batch 6) — set-dressing on the ground
        propset = {
            1: [("prop_fusebox", 430, 64), ("prop_generator", 1180, 74),
                ("prop_panel", 2050, 62), ("prop_generator", 2760, 74)],
            2: [("prop_vent", 520, 60), ("prop_panel", 1360, 62),
                ("prop_vent", 2120, 60), ("prop_fusebox", 2820, 64)],
            3: [("prop_bench", 380, 70), ("prop_generator", 1240, 74),
                ("prop_bench", 2260, 70)],
            4: [("prop_station", 560, 86), ("prop_generator", 1420, 74),
                ("prop_fusebox", 2320, 64), ("prop_panel", 2900, 62)],
            5: [("prop_station", 470, 86), ("prop_vent", 1120, 60),
                ("prop_panel", 1720, 62), ("prop_station", 2440, 86),
                ("prop_generator", 3020, 74)],
        }
        # Batch 6 Interactive Objects: the generator/fusebox/panel/station/vent/
        # bench you added are now USABLE — Ty presses E to power one on for a
        # themed reward (see Prop.USE), not just backdrop dressing.
        self.props = [Prop(key, x, ph)
                      for (key, x, ph) in propset.get(self.mission, [])]
        # carriable supply crates (Batch 7): Ty can pick up, carry, throw and
        # place a crate. Non-solid so the sprint path stays clear; placed off the
        # main line as optional interacts (the auto-bot ignores the interact key,
        # so crates and props are pure scenery to --selftest).
        crate_spots = {
            1: [(560, "SAMPLES"), (2180, "SPORE-KIT")],
            2: [(720, "FILTERS"), (2260, "SAMPLES")],
            3: [(640, "SPORE-KIT"), (2040, "SAMPLES")],
            4: [(760, "FILTERS"), (2600, "SAMPLES")],
            5: [(700, "SAMPLES"), (2120, "SPORE-KIT")],
        }
        self.crates = [Crate(x, GROUND_Y - 30, lbl)
                       for (x, lbl) in crate_spots.get(self.mission, [])]
        self.interact_msg = ""
        self.interact_msg_t = 0.0

    BOSS_QUOTE = {1: "\"THIS HOME... IS MINE!\"",
                  2: "\"YOU CANNOT WASH AWAY PERFECTION.\"",
                  3: "\"THE SKY BELONGS TO THE HIVE.\"",
                  4: "\"THE FOUNDATION ROTS WITH ME.\"",
                  5: "\"I AM EVERY SPORE YOU HAVE EVER FOUGHT.\""}
    REWARD_CASSETTES = {1: 120, 2: 180, 3: 250, 4: 350, 5: 500}

    def spawn_boss(self):
        self.boss = {1: Boss, 2: ShowerBeast, 3: SporeQueen,
                     4: CrawlorBoss, 5: MoldiusPrime}[self.mission]()
        self.boss_intro = 3.0
        self.snd.play("boss")

    # -- update -------------------------------------------------------------- #
    def update(self, dt, keys):
        if self.state != STATE_PLAY:
            self.snd.stop_music()
            return
        self.snd.music(self.mission)
        self.shake = max(0.0, self.shake - dt * 60)
        # hit-stop: a couple frozen frames on a big impact makes hits land hard
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            self.parts.update(dt)          # let particles keep popping
            return
        p = self.player
        # moving platforms (Mega Man dynamics): update, then carry whatever Ty
        # is riding by the platform's per-frame delta so momentum feels real
        ride = getattr(p, "ride", None)
        for m in self.movers:
            m.update(dt, ridden=(m is ride))
        if ride is not None and ride.solid():
            p.x += ride.dx
            p.y += ride.dy
            if ride.mode == "belt" and p.on_ground:   # conveyor shove
                p.x += ride.push * dt
        all_plats = self.plats + [m.rect() for m in self.movers if m.solid()]
        p.update(dt, keys, all_plats, self.shots, self.parts, self.snd,
                 self.ladders)
        # figure out which platform Ty is standing on now (for next-frame carry)
        p.ride = None
        for m in self.movers:
            if not m.solid():
                continue
            mx, my, mw, mh = m.rect()
            if p.on_ground and abs((p.y + p.h) - my) < 4 \
                    and p.x + p.w > mx + 2 and p.x < mx + mw - 2:
                p.ride = m
                break

        # crouch-context poses: beside cover (a background prop) or over a pickup
        pcx = p.x + p.w / 2
        p.near_prop = p.crouching and any(
            abs(pr.x - pcx) < 48 for pr in self.props)
        p.near_pickup = p.crouching and (
            any(not c.got and abs(c.x - pcx) < 32 for c in self.coins)
            or any(not wp.got and abs(wp.x - pcx) < 40 for wp in self.weapons))

        # Dr. Mira support ally: trail Ty and heal him when he's hurt
        self.mira.update(dt, p, self.parts, self.snd)

        # MOLD-E companion: ease toward a spot just behind & above Ty
        self.molde_t += dt
        tx = p.x + p.w / 2 - p.facing * 46
        ty = p.y - 24
        k = min(1.0, dt * 5.0)
        self.molde_x += (tx - self.molde_x) * k
        self.molde_y += (ty - self.molde_y) * k
        self.molde_face = p.facing

        # allied turrets scan and fire at nearby mold enemies
        for tr in self.turrets:
            tr.update(dt, self.enemies, self.shots)

        # camera
        if self.boss:
            self.cam = CAM_BOSS
        else:
            self.cam = max(0, min(LEVEL_W - WIDTH, p.x + p.w / 2 - WIDTH * 0.4))
            if p.x > BOSS_TRIGGER:
                self.spawn_boss()

        self._new_enemies = []
        self._new_shots = []      # e.g. Corrupt Cyst death-explosion spores
        for e in self.enemies:
            e.update(dt, p, self.shots, self.parts, self.acids)
        if self.boss:
            self.boss.update(dt, p, self.shots, self.parts, self.enemies)

        # hazards: steam damages (L2), updraft lifts (L3), water slows (L4),
        # spikes are instant death (Mega Man)
        for hz in self.hazards:
            hz.update(dt)
            if overlap(*hz.rect(), *p.rect()):
                if hz.kind == "updraft":
                    p.vy = min(p.vy, -260)
                    p.jumps = 2
                elif hz.kind == "water":
                    p.slow = 0.12
                elif hz.kind == "spike":
                    if p.iframe <= 0 and not p.dead:
                        p.hp = 0
                        p.dead = True
                        self.parts.spark(p.x + p.w / 2, p.y + p.h,
                                         C_DANGER, 16, 320)
                        self.shake = max(self.shake, 10)
                elif hz.on > 0:
                    p.hurt(3, self.parts)

        # Toxic Slime acid pools: age out, and corrode Ty while he stands in one.
        # Damage is a gentle direct tick (no hit-stagger) so a lingering pool can
        # never knock Ty back into a hazard or lock his advance.
        in_acid = False
        for a in self.acids:
            a[3] -= dt
            ax, ay, ar = a[0], a[1], a[2]
            if a[3] > 0 and not p.dead and overlap(ax - ar, ay - ar * 0.6,
                                                   ar * 2, ar * 1.2, *p.rect()):
                in_acid = True
        self.acids = [a for a in self.acids if a[3] > 0]
        if in_acid and not p.dead:
            self.acid_tick = getattr(self, "acid_tick", 0.0) - dt
            if self.acid_tick <= 0:
                self.acid_tick = 0.5
                p.hp -= 2
                self.parts.spark(p.x + p.w / 2, p.y + p.h, C_TOXIC, 6, 180)
                if p.hp <= 0:
                    p.hp = 0
                    p.dead = True
                    self.snd.play("lose")
        else:
            self.acid_tick = 0.0

        # fell down a pit — instant death (Mega Man)
        if p.y > HEIGHT + 30 and not p.dead:
            p.hp = 0
            p.dead = True
            self.snd.play("lose")

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
                        self._split(e, charged=False)
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
                g = getattr(sh, "grav", 0)
                if g:
                    sh.vy += g * dt
            if sh.hostile:
                if overlap(*sh.rect(), *p.rect()):
                    if p.iframe <= 0 and p.dash_t <= 0:
                        self.shake = max(self.shake, 7)
                        self.hitstop = max(self.hitstop, 0.05)
                    p.hurt(4, self.parts)
                    sh.dead = True
                    self.snd.play("hit")
            else:
                # a crouch-fired (low) shot leaves the braced kneel at chest
                # height but reaches DOWN, so it still rakes the low crawlers.
                if sh.low:
                    sx0, sy0, sw, sh0 = sh.rect()
                    shot_hit = (sx0, sy0, sw, sh0 + 34)
                else:
                    shot_hit = sh.rect()
                for e in self.enemies:
                    if not e.dead and overlap(*shot_hit, *e.rect()):
                        # crouch_only mold is armoured on top — a standing shot
                        # pings off it; only a crouch-fired (low) shot connects.
                        if e.crouch_only and not sh.low:
                            self.parts.spark(sh.x, sh.y, (200, 200, 210), 4, 160)
                            sh.dead = True
                            break
                        self.parts.spark(sh.x, sh.y, sh.color or C_SHOT, 6, 200)
                        e.x += 14 if sh.vx > 0 else -14      # knockback
                        if e.hurt(sh.dmg, self.parts):
                            self.score += 100
                            self.spores = max(0, self.spores - 50)
                            self.shake = max(self.shake, 5)
                            self.snd.play("kill")
                            self._split(e, charged=(sh.level >= 2))
                            self._maybe_drop(e)
                        sh.dead = True
                        break
                if not sh.dead and not getattr(sh, "from_turret", False) \
                        and self.boss and overlap(*sh.rect(), *self.boss.rect()):
                    dmg = sh.dmg
                    self.parts.spark(sh.x, sh.y, sh.color or C_SHOT, 6, 200)
                    if self.boss.weak_open > 0 and overlap(*sh.rect(), *self.boss.weak_rect()):
                        dmg *= 2
                        self.parts.spark(sh.x, sh.y, (150, 255, 180), 8, 260)
                        self.shake = max(self.shake, 10)
                        self.hitstop = max(self.hitstop, 0.04)
                        self.snd.play("weak")
                    else:
                        self.shake = max(self.shake, 4)
                        self.snd.play("bosshit")
                    if self.boss.hurt(dmg, self.parts):
                        self._boss_defeated()
                    sh.dead = True
        if self._new_shots:
            self.shots.extend(self._new_shots)
            self._new_shots = []
        self.shots = [s for s in self.shots if not s.dead]
        if self._new_enemies:
            self.enemies.extend(self._new_enemies)

        # crouch melee: a short front swing that clears nearby mold (and can
        # chip a boss / crack an open weak point)
        if p.melee_fire:
            p.melee_fire = False
            mr = p.melee_rect()
            self.shake = max(self.shake, 5)
            for e in self.enemies:
                if not e.dead and overlap(*mr, *e.rect()):
                    self.parts.spark(e.x + e.w / 2, e.y + e.h / 2,
                                     C_TEAL_LT, 8, 240)
                    e.x += 20 * p.facing                    # knockback
                    if e.hurt(MELEE_DMG, self.parts):
                        self.score += 100
                        self.spores = max(0, self.spores - 50)
                        self.snd.play("kill")
                        self._split(e, charged=False)
                        self._maybe_drop(e)
            self.enemies = [e for e in self.enemies if not e.dead]
            if self.boss and overlap(*mr, *self.boss.rect()):
                if self.boss.weak_open > 0 and overlap(*mr, *self.boss.weak_rect()):
                    self.snd.play("weak")
                    if self.boss.hurt(MELEE_DMG * 2, self.parts):
                        self._boss_defeated()
                else:
                    self.snd.play("bosshit")
                    if self.boss.hurt(MELEE_DMG, self.parts):
                        self._boss_defeated()

        # enemy contact damage
        for e in self.enemies:
            if not e.dead and overlap(*e.rect(), *p.rect()):
                if p.iframe <= 0 and p.dash_t <= 0:
                    self.shake = max(self.shake, 7)
                    self.hitstop = max(self.hitstop, 0.05)
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
                if p.crouching:            # grabbing it low = item pose
                    p.item_t = 0.5
                self.snd.play("coin")
        self.coins = [c for c in self.coins if not c.got]

        # pickups (health / energy)
        for pk in self.pickups:
            if not pk.got and overlap(pk.x - 12, pk.y - 12, 24, 24, *p.rect()):
                pk.got = True
                if p.crouching:                # grabbed low = item pose
                    p.item_t = 0.5
                if pk.kind == "health":
                    p.hp = min(p.maxhp, p.hp + HP_PACK)
                    self.snd.play("health")
                else:
                    p.energy = min(p.maxenergy, p.energy + ENERGY_CELL)
                    self.snd.play("energy")
        self.pickups = [pk for pk in self.pickups if not pk.got]

        # weapon pick-ups (Batch 4): walk over one to equip it
        for wp in self.weapons:
            if not wp.got and overlap(*wp.rect(), *p.rect()):
                wp.got = True
                p.weapon = wp.wid
                self.weapon_msg = WEAPONS[wp.wid]["name"]
                self.weapon_msg_t = 2.2
                self.snd.play("weapon")
        self.weapons = [wp for wp in self.weapons if not wp.got]
        self.weapon_msg_t = max(0.0, getattr(self, "weapon_msg_t", 0.0) - dt)

        # supply crates + Batch 6 interactive objects: pick up / carry / throw /
        # place a crate, and USE a generator / fusebox / panel / station / etc.
        self._interact(dt, p)

        if p.dead:
            self.state = STATE_OVER
            self.bank += self.cassettes
            self.snd.play("lose")
            self.snd.stop_music()

        self.boss_intro = max(0.0, self.boss_intro - dt)
        self.parts.update(dt)

    def _interact(self, dt, p):
        """Item / interact mechanic: advance crates, let Ty pick up / carry /
        throw / place a crate, and USE a Batch 6 interactive object (generator,
        fusebox, panel, station, vent, bench) for a themed reward — the leftover
        TyGuy video clips wired into real gameplay. Crates are non-solid, so they
        never block Ty's run; the auto-bot ignores the interact key."""
        # advance thrown crates; a flying crate smashes the first enemy it hits
        for cr in self.crates:
            cr.update(dt, self.plats)
            if cr.thrown:
                for e in self.enemies:
                    if not e.dead and overlap(*cr.rect(), *e.rect()):
                        self.parts.splat(cr.x + cr.w / 2, cr.y + cr.h / 2,
                                         C_TEAL_LT, 12)
                        if e.hurt(6, self.parts):
                            self.score += 100
                            self.spores = max(0, self.spores - 50)
                            self.snd.play("kill")
                            self._split(e, charged=False)
                            self._maybe_drop(e)
                        cr.vx *= 0.4
                        self.shake = max(self.shake, 5)
                        break
        self.crates = [cr for cr in self.crates if not cr.dead]

        carried = p.carrying
        if carried is not None:
            # ride in Ty's hands at chest height, in front of him
            carried.carried = True
            carried.thrown = False
            carried.x = p.x + p.w / 2 - carried.w / 2 + p.facing * 6
            carried.y = p.y + 4
            if p.want_throw:
                carried.carried = False
                carried.thrown = True
                carried.vx = p.facing * 360
                carried.vy = -220
                carried.x = p.x + p.w / 2 - carried.w / 2 + p.facing * 22
                p.carrying = None
                p.throw_t = 0.30
                self.snd.play("dash")
            elif p.want_interact:
                carried.carried = False
                carried.thrown = False
                carried.vx = carried.vy = 0.0
                carried.y = GROUND_Y - carried.h
                p.carrying = None
                p.place_t = 0.30
                self.snd.play("land")
            self.interact_msg_t = max(0.0, getattr(self, "interact_msg_t", 0.0) - dt)
            return

        # empty-handed: interact picks up the nearest crate, else uses a console
        pcx = p.x + p.w / 2
        if p.want_interact:
            best, bestd = None, 46
            for cr in self.crates:
                if cr.thrown:
                    continue
                d = abs((cr.x + cr.w / 2) - pcx)
                if d < bestd and abs((cr.y + cr.h) - (p.y + p.h)) < 64:
                    best, bestd = cr, d
            if best is not None:
                p.carrying = best
                best.carried = True
                p.pickup_t = 0.28
                self.snd.play("coin")
            else:
                # USE the nearest Batch 6 interactive object on the ground
                for pr in self.props:
                    if pr.used or abs(pr.x - pcx) >= 46:
                        continue
                    if abs((p.y + p.h) - GROUND_Y) > 90:
                        continue                # must be down on the floor by it
                    pr.used = True
                    p.use_t = 0.5
                    kind, amt, label = pr.reward()
                    if kind == "health":
                        p.hp = min(p.maxhp, p.hp + amt)
                    elif kind == "energy":
                        p.energy = min(p.maxenergy, p.energy + amt)
                    else:                       # panel: bonus score / spore purge
                        self.score += 150
                        self.spores = max(0, self.spores - 80)
                    self.interact_msg = label
                    self.interact_msg_t = 2.0
                    self.snd.play("energy")
                    break
        self.interact_msg_t = max(0.0, getattr(self, "interact_msg_t", 0.0) - dt)

    def _boss_defeated(self):
        """Shared mission-win bookkeeping (a shot or a melee can land it)."""
        self.shake = max(self.shake, 18)
        self.hitstop = max(self.hitstop, 0.08)
        self.state = STATE_WIN
        first = self.mission not in self.cleared
        self.cleared.add(self.mission)
        reward = self.REWARD_CASSETTES[self.mission]
        if not first:                # replays give a fraction only
            reward //= 5
        self.bank += self.cassettes + reward
        self.unlocked = max(self.unlocked,
                            min(self.mission + 1, len(MISSIONS)))
        self.snd.play("win")

    def _maybe_drop(self, e):
        r = random.random()
        if r < 0.22:
            self.pickups.append(Pickup(e.x + e.w / 2, e.y, "health"))
        elif r < 0.44:
            self.pickups.append(Pickup(e.x + e.w / 2, e.y, "energy"))

    def _split(self, e, charged):
        # Corrupt Cyst bursts on death — a radial spatter of toxic spores plus a
        # lingering acid pool, so a point-blank kill catches Ty in the blast.
        if e.kind == "corruptcyst":
            cx, cy = e.x + e.w / 2, e.y + e.h / 2
            self.parts.spark(cx, cy, C_TOXIC, 20, 320)
            for ang in range(0, 360, 45):          # 8-way spore burst
                a = math.radians(ang)
                sh = Shot(cx, cy, math.cos(a) * 190, 4, -1, hostile=True)
                sh.vy = math.sin(a) * 190
                self._new_shots.append(sh)
            self.acids.append([cx, GROUND_Y - 4, 20, 2.2, 2.2])
            self.shake = max(self.shake, 6)
        # Swarms / Centipede split unless killed by a charged hit
        if e.kind not in ("ventswarm", "centipede", "cultureswarm") \
                or charged or e.gen >= 2:
            return
        for d in (-1, 1):
            child = Enemy(e.kind, e.x + d * 24, e.y)
            child.w, child.h = int(e.w * 0.66), int(e.h * 0.66)
            child.hp = 3
            child.gen = e.gen + 1
            child.home_y = e.home_y
            child.sprite_aspect = e.sprite_aspect
            self._new_enemies.append(child)

    # -- draw ---------------------------------------------------------------- #
    def draw(self, t):
        # screen shake: render the scene to a buffer, then blit it jittered
        if self.state == STATE_PLAY and self.shake > 0.6:
            if getattr(self, "_buf", None) is None:
                self._buf = pygame.Surface((WIDTH, HEIGHT))
            real = self.screen
            self.screen = self._buf
            self._draw_scene(t)
            self.screen = real
            m = min(self.shake, 14)
            ox = random.uniform(-m, m)
            oy = random.uniform(-m, m)
            real.fill((0, 0, 0))
            real.blit(self._buf, (int(ox), int(oy)))
        else:
            self._draw_scene(t)

    def _draw_scene(self, t):
        s = self.screen
        s.blit(self.bg, (0, 0))
        cam = self.cam

        if self.state == STATE_MENU:
            # DesilPower HQ hub (Ch 3)
            # Commander Ellis (NPC_001) leads from the left
            if self.assets.has("ellis"):
                self.assets.blit_fit(s, "ellis", 78, 350, 138, 300)
            # The Purification Core (CHR_009) — heart of the hub, IDLE (PULSE)
            if self.assets.has("purcore"):
                pulse = 0.5 + 0.5 * math.sin(t * 3.0)
                glow(s, 74, 132, int(42 + 10 * pulse), C_HP,
                     strength=int(50 + 60 * pulse))
                sc = 94 + 6 * pulse
                self.assets.blit_fit(s, "purcore", 74, 132, sc, sc)
            # Purification Hub support crew down the right gutter
            # Captain Rex (CHR_007) leads the squad, then the support staff.
            # Rex shifts stance now and then for a live idle.
            for i, key in enumerate(("rex", "mira", "engineer", "medic")):
                pose = key
                if key == "rex" and self.assets.has("rex_2") \
                        and (t + i) % 3.0 < 0.45:
                    pose = "rex_2"
                if self.assets.has(pose):
                    self.assets.blit_fit(s, pose, 892, 172 + i * 105, 92, 100)
            self._center(self.big, "DESILPOWER HQ", 92, C_TEAL_LT)
            self._center(self.small,
                         "Mission Command · Research Lab · Engineering Bay",
                         132, C_DIM)
            self._center(self.mid, f"Sample Cassettes banked: {self.bank}", 168, C_COIN)
            mname = MISSIONS[self.mission]["name"]
            for i, label in enumerate(self.HQ_ITEMS):
                y = 222 + i * 40
                sel = (i == self.cursor)
                if i == 0:
                    txt = f"Deploy  →  Mission {self.mission}: {mname}"
                elif i == 1:
                    txt = f"Select Mission:  {self.mission}/{len(MISSIONS)}" \
                          + ("   (◀ ▶ / Enter)" if self.unlocked > 1 else "   (locked)")
                else:
                    lvl = (0, 0, self.armor, self.battery, self.speed)[i]
                    txt = f"{label}   Mk{lvl} → {lvl + 1}   [{self.hq_cost(i)} cassettes]"
                col = C_TEAL_LT if sel else C_TEXT
                if sel:
                    pygame.draw.rect(s, (24, 44, 42),
                                     (WIDTH // 2 - 330, y - 15, 660, 32), border_radius=8)
                self._center(self.small if i else self.mid, txt, y, col)
            self._center(self.small, "↑/↓ select   ◀ ▶ change mission   Enter: deploy / buy",
                         HEIGHT - 102, C_DIM)
            self._center(self.small,
                         "In-mission:  Move A/D · Jump Space/W (hold = higher) · "
                         "J blaster (hold = charge) · K HEPA vacuum · ↑↓ climb ladders",
                         HEIGHT - 80, C_DIM)
            self._center(self.small,
                         "Slide: ↓+Jump  ·  Crouch ↓/S (sneak-walk, ducked fire/aim)  ·  "
                         "L dash  ·  crouch+L = slide / melee  ·  mind the pits & spikes!",
                         HEIGHT - 60, C_TEAL_LT)
            self._center(self.mid, MISSIONS[self.mission]["briefing"], HEIGHT - 36, C_TOXIC)
            return

        self._draw_world(t)
        self._hud()

        # boss introduction cutscene banner (V2C8)
        if self.boss_intro > 0 and self.boss:
            band = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
            band.fill((8, 12, 14, 190))
            s.blit(band, (0, HEIGHT // 2 - 60))
            self._center(self.big, self.boss.NAME, HEIGHT // 2 - 24, C_DANGER)
            self._center(self.mid, self.BOSS_QUOTE[self.mission], HEIGHT // 2 + 22, C_TOXIC)

        if self.state in (STATE_WIN, STATE_OVER):
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((8, 12, 14, 190))
            s.blit(veil, (0, 0))
            if self.state == STATE_WIN and self.assets.has("player_victory"):
                self.assets.blit_fit(s, "player_victory", 116, HEIGHT - 92, 130, 168)
            # Dr. Sporead (CHR_008) — the mastermind looms over each victory
            # tease, cackling (idle vial pose <-> arms-up gloat).
            if self.state == STATE_WIN and self.mission < 5 \
                    and self.assets.has("sporead"):
                skey = "sporead"
                if self.assets.has("sporead_gloat") and int(t * 1.6) % 2:
                    skey = "sporead_gloat"
                self.assets.blit_fit(s, skey, WIDTH - 108, HEIGHT - 92,
                                     120, 168, flip=True)
            if self.state == STATE_WIN and self.mission == 5:
                # campaign finale
                self._center(self.big, "MISSION COMPLETE", HEIGHT // 2 - 96, C_TEAL_LT)
                self._center(self.mid, "MOLDIUS PRIME purified. The outbreak is over.",
                             HEIGHT // 2 - 44, C_TEXT)
                for i, ln in enumerate([
                        "Clean air returns. Ty is recognized as the Master Remediator.",
                        "Every home, business, and community is restored.",
                        f"Final score {self.score}  ·  Cassettes banked: {self.bank}"]):
                    self._center(self.small, ln, HEIGHT // 2 - 8 + i * 24, C_DIM)
                self._center(self.small,
                             "...a remote sensor detects a faint signal in an "
                             "unexplored region.", HEIGHT // 2 + 64, C_TOXIC)
            elif self.state == STATE_WIN:
                m = MISSIONS[self.mission]
                self._center(self.big, m["name"] + " RESTORED", HEIGHT // 2 - 92, C_TEAL_LT)
                self._center(self.mid, f"{m['boss']} defeated!", HEIGHT // 2 - 40, C_TEXT)
                self._center(self.small, f"NEW TOOL UNLOCKED:  {m['reward']}  ·  "
                             f"+{self.REWARD_CASSETTES[self.mission]} Sample Cassettes  ·  "
                             "Restoration Badge", HEIGHT // 2 - 8, C_TOXIC)
                self._center(self.small,
                             f"Score {self.score}  ·  Cassettes banked: {self.bank}",
                             HEIGHT // 2 + 18, C_TEXT)
                tease = {1: "Dr. Mira: \"These traces link the Sludge King to "
                            "something bigger — Moldius Prime...\"",
                         2: "Commander Ellis: \"The attic is next.\"",
                         3: "Ellis: \"The next mission takes us beneath the home — "
                            "the crawlspace.\"",
                         4: "Ellis: \"Every sample traces to an abandoned research "
                            "facility. That's the source.\""}[self.mission]
                self._center(self.small, tease, HEIGHT // 2 + 42, C_DIM)
            else:
                self._center(self.big, "TECHNICIAN DOWN", HEIGHT // 2 - 40, C_DANGER)
                self._center(self.mid, f"The mold won this time.  Score {self.score}",
                             HEIGHT // 2 + 16, C_TEXT)
            # the finale carries an extra tease line, so drop the prompt lower
            # there to avoid colliding with it
            pe_y = HEIGHT // 2 + (104 if (self.state == STATE_WIN
                                          and self.mission == 5) else 66)
            self._center(self.mid, "Press Enter — return to DesilPower HQ",
                         pe_y, C_TEAL_LT)

    def _draw_world(self, t):
        s, cam = self.screen, self.cam
        # Batch 6 Interactive Objects on the ground: full-bright with a pulsing
        # glow while still usable (press E), dimmed once spent. Drawn behind the
        # platforms/enemies from the real cut art.
        for pr in getattr(self, "props", []):
            key, px, ph = pr.key, pr.x, pr.ph
            sx = px - cam
            if sx < -120 or sx > WIDTH + 120 or not self.assets.has(key):
                continue
            img = self.assets.imgs[key]
            aw, ah = img.get_size()
            sc = ph / ah
            dw, dh = max(1, int(aw * sc)), max(1, int(ah * sc))
            if not pr.used:
                glow(s, sx, GROUND_Y - dh * 0.5, dh * 0.7,
                     (110, 220, 160), int(46 + 30 * math.sin(t * 4)))
            sp = pygame.transform.smoothscale(img, (dw, dh)).copy()
            tint = (120, 130, 120, 255) if pr.used else (240, 248, 240, 255)
            sp.fill(tint, special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(sp, (int(sx - dw / 2), int(GROUND_Y - dh)))
        # platforms
        for (x, y, w, h) in self.plats:
            sx = x - cam
            if sx + w < 0 or sx > WIDTH:
                continue
            pkey = {1: "platform", 2: "platform2", 3: "platform3",
                    4: "platform4", 5: "platform5"}[self.mission]
            if self.assets.has(pkey):
                s.blit(pygame.transform.smoothscale(
                    self.assets.imgs[pkey], (int(w), int(h))), (int(sx), int(y)))
            elif self.mission == 2:
                pygame.draw.rect(s, C_TILE_DK, (int(sx), int(y), int(w), int(h)))
                pygame.draw.rect(s, C_TILE, (int(sx), int(y), int(w), 6))
            elif self.mission == 3:
                pygame.draw.rect(s, C_WOOD_DK, (int(sx), int(y), int(w), int(h)))
                pygame.draw.rect(s, C_WOOD, (int(sx), int(y), int(w), 6))
            elif self.mission == 4:
                pygame.draw.rect(s, C_MUD_DK, (int(sx), int(y), int(w), int(h)))
                pygame.draw.rect(s, C_MUD, (int(sx), int(y), int(w), 6))
            elif self.mission == 5:
                pygame.draw.rect(s, C_LAB_DK, (int(sx), int(y), int(w), int(h)))
                pygame.draw.rect(s, C_LAB, (int(sx), int(y), int(w), 6))
            else:
                pygame.draw.rect(s, (46, 40, 34), (int(sx), int(y), int(w), int(h)))
                pygame.draw.rect(s, (70, 104, 52), (int(sx), int(y), int(w), 6))
        # ladders (Mega Man): two rails + rungs
        for (lx, ly, lw, lh) in self.ladders:
            sx = lx - cam
            if sx + lw < 0 or sx > WIDTH:
                continue
            # warm metal/wood tone so Ty's climb pose (which carries its own
            # ladder grip) blends onto it
            pygame.draw.rect(s, (120, 108, 74), (int(sx), int(ly), 4, int(lh)))
            pygame.draw.rect(s, (120, 108, 74), (int(sx + lw - 4), int(ly), 4, int(lh)))
            for ry in range(int(ly), int(ly + lh), 15):
                pygame.draw.line(s, (176, 162, 116), (int(sx), ry),
                                 (int(sx + lw), ry), 3)
        # moving platforms (Mega Man dynamics)
        for m in self.movers:
            if not m.solid():
                continue
            mx, my, mw, mh = m.rect()
            sx = mx - cam + (math.sin(t * 40) * m.shk)
            if sx + mw < 0 or sx > WIDTH:
                continue
            base = {"fall": (120, 96, 60), "belt": (60, 92, 96)}.get(
                m.mode, (60, 80, 110))
            edge = {"fall": (180, 150, 90), "belt": (120, 200, 210)}.get(
                m.mode, (120, 150, 200))
            pygame.draw.rect(s, base, (int(sx), int(my), int(mw), int(mh)),
                             border_radius=4)
            pygame.draw.rect(s, edge, (int(sx), int(my), int(mw), 4),
                             border_radius=4)
            if m.mode == "belt":                 # scrolling conveyor chevrons
                off = int(t * 90) % 24
                for cxp in range(-24, int(mw) + 24, 24):
                    bx = int(sx) + cxp + off
                    pygame.draw.line(s, edge, (bx, int(my) + mh - 5),
                                     (bx + 8, int(my) + 4), 2)
            elif m.mode == "v":                  # elevator up-arrow
                pygame.draw.polygon(s, edge, [
                    (sx + mw / 2, my - 5), (sx + mw / 2 - 5, my + 2),
                    (sx + mw / 2 + 5, my + 2)])
            elif m.mode == "h":                  # side thrust markers
                midy = int(my + mh / 2)
                pygame.draw.circle(s, edge, (int(sx + 6), midy), 3)
                pygame.draw.circle(s, edge, (int(sx + mw - 6), midy), 3)
        for tr in self.turrets:
            tr.draw(s, cam, self.assets)
        for hz in self.hazards:
            hz.draw(s, cam, t)
        # Toxic Slime acid pools — corrosive splats on the ground (fade as they
        # age); drawn under the enemies/coins so they read as floor hazards
        for a in self.acids:
            ax, ay, ar, life, maxlife = a
            f = max(0.0, min(1.0, life / maxlife))
            rr = int(ar * (0.55 + 0.45 * f))
            pool = pygame.Surface((rr * 2, rr), pygame.SRCALPHA)
            pygame.draw.ellipse(pool, (150, 200, 60, int(150 * f)),
                                (0, 0, rr * 2, rr))
            pygame.draw.ellipse(pool, (90, 130, 40, int(190 * f)),
                                (0, 0, rr * 2, rr), 2)
            s.blit(pool, (int(ax - cam - rr), int(ay - rr * 0.5)))
        for c in self.coins:
            c.draw(s, cam, self.assets, t)
        for pk in self.pickups:
            pk.draw(s, cam, t)
        for wp in self.weapons:
            wp.draw(s, cam, self.assets, t)
        for e in self.enemies:
            e.draw(s, cam, self.assets)
        if self.boss:
            self.boss.draw(s, cam, self.assets)
        # MOLD-E companion drone hovers behind Ty; switches to ALERT near mold
        px = self.player.x + self.player.w / 2
        near = any(not e.dead and abs((e.x + e.w / 2) - px) < 260
                   for e in self.enemies) or self.boss is not None
        if near and self.assets.has("molde_alert"):
            mkey = "molde_alert"                    # reacts to danger
        elif abs(self.player.vx) < 12 and self.assets.has("molde_scan"):
            mkey = "molde_scan"                     # scans while Ty is still
        else:
            mkey = "molde"                          # follows in motion
        if self.assets.has(mkey):
            bob = math.sin(self.molde_t * 3.2) * 4
            self.assets.blit_fit(s, mkey, self.molde_x - cam,
                                 self.molde_y + bob, 48, 48,
                                 flip=self.molde_face < 0)
        # supply crates (Batch 7): grounded ones sit behind Ty; a carried one
        # rides in his hands and is drawn in front after the player
        for cr in getattr(self, "crates", []):
            if not cr.carried:
                cr.draw(s, cam, t)
        self.mira.draw(s, cam, self.assets, t, self.player)
        self.player.draw(s, cam, self.assets, t)
        for cr in getattr(self, "crates", []):
            if cr.carried:
                cr.draw(s, cam, t)
        for sh in self.shots:
            sh.draw(s, cam, self.assets)
        self.parts.draw(s, cam)

    def _panel(self, x, y, w, h, fill=(12, 18, 20, 210), border=(74, 150, 120),
               r=8):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, fill, (0, 0, w, h), border_radius=r)
        pygame.draw.rect(surf, border, (0, 0, w, h), width=2, border_radius=r)
        self.screen.blit(surf, (x, y))

    def _bar(self, x, y, w, h, frac, col, r=5):
        s = self.screen
        pygame.draw.rect(s, (8, 12, 13), (x, y, w, h), border_radius=r)
        fw = max(0, int((w - 4) * max(0.0, min(1.0, frac))))
        if fw > 0:
            pygame.draw.rect(s, col, (x + 2, y + 2, fw, h - 4), border_radius=r - 1)

    def _hud(self):
        s = self.screen
        p = self.player
        # ---- player status panel (top-left) ----
        # panel is sized to contain the bars AND their right-hand labels; the
        # widest label ("HP 140/140" at max armor) ends near x333, so the border
        # sits past that with a clean margin
        self._panel(14, 12, 332, 74)
        # portrait
        pygame.draw.rect(s, (8, 14, 16), (22, 20, 58, 58), border_radius=6)
        if self.assets.has("player"):
            self.assets.blit_fit(s, "player", 51, 49, 54, 54)
        pygame.draw.rect(s, (74, 150, 120), (22, 20, 58, 58), width=2, border_radius=6)
        self._t(self.name_f, "TY", (90, 18), C_TEXT)
        # HP + energy bars
        self._bar(90, 44, 168, 15, p.hp / p.maxhp, C_HP)
        self._t(self.tiny, f"HP {int(p.hp)}/{int(p.maxhp)}", (264, 45), C_DIM)
        self._bar(90, 63, 168, 12, p.energy / p.maxenergy, (96, 172, 240))
        self._t(self.tiny, "ENERGY", (264, 63), C_DIM)

        # ---- score / resources (top-right) ----
        self._panel(WIDTH - 250, 12, 236, 74)
        self._t(self.mid, f"SCORE {self.score}", (WIDTH - 240, 16), C_TEXT)
        self._t(self.tiny, f"SPORE COUNT {self.spores}", (WIDTH - 240, 46), C_TOXIC)
        self._t(self.tiny, f"CASSETTES {self.cassettes}/{self.cassettes_total}",
                (WIDTH - 240, 66), C_COIN)

        # ---- objective tracker (top-left, below status) ----
        if self.boss and self.boss_intro <= 0:
            self._panel(14, 94, 214, 46, border=(150, 90, 88))
            self._t(self.tiny, "OBJECTIVE", (24, 100), (232, 140, 100))
            self._t(self.small, f"Defeat {self.boss.NAME.title()}", (24, 116), C_TEXT)

        # ---- weapon chip (bottom-left) ----
        wcol = WEAPONS[p.weapon]["color"] if p.weapon else C_SHOT
        wlabel = WEAPONS[p.weapon]["name"] if p.weapon else "HEPA BLASTER"
        self._panel(14, HEIGHT - 62, 250, 48, border=tuple(wcol))
        pygame.draw.rect(s, (8, 14, 16), (22, HEIGHT - 54, 40, 32), border_radius=5)
        wicon = "wpn_" + p.weapon if p.weapon else None
        if wicon and self.assets.has(wicon):
            self.assets.blit_fit(s, wicon, 42, HEIGHT - 38, 36, 28)
        else:
            fcircle(s, 42, HEIGHT - 38, 9, wcol)
        self._t(self.small, wlabel, (70, HEIGHT - 52), wcol)
        # charge meter under the name
        ch = min(1.0, p.charge / 0.9) if p.charging else 0
        self._bar(70, HEIGHT - 30, 180, 9, ch, wcol, r=4)

        # ---- weapon pick-up toast ----
        if self.weapon_msg_t > 0:
            self._center(self.mid, "EQUIPPED: " + self.weapon_msg, 150, C_TEAL_LT)
        # ---- console / interact toast ----
        if getattr(self, "interact_msg_t", 0.0) > 0:
            self._center(self.mid, self.interact_msg, 178, (150, 220, 160))

        # ---- boss health bar (bottom-center) ----
        if self.boss:
            ph = self.boss.phase()
            pcol = {1: (232, 96, 92), 2: (240, 168, 72),
                    3: (206, 96, 208)}.get(ph, (206, 96, 208))
            bw, bh = 470, 66
            bx = WIDTH // 2 - bw // 2
            by = HEIGHT - 78
            self._panel(bx, by, bw, bh, fill=(10, 16, 18, 220),
                        border=(60, 74, 78), r=9)
            self._t(self.boss_f, self.boss.NAME, (bx + 16, by + 8), pcol)
            self._t(self.small, "(Phase %d)" % ph,
                    (bx + 22 + self.boss_f.size(self.boss.NAME)[0], by + 14), C_DIM)
            frac = max(0, self.boss.hp / self.boss.maxhp)
            self._bar(bx + 16, by + 38, bw - 32, 18, frac, pcol, r=6)
            hp_txt = f"{int(self.boss.hp)} / {int(self.boss.maxhp)} HP"
            g = self.tiny.render(hp_txt, True, C_TEXT)
            s.blit(g, (bx + bw - 18 - g.get_width(), by + 40))
            if self.boss.weak_open > 0:
                hint = {1: "WEAK POINT OPEN — hit the chest valve!",
                        2: "WEAK POINT OPEN — dash behind and hit the regulator!",
                        3: "WEAK POINT OPEN — hit the Queen's exposed core!",
                        4: "WEAK POINT OPEN — hit the exposed segment core!",
                        5: "PURIFICATION NODE EXPOSED — hit the core!"}[self.mission]
                self._center(self.small, hint, by - 22, C_TEAL_LT)

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
            elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d) \
                    and self.cursor == 1:
                self.mission = self.mission % self.unlocked + 1
            elif key == pygame.K_RETURN:
                if self.cursor == 0:
                    self.reset()
                    self.state = STATE_PLAY
                elif self.cursor == 1:
                    self.mission = self.mission % self.unlocked + 1
                else:
                    cost = self.hq_cost(self.cursor)
                    if self.bank >= cost:
                        self.bank -= cost
                        if self.cursor == 2:
                            self.armor += 1
                        elif self.cursor == 3:
                            self.battery += 1
                        elif self.cursor == 4:
                            self.speed += 1
                        self.snd.play("coin")
        elif self.state in (STATE_WIN, STATE_OVER) and key == pygame.K_RETURN:
            if self.state == STATE_WIN:
                self.mission = self.unlocked   # advance selection to next mission
            self.cursor = 0
            self.state = STATE_HQ


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
class _AutoKeys(dict):
    """dict of held keys that defaults missing keys to 'not pressed'."""
    def __missing__(self, _):
        return False


def _bot_keys(game, st, i):
    """World-aware auto-player used by --selftest and --demo. Walks Ty to the
    boss along the ground path: fires the blaster, holds jumps for full height
    (variable-jump) with a mid-air double-jump to clear pits, leaps spikes /
    steam vents / blocking enemies, then ducks-and-hops to dodge at the boss.
    (Ladders are an optional player route, so the bot ignores them.)"""
    K = _AutoKeys()
    p = game.player
    K[pygame.K_j] = (i % 6) < 2                 # keep the blaster firing
    front = p.x + p.w

    def solid_below(x):
        fy = p.y + p.h
        for (px, py, pw, ph) in game.plats:
            if px - 2 <= x <= px + pw + 2 and fy - 12 <= py <= fy + 180:
                return True
        return False

    def hazard_ahead():
        for hz in game.hazards:
            if hz.kind == "spike":
                left, right = hz.x, hz.x + hz.zh
            elif hz.kind == "steam":
                left, right = hz.x - 34, hz.x + 34
            else:
                continue
            if front + 4 < right and left < front + 62:
                return True
        return False

    def enemy_block():
        return any(not e.dead and 0 < (e.x - p.x) < 88 and abs(e.y - p.y) < 72
                   for e in game.enemies)

    def short_ahead():
        # a CROUCH-ONLY crawler right in front on solid ground — standing fire
        # pings off it, so the bot has to duck to shoot it out.
        for e in game.enemies:
            if e.dead or not e.crouch_only:
                continue
            if (0 < (e.x - front) < 82
                    and abs((e.y + e.h) - (p.y + p.h)) < 46
                    and solid_below(front + 20)):
                return True
        return False

    if game.boss is not None:
        # boss: hold the line and fire; duck to shrink the hitbox, and hop to
        # dodge — vertical dodging while keeping the blaster on target
        K[pygame.K_j] = (i % 5) < 2
        want = False
        if st.get("jt", 0) > 0:
            st["jt"] -= 1
            want = True
        else:
            phase = (i // 22) % 3
            if phase == 2 and p.on_ground and not st.get("sp", False):
                st["jt"] = 10                    # hop
                want = True
            elif p.on_ground:
                K[pygame.K_DOWN] = True          # duck (low hitbox, still fires)
        K[pygame.K_SPACE] = want
        st["sp"] = want
        return K

    def hazard_soon():
        for hz in game.hazards:
            if hz.kind == "spike":
                left, right = hz.x, hz.x + hz.zh
            elif hz.kind == "steam":
                left, right = hz.x - 34, hz.x + 34
            else:
                continue
            if front < right and left < front + 150:
                return True
        return False

    # crouch-shoot a crouch-only crawler blocking the ground path: duck (C) so
    # the muzzle drops to hit it, stop, and let the pulsing blaster clear it —
    # but never while a spike/vent is close, where jumping has to take priority.
    if (p.on_ground and short_ahead() and not hazard_soon()
            and not (not solid_below(front + 18))):
        K[pygame.K_c] = True
        K[pygame.K_RIGHT] = False
        st["sp"] = False
        return K

    # jump state machine: holds a jump for full height, and re-presses (a real
    # edge) for a mid-air double jump when still stranded over a pit. Releasing
    # for a frame before re-pressing is what creates the edge.
    # stuck detection: if Ty is on the ground pressing right but not advancing,
    # a low ledge/block is in the way — hop to clear it (but not right at a
    # spike/pit, where the normal hazard jump already handles the timing).
    stuck = False
    if p.on_ground:
        prog = p.x - st.get("lastx", p.x - 5)
        st["lastx"] = p.x
        st["stuck"] = st.get("stuck", 0) + 1 if prog < 0.6 else 0
        stuck = st["stuck"] > 16 and not hazard_soon() and solid_below(front + 18)
    else:
        st["stuck"] = 0

    want_space = False
    if st.get("jt", 0) > 0:                     # still holding the current jump
        st["jt"] -= 1
        want_space = True
    else:
        pit = not solid_below(front + 18)       # gap just ahead on the ground
        stranded = (not p.on_ground and p.vy > 30 and p.jumps > 0
                    and not solid_below(front + 6))   # falling into a pit
        boss_hop = game.boss is not None and p.on_ground and i % 48 == 0
        ground_danger = p.on_ground and (pit or hazard_ahead() or enemy_block())
        if ground_danger or stranded or boss_hop or stuck:
            if not st.get("sp", False):         # need a release first for an edge
                st["jt"] = 20
                want_space = True
                st["stuck"] = 0
    K[pygame.K_SPACE] = want_space
    st["sp"] = want_space

    K[pygame.K_RIGHT] = game.boss is None
    return K


def run(selftest=False, demo=False):
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
        def play_mission(m):
            game.mission = m
            game.unlocked = max(game.unlocked, m)
            game.reset()
            game.state = STATE_PLAY
            st = {}
            for i in range(9000):
                keys = _bot_keys(game, st, i)
                game.update(1 / FPS, keys)
                game.draw(i / FPS)
                if game.state in (STATE_WIN, STATE_OVER):
                    break
            print("selftest M%d: state=%s frame=%d hp=%d boss=%s score=%d"
                  % (m, game.state, i, game.player.hp,
                     game.boss.NAME if game.boss else "-", game.score))
            return game.state

        results = [play_mission(m) for m in (1, 2, 3, 4, 5)]
        pygame.quit()
        if not all(r == STATE_WIN for r in results):
            print("SELFTEST FAILED:", results)
            raise SystemExit(1)
        print("selftest OK: all 5 missions win")
        return tuple(results)

    if demo:
        # watchable auto-playthrough: the bot walks Ty through all 5 missions
        def _pump():
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (
                        e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    return False
            return True

        for m in (1, 2, 3, 4, 5):
            game.mission = m
            game.unlocked = max(game.unlocked, m)
            game.reset()
            game.state = STATE_PLAY
            st = {}
            for i in range(9000):
                clock.tick(FPS)
                if not _pump():
                    pygame.quit()
                    return
                keys = _bot_keys(game, st, i)
                game.update(1 / FPS, keys)
                game.draw(pygame.time.get_ticks() / 1000.0)
                pygame.display.flip()
                if game.state in (STATE_WIN, STATE_OVER):
                    break
            for _ in range(int(FPS * 2.5)):   # linger on the result screen
                clock.tick(FPS)
                if not _pump():
                    pygame.quit()
                    return
                game.draw(pygame.time.get_ticks() / 1000.0)
                pygame.display.flip()
        pygame.quit()
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
    run(selftest="--selftest" in sys.argv, demo="--demo" in sys.argv)
