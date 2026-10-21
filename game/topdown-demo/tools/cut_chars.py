"""Cut the painted character sheets into sprites for the top-down demo.
Background is flat grey; flood-fill it from the crop border, feather the edge, trim, scale to a fixed height."""
import json, base64, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[3]; SRC = ROOT/"assets/source/characters"
OUT = ROOT/"assets/processed/topdown"; OUT.mkdir(parents=True, exist_ok=True)
# name: (sheet, crop box, output height px)
CUTS = {
 "hero_front": ("hero_travel_turnaround.png", (285, 50, 520, 745), 300),
 "hero_side":  ("hero_travel_turnaround.png", (560, 50, 760, 745), 300),
 "hero_back":  ("hero_travel_turnaround.png", (765, 50, 990, 745), 300),
 "lin":   ("npc_fullbody_seaside_draft.png", (300, 30, 490, 530), 290),
 "lu":    ("npc_fullbody_seaside_draft.png", (565, 150, 710, 526), 220),
 "ayi":   ("npc_fullbody_seaside_draft.png", (810, 60, 1010, 515), 270),
 "azhen": ("npc_fullbody_seaside_draft.png", (55, 50, 225, 527), 280),
}
FACES = {"lin": (360, 45, 460, 145), "ayi": (845, 75, 945, 175), "azhen": (100, 60, 200, 160)}
def cut(sheet, box):
    im = Image.open(SRC/sheet).convert("RGB").crop(box); a = np.asarray(im).astype(np.int16)
    bg = np.array([212, 212, 212]); d = np.abs(a - bg).max(-1)
    cand = d < 14
    lab, n = ndimage.label(cand)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgm = np.isin(lab, list(border))
    fg = ~bgm
    fg = ndimage.binary_opening(fg, iterations=1)
    lab2, n2 = ndimage.label(fg)
    if n2 > 1:
        sizes = ndimage.sum(fg, lab2, range(1, n2+1)); keep = 1 + int(np.argmax(sizes))
        fg = ndimage.binary_dilation(lab2 == keep, iterations=1) & fg | (lab2 == keep)
    alpha = Image.fromarray((fg*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.8))
    al = np.asarray(alpha).astype(np.float32)/255
    # de-fringe: pull edge colours away from the grey background
    rgb = a.astype(np.float32); m = (al > .02) & (al < .98)
    rgb[m] = np.clip((rgb[m] - bg*(1-al[m, None]))/np.maximum(al[m, None], .35), 0, 255)
    out = Image.fromarray(np.dstack([rgb, al*255]).astype(np.uint8), "RGBA")
    return out.crop(out.getbbox())
A = {}
for k, (sheet, box, h) in CUTS.items():
    im = cut(sheet, box); w = round(im.width*h/im.height); im = im.resize((w, h), Image.LANCZOS)
    im.save(OUT/f"{k}.png"); b = io.BytesIO(); im.save(b, "WEBP", quality=90)
    A["c_"+k] = "data:image/webp;base64,"+base64.b64encode(b.getvalue()).decode(); print(k, im.size)
for k, box in FACES.items():
    im = Image.open(SRC/"npc_fullbody_seaside_draft.png").convert("RGB").crop(box).resize((160, 160), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=88); A["f_"+k] = "data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode()
cat = Image.open(ROOT/"assets/processed/cat.webp").convert("RGBA"); cat = cat.crop(cat.getbbox()); print("cat", cat.size)
cat = cat.resize((round(cat.width*150/cat.height), 150), Image.LANCZOS); b = io.BytesIO(); cat.save(b, "WEBP", quality=90)
A["c_cat"] = "data:image/webp;base64,"+base64.b64encode(b.getvalue()).decode()
(OUT/"sprites.json").write_text(json.dumps(A)); print("ok")
