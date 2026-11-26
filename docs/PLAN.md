# Kalmarium Apps hub and Play developer page - plan (26 Nov 2026)

Scope: (1) make https://play.google.com/store/apps/developer?id=Kalmarium+Services look professional; (2) build one hub site for the 9 live apps on GitHub Pages, findable and linked from Play. This is a plan, not code. Nothing was changed anywhere except this file.

Sources read: the 9 info-site repos under C:\dev, `overwatch/docs/marketing-audit-2026-11-22.md`, `marketing-todo.md`, `site-fix-brief.md`, `overwatch/src/connectors/siteCheck.ts`, `overwatch/src/web.ts`, `overwatch/src/seed.ts`, the store folders, the live Play developer page (fetched 26 Nov) and Play Console Help article 9873827 ("Create or update your developer profile").

Findings that change the work (verified in files, not guessed):
- The public developer page lists all 9 apps. Four cards show a YouTube thumbnail (Knowdrop `GaIAvPnITpM`, Lingua Pairs `MUHGI4thGqQ`, Bilingua `ditH32F_NWM`, Ultimate Net Troubleshooter `TF6OvqklJd0`); the other five show a feature graphic or screenshot. Crack A Fold shows USD 1.79 in the US store (site says EUR 1.99).
- `lazy-intercom-info/index.html` has no visit script, no referrer tag on its Play links and no "More from Kalmarium" footer.
- `mahjong365-info` is a 1.5 KB stub: no canonical, Open Graph, schema, Play link, robots, sitemap or images; its custom domain is still `CNAME.pending`.
- `overwatch/src/seed.ts` has no app rows for Lazy Intercom or Mahjong365 (the live database may differ; check).
- `ffprobe`/`ffmpeg` is not on PATH on this PC; video re-encoding needs it installed first.
- `apps.kalmarium.com` does not resolve today (free to use).

---

## A. Play developer page: what it can and cannot do

Verdict: the page can get a header banner, a developer icon, one 140-character line, one website link and one featured app. That is all. It is enough to stop looking auto-generated, and most of the remaining "professional" impression comes from the 9 app cards, which are controlled per app listing, not on the developer page.

Where: Play Console > Settings (Manage account) > Account details > **Play developer profile** (https://play.google.com/console/developers/account/public-details). Requirement: at least one published app (met).

| Field | Limit | What to enter |
|---|---|---|
| Developer icon | 512 x 512, 32-bit PNG | Kalmarium mark on a solid deep-teal square (see C). Built as SVG, exported to PNG. No AI. |
| Header image | 4096 x 2304, JPG or 24-bit PNG, no alpha | Composed banner: the 9 real app icons in a row plus three real phone screenshots on the paper/teal brand colours, wordmark "Kalmarium" and nothing else. Rendered from HTML with headless Chrome at 4096 x 2304 (same method as the Bilingua one-pager). Keep everything important inside the centre 60 percent of the width and centre 50 percent of the height; Play crops the banner differently on phone, tablet and web, and the crop is not documented. No AI art, so no AI label needed. |
| Promotional text | 140 characters, translatable | `Small, honest Android apps and games from the Netherlands: trivia, mahjong, a tank shooter, language learning, exam prep and network tools.` (139 characters). Add nl-NL, de-DE and hu-HU translations later; not needed for launch. |
| Website address | one URL | `https://apps.kalmarium.com/` (enter only after the hub is live over HTTPS). |
| Featured app | one of your apps | **Knowdrop** (`com.kalmarium.quizdrop`): broadest audience, has a video, has a rating. Not Bilingua until its uninstall rate is understood. |

Timing: preview URL within about 1 hour, public within 24 hours; later edits about 1 hour.

Not controllable on the developer page:
- Developer name stays "Kalmarium Services" (changing it is a separate account-level action; do not).
- No long description, no second link, no social links, no video, no sections or categories.
- Order of the app list and which image each card shows (Play picks the listing's video thumbnail, else feature graphic or screenshot).
- Ratings, download counts ("0+", "1+") and prices shown on cards.
- How the header is cropped per device.
- The page's own SEO title ("Android Apps by Kalmarium Services on Google Play") and its generic meta description.

What actually lifts the page (per app, Main store listing; needs the owner's go-ahead each time):
1. Give the five cards without a video a consistent look: add a YouTube promo video to Tankageddon (trailer exists: `tankageddon/site/trailer.mp4`), Crack A Fold (a clean promo, not the FGS demo `QoV_xSBg02A`) and Lazy Intercom (`lazy-intercom-info/demo.mp4`). Mahjong365 and Prep 4 Cert: check feature graphics read well at 416 x 235.
2. Feature graphics: check all 9 at card size for legible name and a shared quiet convention (name bottom-left, no badge clutter). Fix only the ones that fail; no new art budget planned for this.
3. Each listing's Website field keeps pointing at its own app site (app-ads.txt lives there). Only the developer profile points at the hub.

---

## B. Hub site architecture

**Domain: `https://apps.kalmarium.com/`**, repo `gaborkalmar83/kalmarium-apps` (public), GitHub Pages from `main` root, `CNAME` file = `apps.kalmarium.com`, Wix DNS CNAME `apps` -> `gaborkalmar83.github.io`.
- Why `apps.`: 5 of 9 products are not games, so `games.` is wrong; `play.` collides with "Google Play" and with the existing `knowdrop-play.kalmarium.com`; "Kalmarium apps" is the query people will type.

**Structure: 4 content pages, hand-sized, generated from one data file.**

| URL | Purpose | Apps |
|---|---|---|
| `/` | All 9 apps, brand, who we are | all |
| `/games/` | Category landing page | Knowdrop, Mahjong365, Tankageddon |
| `/learning/` | Category landing page | Lingua Pairs, Bilingua, Prep 4 Cert |
| `/tools/` | Category landing page ("Tools and fun") | Ultimate Network Troubleshooter, Lazy Intercom, Crack A Fold |
| `/privacy-policy.html`, `/404.html` | Required pages | |

- Each app has exactly one home category (Lingua Pairs lives in Learning; Games carries a one-line cross-link to it).
- No per-app pages on the hub. The app sites are the canonical page for each app; a hub copy would compete with them.
- Category pages must be deeper than the home page (longer text, 3 screenshots, video, "who is it for"), otherwise they are thin duplicates. If time is short, ship `/` first and the three category pages in the same week, not later.

**Home page sections, in order**
1. Header: wordmark "Kalmarium Apps", nav: Games, Learning, Tools, About. No hamburger: four short links wrap on mobile.
2. Hero: H1, one honest sentence, the 9 real icons as a tappable strip (anchor links). Text is the LCP element.
3. Catalogue: 9 entries numbered 01-09, grouped under three H2 category headings, each entry an `article` with id (`#knowdrop`, `#mahjong365`, ...).
4. "How we build" strip: 4 plain facts that are true for every app and checkable (see copy below).
5. About: Kalmarium Services B.V., Almere, Netherlands; one person studio; contact email.
6. Footer: category links, all 9 app sites with descriptors, Play developer page, privacy policy, email, "Some artwork on this site is AI-generated".

"How we build" facts (keep only what holds for all 9; verify against each privacy policy before publishing): no account needed to start; no subscription required to use the core app (Knowdrop has an optional Plus subscription, so word it as "no forced subscription" or drop it); ads, where present, are a small banner and can be removed with a one-time purchase; this website uses no cookies.

**Per-app card content (same fields for all 9)**
- Icon (real), name + descriptor as H3 link text, e.g. "Knowdrop - daily trivia quiz".
- One-line hook (max 110 characters).
- 3 bullets (facts from the app site, max 70 characters each).
- Spec row in small caps: `ANDROID` - audience - price/ads statement.
- One landscape tile image (video poster where a video exists).
- Two buttons: "Get it on Google Play" (aria-label includes the app name) and "More about <name>" to the app site.

Facts sheet for the cards (taken from the app sites; worker B re-verifies each line against the live site before use):

| App | Hook | Price / ads statement | Audience |
|---|---|---|---|
| Knowdrop | A fresh Daily Drop of 10 fact-checked questions every day | Free, with ads; optional purchases turn ads off | Quiz fans, friends and family |
| Mahjong365 | Calm mahjong solitaire with a level for every day of the year | Free, one small banner, no pop-up ads; optional lifetime Premium | Relaxed puzzle players, large tiles |
| Tankageddon | One tank against the alien invasion: 99 levels, 99 boss fights | Free, small banner; one-time Premium removes ads | Arcade shooter players, offline |
| Lingua Pairs | The memory game where you match a word with its translation | Free, small banner; one-time purchase removes ads | Language learners (DE, ES, FR, NL, HU, EN) |
| Bilingua | Read any EPUB or PDF with every sentence translated underneath | No ads; 14-day free trial, then a one-time purchase | Language learners who read books |
| Prep 4 Cert | Original practice questions for 47 Microsoft certification exams | Free preview of 15 questions per exam; one-time purchase per bank; small banner in the free version | IT professionals and students |
| Ultimate Network Troubleshooter | WiFi analyzer, speed test, port scanner and network map in one app | Free, one small banner; one-time purchase removes it | Home users, IT and network people |
| Lazy Intercom | Hold a button, speak, and the family hears it, even with headphones on | Free, one small banner; Remove ads is EUR 1.99 once | Households on one Wi-Fi |
| Crack A Fold | A prank for foldable phones: they fold it, the screen seems to crack | Paid, about EUR 1.99 (varies by country); no ads, no data | Owners of foldable phones |

**Linking and tags (established pattern, hub variant)**
- Play: `https://play.google.com/store/apps/details?id=<package>&amp;referrer=utm_source%3Dhub%26utm_medium%3D<home|games|learning|tools>`. The site check only requires `referrer=`; `utm_source=hub` separates hub installs from app-site installs (`utm_source=website`) in Play Console acquisition reports.
- App sites: `https://<host>/?utm_source=hub&utm_medium=<page>` so each app site's OverWatch counter shows "hub / home" etc. Canonicals on the app sites already strip the query.
- Mahjong365 links go to `https://mahjong365.kalmarium.com/` only after its DNS is live; until then `https://gaborkalmar83.github.io/mahjong365-info/`.
- Visit counter on every hub page: `<script defer src="https://overwatch.kalmarium.com/h.js" data-app="kalmarium-hub"></script>`. **Recommendation: yes, add a `kalmarium-hub` app id in OverWatch** (kind app, no package name, no AdMob id, enabled) plus a `site-check` source with url `https://apps.kalmarium.com`. With no package name the `playlive` check is skipped, with no AdMob id the `appads` check is skipped, and the `schema` check passes on the ItemList's MobileApplication/VideoGame items. Add `apps.kalmarium.com` to the own-hosts list if one is configured, so internal clicks do not count as referrers.
- Ship `app-ads.txt` on the hub anyway (same publisher line). Costs nothing and protects ad serving if a listing's website ever points here.

**Video strategy: self-hosted MP4 behind a click-to-load facade. No YouTube embeds.**
- An embed (even youtube-nocookie) loads third-party scripts, which breaks the owner rule. Instead: a poster image with a play button; on click a 15-line vanilla script replaces it with `<video controls playsinline preload="none">` and starts it. Without JS, the poster is a plain link to the MP4. Next to it a text link "Watch on YouTube" where an id exists.
- Encode: H.264 + AAC (or silent), 1280 x 720 for 16:9 (720 x 1280 for portrait), `-crf 28 -preset slow -movflags +faststart`, cap 2.5 MB per file, max 60 seconds (cut longer promos). Poster: WebP 800 x 450, max 45 KB.

| App | Source | On hub |
|---|---|---|
| Knowdrop | `knowdrop/store/video-1.4.0/knowdrop-promo-16x9.mp4` (4.4 MB) | re-encode; YouTube `GaIAvPnITpM` |
| Lingua Pairs | `lingua-pairs/store/video/lingua-pairs-promo-16x9.mp4` (2.0 MB) | re-encode; YouTube `MUHGI4thGqQ` |
| Tankageddon | `tankageddon/site/trailer.mp4` (3.7 MB) + `img/trailer-poster.jpg` | re-encode to 2.5 MB |
| Bilingua | `lingua-reader/store/marketing/bilingua-promo-5.9-1080p.mp4` (2.8 MB) | cut to 60 s; YouTube `ditH32F_NWM` |
| Lazy Intercom | `lazy-intercom-info/demo.mp4` (0.4 MB) | use as is |
| Crack A Fold | `crack-a-fold/store/crackafold-fgs-demo.mp4` (2.1 MB) is a compliance demo | **no video in v1**; screenshots only |
| Network Troubleshooter | YouTube `TF6OvqklJd0`; local source not found | text link to YouTube only in v1, unless the owner supplies the MP4 |
| Prep 4 Cert | a YouTube video exists (audit); id not in the repos | text link once the owner gives the id |
| Mahjong365 | none | screenshots only |

**Image strategy** (reuse first; all WebP, explicit `width`/`height`, `loading="lazy"` below the hero, `decoding="async"`)
- `img/<id>/icon.webp` 192 x 192, max 12 KB (from each store `icon-512.png` or site `icon.png`).
- `img/<id>/tile.webp` 800 x 450, max 60 KB (Tankageddon `keyart.jpg`, Lazy Intercom `hero.webp`, others cropped from the 1024 x 500 feature graphics, Mahjong365 from `mahjong365/store/play/feature-1024x500.png`).
- `img/<id>/shot-1..3.webp` 360 px wide, max 25 KB each (category pages only): from the info-site `img/` folders; Mahjong365 from `store/play/phone-01..08.png`.
- `og.jpg` 1200 x 630, max 150 KB: the Play header composition re-rendered at that size.

**Performance budget**
- Home: max 450 KB transferred on first view (no video until clicked), max 25 requests, HTML max 40 KB, one CSS file max 14 KB, one JS file max 3 KB, zero web fonts.
- LCP under 1.8 s on a mid-range phone on 4G (LCP element is the H1 text), CLS under 0.05, TBT about 0.
- Lighthouse mobile targets: Performance 95+, Accessibility 100, Best Practices 100, SEO 100.

---

## C. Visual design direction

**Concept: a printed product catalogue, not an app-store clone.** Warm paper background, dark ink, numbered entries (01-09), a serif display face, small-caps spec rows like a parts list. It is calm, it suits "small honest studio", and it does not look like every dark gradient app page. The app sites keep their own identities; the hub is the neutral shelf they sit on.

Palette (the hues already shared by the app sites: teal, amber, cream, vermilion). Rule for workers: no colour with a hue between 235 and 330 degrees anywhere, including shadows, gradients, focus rings and SVGs.

| Token | Light | Dark | Use |
|---|---|---|---|
| paper | `#F4EFE6` | `#0E1416` | page background |
| surface | `#FBF8F2` | `#151E21` | cards |
| ink | `#14181A` | `#E9EEF0` | text |
| muted | `#5A5F5C` | `#9AA8AD` | secondary text (check 4.5:1) |
| line | `#D8D0C2` | `#2A383D` | hairlines |
| brand | `#0F5257` | `#3FD0C4` | links, wordmark, primary button |
| accent | `#B5730A` text / `#F2B134` fill | `#FFB347` | numbers, highlights |
| signal | `#C23A26` | `#E8654F` | rare emphasis only |

Each catalogue entry carries a 4 px side rule in that app's own accent (Knowdrop `#16a34a`, Mahjong365 `#D9412B`, Tankageddon `#3fd0c4`, Lingua Pairs `#F0553A`, Bilingua `#1a6b4b`, Prep 4 Cert `#3ed6b8`, Net Troubleshooter `#00A88F`, Lazy Intercom `#E8553A`, Crack A Fold `#2EC4B6`). All pass the hue rule.

Type (system only): display `Georgia, "Iowan Old Style", "Palatino Linotype", serif` weight 700 for H1/H2 and the entry numbers; body `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` 17 px / 1.6; spec rows `ui-monospace, "Cascadia Mono", Consolas, monospace` 12.5 px uppercase with letter-spacing.

Layout: single column to 720 px on phones; from 900 px each entry is a two-column row (text left, tile right, alternating), max width 1120 px; hairline rules between entries instead of card shadows. Icon strip in the hero is a 3 x 3 grid on phones, one row of 9 on desktop.

Motion: none on load. Hover/focus: 120 ms colour and 2 px translate on buttons only; everything off under `prefers-reduced-motion`. Dark/light follows `prefers-color-scheme` only; no toggle, no storage. Visible focus ring (2 px brand + 2 px offset). Tap targets at least 44 px.

**Azure image shot list: the honest answer is zero required images.**
The hub's hero is typography plus real icons; tiles are existing key art and feature graphics; the Play header and og image are composed from real icons and screenshots. That is more credible for buyers than stock-like AI art and needs no "AI-generated" label on the store.

One optional shot, to be used only if the first build review finds the hero flat:

| # | Use | Size / quality | Cost | Prompt |
|---|---|---|---|---|
| 1 (optional) | Faint hero backdrop on `/` behind the icon strip, at 12-18 percent opacity; also the og image background | 1536 x 1024, medium (about USD 0.07); one retry allowed; high (about USD 0.19) only if medium shows artefacts | USD 0.07-0.26, about EUR 0.07-0.24 | "Top-down still life on warm cream paper: a matte dark-teal Android phone lying face down, a few blank ivory mahjong-style tiles without any symbols, a short ochre pencil, a small folded paper map, and a coiled teal cable, arranged loosely with generous empty space in the centre and left. Soft daylight from the upper left, gentle long shadows, muted palette of cream, deep teal, amber and a little vermilion red. Flat editorial product-catalogue photography, fine paper grain. No text, no letters, no logos, no numbers, no people, no purple, no violet, no indigo, no neon, no gradients." |

Hard cap: 3 generations in total, at most USD 0.57 (about EUR 0.53), well under EUR 2. If used, the footer line "Hero illustration: AI-generated" is mandatory, and it is not used on Play.

---

## D. SEO plan (seo-audit method: intent, on-page, technical, links, measurement)

**Page-level targets**

| Page | Primary keyword | Secondary | Intent | Title (chars) | Meta description (chars) |
|---|---|---|---|---|---|
| `/` | Kalmarium apps | Kalmarium Services Android apps | navigational / brand | `Kalmarium Apps: Android Games, Learning Apps and Tools` (54) | `Nine Android apps and games by Kalmarium Services: daily trivia, mahjong, a tank shooter, language learning, Microsoft exam practice and network tools. On Google Play.` (167) |
| `/games/` | offline Android games | trivia, mahjong, tank shooter | commercial / install | `Android Games by Kalmarium: Trivia, Mahjong, Tank Shooter` (57) | `Three Android games you can play offline: Knowdrop daily trivia quiz, Mahjong365 mahjong solitaire and Tankageddon, a tank shooter with 99 boss fights. Free to start.` (166) |
| `/learning/` | learning apps for Android | language learning, Microsoft exam practice | commercial / install | `Learning Apps for Android: Languages and Microsoft Exams` (56) | `Learn words with the Lingua Pairs memory game, read books in two languages with Bilingua, and practise for 47 Microsoft certification exams with Prep 4 Cert.` (157) |
| `/tools/` | Android network and home tools | WiFi analyzer, family intercom, fold prank | commercial / install | `Android Tools and Fun: WiFi Analyzer, Intercom, Fold Prank` (58) | `Ultimate Network Troubleshooter for WiFi and speed checks, Lazy Intercom for calling the family without shouting, and Crack A Fold, a prank for foldable phones.` (160) |

**App-block targets** (the block's H3, link anchor text and ItemList description carry these; the app site remains the ranking page)

| App block | H3 / anchor text | Primary keyword | Secondary | Intent |
|---|---|---|---|---|
| `#knowdrop` | Knowdrop - daily trivia quiz | daily trivia quiz app | trivia battle with friends | install |
| `#mahjong365` | Mahjong365 - daily mahjong solitaire | mahjong solitaire large tiles | mahjong no pop-up ads | install |
| `#tankageddon` | Tankageddon - offline tank shooter | offline tank game android | tank game with boss fights | install |
| `#lingua-pairs` | Lingua Pairs - language memory game | vocabulary matching game | learn Dutch / Hungarian words | install |
| `#bilingua` | Bilingua - bilingual book reader | bilingual books app | parallel text EPUB reader | install |
| `#prep4cert` | Prep 4 Cert - Microsoft exam practice | Microsoft exam practice questions | AZ-900 practice app | install |
| `#network-troubleshooter` | Ultimate Network Troubleshooter - WiFi analyzer and network tools | wifi analyzer android | iperf3 android, port scanner | install |
| `#lazy-intercom` | Lazy Intercom - family intercom app | family intercom app android | wifi intercom with headphones | install |
| `#crack-a-fold` | Crack A Fold - foldable phone prank | foldable phone crack prank | Galaxy Z Fold cracked screen prank | install |

**Heading outline, home page**
- H1: `Android apps and games by Kalmarium`
- H2 Games > H3 x3; H2 Learning > H3 x3; H2 Tools and fun > H3 x3
- H2 How we build; H2 About Kalmarium Services; (footer nav is not a heading)
- Category pages: H1 = title phrase without the brand; one H2 per app, H3 for "What you get", "Who it is for", "Price"; H2 "Which one should I pick?" (3-4 real questions; add FAQPage schema only for questions shown).

**JSON-LD (one `@graph` per page, no ratings, no review counts, no download numbers)**
- `Organization` `@id` `https://apps.kalmarium.com/#org`: name "Kalmarium Services", legalName "Kalmarium Services B.V.", url, logo (512 PNG), email, address (Almere, NL), `sameAs`: Play developer page, YouTube channel, `https://kalmarium.com`.
- `WebSite` `@id` `/#website`: name "Kalmarium Apps", url, publisher -> org, inLanguage "en". No SearchAction (there is no search).
- `ItemList` (home: 9 items; category page: 3) of `ListItem` with `item` = `VideoGame` (Knowdrop, Mahjong365, Tankageddon) or `MobileApplication` (the other six; Lingua Pairs with applicationCategory "GameApplication"): name, description, operatingSystem "Android", applicationCategory, url (app site), installUrl (Play), image, `offers` {price "0" or "1.99", priceCurrency "EUR"}, author -> org.
- Category pages add `BreadcrumbList` (Home > Games).
- Videos: `VideoObject` only for self-hosted clips, with real `uploadDate`, `contentUrl`, `thumbnailUrl`, duration.

**Technical**
- `robots.txt`: `User-agent: *`, `Allow: /`, `Sitemap: https://apps.kalmarium.com/sitemap.xml`.
- `sitemap.xml`: `/`, `/games/`, `/learning/`, `/tools/`, `/privacy-policy.html`, each with `lastmod`.
- Self canonical on every page, trailing-slash URLs for folders, `lang="en"`, Open Graph + `twitter:card=summary_large_image`, one H1, alt text on every image (icon alt = "<App> app icon"), `theme-color` light and dark.
- Enforce HTTPS in the Pages settings; `404.html` links back to the catalogue.

**Internal links and backlinks**
1. Hub -> each app site (descriptor anchors above) and -> each Play listing. 18 outbound links to own properties per home page.
2. Each of the 9 app sites: in "More from Kalmarium", add as first item `All Kalmarium apps` -> `https://apps.kalmarium.com/`, and add the two missing apps (Lazy Intercom, Mahjong365) to every footer. Lazy Intercom's site needs the whole footer; Mahjong365's site needs a full rebuild per `site-fix-brief.md` first.
3. Play developer profile Website -> hub.
4. kalmarium.com (Wix): add an "Apps" menu item linking to the hub. This is the strongest link available and closes the open "your call" item in `marketing-todo.md`.
5. YouTube channel "Kalmarium Services": hub link in the channel links and first line of every video description (tagged `?utm_source=youtube&utm_medium=description`).
6. GitHub profile website field -> hub. No directory spam, no paid links.

**Search Console** (the Domain property for kalmarium.com is already verified and covers the new subdomain)
1. After HTTPS works: Sitemaps > add `https://apps.kalmarium.com/sitemap.xml`.
2. URL inspection > Request indexing for `/`, `/games/`, `/learning/`, `/tools/`.
3. Day 7: Pages report (indexed count = 5), Enhancements shows no structured-data errors.
4. Day 28: Performance filtered to `apps.kalmarium.com`: queries, impressions, clicks, average position.

**What to measure (monthly, next to the existing Play acquisition review)**
- OverWatch `kalmarium-hub`: visits, top pages, referrers (expect `play.google.com`, `kalmarium.com`, the app sites), countries.
- OverWatch per app site: campaign tag `hub / <page>` visits (hub -> app site click-through).
- Play Console > Store listing acquisition: visitors and installs with `utm_source=hub`, per app.
- Search Console: brand query impressions and clicks; number of indexed hub pages.
- Success after 90 days: hub indexed, ranks first for "Kalmarium apps", sends a measurable share of app-site visits, and at least one tracked install per month per active app from `hub`.

**Realistic expectation**
- Will rank within 2-6 weeks: brand queries ("Kalmarium apps", "Kalmarium Services apps", "Kalmarium Android"). Volume is tiny today.
- App name + descriptor queries will (and should) land on the app sites, with the hub as a sitelink or second result.
- Will not rank from the hub: generic head terms (wifi analyzer android, mahjong solitaire, trivia quiz app, AZ-900 practice test). Those belong to the app sites and the later per-exam / per-tool / per-language pages.
- Honest forecast: under 50 organic visits per month to the hub in the first quarter. Its value is entity consolidation, internal links for the app sites, a credible destination for the Play "Website" button, and attribution data.

**Keyword opportunities (no volume data available; difficulty is judgement, as in the 22 Nov audit)**

| # | Keyword | Target page | Intent | Difficulty |
|---|---|---|---|---|
| 1 | kalmarium apps | hub `/` | navigational | Low |
| 2 | offline android games no pop-up ads | hub `/games/` | commercial | Medium |
| 3 | mahjong solitaire large tiles | mahjong365 site | install | Medium |
| 4 | mahjong daily challenge offline | mahjong365 site | install | Low-Medium |
| 5 | offline tank game android | tankageddon site | install | Medium-High |
| 6 | tank game with boss fights | tankageddon site | install | Low-Medium |
| 7 | daily quiz app fact-checked questions | knowdrop site | install | Low-Medium |
| 8 | vocabulary matching game android | lingua site | install | Medium |
| 9 | learn Hungarian words app | lingua site (later per-language page) | install | Low |
| 10 | parallel text epub reader | bilingua site | install | Low-Medium |
| 11 | read books in two languages app | bilingua site, hub `/learning/` | commercial | Medium |
| 12 | AI-103 / AB-900 / GH-900 practice questions | prep4cert (later per-exam pages) | install | Low |
| 13 | iperf3 android app | netcheck site (later per-tool page) | install | Low-Medium |
| 14 | family intercom app android wifi | intercom site, hub `/tools/` | install | Low-Medium |
| 15 | foldable phone crack prank | crackafold site | install | Low |

---

## E. Build checklist (two workers in parallel, no shared files)

Repo layout:
```
CNAME  robots.txt  sitemap.xml  app-ads.txt  README.md
index.html  games/index.html  learning/index.html  tools/index.html      (generated, committed)
privacy-policy.html  404.html  og.jpg
assets/site.css  assets/site.js  assets/logo.svg  assets/favicon.png
data/apps.json                      (single source of app facts and copy)
img/<id>/icon.webp tile.webp shot-1..3.webp      video/<id>.mp4 video/<id>-poster.webp
brand/play-header.html play-header-4096x2304.jpg dev-icon-512.png og.html
tools/build.py  tools/check.py      docs/PLAN.md docs/CONTRACT.md docs/PLAY-CONSOLE-SHEET.md
```
App ids (fixed): `knowdrop, mahjong365, tankageddon, lingua-pairs, bilingua, prep4cert, network-troubleshooter, lazy-intercom, crack-a-fold`.

**Step 0 - contract (lead, before the split, about 30 minutes):** create the repo locally, write `docs/CONTRACT.md`: the `data/apps.json` schema (id, name, descriptor, category, package, site, hook, bullets[3], price, audience, schemaType, offerPrice, accent, video{file,poster,youtube,duration,uploadDate}, aiArt:boolean, alt texts), the image/video file names and pixel sizes above, and the link/tag patterns from section B. Both workers read it; neither edits it without telling the other.

**Worker A - code and structure (owns: `assets/**`, `tools/**`, `index.html`, `games/`, `learning/`, `tools/` page output, `privacy-policy.html`, `404.html`, `CNAME`, `robots.txt`, `sitemap.xml`, `app-ads.txt`, `README.md`)**
1. `assets/site.css` from section C tokens (light + dark), catalogue layout, focus styles.
2. `assets/site.js`: the video facade only (click to create `<video>`), under 3 KB, no storage, no network calls.
3. `tools/build.py` (Python stdlib only): reads `data/apps.json`, writes the 4 pages with head block, JSON-LD `@graph`, cards, tagged links, visit script. Works with placeholder data until B delivers.
4. `privacy-policy.html` (short: no cookies, the "Website visits" paragraph from `site-fix-brief.md`, self-hosted video, outbound links to Google Play, contact), `404.html`, `robots.txt`, `sitemap.xml`, `app-ads.txt` (copy from an app site), `CNAME`.
5. `tools/check.py`: the acceptance tests below, exit code non-zero on any failure.
6. Integration: run the build on B's final data, fix, commit, push, enable Pages.

**Worker B - content, media and brand (owns: `data/apps.json`, `img/**`, `video/**`, `brand/**`, `og.jpg`, `assets/logo.svg`, `assets/favicon.png`, `docs/PLAY-CONSOLE-SHEET.md`; later the footer edits in the 9 app-site repos)**
1. Fill `data/apps.json` from the live app sites and store listings; every claim traceable to a source file; no ratings, downloads or reviews; no em-dashes.
2. Category page long copy (inside `apps.json` as `long` fields): 80-120 words per app, "who it is for", price.
3. Images: copy, crop and compress to the names and budgets in section B (Pillow). Mark `aiArt:true` where the source art is AI-generated (Crack A Fold art, Lingua Pairs feature and welcome art; check the others).
4. Video: install ffmpeg (winget `Gyan.FFmpeg`, with the owner's OK), re-encode the five clips, make posters.
5. Brand: `logo.svg`, `dev-icon-512.png`, `play-header.html` -> `play-header-4096x2304.jpg` (headless Chrome), `og.jpg` 1200 x 630.
6. `docs/PLAY-CONSOLE-SHEET.md`: the exact section A values and upload file paths for the owner.
7. After the hub is live: footer link patch in each app-site repo (one commit per repo, per `site-fix-brief.md` rules), including the missing Lazy Intercom footer, tags and visit script. The Mahjong365 site rebuild is its own task and should be assigned separately.

**Owner / lead steps (not the workers):** Wix DNS records; GitHub Pages custom domain + Enforce HTTPS; OverWatch app id `kalmarium-hub` (+ Lazy Intercom and Mahjong365 if missing); Play Console developer profile entry; Search Console sitemap; Wix "Apps" menu link.

**Order:** Step 0 -> A1-A5 in parallel with B1-B6 -> A6 integration -> DNS + Pages -> OverWatch id -> acceptance on the live URL -> Play profile Website -> B7 backlinks -> Search Console.

**Acceptance tests (all must pass on the live URL)**
1. `npx tsx scripts/check-site.ts https://apps.kalmarium.com` from C:\dev\overwatch: PASS on every line (no package argument, no `--ads`).
2. HTML validity: all 6 pages pass the Nu HTML checker (vnu.jar locally, or validator.w3.org/nu by URL) with 0 errors.
3. Links: every `href`/`src` resolves with HTTP 200 (internal and the 9 app sites and 9 Play listings); every Play link contains the right package id and `referrer=utm_source%3Dhub`.
4. JSON-LD parses as JSON; ItemList count is 9 on home and 3 per category page; no `aggregateRating`, `ratingValue`, `reviewCount` or `interactionCount` anywhere.
5. No purple: every hex, `rgb()` and `hsl()` colour in HTML, CSS and SVG has a hue outside 235-330 degrees (script in `check.py`); composed images reviewed by eye.
6. No em-dashes or en-dashes: no U+2014, U+2013, `&mdash;` or `&ndash;` in any HTML, CSS, JSON, TXT or MD file.
7. No third parties: no `<script src>`, `<link>`, `<img>`, `<iframe>`, font or CSS `url()` pointing off-site except `overwatch.kalmarium.com/h.js`; no `document.cookie`, `localStorage` or `sessionStorage` in the JS.
8. Weight: home first view under 450 KB and 25 requests; each image and video inside its budget; `og.jpg` under 150 KB and exactly 1200 x 630.
9. Lighthouse mobile (Chrome DevTools): Performance 95+, Accessibility 100, Best Practices 100, SEO 100; LCP under 1.8 s, CLS under 0.05.
10. Accessibility by hand: keyboard-only pass through nav, cards and video button; visible focus; contrast 4.5:1 in both themes; works at 320 px width and at 200 percent zoom; works with JS off (video becomes a link).
11. Head block per page: title 25-65 characters, description 70-170, one H1, self canonical, Open Graph complete.
12. Honesty review: each price/ads statement matches the app's current Play listing on the day of launch.
13. OverWatch: one test visit shows up under `kalmarium-hub` within minutes; Sites page shows score 100.

---

## F. Risks and owner decisions

Decisions needed (my recommendation first):
1. **Subdomain: `apps.kalmarium.com`.** Approve, and add the Wix DNS CNAME `apps` -> `gaborkalmar83.github.io`. In the same Wix session add `mahjong365` -> same target and rename `CNAME.pending` to `CNAME` in that repo. Certificates can take up to an hour or more; do not enter the URL in Play before HTTPS works.
2. **Featured app on the developer profile: Knowdrop.** Alternative: Mahjong365 (listing localised in 17 languages) once it has ratings.
3. **OverWatch id `kalmarium-hub`: yes.** Also confirm Lazy Intercom and Mahjong365 exist as apps in the live OverWatch database; they are not in `seed.ts`.
4. **Which apps count as live: the 9 listed.** Bilingua Tutor stays out. Arbor (sideloaded) stays out.
5. **Wix "Apps" menu link on kalmarium.com: yes.** It mixes the consulting brand with consumer apps; if that is unwanted, put the link in the Wix footer only.
6. **Generated images: none** (section C). Approve the single optional backdrop only after seeing the first build.
7. **ffmpeg install** on this PC for the video re-encode: approve, or accept posters with YouTube text links only.
8. **Company details in the footer:** Dutch companies must show their KvK number (and VAT id) on their website. Decide whether to print them on the hub; I recommend yes, it also reads as more trustworthy. Please confirm the exact legal requirement with your accountant; I have not verified it against the current rule text.

Risks:
- **Header crop on Play** is undocumented and differs per device. Mitigation: centre-safe composition, check the preview URL on phone and desktop before leaving it.
- **Two unfinished app sites** (Mahjong365 stub, Lazy Intercom missing tags and footer) will be linked from a page that claims a professional portfolio. Fix them in the same week or the hub exposes the gap.
- **Thin category pages.** If the long copy is skipped they add nothing; then ship the home page only.
- **Duplicate content with the app sites.** Card copy must be rewritten summaries, not pasted paragraphs.
- **Prices drift.** Crack A Fold is EUR 1.99 on its site and USD 1.79 in the US store; say "about EUR 1.99, varies by country". Re-check all price lines at launch.
- **Names and trademarks:** Prep 4 Cert uses "Microsoft" and exam codes descriptively: keep the "not an exam dump" line and add "Not affiliated with or endorsed by Microsoft" beside it on the hub. Mahjong365 can be confused with Microsoft 365 branding and with other "Mahjong 365" apps; Tankageddon shares its name with an unrelated game at tankageddon.com; "Bilingua" is used by other language products; Crack A Fold copy mentions foldable phone brands (keep it generic on the hub: "foldable phones"). Always pair names with descriptors, as the audit advised.
- **Honest numbers.** Several listings show "0+" or "1+" downloads. The hub shows none, and must not imply popularity ("loved by", "thousands of") anywhere.
- **Knowdrop ad format and subscription** are not fully described on its site; verify before writing the "How we build" claims, or scope each claim to the apps it is true for.
- **Bilingua's uninstall rate** (7 in 10 in the audit) is unresolved; the hub lists it but does not feature it first.
- **GitHub Pages** needs a public repo on a free plan; nothing private (keys, drafts, raw store folders) may be committed. Media adds about 12 MB, far below the limits.
- **Play profile edits** go live within 1 to 24 hours and need the owner's sign-in; workers must not touch any console.
