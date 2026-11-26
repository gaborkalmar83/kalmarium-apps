# Contract between Worker A (code) and Worker B (content and media)

Read docs/PLAN.md sections B, C, D, E first. This file only fixes the interfaces. Do not edit it without telling the lead.

## Rules for everybody
- Static site, GitHub Pages, repo root = site root. Python stdlib (+ Pillow for images) only. No third-party requests except `https://overwatch.kalmarium.com/h.js` (`data-app="kalmarium-hub"`).
- No purple/violet/indigo (no hue 235-330 degrees anywhere). No em-dashes or en-dashes in any text, use a plain hyphen.
- No invented ratings, review counts, download numbers. No "loved by", "thousands of".
- Copy is written from the app's own site and store listing, rewritten (not pasted).
- Never commit secrets, raw store folders, or anything outside the owned file lists. Do not run `git push`; the lead pushes.
- ffmpeg: `C:/Users/gabor/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/scratch-workspaces/f649ba4e-ea1c-45b1-83c4-f8dab28879e9/4338aeda-34ea-4ff4-be69-888b3847821f/scratch-2026-11-08-197d33/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe` exists (no ffprobe; use `ffmpeg -i`). Test that it has libx264 (`-encoders`). If it lacks it, report it and skip re-encoding: use poster plus link only.
- Headless Chrome for rendering: `C:/Program Files/Google/Chrome/Application/chrome.exe --headless=new --screenshot=out.png --window-size=W,H --hide-scrollbars file:///...`.

## App ids (fixed)
`knowdrop, mahjong365, tankageddon, lingua-pairs, bilingua, prep4cert, network-troubleshooter, lazy-intercom, crack-a-fold`
Order on the site: games (knowdrop, mahjong365, tankageddon), learning (lingua-pairs, bilingua, prep4cert), tools (network-troubleshooter, lazy-intercom, crack-a-fold).

## data/apps.json (Worker B writes, Worker A reads)
```json
{
  "site": {"url": "https://apps.kalmarium.com", "name": "Kalmarium Apps", "org": "Kalmarium Services", "legalName": "Kalmarium Services B.V.",
           "email": "kalmariumservices@gmail.com", "city": "Almere", "country": "NL",
           "playDeveloper": "https://play.google.com/store/apps/developer?id=Kalmarium+Services", "youtubeChannel": "<url or empty>"},
  "categories": [
    {"id": "games", "title": "Games", "path": "/games/", "h1": "...", "intro": "2-3 sentences", "faq": [{"q": "...", "a": "..."}]},
    {"id": "learning", "...": "..."}, {"id": "tools", "title": "Tools and fun", "...": "..."}
  ],
  "apps": [
    {
      "id": "knowdrop", "name": "Knowdrop", "descriptor": "daily trivia quiz", "category": "games",
      "package": "com.kalmarium.quizdrop", "site": "https://knowdrop.kalmarium.com/",
      "hook": "max 110 chars", "bullets": ["max 70 chars", "...", "..."],
      "audience": "...", "price": "Free, with ads; optional purchases turn ads off", "offerPrice": "0", "offerCurrency": "EUR",
      "schemaType": "VideoGame|MobileApplication", "applicationCategory": "GameApplication|EducationalApplication|UtilitiesApplication|...",
      "accent": "#16a34a",
      "long": "80-120 words for the category page, rewritten", "who": "1-2 sentences", "pick": "one line used in the 'which one' answer",
      "alt": {"icon": "Knowdrop app icon", "tile": "...", "shots": ["...", "...", "..."]},
      "aiArt": false,
      "video": null,
      "youtube": "GaIAvPnITpM or empty"
    }
  ]
}
```
`video` is `null` or `{"file": "video/knowdrop.mp4", "poster": "video/knowdrop-poster.webp", "duration": 45, "uploadDate": "2026-11-20", "width": 1280, "height": 720, "bytes": 2400000, "title": "...", "description": "..."}`.
`site` of mahjong365 is `https://gaborkalmar83.github.io/mahjong365-info/` until its own domain is live.

## Files (Worker B delivers, Worker A references)
- `img/<id>/icon.webp` 192x192, `img/<id>/tile.webp` 800x450, `img/<id>/shot-1.webp..shot-3.webp` 360 px wide (aspect kept), `video/<id>.mp4`, `video/<id>-poster.webp` 800x450.
- `og.jpg` 1200x630, `assets/logo.svg`, `assets/favicon.png` 64x64 and `assets/apple-touch-icon.png` 180x180 (Worker B).
- Worker A must build with placeholders when a file is missing (checker reports missing files, build does not crash).

## Link patterns (Worker A implements)
- Play: `https://play.google.com/store/apps/details?id=<package>&referrer=utm_source%3Dhub%26utm_medium%3D<home|games|learning|tools>` (write `&amp;` in HTML).
- App site: `<site>?utm_source=hub&utm_medium=<home|games|learning|tools>` (for the github.io fallback the same).
- Anchor ids on the home page: `#<id>`.

## Build and check
- `python tools/build.py` writes `index.html`, `games/index.html`, `learning/index.html`, `tools/index.html` (committed output), and `sitemap.xml`.
- `python tools/check.py [--live]` runs the acceptance tests in docs/PLAN.md section E; exit code 1 on failure; prints PASS/FAIL per line.
