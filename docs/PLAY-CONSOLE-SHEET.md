# Play Console sheet: Play developer profile

For the owner. Nothing here has been entered anywhere; a worker never touches the console.

Where: Play Console > Settings (Manage account) > Account details > **Play developer profile**
https://play.google.com/console/developers/account/public-details

## Values to enter

| Field | Value |
|---|---|
| Developer icon | `brand/dev-icon-512.png` (512 x 512, 32-bit PNG, the K mark on a solid deep teal square) |
| Header image | `brand/play-header-4096x2304.jpg` (4096 x 2304, JPG, no alpha) |
| Promotional text (140 max, this is 139) | `Small, honest Android apps and games from the Netherlands: trivia, mahjong, a tank shooter, language learning, exam prep and network tools.` |
| Website | `https://apps.kalmarium.com/` |
| Featured app | Knowdrop (`com.kalmarium.quizdrop`) |

Full paths from the repo root `C:\dev\kalmarium-apps`:
- `C:\dev\kalmarium-apps\brand\dev-icon-512.png`
- `C:\dev\kalmarium-apps\brand\play-header-4096x2304.jpg`

Do not change the developer name ("Kalmarium Services"); that is a separate account-level action.

## Order of steps

1. Wait until `https://apps.kalmarium.com/` loads over HTTPS (DNS CNAME `apps` -> `gaborkalmar83.github.io` is set, GitHub Pages custom domain verified, Enforce HTTPS ticked). Do not enter the Website field before that.
2. Open the Play developer profile page (link above).
3. Upload the developer icon: `brand/dev-icon-512.png`.
4. Upload the header image: `brand/play-header-4096x2304.jpg`.
5. Paste the promotional text exactly as above. Check the counter shows 139 of 140.
6. Enter the website address `https://apps.kalmarium.com/`.
7. Pick the featured app: Knowdrop.
8. Save and use the preview. A preview link is available within about 1 hour; public within about 24 hours. Later edits take about 1 hour.
9. Check the preview on a phone and on a desktop browser. Play crops the header differently per device and does not document the crop. The wordmark, the nine icons and the URL line sit inside the centre 60 percent of the width and 50 percent of the height; the two phone screenshots at the sides are decorative and may be cut. See `brand/play-header-safe-preview.png` for 16:9, 2:1 and 4:3 crops.
10. If a crop looks wrong, edit `brand/play-header.html`, render it again with headless Chrome at 4096 x 2304 and re-upload.

## Notes

- The header contains no AI-generated art of its own. It shows the nine real app icons (some icons are AI-generated art, see `aiArt` in `data/apps.json`) and two real screenshots, so no separate AI label is needed for the header.
- Optional later: add nl-NL, de-DE and hu-HU translations of the promotional text.
- Not controllable on this page: the order of the app list, the image each app card shows, ratings, download counts and prices shown on the cards.
