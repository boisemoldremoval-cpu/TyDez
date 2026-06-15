"""Render a cute cartoon lighthouse character at sunset (PIL only, no AI credits)."""
import math
from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 800
img = Image.new("RGB", (W, H))
px = img.load()

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# --- Sky: sunset vertical gradient ---
top = (38, 52, 110)       # deep dusk blue
mid = (240, 138, 96)      # warm orange
horizon = (255, 214, 150) # peachy glow
for y in range(H):
    t = y / H
    if t < 0.55:
        c = lerp(top, mid, t / 0.55)
    else:
        c = lerp(mid, horizon, (t - 0.55) / 0.45)
    for x in range(W):
        px[x, y] = c

draw = ImageDraw.Draw(img, "RGBA")

# --- Sun glow ---
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
sx, sy = 850, 430
for r, a in [(220, 40), (160, 60), (110, 90), (70, 150), (40, 220)]:
    gd.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 240, 200, a))
glow = glow.filter(ImageFilter.GaussianBlur(18))
img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))
draw = ImageDraw.Draw(img, "RGBA")

# --- Clouds ---
def cloud(cx, cy, s, alpha=200):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for dx, dy, r in [(-60, 10, 38), (-20, -8, 48), (30, -2, 44), (70, 14, 34), (10, 22, 40)]:
        ld.ellipse([cx + dx*s - r*s, cy + dy*s - r*s, cx + dx*s + r*s, cy + dy*s + r*s],
                   fill=(255, 240, 235, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(4))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))

cloud(250, 170, 1.0, 180)
cloud(980, 150, 0.8, 150)
draw = ImageDraw.Draw(img, "RGBA")

# --- Sea ---
sea_top = 560
sea_hi = (255, 198, 150)
sea_lo = (60, 96, 150)
for y in range(sea_top, H):
    t = (y - sea_top) / (H - sea_top)
    c = lerp(sea_hi, sea_lo, t)
    draw.line([(0, y), (W, y)], fill=c)
# sun reflection + wave glints
for i in range(18):
    y = sea_top + 12 + i * 12
    w = 120 - i * 4
    draw.line([(sx - w//2, y), (sx + w//2, y)], fill=(255, 235, 190, 120), width=3)

# --- Cliff ---
draw.ellipse([280, 520, 720, 760], fill=(70, 96, 70))
draw.ellipse([300, 540, 700, 740], fill=(96, 128, 86))
draw.ellipse([330, 700, 670, 820], fill=(58, 74, 58))

# --- Lighthouse tower (tapered) as its own layer for shading ---
cx = 500
base_y, top_y = 600, 250
base_w, top_w = 150, 96
tower = [
    (cx - base_w/2, base_y), (cx + base_w/2, base_y),
    (cx + top_w/2, top_y), (cx - top_w/2, top_y),
]
tlayer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(tlayer)
td.polygon(tower, fill=(248, 248, 250, 255))
# red stripes
stripes = [(250, 300), (360, 410), (470, 520)]
for y0, y1 in stripes:
    tt0 = (y0 - top_y) / (base_y - top_y)
    tt1 = (y1 - top_y) / (base_y - top_y)
    w0 = top_w + (base_w - top_w) * tt0
    w1 = top_w + (base_w - top_w) * tt1
    td.polygon([(cx - w0/2, y0), (cx + w0/2, y0), (cx + w1/2, y1), (cx - w1/2, y1)],
               fill=(214, 64, 58, 255))
# cylinder shading: darken left & right edges
mask = tlayer.split()[3]
shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shade)
for x in range(cx - base_w//2 - 4, cx + base_w//2 + 4):
    d = abs(x - (cx - 18)) / (base_w * 0.62)
    a = int(max(0, min(150, (d - 0.25) * 200)))
    sd.line([(x, top_y), (x, base_y)], fill=(20, 28, 60, a))
shade.putalpha(Image.composite(shade.split()[3], Image.new("L", (W, H), 0), mask))
tlayer = Image.alpha_composite(tlayer, shade)
# warm sun side highlight
hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(hl)
for x in range(cx, cx + base_w//2):
    d = (x - cx) / (base_w * 0.5)
    a = int(max(0, min(90, d * 90)))
    hd.line([(x, top_y), (x, base_y)], fill=(255, 210, 150, a))
hl.putalpha(Image.composite(hl.split()[3], Image.new("L", (W, H), 0), mask))
tlayer = Image.alpha_composite(tlayer, hl)
img.paste(Image.alpha_composite(img.convert("RGBA"), tlayer).convert("RGB"), (0, 0))
draw = ImageDraw.Draw(img, "RGBA")

# --- Gallery platform ---
draw.rectangle([cx - 70, top_y - 16, cx + 70, top_y], fill=(90, 96, 110))
draw.rectangle([cx - 74, top_y - 22, cx + 74, top_y - 16], fill=(120, 128, 142))

# --- Lamp room + glow ---
lr_top, lr_bot = top_y - 78, top_y - 22
draw.rectangle([cx - 40, lr_top, cx + 40, lr_bot], fill=(60, 66, 84))
lampglow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
lg = ImageDraw.Draw(lampglow)
lg.ellipse([cx - 70, lr_top - 30, cx + 70, lr_bot + 30], fill=(255, 240, 170, 180))
lg.rectangle([cx - 30, lr_top + 8, cx + 30, lr_bot - 6], fill=(255, 248, 205, 255))
lampglow = lampglow.filter(ImageFilter.GaussianBlur(6))
img.paste(Image.alpha_composite(img.convert("RGBA"), lampglow).convert("RGB"), (0, 0))
draw = ImageDraw.Draw(img, "RGBA")

# --- Light beams ---
beams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(beams)
ly = (lr_top + lr_bot) // 2
bd.polygon([(cx, ly), (W, ly - 120), (W, ly + 40)], fill=(255, 244, 190, 70))
bd.polygon([(cx, ly), (cx - 360, ly - 150), (cx - 360, ly - 30)], fill=(255, 244, 190, 55))
beams = beams.filter(ImageFilter.GaussianBlur(8))
img.paste(Image.alpha_composite(img.convert("RGBA"), beams).convert("RGB"), (0, 0))
draw = ImageDraw.Draw(img, "RGBA")

# --- Roof ---
draw.polygon([(cx - 46, lr_top), (cx + 46, lr_top), (cx, lr_top - 46)], fill=(196, 54, 50))
draw.ellipse([cx - 6, lr_top - 60, cx + 6, lr_top - 48], fill=(255, 236, 150))

# --- Character face on the tower ---
ey = 360
draw.ellipse([cx - 46, ey - 30, cx - 6, ey + 18], fill=(255, 255, 255))
draw.ellipse([cx + 6, ey - 30, cx + 46, ey + 18], fill=(255, 255, 255))
draw.ellipse([cx - 34, ey - 18, cx - 16, ey + 6], fill=(40, 48, 70))
draw.ellipse([cx + 18, ey - 18, cx + 36, ey + 6], fill=(40, 48, 70))
draw.ellipse([cx - 30, ey - 14, cx - 24, ey - 8], fill=(255, 255, 255))
draw.ellipse([cx + 22, ey - 14, cx + 28, ey - 8], fill=(255, 255, 255))
# rosy cheeks
draw.ellipse([cx - 52, ey + 14, cx - 28, ey + 34], fill=(255, 150, 130, 120))
draw.ellipse([cx + 28, ey + 14, cx + 52, ey + 34], fill=(255, 150, 130, 120))
# smile
draw.arc([cx - 26, ey + 18, cx + 26, ey + 54], start=20, end=160, fill=(70, 40, 40), width=5)

img.save("lighthouse.png")
print("saved lighthouse.png", img.size)
