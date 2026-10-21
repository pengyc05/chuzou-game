"""Build game/xiangye-cards/index.html: embed scenes, masks, thumbs, 小路 portrait and the portrait shader."""
import base64, io, json, re
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
SC = ROOT / "assets/processed/scenes"
LP = ROOT / "game/live-portrait-demo"
KEYS = ["cunkou","tiangeng","shiqiao","dahe","xuexiao","laojie","zhulin","laomiao","shanding"]
def uri(p, mime=None):
    p = Path(p); mime = mime or {".jpg":"image/jpeg",".png":"image/png",".webp":"image/webp"}[p.suffix]
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
A = {}
for k in KEYS:
    A["img_"+k] = uri(SC/f"{k}.jpg"); A["msk_"+k] = uri(SC/f"{k}_mask.png"); A["th_"+k] = uri(SC/f"{k}_thumb.jpg")
A["th_big"] = A["img_cunkou"]
la = json.loads((LP/"assets.json").read_text())
A["lu_girl"], A["lu_m1"], A["lu_m2"] = la["girl"], la["m1"], la["m2"]
# round face crop for name-tag portrait and card badge
girl = Image.open(io.BytesIO(base64.b64decode(la["girl"].split(",",1)[1]))).convert("RGBA")
face = girl.crop((330, 250, 610, 530)).resize((160,160), Image.LANCZOS)
bg = Image.new("RGBA", face.size, (255,247,230,255)); bg.alpha_composite(face)
b = io.BytesIO(); bg.convert("RGB").save(b, "JPEG", quality=88)
A["lu_face"] = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
src = (LP/"index.src.html").read_text()
fs = re.search(r"const FS=(`precision.*?`);", src, re.S).group(1)
page = (HERE/"index.src.html").read_text()
assert "/*ASSETS*/" in page and "/*PORTRAIT_FS*/''" in page
page = page.replace("/*ASSETS*/", "const A=" + json.dumps(A) + ";").replace("/*PORTRAIT_FS*/''", fs)
(HERE/"index.html").write_text(page)
print("index.html", round(len(page)/1e6,2), "MB")
