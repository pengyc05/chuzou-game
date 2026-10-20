# 出走 (chuzou-game) — notes for Claude

The owner writes in Chinese; reply in Chinese. They confirm decisions one point at a time, so propose, get a yes, then build.

## Decisions already made
- Engine: three.js r160 in a single HTML page; ship to Steam later via Electron (`build.py --offline`). Steam is the main platform; China release needs a 版号, so not now.
- Look: 3D scenes + toon shading + ink outlines; Japanese hand-painted (Ghibli-like) palette. Art comes from Gemini (2D) and later Meshy/Tripo (3D hero).
- UI: option C "乡间木牌" — hanging wooden sign, cream boards with thick brown rims (#5e4027), wooden buttons, rounded dialogue box with a wooden name tag and round portrait. Do not switch back to the earlier thin black-bordered paper notes.
- Chapter 1 is a mountain village named 乡野村 (田园、小溪、学校、山、草木) with four seasons; staying longer moves the seasons on. Player can stay several days; jobs refresh daily. Hero name is chosen at the start (default 陈默). Game title: 《出走》.
- Not decided yet: the villagers (who lives in 乡野村), their jobs/stories, whether the prologue keeps the "repeat the same day" loop.

## How the 3D page is built
- Edit `game/xiangye-3d/index.src.html`; never edit `dist/`. `/*ASSETS*/` is replaced by `assets.json` at build time.
- Terrain height `H(x,z)`, collision `blocked(x,z)`, paths `ALLPATHS`, fields `FIELDS`, houses `HOUSES`.
- Stylized parts: `TM()` toon material, `ink()` edge lines, `hull()` character outlines, `HERO` procedural walk, `Foliage()` leaf-card trees, `GRASS` (player-following patch over a baked heightmap `HM`), `RICE` (seasonal rows in fields).
- Season/time tables: `SEASONS`, `TIMES`; `applySeason()` / `applyLight()` push colours into every shader.

## Testing
Headless Chromium with SwiftShader runs at 1–2 fps, so judge visuals from screenshots, not smoothness, and wait several seconds after teleporting the player (the camera lerps). Route the jsdelivr three.js URL to `vendor/three.min.js` when testing offline.
