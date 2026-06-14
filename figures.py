"""Cel-shaded Bible-times figures (robed people + donkey) for the parable."""
import math
from PIL import Image, ImageDraw, ImageFilter


def _cap(d, p0, p1, w, c):
    d.line([p0, p1], fill=c, width=int(w))
    r = w / 2
    for x, y in (p0, p1):
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)


def _le(o, ang, L):
    a = math.radians(ang)
    return (o[0] + math.sin(a) * L, o[1] + math.cos(a) * L)


def _outline(base, body, ow, col=(34, 26, 22)):
    sil = Image.new("RGBA", base.size, (*col, 0))
    sil.putalpha(body.split()[3].filter(ImageFilter.MaxFilter(ow * 2 + 1)))
    base.alpha_composite(sil)
    base.alpha_composite(body)


def _c(r, g, b): return (r, g, b)

TRAVELER = {"robe": _c(206, 178, 120), "robe_sh": _c(176, 150, 96), "sash": _c(150, 110, 70),
            "cloth": _c(214, 196, 150), "band": _c(150, 110, 70), "skin": _c(226, 178, 140),
            "hair": _c(70, 50, 34), "beard": _c(86, 62, 42)}
PRIEST = {"robe": _c(238, 234, 222), "robe_sh": _c(214, 208, 190), "sash": _c(214, 178, 60),
          "cloth": _c(244, 240, 228), "band": _c(214, 178, 60), "skin": _c(232, 188, 150),
          "hair": _c(150, 150, 150), "beard": _c(180, 180, 180)}
LEVITE = {"robe": _c(80, 110, 175), "robe_sh": _c(60, 86, 142), "sash": _c(44, 64, 110),
          "cloth": _c(150, 170, 210), "band": _c(44, 64, 110), "skin": _c(220, 172, 132),
          "hair": _c(48, 38, 30), "beard": _c(60, 46, 34)}
SAMARITAN = {"robe": _c(196, 96, 70), "robe_sh": _c(166, 76, 54), "sash": _c(110, 70, 50),
             "cloth": _c(220, 170, 110), "band": _c(110, 70, 50), "skin": _c(216, 168, 128),
             "hair": _c(60, 44, 32), "beard": _c(74, 54, 38)}
INNKEEPER = {"robe": _c(110, 150, 110), "robe_sh": _c(86, 122, 88), "sash": _c(200, 190, 170),
             "cloth": _c(180, 170, 150), "band": _c(120, 100, 80), "skin": _c(228, 184, 146),
             "hair": _c(54, 42, 32), "beard": _c(66, 50, 38)}


def draw_robed(base, cx, feet_y, H, pal, pose=None):
    pose = pose or {}
    sz = base.size
    body = Image.new("RGBA", sz, (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    skin = pal["skin"]; robe = pal["robe"]; robe_sh = pal["robe_sh"]; cloth = pal["cloth"]
    hr = H * 0.13
    bobv = pose.get("bob", 0.0)
    feet_y += bobv
    hcy = feet_y - H * 0.86; shy = feet_y - H * 0.72
    lean = pose.get("lean", 0); ldx = math.sin(math.radians(lean)) * H * 0.10
    # robe
    d.polygon([(cx - H * 0.12 + ldx, shy), (cx + H * 0.12 + ldx, shy),
               (cx + H * 0.22, feet_y), (cx - H * 0.22, feet_y)], fill=robe)
    d.polygon([(cx - H * 0.17, (shy + feet_y) / 2), (cx + H * 0.17, (shy + feet_y) / 2),
               (cx + H * 0.22, feet_y), (cx - H * 0.22, feet_y)], fill=robe_sh)
    d.line([(cx - H * 0.13 + ldx, shy + H * 0.16), (cx + H * 0.13 + ldx, shy + H * 0.18)],
           fill=pal["sash"], width=int(H * 0.05))
    # sandals
    for s in (-1, 1):
        d.ellipse([cx + s * H * 0.08 - H * 0.06, feet_y - H * 0.03,
                   cx + s * H * 0.08 + H * 0.06, feet_y + H * 0.02], fill=(120, 90, 60))
    # arms
    shl = (cx - H * 0.11 + ldx, shy + H * 0.03); shr = (cx + H * 0.11 + ldx, shy + H * 0.03)
    al = pose.get("arm_l", 16); ar = pose.get("arm_r", 16)
    for sh, ang, sgn in ((shl, -al, -1), (shr, ar, 1)):
        elb = _le(sh, ang, H * 0.18)
        hand = _le(elb, ang + sgn * pose.get("elbow", 10), H * 0.16)
        _cap(d, sh, elb, H * 0.10, robe)
        _cap(d, elb, hand, H * 0.07, skin)
        d.ellipse([hand[0] - H * 0.045, hand[1] - H * 0.045,
                   hand[0] + H * 0.045, hand[1] + H * 0.045], fill=skin)
    # neck + head
    hx = cx + ldx * 1.2
    _cap(d, (hx, shy - H * 0.02), (hx, shy + H * 0.03), H * 0.06, skin)
    d.ellipse([hx - hr, hcy - hr, hx + hr, hcy + hr], fill=skin)
    if pal.get("beard", None):
        d.ellipse([hx - hr * 0.92, hcy + hr * 0.05, hx + hr * 0.92, hcy + hr * 1.55], fill=pal["beard"])
        d.ellipse([hx - hr * 0.55, hcy - hr * 0.05, hx + hr * 0.55, hcy + hr * 0.62], fill=skin)
    # head cloth: top drape + side drapes
    d.chord([hx - hr * 1.18, hcy - hr * 1.35, hx + hr * 1.18, hcy + hr * 0.35], 150, 390, fill=cloth)
    d.polygon([(hx - hr * 1.12, hcy - hr * 0.3), (hx - hr * 0.6, hcy - hr * 0.3),
               (hx - hr * 0.7, hcy + hr * 1.1), (hx - hr * 1.15, hcy + hr * 1.0)], fill=cloth)
    d.polygon([(hx + hr * 1.12, hcy - hr * 0.3), (hx + hr * 0.6, hcy - hr * 0.3),
               (hx + hr * 0.7, hcy + hr * 1.1), (hx + hr * 1.15, hcy + hr * 1.0)], fill=cloth)
    d.line([(hx - hr * 1.0, hcy - hr * 0.55), (hx + hr * 1.0, hcy - hr * 0.55)],
           fill=pal.get("band", robe_sh), width=int(H * 0.022))
    ow = max(3, int(H * 0.015))
    _outline(base, body, ow)
    # face
    fd = ImageDraw.Draw(base); ey = hcy + hr * 0.02
    blink = pose.get("blink", 0)
    for s in (-1, 1):
        ex = hx + s * hr * 0.42
        if blink:
            fd.line([(ex - hr * 0.16, ey), (ex + hr * 0.16, ey)], fill=(40, 30, 28), width=3)
        else:
            fd.ellipse([ex - hr * 0.16, ey - hr * 0.17, ex + hr * 0.16, ey + hr * 0.17],
                       fill=(255, 255, 255), outline=(40, 30, 28), width=2)
            fd.ellipse([ex - hr * 0.07, ey - hr * 0.04, ex + hr * 0.07, ey + hr * 0.12], fill=(45, 32, 28))
    brow = pose.get("brow", "normal"); bw = max(2, int(hr * 0.12)); by = ey - hr * 0.34
    for s in (-1, 1):
        ex = hx + s * hr * 0.42
        if brow == "sad":
            fd.line([(ex - s * hr * 0.16, by - hr * 0.04), (ex + s * hr * 0.16, by + hr * 0.08)],
                    fill=pal["hair"], width=bw)
        elif brow == "kind":
            fd.arc([ex - hr * 0.2, by - hr * 0.02, ex + hr * 0.2, by + hr * 0.3], 200, 340,
                   fill=pal["hair"], width=bw)
        else:
            fd.line([(ex - hr * 0.16, by), (ex + hr * 0.16, by)], fill=pal["hair"], width=bw)
    mo = pose.get("mouth", "neutral"); my = hcy + hr * 0.5
    if mo == "smile":
        fd.arc([hx - hr * 0.28, my - hr * 0.25, hx + hr * 0.28, my + hr * 0.35], 20, 160,
               fill=(150, 80, 70), width=3)
    elif mo == "sad":
        fd.arc([hx - hr * 0.28, my + hr * 0.05, hx + hr * 0.28, my + hr * 0.6], 200, 340,
               fill=(150, 80, 70), width=3)
    return base


def draw_hurt(base, cx, ground_y, H, pal):
    """Traveler slumped/sitting at the roadside, hurt."""
    sz = base.size
    body = Image.new("RGBA", sz, (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    skin = pal["skin"]; robe = pal["robe"]; robe_sh = pal["robe_sh"]; cloth = pal["cloth"]
    hr = H * 0.13
    # body lump on ground
    d.ellipse([cx - H * 0.26, ground_y - H * 0.22, cx + H * 0.30, ground_y + H * 0.04], fill=robe)
    d.ellipse([cx - H * 0.10, ground_y - H * 0.10, cx + H * 0.30, ground_y + H * 0.04], fill=robe_sh)
    # legs out
    _cap(d, (cx + H * 0.05, ground_y - H * 0.06), (cx + H * 0.34, ground_y - H * 0.02), H * 0.09, robe)
    d.ellipse([cx + H * 0.32, ground_y - H * 0.06, cx + H * 0.42, ground_y + H * 0.0], fill=(120, 90, 60))
    # an arm
    _cap(d, (cx - H * 0.08, ground_y - H * 0.16), (cx + H * 0.06, ground_y - H * 0.02), H * 0.07, skin)
    # head leaning
    hx = cx - H * 0.14; hcy = ground_y - H * 0.30
    d.ellipse([hx - hr, hcy - hr, hx + hr, hcy + hr], fill=skin)
    d.ellipse([hx - hr * 0.9, hcy + hr * 0.05, hx + hr * 0.9, hcy + hr * 1.4], fill=pal["beard"])
    d.ellipse([hx - hr * 0.5, hcy - hr * 0.05, hx + hr * 0.5, hcy + hr * 0.55], fill=skin)
    d.chord([hx - hr * 1.15, hcy - hr * 1.3, hx + hr * 1.15, hcy + hr * 0.3], 150, 390, fill=cloth)
    _outline(base, body, max(3, int(H * 0.015)))
    fd = ImageDraw.Draw(base); ey = hcy + hr * 0.02
    for s in (-1, 1):
        ex = hx + s * hr * 0.4
        fd.line([(ex - hr * 0.14, ey), (ex + hr * 0.14, ey)], fill=(40, 30, 28), width=3)  # closed eyes
    fd.line([(hx - hr * 0.34, ey - hr * 0.3), (hx, ey - hr * 0.18)], fill=pal["hair"], width=3)
    fd.arc([hx - hr * 0.25, hcy + hr * 0.55, hx + hr * 0.25, hcy + hr * 1.0], 200, 340,
           fill=(150, 80, 70), width=3)
    return base


def draw_donkey(base, cx, feet_y, H, pal_load=False):
    sz = base.size
    body = Image.new("RGBA", sz, (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    gray = (150, 142, 138); gray_sh = (122, 115, 112); mane = (90, 84, 80)
    bw, bh = H * 0.5, H * 0.30
    bx, by = cx, feet_y - H * 0.30
    d.ellipse([bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2], fill=gray)
    d.ellipse([bx - bw / 2, by, bx + bw / 2, by + bh / 2], fill=gray_sh)
    # legs
    for lx in (-0.32, -0.12, 0.12, 0.32):
        x = bx + bw * lx
        _cap(d, (x, by + bh * 0.2), (x, feet_y), H * 0.07, gray)
        d.ellipse([x - H * 0.04, feet_y - H * 0.03, x + H * 0.04, feet_y + H * 0.02], fill=(60, 54, 50))
    # neck + head
    neck0 = (bx - bw * 0.42, by - bh * 0.1); head = (bx - bw * 0.66, by - bh * 0.7)
    _cap(d, neck0, head, H * 0.12, gray)
    d.ellipse([head[0] - H * 0.12, head[1] - H * 0.10, head[0] + H * 0.10, head[1] + H * 0.14], fill=gray)
    d.ellipse([head[0] - H * 0.11, head[1] + H * 0.0, head[0] - H * 0.02, head[1] + H * 0.16], fill=gray_sh)  # muzzle
    # ears
    for ex in (-0.04, 0.04):
        d.polygon([(head[0] + ex * H * 0.3, head[1] - H * 0.08),
                   (head[0] + ex * H * 0.3 - H * 0.03, head[1] - H * 0.22),
                   (head[0] + ex * H * 0.3 + H * 0.04, head[1] - H * 0.2)], fill=gray)
    # mane + tail
    _cap(d, (bx - bw * 0.4, by - bh * 0.4), (bx - bw * 0.2, by - bh * 0.55), H * 0.04, mane)
    _cap(d, (bx + bw * 0.5, by), (bx + bw * 0.62, by + bh * 0.5), H * 0.03, mane)
    _outline(base, body, max(3, int(H * 0.014)))
    fd = ImageDraw.Draw(base)
    fd.ellipse([head[0] - H * 0.02, head[1] - H * 0.02, head[0] + H * 0.02, head[1] + H * 0.02], fill=(40, 30, 28))
    return base
