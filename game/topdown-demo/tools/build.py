"""Build game/topdown-demo/index.html: embeds the 石桥小溪 painting and 小路's face."""
import base64, io, json
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]; HERE = Path(__file__).resolve().parents[1]
la = json.loads((ROOT/"game/live-portrait-demo/assets.json").read_text())
girl = Image.open(io.BytesIO(base64.b64decode(la["girl"].split(",",1)[1]))).convert("RGBA")
face = girl.crop((330,250,610,530)).resize((160,160), Image.LANCZOS)
bg = Image.new("RGBA", face.size, (255,247,230,255)); bg.alpha_composite(face)
b = io.BytesIO(); bg.convert("RGB").save(b, "JPEG", quality=88)
A = {"lu_face": "data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode(),
     "shiqiao": "data:image/jpeg;base64,"+base64.b64encode((ROOT/"assets/processed/scenes/shiqiao.jpg").read_bytes()).decode()}
page = (HERE/"index.src.html").read_text().replace("/*ASSETS*/", "const A="+json.dumps(A)+";")
(HERE/"index.html").write_text(page); print("ok", round(len(page)/1e6,2), "MB")
