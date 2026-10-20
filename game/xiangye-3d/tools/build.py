"""Build the single-file game page: index.src.html + assets.json -> dist/index.html.

Run from the repo root:  python3 game/xiangye-3d/tools/build.py [--offline]
  --offline  inline vendor/three.min.js instead of loading it from the CDN
             (use this for the Electron / Steam build, which must work without internet)
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
src = (HERE / "index.src.html").read_text(encoding="utf-8")
assets = json.loads((HERE / "assets.json").read_text())
out = src.replace("/*ASSETS*/", "const ASSETS=" + json.dumps(assets) + ";")
if "--offline" in sys.argv:
    cdn = '<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>'
    out = out.replace(cdn, "<script>" + (HERE / "vendor/three.min.js").read_text(encoding="utf-8") + "</script>")
dist = HERE / "dist"
dist.mkdir(exist_ok=True)
(dist / "index.html").write_text(out, encoding="utf-8")
print(f"dist/index.html  {len(out) // 1024} KB")
