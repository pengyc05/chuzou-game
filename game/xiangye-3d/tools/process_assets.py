"""Turn the raw Gemini art in assets/source/ into game-ready files in assets/processed/
and write game/xiangye-3d/assets.json (data URIs the single-file build embeds).

Run from the repo root:  python3 game/xiangye-3d/tools/process_assets.py
Needs: pip install pillow numpy scipy
"""
import base64, io, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "assets" / "source"
OUT = ROOT / "assets" / "processed"
JSON_OUT = ROOT / "game" / "xiangye-3d" / "assets.json"
OUT.mkdir(parents=True, exist_ok=True)


def key_out_background(im, tol=26):
    """Remove the flat background colour that touches the image border."""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    cand = np.abs(a - bg).sum(2) < tol * 3
    lab, _ = ndimage.label(cand)
    ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    mask = ndimage.binary_opening(np.isin(lab, list(ids)), iterations=1)
    alpha = ndimage.gaussian_filter((~mask).astype(np.float32), 0.8)
    alpha = np.clip((alpha - 0.15) / 0.7, 0, 1)
    return Image.fromarray(np.dstack([a.astype(np.uint8), (alpha * 255).astype(np.uint8)]), "RGBA")


def crop_to_alpha(im, pad=6):
    x0, y0, x1, y1 = im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def fit(im, w, h):
    s = min(w / im.width, h / im.height, 1)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def data_uri(im, fmt, q=82):
    b = io.BytesIO()
    if fmt == "WEBP":
        im.save(b, fmt, quality=q, method=6)
    else:
        im.save(b, fmt, quality=q)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()


A = {}
tree = fit(crop_to_alpha(key_out_background(Image.open(SRC / "environment/tree_camphor_spring.png"), 22)), 512, 700)
tree.save(OUT / "tree.webp"); A["tree"] = data_uri(tree, "WEBP")
cat = fit(crop_to_alpha(key_out_background(Image.open(SRC / "characters/cat.png"), 14)), 300, 300)
cat.save(OUT / "cat.webp"); A["cat"] = data_uri(cat, "WEBP")

# mountains: the white sky above the ridge becomes transparent
m = np.asarray(Image.open(SRC / "environment/bg_mountain_spring.png").convert("RGB")).astype(np.float32)
alpha = np.clip((250 - m.min(2)) / 40, 0, 1)
mt = Image.fromarray(np.dstack([m.astype(np.uint8), (alpha * 255).astype(np.uint8)]), "RGBA")
mt.save(OUT / "mountain.webp"); A["mountain"] = data_uri(mt, "WEBP")

TEX = ["grass_spring", "grass_summer", "grass_autumn", "snow", "dirt_path", "stone_path", "pebbles", "paddy_spring", "paddy_summer"]
KEYS = {"dirt_path": "dirt", "stone_path": "stone"}
for name in TEX:
    im = Image.open(SRC / f"textures/tex_{name}.png").convert("RGB")
    w, h = im.size
    m_ = max(2, int(min(w, h) * 0.03))
    im = im.crop((m_, m_, w - m_, h - m_)).resize((512, 512) if name == "grass_spring" else (256, 256), Image.LANCZOS)
    im.save(OUT / f"tex_{name}.jpg", quality=86)
    A["t_" + KEYS.get(name, name)] = data_uri(im, "JPEG", 86)

con = Image.open(SRC / "environment/concept_spring.png").convert("RGB")
con.save(OUT / "concept_spring.jpg", quality=82); A["concept"] = data_uri(con, "JPEG", 80)

JSON_OUT.write_text(json.dumps(A))
print(f"{len(A)} assets, {sum(len(v) for v in A.values()) // 1024} KB -> {JSON_OUT.relative_to(ROOT)}")
