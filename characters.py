"""
2D cartoon character renderer for the TyGuy Biblical-moral films.

Characters are drawn from primitives (capsule limbs, rounded torso, ellipse
head) onto an RGBA layer so they can be positioned and composited over
animated backgrounds. TyGuy wears his blue hoodie with a white cross.
"""

import math
from PIL import Image, ImageDraw


# --------------------------------------------------------------------------- #
# low-level drawing
# --------------------------------------------------------------------------- #
def _capsule(draw, p0, p1, width, color):
    """A rounded thick line between two points."""
    draw.line([p0, p1], fill=color, width=width)
    r = width / 2
    for (x, y) in (p0, p1):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def _limb_end(origin, angle_deg, length):
    """End point of a limb at `angle_deg` measured clockwise from straight-down."""
    a = math.radians(angle_deg)
    return (origin[0] + math.sin(a) * length,
            origin[1] + math.cos(a) * length)


def _darken(c, f=0.78):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


# --------------------------------------------------------------------------- #
# palettes
# --------------------------------------------------------------------------- #
TYGUY = {
    "skin": (235, 190, 158),
    "hair": (40, 30, 28),
    "beard": (58, 44, 40),
    "shirt": (40, 95, 200),     # blue hoodie
    "shirt_dark": (30, 72, 158),
    "pants": (35, 40, 55),      # dark jeans
    "shoe": (235, 240, 248),
    "shoe_accent": (40, 95, 200),
    "cross": True,
    "beard_on": True,
}

MIA = {
    "skin": (244, 205, 178),
    "hair": (120, 70, 35),
    "beard": None,
    "shirt": (70, 175, 120),    # green top
    "shirt_dark": (52, 140, 96),
    "pants": (150, 95, 70),
    "shoe": (250, 250, 250),
    "shoe_accent": (70, 175, 120),
    "cross": False,
    "beard_on": False,
    "ponytail": True,
}

KID_A = {
    "skin": (236, 188, 150), "hair": (30, 26, 24), "beard": None,
    "shirt": (210, 70, 70), "shirt_dark": (172, 52, 52),
    "pants": (45, 50, 65), "shoe": (40, 40, 48), "shoe_accent": (210, 70, 70),
    "cross": False, "beard_on": False,
}

KID_B = {
    "skin": (210, 160, 120), "hair": (90, 60, 35), "beard": None,
    "shirt": (240, 180, 60), "shirt_dark": (205, 150, 45),
    "pants": (55, 60, 75), "shoe": (240, 240, 245), "shoe_accent": (240, 180, 60),
    "cross": False, "beard_on": False,
}


# --------------------------------------------------------------------------- #
# character
# --------------------------------------------------------------------------- #
def draw_person(base, cx, feet_y, height, pal, pose=None):
    """
    Draw a character onto RGBA image `base`.
      cx, feet_y : horizontal center and ground (feet) position
      height     : full character height in px
    pose keys (all optional):
      arm_l, arm_r : shoulder angles in degrees (0 = straight down, + = outward)
      elbow_l, elbow_r : extra bend at elbow
      walk : 0..1 phase for a gentle step
      lean : body tilt degrees
      mouth : 'smile' | 'sad' | 'neutral' | 'open'
      blink : 0..1
      brow  : 'normal' | 'sad' | 'happy'
    """
    pose = pose or {}
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    H = height
    head_r = H * 0.16
    # vertical anchors
    hip_y = feet_y - H * 0.46
    shoulder_y = feet_y - H * 0.78
    neck_y = feet_y - H * 0.82
    head_cy = feet_y - H * 0.90

    lean = pose.get("lean", 0)
    lean_dx = math.sin(math.radians(lean)) * H * 0.1

    limb_w = int(H * 0.085)
    skin = pal["skin"]

    # ---- legs ----
    walk = pose.get("walk", 0.0)
    step = math.sin(walk * math.tau) * H * 0.06
    leg_len = feet_y - hip_y
    hip_l = (cx - H * 0.07, hip_y)
    hip_r = (cx + H * 0.07, hip_y)
    foot_l = (cx - H * 0.07 + step, feet_y)
    foot_r = (cx + H * 0.07 - step, feet_y)
    knee_l = ((hip_l[0] + foot_l[0]) / 2 - abs(step) * 0.2, (hip_y + feet_y) / 2)
    knee_r = ((hip_r[0] + foot_r[0]) / 2 + abs(step) * 0.2, (hip_y + feet_y) / 2)
    for hip, knee, foot in ((hip_l, knee_l, foot_l), (hip_r, knee_r, foot_r)):
        _capsule(d, hip, knee, limb_w, pal["pants"])
        _capsule(d, knee, foot, limb_w, pal["pants"])
    # shoes
    for foot, lead in ((foot_l, -1), (foot_r, 1)):
        sw = H * 0.13
        sh = H * 0.05
        d.rounded_rectangle(
            [foot[0] - sw * 0.35, foot[1] - sh * 0.4,
             foot[0] + sw * 0.75 * lead if lead > 0 else foot[0] + sw * 0.35,
             foot[1] + sh],
            radius=sh, fill=pal["shoe"])
        d.ellipse([foot[0] - sw * 0.3, foot[1] - sh * 0.2,
                   foot[0] + sw * 0.3, foot[1] + sh * 0.6],
                  fill=pal["shoe_accent"])

    # ---- torso (hoodie) ----
    tw = H * 0.30
    top = shoulder_y - H * 0.02
    d.rounded_rectangle([cx - tw / 2 + lean_dx, top,
                         cx + tw / 2 + lean_dx, hip_y + H * 0.04],
                        radius=H * 0.07, fill=pal["shirt"])
    # hoodie center seam shading
    d.line([(cx + lean_dx, top + H * 0.04), (cx + lean_dx, hip_y)],
           fill=pal["shirt_dark"], width=max(2, int(H * 0.012)))
    # cross emblem
    if pal.get("cross"):
        ccx, ccy = cx + lean_dx, (top + hip_y) / 2
        cw, ch = H * 0.05, H * 0.12
        d.rectangle([ccx - cw / 2, ccy - ch / 2, ccx + cw / 2, ccy + ch / 2],
                    fill=(245, 248, 255))
        d.rectangle([ccx - ch * 0.28, ccy - ch * 0.12,
                     ccx + ch * 0.28, ccy + ch * 0.12], fill=(245, 248, 255))

    # ---- arms ----
    sh_l = (cx - tw / 2 + H * 0.02 + lean_dx, shoulder_y + H * 0.02)
    sh_r = (cx + tw / 2 - H * 0.02 + lean_dx, shoulder_y + H * 0.02)
    arm_l = pose.get("arm_l", 12)
    arm_r = pose.get("arm_r", 12)
    upper = H * 0.20
    fore = H * 0.20
    # left arm (mirror: angle goes left -> negative sin via -arm)
    el_l = _limb_end(sh_l, -arm_l, upper)
    hand_l = _limb_end(el_l, -arm_l + pose.get("elbow_l", 10), fore)
    el_r = _limb_end(sh_r, arm_r, upper)
    hand_r = _limb_end(el_r, arm_r - pose.get("elbow_r", 10), fore)
    for sh, el, hand in ((sh_l, el_l, hand_l), (sh_r, el_r, hand_r)):
        _capsule(d, sh, el, limb_w, pal["shirt"])
        _capsule(d, el, hand, int(limb_w * 0.9), pal["shirt"])
        # hand
        hr = H * 0.05
        d.ellipse([hand[0] - hr, hand[1] - hr, hand[0] + hr, hand[1] + hr],
                  fill=skin)

    # ---- neck + head ----
    head_cx = cx + lean_dx * 1.3
    d.rounded_rectangle([head_cx - H * 0.05, neck_y - H * 0.04,
                         head_cx + H * 0.05, neck_y + H * 0.05],
                        radius=H * 0.03, fill=skin)
    # ears
    er = head_r * 0.32
    for ex in (head_cx - head_r * 0.95, head_cx + head_r * 0.95):
        d.ellipse([ex - er, head_cy - er * 0.6, ex + er, head_cy + er * 0.9],
                  fill=skin)
    # head
    d.ellipse([head_cx - head_r, head_cy - head_r * 1.12,
               head_cx + head_r, head_cy + head_r * 1.05], fill=skin)

    # beard
    if pal.get("beard_on"):
        d.ellipse([head_cx - head_r * 0.92, head_cy - head_r * 0.15,
                   head_cx + head_r * 0.92, head_cy + head_r * 1.08],
                  fill=pal["beard"])
        # carve mouth area back to skin
        d.ellipse([head_cx - head_r * 0.55, head_cy + head_r * 0.05,
                   head_cx + head_r * 0.55, head_cy + head_r * 0.72],
                  fill=skin)

    # hair
    hair = pal["hair"]
    d.ellipse([head_cx - head_r * 1.04, head_cy - head_r * 1.28,
               head_cx + head_r * 1.04, head_cy + head_r * 0.35], fill=hair)
    # face opening (skin) under the hairline
    d.ellipse([head_cx - head_r * 0.92, head_cy - head_r * 0.55,
               head_cx + head_r * 0.92, head_cy + head_r * 1.0], fill=skin)
    if pal.get("beard_on"):
        # re-apply beard lower half over the face opening sides
        d.pieslice([head_cx - head_r * 0.92, head_cy - head_r * 0.55,
                    head_cx + head_r * 0.92, head_cy + head_r * 1.08],
                   start=20, end=160, fill=pal["beard"])
        d.ellipse([head_cx - head_r * 0.5, head_cy + head_r * 0.1,
                   head_cx + head_r * 0.5, head_cy + head_r * 0.7], fill=skin)
    # front hair fringe
    d.chord([head_cx - head_r * 1.02, head_cy - head_r * 1.26,
             head_cx + head_r * 1.02, head_cy + head_r * 0.1],
            start=180, end=360, fill=hair)

    # ponytail
    if pal.get("ponytail"):
        d.ellipse([head_cx + head_r * 0.7, head_cy - head_r * 0.3,
                   head_cx + head_r * 1.5, head_cy + head_r * 0.9], fill=hair)

    # ---- face ----
    eye_y = head_cy + head_r * 0.05
    eye_dx = head_r * 0.42
    blink = pose.get("blink", 0)
    er2 = head_r * 0.16
    for ex in (head_cx - eye_dx, head_cx + eye_dx):
        if blink > 0.5:
            d.line([(ex - er2, eye_y), (ex + er2, eye_y)],
                   fill=(40, 30, 30), width=max(2, int(head_r * 0.07)))
        else:
            d.ellipse([ex - er2, eye_y - er2 * 1.2, ex + er2, eye_y + er2 * 1.2],
                      fill=(250, 250, 250))
            d.ellipse([ex - er2 * 0.55, eye_y - er2 * 0.5,
                       ex + er2 * 0.55, eye_y + er2 * 0.7], fill=(45, 35, 32))
    # brows
    brow = pose.get("brow", "normal")
    bw = max(2, int(head_r * 0.09))
    by = eye_y - head_r * 0.32
    for sgn, ex in ((-1, head_cx - eye_dx), (1, head_cx + eye_dx)):
        if brow == "sad":
            d.line([(ex - er2, by + head_r * 0.08 * (1 if sgn < 0 else 0)),
                    (ex + er2, by - head_r * 0.05 * (1 if sgn < 0 else -1))],
                   fill=pal["hair"], width=bw)
        elif brow == "happy":
            d.arc([ex - er2 * 1.2, by - head_r * 0.05,
                   ex + er2 * 1.2, by + head_r * 0.25],
                  start=200, end=340, fill=pal["hair"], width=bw)
        else:
            d.line([(ex - er2, by), (ex + er2, by)], fill=pal["hair"], width=bw)

    # mouth
    mouth = pose.get("mouth", "smile")
    my = head_cy + head_r * 0.5
    mw = head_r * 0.5
    mc = (120, 50, 50)
    if mouth == "smile":
        d.arc([head_cx - mw, my - mw * 0.7, head_cx + mw, my + mw * 0.8],
              start=20, end=160, fill=mc, width=max(2, int(head_r * 0.1)))
    elif mouth == "sad":
        d.arc([head_cx - mw, my + mw * 0.2, head_cx + mw, my + mw * 1.2],
              start=200, end=340, fill=mc, width=max(2, int(head_r * 0.1)))
    elif mouth == "open":
        d.ellipse([head_cx - mw * 0.55, my - mw * 0.2,
                   head_cx + mw * 0.55, my + mw * 0.8], fill=(110, 45, 45))
    else:
        d.line([(head_cx - mw * 0.7, my), (head_cx + mw * 0.7, my)],
               fill=mc, width=max(2, int(head_r * 0.08)))

    base.alpha_composite(layer)
    return base
