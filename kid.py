"""
Cel-shaded, bold-outlined 2D kids for the TyGuy story (Mia + classmates).

Drawn from primitives onto an RGBA layer, then given a clean outer outline by
dilating the silhouette alpha (MaxFilter) -- this reads as a comic/cel style
that sits comfortably next to the polished TyGuy cutout artwork.
"""

import math
from PIL import Image, ImageDraw, ImageFilter


def _c(r, g, b):
    return (r, g, b)


MIA = {
    "skin": _c(245, 205, 175), "skin_sh": _c(225, 178, 150),
    "hair": _c(120, 72, 38), "hair_sh": _c(96, 56, 28),
    "shirt": _c(235, 95, 120), "shirt_sh": _c(200, 70, 96),   # pink top
    "pants": _c(95, 110, 175), "pants_sh": _c(74, 88, 148),
    "shoe": _c(250, 250, 252), "ponytail": True,
}
KID1 = {
    "skin": _c(232, 185, 148), "skin_sh": _c(208, 162, 128),
    "hair": _c(40, 32, 28), "hair_sh": _c(26, 20, 18),
    "shirt": _c(95, 180, 120), "shirt_sh": _c(74, 150, 96),
    "pants": _c(70, 78, 96), "pants_sh": _c(54, 60, 76),
    "shoe": _c(60, 60, 70), "ponytail": False,
}
KID_TYGUY = {   # kid version of the TyGuy character
    "skin": _c(228, 178, 142), "skin_sh": _c(204, 156, 122),
    "hair": _c(46, 33, 27), "hair_sh": _c(30, 22, 16),
    "shirt": _c(33, 92, 208), "shirt_sh": _c(24, 66, 158),   # royal-blue hoodie
    "pants": _c(28, 30, 38), "pants_sh": _c(20, 22, 28),
    "shoe": _c(33, 92, 208), "ponytail": False,
    "emblem_T": True, "spiky": True,
}
SAM = {   # original hero kid
    "skin": _c(238, 192, 156), "skin_sh": _c(214, 168, 132),
    "hair": _c(58, 40, 26), "hair_sh": _c(40, 26, 16),
    "shirt": _c(70, 150, 210), "shirt_sh": _c(52, 122, 178),   # sky-blue tee
    "pants": _c(70, 80, 100), "pants_sh": _c(54, 62, 80),
    "shoe": _c(245, 230, 90), "ponytail": False,
}
KID2 = {
    "skin": _c(210, 160, 120), "skin_sh": _c(188, 140, 104),
    "hair": _c(70, 50, 30), "hair_sh": _c(52, 36, 20),
    "shirt": _c(240, 190, 70), "shirt_sh": _c(208, 160, 52),
    "pants": _c(80, 70, 100), "pants_sh": _c(62, 54, 80),
    "shoe": _c(240, 240, 245), "ponytail": False,
}


def _capsule(d, p0, p1, w, col):
    d.line([p0, p1], fill=col, width=w)
    r = w / 2
    for (x, y) in (p0, p1):
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def _le(o, ang, L):
    a = math.radians(ang)
    return (o[0] + math.sin(a) * L, o[1] + math.cos(a) * L)


def draw_kid(base, cx, feet_y, H, pal, pose=None):
    pose = pose or {}
    sz = base.size
    body = Image.new("RGBA", sz, (0, 0, 0, 0))
    d = ImageDraw.Draw(body)

    head_r = H * 0.21
    head_cy = feet_y - H * 0.85
    sh_y = feet_y - H * 0.62
    hip_y = feet_y - H * 0.40
    limb = int(H * 0.11)

    walk = pose.get("walk", 0.0)
    step = math.sin(walk * math.tau) * H * 0.06
    lean = pose.get("lean", 0)
    ldx = math.sin(math.radians(lean)) * H * 0.06

    # legs
    for sgn, st in ((-1, step), (1, -step)):
        hip = (cx + sgn * H * 0.08, hip_y)
        foot = (cx + sgn * H * 0.08 + st, feet_y)
        knee = ((hip[0] + foot[0]) / 2, (hip_y + feet_y) / 2)
        _capsule(d, hip, knee, limb, pal["pants"])
        _capsule(d, knee, foot, limb, pal["pants_sh"])
        # shoe
        d.ellipse([foot[0] - H * 0.09, foot[1] - H * 0.04,
                   foot[0] + H * 0.11, foot[1] + H * 0.03], fill=pal["shoe"])

    # torso
    tw = H * 0.30
    d.rounded_rectangle([cx - tw / 2 + ldx, sh_y, cx + tw / 2 + ldx, hip_y + H * 0.03],
                        radius=H * 0.08, fill=pal["shirt"])
    # cel shade lower torso
    d.rounded_rectangle([cx - tw / 2 + ldx, (sh_y + hip_y) / 2,
                         cx + tw / 2 + ldx, hip_y + H * 0.03],
                        radius=H * 0.06, fill=pal["shirt_sh"])

    # arms
    shl = (cx - tw / 2 + ldx + H * 0.02, sh_y + H * 0.03)
    shr = (cx + tw / 2 + ldx - H * 0.02, sh_y + H * 0.03)
    al = pose.get("arm_l", 14)
    ar = pose.get("arm_r", 14)
    for sh, ang, sgn in ((shl, -al, -1), (shr, ar, 1)):
        elb = _le(sh, ang, H * 0.20)
        hand = _le(elb, ang + sgn * pose.get("elbow", 8), H * 0.18)
        _capsule(d, sh, elb, int(limb * 0.92), pal["shirt"])
        _capsule(d, elb, hand, int(limb * 0.82), pal["skin"])
        d.ellipse([hand[0] - H * 0.05, hand[1] - H * 0.05,
                   hand[0] + H * 0.05, hand[1] + H * 0.05], fill=pal["skin"])

    # neck + head
    _capsule(d, (cx + ldx, sh_y - H * 0.02), (cx + ldx, sh_y + H * 0.04),
             int(H * 0.09), pal["skin"])
    hcx = cx + ldx * 1.4
    # back hair / ponytail behind head
    if pal.get("ponytail"):
        d.ellipse([hcx + head_r * 0.4, head_cy - head_r * 0.2,
                   hcx + head_r * 1.5, head_cy + head_r * 1.1], fill=pal["hair_sh"])
    # ears
    for sgn in (-1, 1):
        d.ellipse([hcx + sgn * head_r * 0.9 - head_r * 0.18, head_cy - head_r * 0.1,
                   hcx + sgn * head_r * 0.9 + head_r * 0.22, head_cy + head_r * 0.35],
                  fill=pal["skin"])
    # head
    d.ellipse([hcx - head_r, head_cy - head_r * 1.05,
               hcx + head_r, head_cy + head_r * 1.05], fill=pal["skin"])
    # hair cap
    d.chord([hcx - head_r * 1.04, head_cy - head_r * 1.18,
             hcx + head_r * 1.04, head_cy + head_r * 0.7],
            start=180, end=360, fill=pal["hair"])
    d.ellipse([hcx - head_r * 1.04, head_cy - head_r * 1.2,
               hcx + head_r * 1.04, head_cy - head_r * 0.1], fill=pal["hair"])

    # ---- outline via alpha dilation ----
    ow = max(3, int(H * 0.02))
    alpha = body.split()[3]
    dil = alpha.filter(ImageFilter.MaxFilter(ow * 2 + 1))
    sil = Image.new("RGBA", sz, (26, 22, 30, 0))
    sil.putalpha(dil)
    base.alpha_composite(sil)
    base.alpha_composite(body)

    # ---- face (on top, no outline) ----
    fd = ImageDraw.Draw(base)
    eye_y = head_cy + head_r * 0.08
    eye_dx = head_r * 0.42
    blink = pose.get("blink", 0)
    er = head_r * 0.20
    look = pose.get("look", 0) * head_r * 0.12   # eye gaze offset
    ld = math.radians  # noqa
    for sgn in (-1, 1):
        ex = hcx + sgn * eye_dx
        if blink:
            fd.line([(ex - er, eye_y), (ex + er, eye_y)],
                    fill=(40, 30, 30), width=max(2, int(head_r * 0.09)))
        else:
            fd.ellipse([ex - er, eye_y - er * 1.15, ex + er, eye_y + er * 1.15],
                       fill=(255, 255, 255), outline=(40, 30, 30), width=2)
            fd.ellipse([ex - er * 0.55 + look, eye_y - er * 0.4,
                        ex + er * 0.55 + look, eye_y + er * 0.7], fill=(45, 32, 30))
            fd.ellipse([ex - er * 0.4 + look, eye_y - er * 0.3,
                        ex - er * 0.05 + look, eye_y + er * 0.05], fill=(255, 255, 255))
    # brows
    brow = pose.get("brow", "normal")
    bw = max(2, int(head_r * 0.10))
    by = eye_y - head_r * 0.42
    for sgn in (-1, 1):
        ex = hcx + sgn * eye_dx
        if brow == "sad":
            y_in, y_out = by + head_r * 0.12, by - head_r * 0.04
            pts = [(ex - sgn * er, y_out), (ex + sgn * er, y_in)]
        elif brow == "happy":
            pts = None
            fd.arc([ex - er * 1.2, by - head_r * 0.04, ex + er * 1.2, by + head_r * 0.3],
                   start=200, end=340, fill=pal["hair_sh"], width=bw)
        else:
            pts = [(ex - er, by), (ex + er, by)]
        if brow != "happy":
            fd.line(pts, fill=pal["hair_sh"], width=bw)

    # mouth
    mouth = pose.get("mouth", "smile")
    my = head_cy + head_r * 0.55
    mw = head_r * 0.5
    mc = (150, 70, 70)
    if mouth == "smile":
        fd.arc([hcx - mw, my - mw * 0.7, hcx + mw, my + mw * 0.8],
               start=15, end=165, fill=mc, width=max(2, int(head_r * 0.12)))
    elif mouth == "bigsmile":
        fd.chord([hcx - mw, my - mw * 0.5, hcx + mw, my + mw * 1.1],
                 start=10, end=170, fill=(150, 70, 70))
        fd.chord([hcx - mw * 0.8, my + mw * 0.2, hcx + mw * 0.8, my + mw * 0.9],
                 start=0, end=180, fill=(255, 255, 255))
    elif mouth == "sad":
        fd.arc([hcx - mw * 0.8, my + mw * 0.25, hcx + mw * 0.8, my + mw * 1.25],
               start=200, end=340, fill=mc, width=max(2, int(head_r * 0.12)))
    elif mouth == "open":
        fd.ellipse([hcx - mw * 0.5, my - mw * 0.2, hcx + mw * 0.5, my + mw * 0.8],
                   fill=(150, 70, 70))
    else:
        fd.line([(hcx - mw * 0.6, my), (hcx + mw * 0.6, my)], fill=mc,
                width=max(2, int(head_r * 0.09)))

    # blush
    if pose.get("blush"):
        for sgn in (-1, 1):
            fd.ellipse([hcx + sgn * head_r * 0.55 - head_r * 0.18, my - head_r * 0.18,
                        hcx + sgn * head_r * 0.55 + head_r * 0.18, my - head_r * 0.02],
                       fill=(255, 150, 150, 130))
    return base
