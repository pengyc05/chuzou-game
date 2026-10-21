"""Build per-scene motion masks for the card prototype.

mask RGB: R = water (ripple + sparkle), G = plants (wind sway), B = sky (cloud drift / dusk & night tint).
Run from repo root: python3 game/xiangye-cards/tools/make_masks.py
"""
import json, base64, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "assets" / "source" / "scenes"
OUT = ROOT / "assets" / "processed" / "scenes"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1024, 572

# water areas drawn by eye in 1024x572 image coordinates; colour tests refine them
WATER = {
    "cunkou": [[(540, 405), (600, 398), (665, 410), (655, 448), (560, 442)], [(640, 425), (705, 405), (770, 425), (815, 480), (800, 572), (690, 572), (705, 505), (655, 455)]],
    "tiangeng": [[(0, 232), (1024, 232), (1024, 572), (0, 572)]],
    "shiqiao": [[(230, 330), (430, 300), (430, 270), (640, 270), (760, 300), (800, 420), (770, 572), (190, 572), (320, 450)]],
    "dahe": [[(320, 232), (1024, 175), (1024, 572), (690, 572), (560, 470), (420, 360), (330, 295)]],
    "xuexiao": [], "laojie": [], "zhulin": [], "laomiao": [],
    "shanding": [[(0, 300), (700, 300), (690, 520), (0, 520)]],
}


SKY_MAX = {"cunkou": .55, "tiangeng": .42, "shiqiao": .5, "dahe": .36, "xuexiao": .45, "laojie": .4, "zhulin": .5, "laomiao": .45, "shanding": .36}


def hsv(a):
    r, g, b = [a[..., i] / 255.0 for i in range(3)]
    mx, mn = np.max(a, 2) / 255.0, np.min(a, 2) / 255.0
    d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, d / (mx + 1e-6), 0)
    return h, s, mx


def poly_mask(polys):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon(p, fill=255)
    return np.asarray(m) > 127


masks = {}
for f in sorted(SRC.glob("scene_*_spring.png")):
    key = f.stem.split("_")[2]
    a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
    h, s, v = hsv(a)
    yy = np.mgrid[0:H, 0:W][0] / H
    # sky: bright, bluish or white, connected to the top edge
    skyc = (v > .62) & ((a[..., 2] >= a[..., 0] - 4) | (s < .12)) & (yy < SKY_MAX[key])
    lab, _ = ndimage.label(skyc)
    top = set(np.unique(lab[0])) - {0}
    sky = np.isin(lab, list(top))
    sky = ndimage.binary_closing(sky, iterations=3)
    sky = ndimage.binary_erosion(sky, iterations=3)
    # plants: greens and yellows, pink blossom
    green = (h > 45) & (h < 170) & (s > .22) & (v > .18)
    waterish = (h > 160) & (h < 230)
    area = poly_mask(WATER[key])
    pink = ((h > 300) | (h < 12)) & (s > .12) & (s < .55) & (v > .7)
    plants = (green | pink) & ~sky & ~(waterish & area)
    pw = plants * (.45 + .55 * yy)
    # water: inside drawn areas, not plants, not brown/wood, not dark stones
    area = poly_mask(WATER[key])
    wat = area & (~green | waterish) & (a[..., 2] > a[..., 0] + 6) & (v > .45) & ~sky
    wat = ndimage.binary_opening(wat, iterations=1)
    R = ndimage.gaussian_filter(wat.astype(np.float32), 2.0)
    G = ndimage.gaussian_filter(pw.astype(np.float32), 1.5)
    B = ndimage.gaussian_filter(sky.astype(np.float32), 3.0)
    m = np.dstack([R, G, B])
    m = (np.clip(m / np.maximum(m.max(axis=(0, 1)), 1e-3) if False else m, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(m, "RGB").resize((512, 286), Image.BILINEAR)
    img.save(OUT / f"{key}_mask.png")
    masks[key] = img
    Image.open(f).convert("RGB").save(OUT / f"{key}.jpg", quality=88)
    Image.open(f).convert("RGB").resize((320, 179), Image.LANCZOS).save(OUT / f"{key}_thumb.jpg", quality=84)
    print(key, "water", round(float(wat.mean()), 3), "plants", round(float(plants.mean()), 3), "sky", round(float(sky.mean()), 3))

# contact sheet for checking
keys = list(masks)
sheet = Image.new("RGB", (512 * 3, 286 * 6), (30, 30, 30))
for i, k in enumerate(keys):
    x, y = (i % 3) * 512, (i // 3) * 572
    sheet.paste(Image.open(OUT / f"{k}.jpg").resize((512, 286)), (x, y))
    sheet.paste(masks[k], (x, y + 286))
sheet.save(OUT / "_check.png")
