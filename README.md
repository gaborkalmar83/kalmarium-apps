# Kalmarium Apps hub

Source of https://apps.kalmarium.com/, the catalogue of the nine Kalmarium Android apps. A static site for GitHub Pages: the repo root is the site root, there is no framework and no runtime dependency.

## How it is built

All facts and copy live in one file, `data/apps.json`. `tools/build.py` turns it into the pages that are committed:

| Output | Made by |
|---|---|
| `index.html`, `games/index.html`, `learning/index.html`, `tools/index.html` | `tools/build.py` |
| `privacy-policy.html`, `404.html`, `sitemap.xml` | `tools/build.py` |
| `assets/site.css`, `assets/site.js` | written by hand |
| `CNAME`, `robots.txt`, `app-ads.txt` | written by hand |

Never edit the generated pages by hand; change `data/apps.json` or `tools/build.py` and rebuild. Note that `tools/` holds both the Python scripts and the generated Tools category page `tools/index.html`; the two do not clash.

```
python tools/build.py          # regenerate every page and sitemap.xml
python tools/check.py          # offline acceptance tests, exit code 1 on any FAIL
python tools/check.py --live   # the same plus https://apps.kalmarium.com and the Play and app-site links
```

Python 3.9 or newer, standard library only. `build.py --root DIR` builds into another folder (used for previews). If a file under `img/` or `video/` is missing the build still succeeds and `check.py` names the missing file.

If `vnu.jar` (the Nu HTML checker) is on `VNU_JAR` or passed with `--vnu`, `check.py` runs it; otherwise it falls back to a built-in structure lint.

## Rules the checks enforce

- No colour with a hue between 235 and 330 degrees (no purple, violet or indigo).
- No em-dash or en-dash anywhere in text files.
- No third-party requests except the cookie-free visit script `https://overwatch.kalmarium.com/h.js`; no cookies, no storage, no web fonts.
- Budgets: CSS 14 KB, JS 3 KB, home HTML 40 KB, home first view 450 KB and 25 requests; image and video sizes as in `docs/PLAN.md`.
- No ratings, review counts or download numbers, in the page or in the JSON-LD.
- Every link to Google Play carries the right package id and `referrer=utm_source%3Dhub%26utm_medium%3D<page>`.

## Layout

```
data/apps.json              single source of app facts and copy
img/<id>/                   icon.webp, tile.webp, shot-1..3.webp
video/                      self-hosted clips and posters (click-to-load, no embeds)
brand/                      developer icon, Play header and og image sources
assets/                     site.css, site.js, logo, favicons
tools/                      build.py, check.py, imgsize.py (and the generated Tools page)
docs/                       PLAN.md, CONTRACT.md
```

## Design

A printed product catalogue: warm paper, dark ink, Georgia display type, numbered entries 01-09, one 4 px accent rule per app, hairlines instead of shadows. Light and dark follow `prefers-color-scheme`; there is no toggle and nothing is stored.

Some artwork on the site may be AI-generated; apps with such art are flagged `aiArt` in the data and the footer says so.
