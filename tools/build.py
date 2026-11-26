#!/usr/bin/env python3
"""Build the Kalmarium Apps hub from data/apps.json. Python stdlib only.

Usage:  python tools/build.py [--root DIR] [--data FILE]

Writes index.html, games/index.html, learning/index.html, tools/index.html,
privacy-policy.html, 404.html and sitemap.xml into the repo root (or --root).
Missing image or video files never stop the build: the tags are still written
and tools/check.py reports the missing files.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imgsize import dims  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
VISIT = '<script defer src="https://overwatch.kalmarium.com/h.js" data-app="kalmarium-hub"></script>'
PRIVACY_DATE = "26 November 2026"
OG_W, OG_H = 1200, 630

# Title (25-65 chars) and description (70-170 chars) per page, from docs/PLAN.md section D.
SEO = {
    "home": ("Kalmarium Apps: Android Apps and Games by Kalmarium Services",
             "Nine Android apps and games by Kalmarium Services of Almere, the Netherlands: trivia, mahjong, a tank shooter, language learning, exam practice, network tools."),
    "about": ("About Kalmarium Services: Android Apps from the Netherlands",
              "Kalmarium Services B.V. is a small independent studio in Almere, the Netherlands, making Android apps and games for Google Play. Company facts and contact."),
    "press": ("Kalmarium Apps Press Kit: Icons, Screenshots and Facts",
              "Press kit for the nine Android apps by Kalmarium Services: icons, screenshots, the developer logo and one-line facts per app, free to use in articles."),
    "games": ("Android Games by Kalmarium: Trivia, Mahjong, Tank Shooter",
              "Three Android games you can play offline: Knowdrop trivia quiz, Mahjong365 solitaire and Tankageddon, a tank shooter with 99 boss fights."),
    "learning": ("Learning Apps for Android: Languages and Microsoft Exams",
                 "Learn words with the Lingua Pairs memory game, read books in two languages with Bilingua, and practise for 47 Microsoft certification exams with Prep 4 Cert."),
    "tools": ("Android Tools and Fun: WiFi Analyzer, Intercom, Fold Prank",
              "Ultimate Network Troubleshooter for WiFi and speed checks, Lazy Intercom for calling the family without shouting, and Crack A Fold, a prank for foldable phones."),
}
NAV_LABEL = {"games": "Games", "learning": "Learning", "tools": "Tools"}
BAD_DASH = {chr(0x2014): " - ", chr(0x2013): "-"}

E = lambda s: html.escape(str(s), quote=True)  # noqa: E731


def clean(obj, warn):
    """Replace em/en dashes in data strings (rule: plain hyphens only) and report it."""
    if isinstance(obj, str):
        out = obj
        for bad, good in BAD_DASH.items():
            if bad in out:
                warn.append("dash replaced in: " + obj[:60])
                out = out.replace(bad, good)
        return out
    if isinstance(obj, list):
        return [clean(x, warn) for x in obj]
    if isinstance(obj, dict):
        return {k: clean(v, warn) for k, v in obj.items()}
    return obj


class Site:
    def __init__(self, root, data_path):
        self.root = Path(root)
        self.warnings = []
        raw = json.loads(Path(data_path).read_text(encoding="utf-8"))
        data = clean(raw, self.warnings)
        self.site = data["site"]
        self.url = self.site["url"].rstrip("/")
        self.cats = data["categories"]
        for c in self.cats:
            # Display name: "name" if the data has it (then "title" is the page title), else "title".
            c["label"] = c.get("name") or c["title"]
            c["seo_title"] = c["title"] if "name" in c else None
            c["seo_desc"] = c.get("description")
        self.apps = data["apps"]
        self.byid = {a["id"]: a for a in self.apps}
        # Display order follows the category order, then the app order inside the file.
        order = []
        for c in self.cats:
            order += [a for a in self.apps if a["category"] == c["id"]]
        self.apps = order
        self.index = {a["id"]: i + 1 for i, a in enumerate(self.apps)}
        self.total = len(self.apps)
        self.ai_art = any(a.get("aiArt") for a in self.apps)
        self.lint()

    def lint(self):
        w = self.warnings.append
        for a in self.apps:
            if len(a.get("hook", "")) > 110:
                w("%s: hook over 110 chars" % a["id"])
            if len(a.get("bullets", [])) != 3:
                w("%s: expected 3 bullets" % a["id"])
            for b in a.get("bullets", []):
                if len(b) > 70:
                    w("%s: bullet over 70 chars: %s" % (a["id"], b[:40]))
            for k in ("name", "descriptor", "package", "site", "accent", "schemaType", "category"):
                if not a.get(k):
                    w("%s: missing %s" % (a["id"], k))

    # ---- file helpers -------------------------------------------------
    def exists(self, rel):
        return (self.root / rel.lstrip("/")).is_file()

    def size_of(self, rel, default):
        d = dims(self.root / rel.lstrip("/"))
        return d if d else default

    def lastmod(self):
        files = [self.root / "data" / "apps.json", Path(__file__), self.root / "assets" / "site.css"]
        t = max((f.stat().st_mtime for f in files if f.exists()), default=0)
        return datetime.date.fromtimestamp(t).isoformat() if t else datetime.date.today().isoformat()

    # ---- links --------------------------------------------------------
    def play(self, a, medium):
        return ("https://play.google.com/store/apps/details?id=%s&referrer=utm_source%%3Dhub%%26utm_medium%%3D%s"
                % (a["package"], medium))

    def playpage(self, a):
        return "https://play.google.com/store/apps/details?id=%s" % a["package"]

    def sitelink(self, a, medium):
        base = a["site"]
        return base + ("&" if "?" in base else "?") + "utm_source=hub&utm_medium=" + medium

    def abs(self, rel):
        return self.url + "/" + rel.lstrip("/")

    def cat_of(self, a):
        return next(c for c in self.cats if c["id"] == a["category"])


# ---------------------------------------------------------------- JSON-LD
def ld_script(graph):
    text = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json">%s</script>' % text.replace("</", "<\\/")


def ld_org(s):
    site = s.site
    same = [site["playDeveloper"]]
    if site.get("youtubeChannel"):
        same.append(site["youtubeChannel"])
    same.append("https://kalmarium.com")
    return {
        "@type": "Organization", "@id": s.url + "/#org", "name": site["org"], "legalName": site["legalName"],
        "alternateName": ["Kalmarium", "Kalmarium Apps"],
        "url": s.url + "/", "logo": s.abs("brand/dev-icon-512.png"), "email": site["email"],
        "description": "Independent studio in Almere, the Netherlands, making Android apps and games for Google Play.",
        "contactPoint": {"@type": "ContactPoint", "email": site["email"], "contactType": "customer support"},
        "address": {"@type": "PostalAddress", "addressLocality": site["city"], "addressCountry": site["country"]},
        "sameAs": same,
    }


def ld_website(s):
    return {"@type": "WebSite", "@id": s.url + "/#website", "name": s.site["name"], "url": s.url + "/",
            "publisher": {"@id": s.url + "/#org"}, "inLanguage": "en"}


def ld_app(s, a, medium):
    node = {
        "@type": a["schemaType"], "@id": a["site"] + "#app", "name": a["name"], "description": a["hook"], "operatingSystem": "Android",
        "applicationCategory": a["applicationCategory"], "url": a["site"], "installUrl": s.play(a, medium),
        "image": s.abs("img/%s/tile.webp" % a["id"]),
        "offers": {"@type": "Offer", "price": str(a["offerPrice"]), "priceCurrency": a.get("offerCurrency", "EUR")},
        "author": {"@id": s.url + "/#org"}, "publisher": {"@id": s.url + "/#org"}, "sameAs": [s.playpage(a)],
    }
    if a["schemaType"] == "VideoGame":
        node["gamePlatform"] = "Android"
    return node


def ld_video(s, a):
    v = a["video"]
    return {
        "@type": "VideoObject", "name": v.get("title") or a["name"] + " video", "description": v.get("description") or a["hook"],
        "thumbnailUrl": s.abs(v["poster"]), "uploadDate": v["uploadDate"], "contentUrl": s.abs(v["file"]),
        "duration": "PT%dS" % int(v["duration"]) if v.get("duration") else None,
        "width": v.get("width"), "height": v.get("height"),
    }


def ld_list(s, apps, medium, pageurl):
    return {"@type": "ItemList", "@id": pageurl + "#list", "numberOfItems": len(apps),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": ld_app(s, a, medium)} for i, a in enumerate(apps)]}


def compact(node):
    return {k: v for k, v in node.items() if v is not None}


# ---------------------------------------------------------------- chrome
def head(s, page, title, desc, path, graph=None, noindex=False):
    canon = s.url + path
    og = s.abs("og.jpg")
    lines = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>%s</title>" % E(title),
        '<meta name="description" content="%s">' % E(desc),
        '<link rel="canonical" href="%s">' % E(canon),
    ]
    if noindex:
        lines.append('<meta name="robots" content="noindex">')
    lines += [
        '<meta name="theme-color" content="#F4EFE6" media="(prefers-color-scheme: light)">',
        '<meta name="theme-color" content="#0E1416" media="(prefers-color-scheme: dark)">',
        '<meta name="color-scheme" content="light dark">',
        '<link rel="icon" type="image/png" href="/assets/favicon.png">',
        '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="%s">' % E(s.site["name"]),
        '<meta property="og:locale" content="en_US">',
        '<meta property="og:title" content="%s">' % E(title),
        '<meta property="og:description" content="%s">' % E(desc),
        '<meta property="og:url" content="%s">' % E(canon),
        '<meta property="og:image" content="%s">' % E(og),
        '<meta property="og:image:width" content="%d">' % OG_W,
        '<meta property="og:image:height" content="%d">' % OG_H,
        '<meta property="og:image:alt" content="Kalmarium Apps: Android apps and games by Kalmarium Services">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % E(title),
        '<meta name="twitter:description" content="%s">' % E(desc),
        '<meta name="twitter:image" content="%s">' % E(og),
        '<link rel="stylesheet" href="/assets/site.css">',
    ]
    if graph:
        lines.append(ld_script(graph))
    lines += ['<script defer src="/assets/site.js"></script>', VISIT]
    return "<head>\n" + "\n".join(lines) + "\n</head>"


def masthead(s, page):
    logo = ""
    if s.exists("assets/logo.svg"):
        logo = '<img src="/assets/logo.svg" width="30" height="30" alt="Kalmarium logo">'
    items = []
    for c in s.cats:
        label = NAV_LABEL.get(c["id"], c["label"])
        cur = ' aria-current="page"' if page == c["id"] else ""
        items.append('<li><a href="%s"%s>%s</a></li>' % (E(c["path"]), cur, E(label)))
    for pid, label in (("about", "About"), ("press", "Press")):
        cur = ' aria-current="page"' if page == pid else ""
        items.append('<li><a href="/%s/"%s>%s</a></li>' % (pid, cur, label))
    return (
        '<a class="skip" href="#main">Skip to content</a>\n'
        '<header class="mast"><div class="wrap bar">\n'
        '<a class="brand" href="/">%s<span>Kalmarium <i>Apps</i></span></a>\n'
        '<nav aria-label="Main"><ul>%s</ul></nav>\n</div></header>' % (logo, "".join(items))
    )


def app_label(a):
    return '%s<span class="d"> - %s</span>' % (E(a["name"]), E(a["descriptor"]))


def footer(s, page):
    apps = "".join(
        '<li><a href="%s">%s<span>&nbsp;- %s</span></a></li>' % (E(s.sitelink(a, page)), E(a["name"]), E(a["descriptor"]))
        for a in s.apps)
    browse = ['<li><a href="/">All apps</a></li>']
    browse += ['<li><a href="%s">%s</a></li>' % (E(c["path"]), E(c["label"])) for c in s.cats]
    browse.append('<li><a href="/about/">About</a></li>')
    browse.append('<li><a href="/press/">Press kit</a></li>')
    kal = ['<li><a href="%s">Google Play developer page</a></li>' % E(s.site["playDeveloper"]),
           '<li><a href="https://kalmarium.com">kalmarium.com</a></li>']
    if s.site.get("youtubeChannel"):
        kal.append('<li><a href="%s">YouTube channel</a></li>' % E(s.site["youtubeChannel"]))
    kal += ['<li><a href="/privacy-policy.html">Privacy policy</a></li>',
            '<li><a href="mailto:%s">%s</a></li>' % (E(s.site["email"]), E(s.site["email"]))]
    legal = ["<p>&copy; %s, %s, Netherlands. This website uses no cookies.</p>" % (E(s.site["legalName"]), E(s.site["city"]))]
    if "prep4cert" in s.byid:
        legal.append("<p>Prep 4 Cert offers original practice questions and is an independent product. "
                     "Not affiliated with or endorsed by Microsoft.</p>")
    legal.append("<p>Google Play and the Google Play logo are trademarks of Google LLC.</p>")
    if s.ai_art:
        legal.append("<p>%s</p>" % E(s.site.get("aiNote") or "Some artwork on this site is AI-generated."))
    return (
        '<footer class="foot"><div class="wrap">\n<div class="fcols">\n'
        '<nav class="apps" aria-label="App websites"><p class="fh">The apps and their sites</p><ul>%s</ul></nav>\n'
        '<nav aria-label="Browse"><p class="fh">Browse</p><ul>%s</ul></nav>\n'
        '<nav aria-label="Kalmarium"><p class="fh">Kalmarium</p><ul>%s</ul></nav>\n</div>\n'
        '<div class="legal">%s</div>\n</div></footer>' % (apps, "".join(browse), "".join(kal), "".join(legal))
    )


def page_shell(s, page, title, desc, path, main, graph=None, noindex=False):
    return (
        '<!doctype html>\n<html lang="en">\n%s\n<body>\n%s\n<main id="main">\n%s\n</main>\n%s\n</body>\n</html>\n'
        % (head(s, page, title, desc, path, graph, noindex), masthead(s, page), main, footer(s, page))
    )


# ---------------------------------------------------------------- app blocks
def img_tag(s, rel, alt, default, cls="", lazy=True, extra="", force=None):
    w, h = force or s.size_of(rel, default)
    return '<img%s src="/%s" width="%d" height="%d" alt="%s"%s decoding="async"%s>' % (
        ' class="%s"' % cls if cls else "", E(rel), w, h, E(alt), ' loading="lazy"' if lazy else "", extra)


def media_block(s, a, tall_ok=True):
    """Tile or video facade. Returns inner HTML of the <figure class="tile">."""
    alt = a.get("alt", {}).get("tile") or "%s on Android" % a["name"]
    v = a.get("video")
    parts = []
    if v:
        poster = v["poster"]
        vid_title = v.get("title") or a["name"] + " video"
        label = "Play video: %s" % vid_title
        w, h = v.get("width") or 1280, v.get("height") or 720
        tall = " tall" if h > w else ""
        parts.append(
            '<a class="vid%s" href="/%s" data-video="%s" aria-label="%s">%s<span class="play" aria-hidden="true"><i></i></span></a>'
            % (tall, E(v["file"]), E(label), E(label), img_tag(s, poster, alt, (800, 450))))
    else:
        parts.append(img_tag(s, "img/%s/tile.webp" % a["id"], alt, (800, 450)))
    if a.get("youtube"):
        parts.append('<figcaption><a href="https://www.youtube.com/watch?v=%s">Watch %s on YouTube</a></figcaption>'
                     % (E(a["youtube"]), E(a["name"])))
    return "".join(parts)


def buttons(s, a, medium):
    return (
        '<div class="btns">'
        '<a class="play-badge" href="%s" rel="noopener" aria-label="Get it on Google Play: %s">'
        '<img src="/img/google-play-badge.png" width="646" height="250" alt="Get it on Google Play" loading="lazy" decoding="async"></a>'
        '<a class="btn alt" href="%s" aria-label="More about %s, the %s, on its own website">More about %s</a></div>'
        % (E(s.play(a, medium)), E(a["name"]), E(s.sitelink(a, medium)), E(a["name"]), E(a["descriptor"]), E(a["name"]))
    )


def ms_note(a):
    if a["id"] != "prep4cert":
        return ""
    return '<p class="note">Original practice questions, not an exam dump. Not affiliated with or endorsed by Microsoft.</p>'


def entry_home(s, a, medium, flip):
    n = "%02d" % s.index[a["id"]]
    bullets = "".join("<li>%s</li>" % E(b) for b in a["bullets"])
    icon = img_tag(s, "img/%s/icon.webp" % a["id"], a.get("alt", {}).get("icon") or a["name"] + " app icon", (192, 192), force=(56, 56))
    return (
        '<article class="entry%s" id="%s" aria-labelledby="%s-h" style="--a:%s">\n'
        '<div class="txt">\n<p class="no" aria-hidden="true">%s<small>/ %02d</small></p>\n'
        '<div class="eh">%s<h3 id="%s-h"><a href="%s">%s</a></h3></div>\n'
        '<p class="hook">%s</p>\n<ul class="pts">%s</ul>\n'
        '<dl class="spec"><div><dt>Platform</dt><dd>Android</dd></div><div><dt>For</dt><dd>%s</dd></div>'
        '<div><dt>Price</dt><dd>%s</dd></div></dl>\n%s\n%s\n</div>\n'
        '<figure class="tile">%s</figure>\n</article>'
        % (" flip" if flip else "", E(a["id"]), E(a["id"]), E(a["accent"]), n, s.total, icon, E(a["id"]),
           E(s.sitelink(a, medium)), app_label(a), E(a["hook"]), bullets, E(a["audience"]), E(a["price"]),
           ms_note(a), buttons(s, a, medium), media_block(s, a))
    )


def entry_deep(s, a, medium, flip):
    n = "%02d" % s.index[a["id"]]
    bullets = "".join("<li>%s</li>" % E(b) for b in a["bullets"])
    icon = img_tag(s, "img/%s/icon.webp" % a["id"], a.get("alt", {}).get("icon") or a["name"] + " app icon", (192, 192), force=(56, 56))
    shots = ""
    alts = a.get("alt", {}).get("shots") or []
    imgs = []
    for i, alt in enumerate(alts[:3], 1):
        imgs.append(img_tag(s, "img/%s/shot-%d.webp" % (a["id"], i), alt, (360, 780)))
    if imgs:
        shots = '<div class="shots">%s</div>' % "".join(imgs)
    return (
        '<article class="deep%s" id="%s" aria-labelledby="%s-h" style="--a:%s">\n'
        '<header class="dh"><p class="no" aria-hidden="true">%s</p>%s<h2 id="%s-h"><a href="%s">%s</a></h2></header>\n'
        '<div class="dgrid">\n<div class="txt">\n<p class="hook">%s</p>\n<p>%s</p>\n'
        '<h3>What you get</h3>\n<ul class="pts">%s</ul>\n'
        '<h3>Who it is for</h3>\n<p>%s</p>\n<h3>Price</h3>\n<p>%s</p>\n%s\n%s\n</div>\n'
        '<div class="media"><figure class="tile">%s</figure>%s</div>\n</div>\n</article>'
        % (" flip" if flip else "", E(a["id"]), E(a["id"]), E(a["accent"]), n, icon, E(a["id"]),
           E(s.sitelink(a, medium)), app_label(a), E(a["hook"]), E(a.get("long", "")), bullets,
           E(a.get("who", a["audience"])), E(a["price"]), ms_note(a), buttons(s, a, medium),
           media_block(s, a), shots)
    )


# ---------------------------------------------------------------- pages
HOW = [
    ("No account to start", "Open any of the apps and use it. None of them asks you to sign up first."),
    ("No forced subscription", "The core of each app works without a subscription. Anything paid is optional and listed on the store page."),
    ("Ads you can remove", "Where an app shows ads, a purchase turns them off. Some of the apps have no ads at all."),
    ("No cookies on this site", "This website sets no cookies and stores nothing on your device."),
]


def first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return m.group(1) if m else text.strip()


NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
NOUN = {"games": "games", "learning": "learning apps", "tools": "tools"}


def lede(s):
    parts = []
    for c in s.cats:
        k = len([a for a in s.apps if a["category"] == c["id"]])
        if k:
            parts.append("%s %s" % (NUM.get(k, k), NOUN.get(c["id"], c["label"].lower())))
    listing = ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else "".join(parts)
    return "%s small Android apps from one independent studio in the Netherlands: %s, all on Google Play." % (
        str(NUM.get(s.total, s.total)).capitalize(), listing)


def about_html(s, home=True):
    site = s.site
    text = site.get("about")
    if not text:
        text = ("%s is a one-person studio in %s, the Netherlands. It makes small Android apps and games and publishes them on Google Play. "
                "Each app has its own website and privacy policy; this site is the catalogue that ties them together. "
                "Questions, bug reports and ideas are welcome by email." % (site["legalName"], site["city"]))
    out = []
    for para in text.split("\n\n"):
        h = E(para)
        h = h.replace(E(site["email"]), '<a href="mailto:%s">%s</a>' % (E(site["email"]), E(site["email"])))
        out.append("<p>%s</p>" % h)
    if home:
        out.append('<p><a href="/about/">More about Kalmarium Services</a> &middot; <a href="/press/">Press kit</a></p>')
    return "\n".join(out)


def page_home(s):
    title = s.site.get("homeTitle") or SEO["home"][0]
    desc = s.site.get("homeDescription") or SEO["home"][1]
    n = s.total
    strip = "".join(
        '<li><a href="#%s"><b aria-hidden="true">%02d</b>%s<span aria-hidden="true">%s</span></a></li>'
        % (E(a["id"]), s.index[a["id"]],
           img_tag(s, "img/%s/icon.webp" % a["id"], a.get("alt", {}).get("icon") or a["name"] + " app icon", (192, 192), lazy=False,
                   force=(80, 80)),
           E(a["name"]))
        for a in s.apps)
    cats_html = []
    k = 0
    for c in s.cats:
        capps = [a for a in s.apps if a["category"] == c["id"]]
        if not capps:
            continue
        rows = []
        for a in capps:
            rows.append(entry_home(s, a, "home", k % 2 == 1))
            k += 1
        first, last = s.index[capps[0]["id"]], s.index[capps[-1]["id"]]
        rng = "Entries %02d-%02d" % (first, last) if first != last else "Entry %02d" % first
        cats_html.append(
            '<section class="wrap cat" id="cat-%s" aria-labelledby="cat-%s-h">\n'
            '<div class="cat-h"><h2 id="cat-%s-h">%s</h2><p>%s &middot; <a href="%s">See the %s page</a></p></div>\n'
            '<p class="cat-i">%s</p>\n%s\n</section>'
            % (E(c["id"]), E(c["id"]), E(c["id"]), E(c["label"]), rng, E(c["path"]), E(c["label"]),
               E(first_sentence(c["intro"])), "\n".join(rows)))
    site = s.site
    facts = [(f["title"], f["text"]) for f in site.get("howWeBuild", [])] or HOW
    how = "".join('<li><span>%02d</span><b>%s</b><p>%s</p></li>' % (i + 1, E(h), E(t)) for i, (h, t) in enumerate(facts))
    h1 = site.get("h1") or "Android apps and games by Kalmarium"
    m = re.match(r"(.*?)\s+(by \S+)$", h1)
    h1_html = "%s <em>%s</em>" % (E(m.group(1)), E(m.group(2))) if m else E(h1)
    about = (
        '<section class="wrap about" id="about" aria-labelledby="about-h">\n<div>\n<h2 id="about-h">About %s</h2>\n'
        '%s\n</div>\n'
        '<dl class="co"><dt>Company</dt><dd>%s</dd><dt>Based in</dt><dd>%s, Netherlands</dd>'
        '<dt>Email</dt><dd><a href="mailto:%s">%s</a></dd><dt>On Google Play</dt><dd><a href="%s">Kalmarium Services</a></dd></dl>\n</section>'
        % (E(site["org"]), about_html(s), E(site["legalName"]), E(site["city"]),
           E(site["email"]), E(site["email"]), E(site["playDeveloper"])))
    main = (
        '<section class="wrap hero" aria-labelledby="top-h">\n'
        '<p class="kicker">The catalogue &middot; %d apps &middot; Android</p>\n'
        '<h1 id="top-h">%s</h1>\n'
        '<p class="lede">%s</p>\n<ol class="strip" aria-label="All apps">%s</ol>\n<div class="ruler" aria-hidden="true"></div>\n</section>\n'
        '%s\n<section class="band" aria-labelledby="how-h"><div class="wrap">\n<h2 id="how-h">How we build</h2>\n<ol>%s</ol>\n</div></section>\n%s'
        % (n, h1_html, E(site.get("lead") or lede(s)),
           strip, "\n".join(cats_html), how, about))
    graph = [ld_org(s), ld_website(s), ld_list(s, s.apps, "home", s.url + "/")]
    graph += [compact(ld_video(s, a)) for a in s.apps if a.get("video")]
    return page_shell(s, "home", title, desc, "/", main, graph)


def page_category(s, c):
    cid = c["id"]
    dflt = SEO.get(cid, (c["label"] + " by Kalmarium", c.get("intro", "")[:160]))
    title = c.get("seo_title") or dflt[0]
    desc = c.get("seo_desc") or dflt[1]
    capps = [a for a in s.apps if a["category"] == cid]
    crumbs = ('<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">%s</span></nav>'
              % E(c["label"]))
    cross = ""
    intro = E(c["intro"])
    if cid == "games" and "lingua-pairs" in s.byid:
        link = '<a href="/learning/#lingua-pairs">Lingua Pairs</a>'
        if "Lingua Pairs" in intro:
            intro = intro.replace("Lingua Pairs", link, 1)  # the intro already mentions it: link that mention
        else:
            cross = ('<p class="cross">Looking for Lingua Pairs, the language memory game? It lives under '
                     '<a href="/learning/#lingua-pairs">Learning</a>.</p>')
    deeps = "\n".join(entry_deep(s, a, cid, i % 2 == 1) for i, a in enumerate(capps))
    pick_rows = "".join('<div><dt><a href="#%s">%s</a></dt><dd>%s</dd></div>'
                        % (E(a["id"]), E(a["name"]), E(a.get("pick", a["hook"]))) for a in capps)
    faq = c.get("faq") or []
    faq_html = "".join("<h3>%s</h3>\n<p>%s</p>\n" % (E(f["q"]), E(f["a"])) for f in faq)
    others = " &middot; ".join('<a href="%s">%s</a>' % (E(o["path"]), E(o["label"])) for o in s.cats if o["id"] != cid)
    main = (
        '<div class="wrap phead">\n%s\n<h1>%s</h1>\n<p class="lede">%s</p>\n%s\n</div>\n'
        '<div class="wrap">\n%s\n'
        '<section class="pick" aria-labelledby="pick-h">\n<h2 id="pick-h">Which one should I pick?</h2>\n<dl>%s</dl>\n%s</section>\n'
        '<p class="others">More from the catalogue: %s &middot; <a href="/">All apps</a></p>\n</div>'
        % (crumbs, E(c["h1"]), intro, cross, deeps, pick_rows, faq_html, others))
    path = c["path"]
    pageurl = s.url + path
    graph = [ld_org(s), ld_website(s),
             {"@type": "BreadcrumbList", "@id": pageurl + "#crumbs", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": s.url + "/"},
                 {"@type": "ListItem", "position": 2, "name": c["label"], "item": pageurl}]},
             ld_list(s, capps, cid, pageurl)]
    graph += [compact(ld_video(s, a)) for a in capps if a.get("video")]
    if faq:
        graph.append({"@type": "FAQPage", "@id": pageurl + "#faq", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    return page_shell(s, cid, title, desc, path, main, graph)


def crumbs(label):
    return ('<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">%s</span></nav>' % E(label))


def crumb_ld(s, label, path):
    pageurl = s.url + path
    return {"@type": "BreadcrumbList", "@id": pageurl + "#crumbs", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": s.url + "/"},
        {"@type": "ListItem", "position": 2, "name": label, "item": pageurl}]}


def page_about(s):
    site = s.site
    title, desc = SEO["about"]
    paras = about_html(s, home=False)
    rows = "".join(
        '<tr><th scope="row"><a href="%s">%s</a></th><td data-l="What it does">%s</td><td data-l="Price">%s</td>'
        '<td data-l="Links"><a href="%s">Website</a> &middot; <a href="%s" rel="noopener">Google Play</a></td></tr>'
        % (E(s.sitelink(a, "about")), E(a["name"]), E(a["hook"]), E(a["price"]), E(s.sitelink(a, "about")), E(s.play(a, "about")))
        for a in s.apps)
    facts = site.get("howWeBuild", [])
    how = "".join("<li><b>%s.</b> %s</li>" % (E(f["title"]), E(f["text"])) for f in facts)
    yt = ""
    if site.get("youtubeChannel"):
        yt = '<dt>YouTube</dt><dd><a href="%s">@kalmariumservices</a></dd>' % E(site["youtubeChannel"])
    co = (
        '<dl class="co"><dt>Legal name</dt><dd>%s</dd><dt>Based in</dt><dd>%s, Netherlands</dd>'
        '<dt>Email</dt><dd><a href="mailto:%s">%s</a></dd><dt>On Google Play</dt><dd><a href="%s">Kalmarium Services</a></dd>%s'
        '<dt>Company website</dt><dd><a href="https://kalmarium.com">kalmarium.com</a></dd></dl>'
        % (E(site["legalName"]), E(site["city"]), E(site["email"]), E(site["email"]), E(site["playDeveloper"]), yt))
    ai = E(site.get("aiNote") or "Some artwork on this site is AI-generated.")
    main = (
        '<div class="wrap phead">\n%s\n<h1>About Kalmarium Services</h1>\n'
        '<p class="lede">An independent Android studio in Almere, the Netherlands, with nine apps and games on Google Play.</p>\n</div>\n'
        '<div class="wrap doc wide">\n<h2>Who we are</h2>\n%s\n'
        '<h2>The nine apps</h2>\n<table class="tbl"><thead><tr><th scope="col">App</th><th scope="col">What it does</th>'
        '<th scope="col">Price</th><th scope="col">Links</th></tr></thead><tbody>%s</tbody></table>\n'
        '<h2>How we build</h2>\n<ul class="pts">%s</ul>\n'
        '<h2>Company facts</h2>\n%s\n'
        '<h2>Privacy and AI</h2>\n<p>Each app has its own privacy policy on its own website. This website has a short '
        '<a href="/privacy-policy.html">privacy policy</a> of its own. %s We mark the apps with AI-generated artwork on the <a href="/press/">press page</a>.</p>\n</div>'
        % (crumbs("About"), paras, rows, how, co, ai))
    graph = [ld_org(s), ld_website(s),
             {"@type": "AboutPage", "@id": s.url + "/about/#page", "url": s.url + "/about/", "name": title,
              "isPartOf": {"@id": s.url + "/#website"}, "about": {"@id": s.url + "/#org"}, "inLanguage": "en"},
             crumb_ld(s, "About", "/about/")]
    return page_shell(s, "about", title, desc, "/about/", main, graph)


def kb(n):
    return "%d KB" % max(1, round(n / 1024))


def press_files(s, a):
    """Press-kit files for one app: (label, path, 'W x H', bytes, format)."""
    out = []
    items = [("Icon", "img/press/%s/icon-512.png" % a["id"])]
    items += [("Screenshot %d" % i, "img/press/%s/screenshot-%d.jpg" % (a["id"], i)) for i in (1, 2, 3)]
    for label, rel in items:
        p = s.root / rel
        d = dims(p)
        n = p.stat().st_size if p.is_file() else 0
        out.append((label, "/" + rel, "%d x %d" % d if d else "", n, rel.rsplit(".", 1)[1].upper()))
    return out


def fsz(s, rel):
    p = s.root / rel
    return p.stat().st_size if p.is_file() else 0


def page_press(s):
    site = s.site
    title, desc = SEO["press"]
    blocks = []
    for a in s.apps:
        spec = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (k, v)
                       for k, v in (("Platform", "Android"), ("Price", E(a["price"])), ("For", E(a["audience"]))))
        spec += ('<div><dt>Package</dt><dd>%s</dd></div><div><dt>Site</dt><dd><a href="%s">%s</a></dd></div>'
                 '<div><dt>Play</dt><dd><a href="%s" rel="noopener">%s on Google Play</a></dd></div>'
                 % (E(a["package"]), E(s.sitelink(a, "press")), E(a["site"].replace("https://", "").rstrip("/")),
                    E(s.play(a, "press")), E(a["name"])))
        if a.get("aiArt"):
            spec += "<div><dt>Art</dt><dd>Some of the artwork is AI-generated.</dd></div>"
        dl = "".join('<li><a href="%s">%s %s</a>, %s %s, %s</li>' % (E(path), E(a["name"]), label.lower(), dim, fmt, kb(n))
                     for label, path, dim, n, fmt in press_files(s, a))
        icon = img_tag(s, "img/%s/icon.webp" % a["id"], a.get("alt", {}).get("icon") or a["name"] + " app icon", (192, 192), force=(56, 56))
        blocks.append(
            '<article class="deep" id="%s" aria-labelledby="%s-h" style="--a:%s">\n'
            '<header class="dh">%s<h2 id="%s-h">%s<span class="d"> - %s</span></h2></header>\n'
            '<p class="hook">%s</p>\n<dl class="spec">%s</dl>\n<ul class="pts">%s</ul>\n</article>'
            % (E(a["id"]), E(a["id"]), E(a["accent"]), icon, E(a["id"]), E(a["name"]), E(a["descriptor"]), E(a["hook"]), spec, dl))
    dev = (
        '<ul class="pts"><li><a href="/brand/dev-icon-512.png">Developer icon</a>, 512 x 512 PNG, %s</li>'
        '<li><a href="/brand/play-header-4096x2304.jpg">Developer header</a>, 4096 x 2304 JPG, %s</li>'
        '<li><a href="/assets/logo.svg">Kalmarium logo</a>, SVG, %s</li></ul>'
        % (kb(fsz(s, "brand/dev-icon-512.png")), kb(fsz(s, "brand/play-header-4096x2304.jpg")), kb(fsz(s, "assets/logo.svg"))))
    main = (
        '<div class="wrap phead">\n%s\n<h1>Press kit</h1>\n'
        '<p class="lede">Icons, screenshots and plain facts for the nine Android apps by Kalmarium Services. Free to use in articles and reviews about the apps. '
        'Please do not alter the icons. There are no ratings or download numbers here because we do not publish any.</p>\n</div>\n'
        '<div class="wrap">\n<section class="deep" aria-labelledby="dev-h">\n<h2 id="dev-h">Kalmarium Services</h2>\n'
        '<p class="hook">Independent studio in %s, the Netherlands. Apps and games for Android, published on Google Play.</p>\n%s\n'
        '<p>Press contact: <a href="mailto:%s">%s</a>. More about us on the <a href="/about/">About page</a>.</p>\n</section>\n%s\n</div>'
        % (crumbs("Press kit"), E(site["city"]), dev, E(site["email"]), E(site["email"]), "\n".join(blocks)))
    graph = [ld_org(s), ld_website(s),
             {"@type": "CollectionPage", "@id": s.url + "/press/#page", "url": s.url + "/press/", "name": title,
              "isPartOf": {"@id": s.url + "/#website"}, "about": {"@id": s.url + "/#org"}, "inLanguage": "en"},
             crumb_ld(s, "Press kit", "/press/")]
    return page_shell(s, "press", title, desc, "/press/", main, graph)


def page_privacy(s):
    site = s.site
    email = E(site["email"])
    main = (
        '<div class="wrap"><div class="doc">\n<h1>Privacy policy</h1>\n'
        '<p class="lede">For the website %s. Last updated: %s.</p>\n'
        '<p>This website is run by %s, %s, the Netherlands (&ldquo;we&rdquo;). We are the controller for the data described here.</p>\n'
        '<h2>In short</h2>\n<p>This website sets no cookies, has no accounts, no forms, no advertising and no third-party scripts or fonts. '
        'It only counts page views with a script that stores nothing on your device.</p>\n'
        '<h2>Website visits</h2>\n'
        '<p>This website counts page views with a cookie-free script that stores nothing on your device and sends only the page address, '
        'the referring website and the country (derived from your network address, which is not kept). It is switched off if your browser sends Do Not Track.</p>\n'
        '<h2>Hosting</h2>\n<p>The site is hosted on GitHub Pages. As with any website, the host receives your network address when your browser asks for a page, '
        'and may keep it in its own server logs under its own policy. We do not receive those logs.</p>\n'
        '<h2>Video</h2>\n<p>Videos on this site are files that we host ourselves. Nothing is loaded from a video service. A video starts loading only when you press play. '
        'Some entries also link to a video on YouTube; that is an ordinary link, and YouTube applies its own policy if you follow it.</p>\n'
        '<h2>Links to other websites</h2>\n<p>The links to Google Play, to the website of each app, to kalmarium.com and to YouTube lead to other sites. '
        'Links to Google Play carry a campaign tag (utm_source=hub) so that we can see which page an install came from. The tag does not identify you. '
        'Each app has its own privacy policy on its own website.</p>\n'
        '<h2>Your rights</h2>\n<p>Because we keep no personal data about visitors to this site, there is usually nothing to access, correct or delete. '
        'If you think we hold data about you, write to us and we will answer. You can also complain to the Dutch data protection authority (Autoriteit Persoonsgegevens).</p>\n'
        '<h2>Changes and contact</h2>\n<p>If this policy changes, the new version will be published on this page with a new date. '
        'Questions: <a href="mailto:%s">%s</a>.</p>\n</div></div>'
        % (E(s.url.replace("https://", "")), PRIVACY_DATE, E(site["legalName"]), E(site["city"]), email, email))
    return page_shell(s, "privacy", "Privacy Policy - Kalmarium Apps",
                      "How the Kalmarium Apps website handles data: no cookies, no accounts, a cookie-free visit counter, self-hosted video and links to Google Play.",
                      "/privacy-policy.html", main, [ld_org(s), ld_website(s)])


def page_404(s):
    links = "".join('<li><a href="%s">%s</a></li>' % (E(c["path"]), E(c["label"])) for c in s.cats)
    main = (
        '<div class="wrap"><div class="doc">\n<p class="kicker">Error 404</p>\n<h1>Page not found</h1>\n'
        '<p class="lede">That page is not in the catalogue. It may have moved, or the address may have a typo.</p>\n'
        '<div class="btns"><a class="btn" href="/">Back to all apps</a></div>\n'
        '<h2>Or browse by category</h2>\n<ul class="pts">%s</ul>\n</div></div>' % links)
    return page_shell(s, "404", "Page not found - Kalmarium Apps",
                      "This page does not exist. Go back to the Kalmarium Apps catalogue of Android games, learning apps and tools.",
                      "/404.html", main, None, noindex=True)


def esc_x(v):
    return html.escape(str(v), quote=False)


def sitemap(s, pages):
    """pages: list of (url, html text). lastmod moves only when a page's text changes (ledger in data/lastmod.json)."""
    import hashlib
    ledger_p = s.root / "data" / "lastmod.json"
    ledger = json.loads(ledger_p.read_text(encoding="utf-8")) if ledger_p.is_file() else {}
    today = datetime.date.today().isoformat()
    out = {}
    body = []
    for url, text in pages:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        old = ledger.get(url)
        out[url] = old if old and old["hash"] == h else {"hash": h, "date": today}
        vids = ""
        cat = next((c for c in s.cats if s.url + c["path"] == url), None)
        for a in s.apps:
            v = a.get("video")
            if v and (url == s.url + "/" or (cat and a["category"] == cat["id"])):
                vids += ("<video:video><video:thumbnail_loc>%s</video:thumbnail_loc><video:title>%s</video:title>"
                         "<video:description>%s</video:description><video:content_loc>%s</video:content_loc>"
                         "<video:duration>%d</video:duration><video:publication_date>%s</video:publication_date></video:video>"
                         % (esc_x(s.abs(v["poster"])), esc_x(v.get("title") or a["name"] + " video"), esc_x(v.get("description") or a["hook"]),
                            esc_x(s.abs(v["file"])), int(v.get("duration") or 0), esc_x(v["uploadDate"])))
        body.append("  <url><loc>%s</loc><lastmod>%s</lastmod>%s</url>\n" % (url, out[url]["date"], vids))
    text = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n%s</urlset>\n' % "".join(body))
    return text, json.dumps(out, indent=1, sort_keys=True) + "\n"


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and p.read_text(encoding="utf-8") == text:
        return False
    p.write_text(text, encoding="utf-8", newline="\n")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(REPO), help="site root (default: the repo)")
    ap.add_argument("--data", default=None, help="data file (default: <root>/data/apps.json)")
    args = ap.parse_args(argv)
    root = Path(args.root)
    data = Path(args.data) if args.data else root / "data" / "apps.json"
    if not data.is_file():
        print("ERROR: %s not found" % data, file=sys.stderr)
        return 2
    s = Site(root, data)
    outputs = {"index.html": page_home(s), "about/index.html": page_about(s), "press/index.html": page_press(s),
               "privacy-policy.html": page_privacy(s), "404.html": page_404(s)}
    for c in s.cats:
        outputs[c["path"].strip("/") + "/index.html"] = page_category(s, c)
    order = ["index.html"] + [c["path"].strip("/") + "/index.html" for c in s.cats] + ["about/index.html", "press/index.html", "privacy-policy.html"]
    urls = {"index.html": "/", "about/index.html": "/about/", "press/index.html": "/press/", "privacy-policy.html": "/privacy-policy.html"}
    for c in s.cats:
        urls[c["path"].strip("/") + "/index.html"] = c["path"]
    sm, ledger = sitemap(s, [(s.url + urls[r], outputs[r]) for r in order])
    outputs["sitemap.xml"] = sm
    outputs["data/lastmod.json"] = ledger
    for rel, text in outputs.items():
        changed = write(root, rel, text)
        print("%-24s %6d bytes%s" % (rel, len(text.encode("utf-8")), "" if changed else " (unchanged)"))
    for w in s.warnings:
        print("WARNING:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
