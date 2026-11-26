#!/usr/bin/env python3
"""Acceptance tests for the Kalmarium Apps hub (docs/PLAN.md section E). Python stdlib only.

Usage:  python tools/check.py [--live] [--root DIR] [--vnu PATH]

Offline mode checks the files in the repo. --live also fetches https://apps.kalmarium.com
and the app and Google Play links. Prints PASS / FAIL / SKIP per line; exit code 1 on any FAIL.
SKIP means the test needs a human, a browser tool or a service that is not available here.
"""
import argparse
import colorsys
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imgsize import dims  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SITE = "https://apps.kalmarium.com"
VISIT_SRC = "https://overwatch.kalmarium.com/h.js"
ADS_LINE = "google.com, pub-6479185943494314, DIRECT, f08c47fec0942fa0"
PAGES = ["index.html", "games/index.html", "learning/index.html", "tools/index.html", "about/index.html", "press/index.html",
         "privacy-policy.html", "404.html"]
CAT_PAGES = {"games": "games/index.html", "learning": "learning/index.html", "tools": "tools/index.html"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BUDGET = {"css": 14 * 1024, "js": 3 * 1024, "html": 40 * 1024, "icon": 12 * 1024, "tile": 60 * 1024,
          "shot": 25 * 1024, "poster": 45 * 1024, "video": 2500 * 1024, "og": 150 * 1024, "first_view": 450 * 1024}
TEXT_EXT = {".html", ".css", ".js", ".json", ".txt", ".md", ".xml", ".svg", ".py", ".csv", ".webmanifest"}
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

RESULTS = []


def rec(status, test, msg):
    RESULTS.append((status, test, msg))
    print("%-5s %-4s %s" % (status, test, msg))


def ok_or_fail(test, problems, ok_msg):
    if problems:
        shown = problems[:12]
        rec("FAIL", test, "%d problem(s)" % len(problems))
        for p in shown:
            print("        - " + p)
        if len(problems) > len(shown):
            print("        - ... and %d more" % (len(problems) - len(shown)))
    else:
        rec("PASS", test, ok_msg)


# ------------------------------------------------------------------ html model
class Doc(HTMLParser):
    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.tags = []        # (tag, attrs dict, line)
        self.text = []
        self.ld = []
        self.errors = []
        self.stack = []
        self._in = None
        self._buf = []
        self.title = ""
        self.src = src
        self.feed(src)
        self.close()
        for t, line in self.stack:
            self.errors.append("line %d: <%s> never closed" % (line, t))

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        self.tags.append((tag, a, self.getpos()[0]))
        if tag in ("script", "style", "title"):
            self._in = (tag, a)
            self._buf = []
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        self.tags.append((tag, a, self.getpos()[0]))

    def handle_endtag(self, tag):
        if self._in and self._in[0] == tag:
            body = "".join(self._buf)
            if tag == "title":
                self.title = body.strip()
            elif tag == "script" and "ld+json" in self._in[1].get("type", ""):
                self.ld.append(body)
            self._in = None
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.errors.append("line %d: unexpected </%s>" % (self.getpos()[0], tag))
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)
        else:
            self.text.append(data)

    def of(self, tag):
        return [(a, ln) for t, a, ln in self.tags if t == tag]

    def meta(self, key, by="name"):
        for a, _ in self.of("meta"):
            if a.get(by, "").lower() == key:
                return a.get("content", "")
        return None

    def link(self, rel):
        for a, _ in self.of("link"):
            if rel in a.get("rel", "").lower().split():
                return a.get("href")
        return None

    @property
    def visible(self):
        return re.sub(r"\s+", " ", " ".join(self.text))


def read(root, rel):
    return (root / rel).read_text(encoding="utf-8")


def to_path(root, url, base_rel):
    """Map an internal URL to a repo file. Returns (Path, fragment) or (None, None)."""
    u = urllib.parse.urlsplit(url)
    if u.scheme or u.netloc:
        if u.netloc != "apps.kalmarium.com":
            return None, None
    p = u.path
    if not p:
        p = "/" + base_rel if base_rel != "index.html" else "/"
    if not p.startswith("/"):
        base_dir = os.path.dirname(base_rel)
        p = "/" + os.path.normpath(os.path.join(base_dir, p)).replace("\\", "/")
    if p.endswith("/"):
        p += "index.html"
    return root / p.lstrip("/"), u.fragment


# ------------------------------------------------------------------ colours
NAMED_BAD = ["purple", "violet", "indigo", "magenta", "fuchsia", "orchid", "plum", "lavender", "thistle", "slateblue",
             "blueviolet", "darkviolet", "mediumpurple", "rebeccapurple", "darkorchid", "mediumorchid", "darkmagenta",
             "mediumslateblue", "darkslateblue", "blue", "navy", "mediumblue", "darkblue"]


def hue_of(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s, l


def find_colours(text):
    out = []
    for m in re.finditer(r"(?<![\w&#/-])#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])", text):
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        out.append((m.group(0), tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))))
    for m in re.finditer(r"rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)", text):
        out.append((m.group(0), tuple(int(float(m.group(i))) for i in (1, 2, 3))))
    for m in re.finditer(r"hsla?\(\s*([\d.]+)(?:deg)?[ ,]+([\d.]+)%[ ,]+([\d.]+)%", text):
        hh, ss, ll = float(m.group(1)), float(m.group(2)) / 100, float(m.group(3)) / 100
        r, g, b = colorsys.hls_to_rgb(hh / 360, ll, ss)
        out.append((m.group(0), (round(r * 255), round(g * 255), round(b * 255))))
    return out


def bad_hue(rgb):
    h, s, l = hue_of(*rgb)
    return 235 <= h <= 330 and s > 0.08 and 0.02 < l < 0.98


def lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------ main checks
def load_data(root):
    return json.loads((root / "data" / "apps.json").read_text(encoding="utf-8"))


def all_files(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith("chrome-profile")]
        for f in fn:
            yield Path(dp) / f


def test_build_current(root, data):
    import build
    s = build.Site(root, root / "data" / "apps.json")
    expect = {"index.html": build.page_home(s), "about/index.html": build.page_about(s), "press/index.html": build.page_press(s),
              "privacy-policy.html": build.page_privacy(s), "404.html": build.page_404(s)}
    for c in s.cats:
        expect[c["path"].strip("/") + "/index.html"] = build.page_category(s, c)
    bad = []
    for rel, text in expect.items():
        p = root / rel
        if not p.exists():
            bad.append("%s missing (run tools/build.py)" % rel)
        elif p.read_text(encoding="utf-8") != text:
            bad.append("%s differs from a fresh build (run tools/build.py)" % rel)
    ok_or_fail("T00", bad + ["build warning: " + w for w in s.warnings], "generated pages match a fresh build, data lint clean")


def test_static_files(root, data):
    bad = []
    cname = root / "CNAME"
    if not cname.exists() or cname.read_text().strip() != "apps.kalmarium.com":
        bad.append("CNAME must contain apps.kalmarium.com")
    rb = root / "robots.txt"
    if not rb.exists():
        bad.append("robots.txt missing")
    else:
        t = rb.read_text()
        if "User-agent: *" not in t or "Allow: /" not in t or "Sitemap: %s/sitemap.xml" % SITE not in t:
            bad.append("robots.txt must allow all and name the sitemap")
    ads = root / "app-ads.txt"
    if not ads.exists() or ADS_LINE not in ads.read_text():
        bad.append("app-ads.txt must contain the publisher line")
    sm = root / "sitemap.xml"
    if not sm.exists():
        bad.append("sitemap.xml missing")
    else:
        locs = re.findall(r"<loc>([^<]+)</loc>", sm.read_text())
        want = [SITE + "/", SITE + "/games/", SITE + "/learning/", SITE + "/tools/", SITE + "/about/", SITE + "/press/",
                SITE + "/privacy-policy.html"]
        if locs != want:
            bad.append("sitemap.xml lists %s, expected %s" % (locs, want))
        if not re.search(r"<lastmod>\d{4}-\d\d-\d\d</lastmod>", sm.read_text()):
            bad.append("sitemap.xml has no lastmod")
    ok_or_fail("T00", bad, "CNAME, robots.txt, sitemap.xml, app-ads.txt are correct")


def test_overwatch_replica(root, docs):
    """Port of overwatch/src/connectors/siteCheck.ts run on the home page and the files next to it."""
    d = docs["index.html"]
    html = d.src
    bad = []
    t = d.title
    if not 25 <= len(t) <= 65:
        bad.append("title %d chars" % len(t))
    desc = d.meta("description") or ""
    if not 70 <= len(desc) <= 170:
        bad.append("description %d chars" % len(desc))
    canon = d.link("canonical") or ""
    if not canon.startswith(SITE):
        bad.append("canonical not on this site")
    if len(re.findall(r"<h1\b", html, re.I)) != 1:
        bad.append("needs exactly one H1")
    for k in ("og:title", "og:description", "og:image"):
        if not d.meta(k, "property"):
            bad.append("missing " + k)
    if not d.meta("viewport"):
        bad.append("viewport missing")
    for t_ in re.findall(r"<img\b[^>]*>", html, re.I):
        if not re.search(r'\balt\s*=\s*"[^"]+"', t_, re.I):
            bad.append("image without non-empty alt: " + t_[:70])
    r = root / "robots.txt"
    if not (r.exists() and re.search(r"sitemap:", r.read_text(), re.I)):
        bad.append("robots.txt without Sitemap line")
    if not (root / "sitemap.xml").exists():
        bad.append("sitemap.xml missing")
    if not re.search(r"MobileApplication|SoftwareApplication|VideoGame", "".join(d.ld)):
        bad.append("no application JSON-LD")
    plays = re.findall(r"https://play\.google\.com/store/apps/details\?[^\"'\s<>]+", html.replace("&amp;", "&"))
    if not plays or not any("referrer=" in p for p in plays):
        bad.append("no tagged Play link")
    if not re.search(r'href\s*=\s*"[^"]*privacy[^"]*"', html, re.I):
        bad.append("privacy policy not linked")
    if "overwatch.kalmarium.com/h.js" not in html:
        bad.append("visit script missing")
    ok_or_fail("T01", bad, "offline replica of OverWatch site-check: every line would PASS on the home page")


def find_vnu(arg):
    cands = [arg, os.environ.get("VNU_JAR"), str(REPO / "tools" / "vnu.jar"), str(REPO / "vnu.jar")]
    for c in cands:
        if c and Path(c).is_file():
            return c
    return None


def lint_doc(rel, d):
    bad = []
    for e in d.errors:
        bad.append("%s: %s" % (rel, e))
    ids = {}
    for tag, a, ln in d.tags:
        if "id" in a:
            if a["id"] in ids:
                bad.append("%s: duplicate id %s" % (rel, a["id"]))
            ids[a["id"]] = ln
    for tag, a, ln in d.tags:
        if tag == "img":
            for k in ("alt", "width", "height", "src"):
                if k not in a:
                    bad.append("%s line %d: <img> without %s" % (rel, ln, k))
        if tag == "a" and "href" not in a:
            bad.append("%s line %d: <a> without href" % (rel, ln))
        if "aria-labelledby" in a and a["aria-labelledby"] not in ids:
            bad.append("%s line %d: aria-labelledby target %s missing" % (rel, ln, a["aria-labelledby"]))
        if tag == "a" and a.get("href", "").startswith("#") and len(a["href"]) > 1 and a["href"][1:] not in ids:
            bad.append("%s line %d: in-page link %s has no target" % (rel, ln, a["href"]))
    html_tag = d.of("html")
    if not html_tag or html_tag[0][0].get("lang") != "en":
        bad.append("%s: <html lang=en> missing" % rel)
    if len(d.of("main")) != 1:
        bad.append("%s: needs exactly one <main>" % rel)
    if not d.src.lstrip().lower().startswith("<!doctype html>"):
        bad.append("%s: no doctype" % rel)
    levels = [int(t[1]) for t, _, _ in d.tags if re.fullmatch(r"h[1-6]", t)]
    prev = 0
    for lv in levels:
        if lv > prev + 1:
            bad.append("%s: heading level jumps from h%d to h%d" % (rel, prev, lv))
        prev = lv
    return bad


def test_validity(root, docs, vnu_arg):
    vnu = find_vnu(vnu_arg)
    java = shutil.which("java")
    if vnu and java:
        files = [str(root / p) for p in PAGES if (root / p).exists()]
        r = subprocess.run([java, "-jar", vnu, "--errors-only", "--no-langdetect"] + files, capture_output=True, text=True, timeout=180)
        out = (r.stdout + r.stderr).strip()
        errs = [ln for ln in out.splitlines() if "error" in ln.lower()]
        if r.returncode == 0 and not errs:
            rec("PASS", "T02", "Nu HTML checker (vnu.jar): 0 errors on %d pages" % len(files))
        else:
            rec("FAIL", "T02", "Nu HTML checker reported errors")
            for ln in errs[:12]:
                print("        - " + ln)
    else:
        rec("SKIP", "T02", "vnu.jar not found (set VNU_JAR or --vnu); using the built-in structure lint instead")
    bad = []
    for rel in PAGES:
        if rel in docs:
            bad += lint_doc(rel, docs[rel])
    ok_or_fail("T02", bad, "structure lint: balanced tags, unique ids, alt+size on images, valid in-page links, heading order, lang, doctype (%d pages)" % len(docs))


def collect_refs(d):
    refs = []
    for tag, a, ln in d.tags:
        for k in ("href", "src", "poster"):
            if k in a and tag != "meta":
                refs.append((tag, k, a[k]))
    return refs


def test_links(root, data, docs):
    bad = []
    n_int = 0
    ids_cache = {}

    def ids_of(p):
        if p not in ids_cache:
            ids_cache[p] = {a.get("id") for _, a, _ in Doc(p.read_text(encoding="utf-8")).tags if "id" in a} if p.suffix == ".html" else set()
        return ids_cache[p]

    pk = {a["package"]: a for a in data["apps"]}
    sites = {a["id"]: a["site"] for a in data["apps"]}
    seen_play = set()
    for rel, d in docs.items():
        for tag, k, url in collect_refs(d):
            if not url or url.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            if tag == "link" and k == "href" and url.startswith("https://") and "canonical" in str([a.get("rel") for t, a, _ in d.tags if t == "link"]):
                pass
            u = urllib.parse.urlsplit(url)
            if u.scheme in ("http", "https") and u.netloc != "apps.kalmarium.com":
                if u.netloc == "play.google.com" and u.path.endswith("/details"):
                    q = urllib.parse.parse_qs(u.query)
                    pkg = (q.get("id") or [""])[0]
                    if pkg not in pk:
                        bad.append("%s: Play link with unknown package %s" % (rel, pkg))
                    ref = (q.get("referrer") or [""])[0]
                    if not ref.startswith("utm_source=hub&utm_medium="):
                        bad.append("%s: Play link for %s lacks referrer=utm_source%%3Dhub: %s" % (rel, pkg, url[:90]))
                    if "referrer=utm_source%3Dhub%26utm_medium%3D" not in url:
                        bad.append("%s: Play referrer not percent-encoded as specified: %s" % (rel, url[:90]))
                    seen_play.add((rel, pkg))
                elif tag == "a" and k == "href":
                    if not any(url.startswith(s) for s in sites.values()) and u.netloc not in (
                            "kalmarium.com", "www.youtube.com", "play.google.com"):
                        bad.append("%s: unexpected outbound link %s" % (rel, url[:90]))
                    for a in data["apps"]:
                        if url.startswith(a["site"]) and "utm_source=hub&utm_medium=" not in url:
                            bad.append("%s: app-site link not tagged: %s" % (rel, url[:90]))
                continue
            n_int += 1
            p, frag = to_path(root, url, rel)
            if p is None:
                continue
            if not p.is_file():
                bad.append("%s: %s -> missing file %s" % (rel, url, p.relative_to(root) if root in p.parents else p))
            elif frag and p.suffix == ".html" and frag not in ids_of(p):
                bad.append("%s: %s -> no #%s in target" % (rel, url, frag))
    home_pk = {pkg for r, pkg in seen_play if r == "index.html"}
    for pkg, a in pk.items():
        if pkg not in home_pk:
            bad.append("home page has no Play link for %s" % a["name"])
        for rel in [CAT_PAGES.get(a["category"])]:
            if rel and (rel, pkg) not in seen_play:
                bad.append("%s has no Play link for %s" % (rel, a["name"]))
    ok_or_fail("T03", bad, "%d internal references resolve; %d tagged Play links carry the right package id and referrer" % (n_int, len(seen_play)))


FORBIDDEN_KEYS = {"aggregateRating", "ratingValue", "reviewCount", "interactionCount", "ratingCount", "review", "bestRating"}


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def test_jsonld(root, data, docs):
    bad = []
    apps_by_cat = {}
    for a in data["apps"]:
        apps_by_cat.setdefault(a["category"], []).append(a)
    for rel in ["index.html"] + list(CAT_PAGES.values()) + ["about/index.html", "press/index.html", "privacy-policy.html"]:
        d = docs.get(rel)
        if d is None:
            continue
        if not d.ld:
            bad.append("%s: no JSON-LD" % rel)
            continue
        nodes = []
        for block in d.ld:
            try:
                j = json.loads(block)
            except ValueError as e:
                bad.append("%s: JSON-LD does not parse: %s" % (rel, e))
                continue
            if j.get("@context") != "https://schema.org":
                bad.append("%s: @context must be https://schema.org" % rel)
            nodes += list(walk(j))
        for n in nodes:
            for k in n:
                if k in FORBIDDEN_KEYS:
                    bad.append("%s: forbidden field %s" % (rel, k))
        types = {}
        for n in nodes:
            t = n.get("@type")
            for tt in (t if isinstance(t, list) else [t]):
                types.setdefault(tt, []).append(n)
        for need in ("Organization", "WebSite"):
            if need not in types:
                bad.append("%s: no %s node" % (rel, need))
        if rel in ("index.html",) or rel in CAT_PAGES.values():
            lists = types.get("ItemList", [])
            want = len(data["apps"]) if rel == "index.html" else len(apps_by_cat.get(next(k for k, v in CAT_PAGES.items() if v == rel), []))
            if len(lists) != 1 or len(lists[0].get("itemListElement", [])) != want:
                bad.append("%s: ItemList must have %d items" % (rel, want))
            else:
                for li in lists[0]["itemListElement"]:
                    it = li.get("item", {})
                    if it.get("@type") not in ("VideoGame", "MobileApplication"):
                        bad.append("%s: ItemList item of type %s" % (rel, it.get("@type")))
                    for k in ("name", "operatingSystem", "applicationCategory", "url", "installUrl", "image", "offers", "author"):
                        if k not in it:
                            bad.append("%s: %s item lacks %s" % (rel, it.get("name"), k))
        if rel in CAT_PAGES.values():
            if "BreadcrumbList" not in types:
                bad.append("%s: BreadcrumbList missing" % rel)
        vids = types.get("VideoObject", [])
        shown = [a for a in data["apps"] if a.get("video") and (rel == "index.html" or CAT_PAGES.get(a["category"]) == rel)]
        if len(vids) != len(shown):
            bad.append("%s: %d VideoObject nodes for %d self-hosted videos" % (rel, len(vids), len(shown)))
        for v in vids:
            for k in ("name", "thumbnailUrl", "uploadDate", "contentUrl", "duration"):
                if not v.get(k):
                    bad.append("%s: VideoObject lacks %s" % (rel, k))
            cu = v.get("contentUrl", "")
            if cu.startswith(SITE) and not (root / cu[len(SITE) + 1:]).is_file():
                bad.append("%s: VideoObject file missing %s" % (rel, cu))
        faqs = types.get("FAQPage", [])
        if rel in CAT_PAGES.values():
            for f in faqs:
                for q in f.get("mainEntity", []):
                    if q["name"] not in d.visible:
                        bad.append("%s: FAQ question not shown on the page: %s" % (rel, q["name"][:50]))
        elif faqs:
            bad.append("%s: FAQPage without visible FAQ" % rel)
    ok_or_fail("T04", bad, "JSON-LD parses; ItemList 9/3/3/3; no rating or count fields; VideoObject only for self-hosted clips; FAQ matches visible text")


def test_hue(root):
    bad = []
    n = 0
    for p in all_files(root):
        rel = p.relative_to(root).as_posix()
        if p.suffix not in (".html", ".css", ".svg") or rel.startswith("docs/"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".html":
            text = re.sub(r'\b(?:href|src|id|for|aria-labelledby|content|alt|aria-label|data-video)\s*=\s*"[^"]*"', " ", text)
            text = re.sub(r'<script type="application/ld\+json">.*?</script>', " ", text, flags=re.S)
        for lit, rgb in find_colours(text):
            n += 1
            if bad_hue(rgb):
                bad.append("%s: %s has hue %d (forbidden 235-330)" % (rel, lit, hue_of(*rgb)[0]))
        for kw in NAMED_BAD:
            if re.search(r"(?:color|fill|stroke|background|stop-color)\s*[:=]\s*[\"']?\s*%s\b" % kw, text, re.I):
                bad.append("%s: colour keyword %s" % (rel, kw))
    ok_or_fail("T05", bad, "%d colour values in HTML, CSS and SVG, none with a hue between 235 and 330 degrees (images still need an eye review)" % n)


_ENT = "&(?:m|n)dash;|&#(?:8212|8211);|&#x(?:2014|2013);"
DASH = re.compile(chr(0x2014) + "|" + chr(0x2013) + "|" + _ENT, re.I)
DASH_CHARS = re.compile(chr(0x2014) + "|" + chr(0x2013))


def test_dashes(root):
    bad = []
    n = 0
    for p in all_files(root):
        if p.suffix.lower() not in TEXT_EXT and p.name not in ("CNAME",):
            continue
        n += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if p.suffix.lower() == ".md":
                line = DASH_CHARS.search(line) and line or re.sub(r"`[^`]*`", "", line)  # rule text in code spans is documentation
            if DASH.search(line):
                bad.append("%s line %d" % (p.relative_to(root).as_posix(), i))
    ok_or_fail("T06", bad, "no em-dash or en-dash (characters or HTML entities) in %d text files" % n)


def test_third_party(root, docs):
    bad = []
    own = {"apps.kalmarium.com"}
    for rel, d in docs.items():
        for tag, a, ln in d.tags:
            for k in ("src", "href", "poster", "data"):
                v = a.get(k)
                if not v:
                    continue
                if tag == "a":
                    continue
                if v.startswith("//") or re.match(r"https?://", v):
                    host = urllib.parse.urlsplit(("https:" + v) if v.startswith("//") else v).netloc
                    if v == VISIT_SRC:
                        continue
                    if host in own and tag == "link" and "canonical" in a.get("rel", ""):
                        continue
                    bad.append("%s line %d: <%s %s=%s> goes off-site" % (rel, ln, tag, k, v[:70]))
            if tag in ("iframe", "embed", "object", "audio", "form"):
                bad.append("%s line %d: <%s> not allowed" % (rel, ln, tag))
            if tag == "script" and not a.get("src") and "ld+json" not in a.get("type", ""):
                bad.append("%s line %d: inline script" % (rel, ln))
            if tag == "link" and a.get("rel") in ("preconnect", "dns-prefetch", "prefetch", "preload"):
                bad.append("%s line %d: link rel=%s" % (rel, ln, a.get("rel")))
        if re.search(r"<style\b", d.src):
            bad.append("%s: inline <style> block" % rel)
        if d.src.count(VISIT_SRC) != 1 or 'data-app="kalmarium-hub"' not in d.src:
            bad.append("%s: visit script must appear once with data-app=kalmarium-hub" % rel)
        head_end = d.src.find("</head>")
        if d.src.find(VISIT_SRC) > head_end or d.src.rfind("<script", 0, head_end) < 0:
            bad.append("%s: visit script not in <head>" % rel)
        elif not d.src[:head_end].rstrip().endswith("</script>"):
            bad.append("%s: visit script is not the last tag before </head>" % rel)
    css = root / "assets" / "site.css"
    if css.exists():
        c = css.read_text(encoding="utf-8")
        if re.search(r"@font-face|@import|url\(\s*[\"']?(https?:)?//", c):
            bad.append("site.css: web font, @import or off-site url()")
        for m in re.finditer(r"url\(\s*[\"']?([^)\"']+)", c):
            if m.group(1).startswith(("http", "//")):
                bad.append("site.css: url(%s)" % m.group(1))
    js = root / "assets" / "site.js"
    if js.exists():
        j = js.read_text(encoding="utf-8")
        for pat in ("document.cookie", "localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "http://", "https://"):
            if pat in j:
                bad.append("site.js contains %s" % pat)
    for p in all_files(root):
        if p.suffix.lower() in (".woff", ".woff2", ".ttf", ".otf", ".eot"):
            bad.append("font file in repo: %s" % p.relative_to(root).as_posix())
    ok_or_fail("T07", bad, "no third-party request except overwatch h.js; no cookies or storage, no fetch, no fonts, no inline script or style")


def fsize(root, rel):
    p = root / rel
    return p.stat().st_size if p.is_file() else None


def test_weight(root, data, docs):
    bad = []

    def need(rel, limit, label, size=None, minsize=None):
        n = fsize(root, rel)
        if n is None:
            bad.append("missing %s" % rel)
            return 0
        if n > limit:
            bad.append("%s is %d KB, budget %d KB (%s)" % (rel, n // 1024, limit // 1024, label))
        if size:
            d = dims(root / rel)
            if d != size:
                bad.append("%s is %s, expected %dx%d" % (rel, "%dx%d" % d if d else "unreadable", size[0], size[1]))
        if minsize:
            d = dims(root / rel)
            if not d or d[0] != minsize:
                bad.append("%s is %s wide, expected %d" % (rel, d[0] if d else "?", minsize))
        return n

    need("assets/site.css", BUDGET["css"], "CSS 14 KB")
    need("assets/site.js", BUDGET["js"], "JS 3 KB")
    html_n = need("index.html", BUDGET["html"], "HTML 40 KB")
    for rel in PAGES:
        n = fsize(root, rel)
        if n and n > BUDGET["html"]:
            bad.append("%s is %d KB" % (rel, n // 1024))
    need("og.jpg", BUDGET["og"], "og 150 KB", size=(1200, 630))
    for a in data["apps"]:
        i = a["id"]
        need("img/%s/icon.webp" % i, BUDGET["icon"], "icon 12 KB", size=(192, 192))
        need("img/%s/tile.webp" % i, BUDGET["tile"], "tile 60 KB", size=(800, 450))
        for k in (1, 2, 3):
            need("img/%s/shot-%d.webp" % (i, k), BUDGET["shot"], "shot 25 KB", minsize=360)
        v = a.get("video")
        if v:
            need(v["file"], BUDGET["video"], "video 2.5 MB")
            need(v["poster"], BUDGET["poster"], "poster 45 KB", size=(800, 450))
            if v.get("duration", 0) > 60:
                bad.append("%s video longer than 60 s" % i)
    n = fsize(root, "img/google-play-badge.png")
    if n is None:
        bad.append("missing img/google-play-badge.png (official badge, copy of factory brand/google-play-badge-en.png)")
    elif dims(root / "img/google-play-badge.png") != (646, 250):
        bad.append("img/google-play-badge.png is not 646x250")
    for a in data["apps"]:
        need("img/press/%s/icon-512.png" % a["id"], 1024 * 1024, "press file 1 MB", size=(512, 512))
        for k in (1, 2, 3):
            need("img/press/%s/screenshot-%d.jpg" % (a["id"], k), 1024 * 1024, "press file 1 MB")
    for rel, size in (("assets/favicon.png", (64, 64)), ("assets/apple-touch-icon.png", (180, 180)), ("brand/dev-icon-512.png", (512, 512))):
        n = fsize(root, rel)
        if n is None:
            bad.append("missing %s" % rel)
        elif dims(root / rel) != size:
            bad.append("%s is not %dx%d" % (rel, size[0], size[1]))
    # first view of the home page: everything the HTML requests without loading=lazy
    d = docs["index.html"]
    files = {"index.html": html_n or 0}
    reqs = 1
    for tag, a, ln in d.tags:
        url = None
        if tag == "link" and a.get("rel") in ("stylesheet", "icon"):
            url = a.get("href")
        elif tag == "script" and a.get("src", "").startswith("/"):
            url = a["src"]
        elif tag == "img" and a.get("loading") != "lazy":
            url = a.get("src")
        if url and url.startswith("/"):
            files[url] = fsize(root, url.lstrip("/")) or 0
    reqs += len(files) - 1 + 1  # the visit script is one more request
    total = sum(files.values()) + 2048  # estimate 2 KB for h.js
    if total > BUDGET["first_view"]:
        bad.append("home first view about %d KB, budget 450 KB" % (total // 1024))
    if reqs > 25:
        bad.append("home first view makes %d requests, budget 25" % reqs)
    ok_or_fail("T08", bad, "budgets hold: CSS %s B, JS %s B, home HTML %s B; first view ~%d KB in %d requests; images, posters, videos, og.jpg within size and pixel budgets"
               % (fsize(root, "assets/site.css"), fsize(root, "assets/site.js"), fsize(root, "index.html"), total // 1024, reqs))


def parse_vars(block):
    return {k: v for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", block)}


def test_a11y(root, docs):
    bad = []
    css = (root / "assets" / "site.css").read_text(encoding="utf-8")
    light_m = re.search(r":root\{([^}]*)\}", css)
    dark_m = re.search(r"prefers-color-scheme:dark\)\{:root\{([^}]*)\}", css)
    light = parse_vars(light_m.group(1)) if light_m else {}
    dark = dict(light)
    if dark_m:
        dark.update(parse_vars(dark_m.group(1)))
    else:
        bad.append("no dark theme override found")
    pairs = [("ink", "paper", 7.0), ("ink", "surface", 7.0), ("muted", "paper", 4.5), ("muted", "surface", 4.5),
             ("brand", "paper", 4.5), ("brand", "surface", 4.5), ("on-brand", "brand", 4.5),
             ("band-ink", "band", 4.5), ("band-mute", "band", 4.5), ("fill", "band", 4.5), ("accent", "paper", 3.0)]
    worst = 99
    for name, theme in (("light", light), ("dark", dark)):
        for fg, bg, need_ in pairs:
            if fg not in theme or bg not in theme:
                bad.append("%s: token %s or %s missing" % (name, fg, bg))
                continue
            c = contrast(hex_rgb(theme[fg]), hex_rgb(theme[bg]))
            if need_ >= 4.5:
                worst = min(worst, c)
            if c < need_:
                bad.append("%s: %s on %s is %.2f:1, needs %.1f" % (name, fg, bg, c, need_))
    for needle, why in ((":focus-visible", "visible focus style"), ("prefers-reduced-motion", "reduced-motion rule"),
                        ("prefers-color-scheme:dark", "dark theme"), ("min-height:48px", "48px tap targets")):
        if needle not in css:
            bad.append("site.css lacks %s" % why)
    for rel, d in docs.items():
        vp = d.meta("viewport") or ""
        if re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale", vp):
            bad.append("%s: viewport blocks zoom" % rel)
        if not any(a.get("class") == "skip" for a in (x[0] for x in d.of("a"))):
            bad.append("%s: no skip link" % rel)
        # every link has a name: text, aria-label or image alt
        src = d.src
        for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", src, re.S):
            attrs, inner = m.group(1), m.group(2)
            has_label = "aria-label=" in attrs or re.search(r">[^<\s]", ">" + re.sub(r"<img[^>]*>", "", inner)) or re.search(r'<img[^>]*alt="[^"]+"', inner)
            if not has_label:
                bad.append("%s: link without an accessible name: %s" % (rel, attrs[:60]))
        for a, ln in d.of("a"):
            if "data-video" in a:
                if not a.get("href", "").endswith(".mp4"):
                    bad.append("%s line %d: video facade without a plain MP4 link (no-JS fallback)" % (rel, ln))
    ok_or_fail("T10", bad, "contrast >= 4.5:1 for text pairs in light and dark (worst %.1f:1); focus, reduced motion, 48px targets, skip links, zoom, link names, no-JS video link. "
               "Keyboard pass, 200%% zoom and a screen reader still need a human" % worst)


def test_head(root, data, docs):
    bad = []
    expected = {"index.html": "/", "games/index.html": "/games/", "learning/index.html": "/learning/",
                "tools/index.html": "/tools/", "about/index.html": "/about/", "press/index.html": "/press/",
                "privacy-policy.html": "/privacy-policy.html", "404.html": "/404.html"}
    for rel, path in expected.items():
        d = docs.get(rel)
        if d is None:
            bad.append("%s missing" % rel)
            continue
        t = d.title
        desc = d.meta("description") or ""
        if not 25 <= len(t) <= 65:
            bad.append("%s: title %d chars (25-65)" % (rel, len(t)))
        if not 70 <= len(desc) <= 170:
            bad.append("%s: description %d chars (70-170)" % (rel, len(desc)))
        h1 = len(d.of("h1"))
        if h1 != 1:
            bad.append("%s: %d H1" % (rel, h1))
        if d.link("canonical") != SITE + path:
            bad.append("%s: canonical is %s" % (rel, d.link("canonical")))
        for k in ("og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name", "og:image:width", "og:image:height", "og:image:alt"):
            if not d.meta(k, "property"):
                bad.append("%s: %s missing" % (rel, k))
        if d.meta("og:url", "property") != SITE + path:
            bad.append("%s: og:url is not the canonical" % rel)
        for k in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if not d.meta(k):
                bad.append("%s: %s missing" % (rel, k))
        if d.meta("twitter:card") != "summary_large_image":
            bad.append("%s: twitter:card must be summary_large_image" % rel)
        themes = [a for a, _ in d.of("meta") if a.get("name") == "theme-color"]
        if len(themes) < 2:
            bad.append("%s: theme-color needs light and dark" % rel)
        if not d.meta("viewport"):
            bad.append("%s: viewport missing" % rel)
        for a, ln in d.of("img"):
            if not a.get("alt", "").strip():
                bad.append("%s line %d: img alt empty" % (rel, ln))
        if rel == "404.html" and d.meta("robots") != "noindex":
            bad.append("404.html should be noindex")
    ok_or_fail("T11", bad, "title 25-65, description 70-170, one H1, self canonical, Open Graph, Twitter, theme-color, alt text on all %d pages" % len(expected))


HYPE = re.compile(r"loved by|thousands of|millions of|best[- ]selling|#1\b|top[- ]rated|five[- ]star|\b5[- ]stars?\b|\d[\d,.]*\+? (?:downloads|installs|users)|award[- ]winning|trusted by|\u2605", re.I)


def test_honesty(root, data, docs):
    bad = []
    for rel, d in docs.items():
        m = HYPE.search(d.visible)
        if m:
            bad.append("%s: popularity or rating wording: %r" % (rel, m.group(0)))
    home = docs["index.html"].visible
    if any(a["id"] == "prep4cert" for a in data["apps"]):
        for rel in ("index.html", CAT_PAGES[next(a["category"] for a in data["apps"] if a["id"] == "prep4cert")]):
            if "Not affiliated with or endorsed by Microsoft" not in docs[rel].visible:
                bad.append("%s: Microsoft disclaimer missing" % rel)
    ai = any(a.get("aiArt") for a in data["apps"])
    line = "Some artwork on this site is AI-generated"
    for rel in PAGES:
        has = line in docs[rel].visible
        if has != ai:
            bad.append("%s: AI-art line %s but aiArt is %s for %s" % (rel, "present" if has else "absent", ai, "some apps" if ai else "no app"))
    if "no forced subscription" not in home.lower():
        bad.append("home: 'no forced subscription' wording missing")
    ok_or_fail("T12", bad, "no ratings or popularity claims; Microsoft disclaimer next to Prep 4 Cert; AI-art line matches aiArt")
    rec("SKIP", "T12", "manual: compare each price and ads line with the app's Play listing on launch day")


def test_brand_rules(root, docs):
    """WP-04 rules: About and Press linked from every page, one spelling of the company, a complete Organization node."""
    bad = []
    legacy = "Kalmarium Services " + "BV"
    for rel, d in docs.items():
        hrefs = {a.get("href") for a, _ in d.of("a")}
        for need_ in ("/about/", "/press/"):
            if need_ not in hrefs:
                bad.append("%s: link to %s missing" % (rel, need_))
        if legacy in d.src or "Kalmarium BV" in d.src:
            bad.append("%s: wrong company spelling (use Kalmarium Services or Kalmarium Services B.V.)" % rel)
        orgs = 0
        for block in d.ld:
            try:
                nodes = list(walk(json.loads(block)))
            except ValueError:
                continue
            for n in nodes:
                if n.get("@type") == "Organization":
                    orgs += 1
                    if not n.get("alternateName"):
                        bad.append("%s: Organization node without alternateName" % rel)
                    if n.get("@id") != SITE + "/#org":
                        bad.append("%s: Organization @id is %s" % (rel, n.get("@id")))
                    if n.get("legalName") != "Kalmarium Services B.V.":
                        bad.append("%s: Organization legalName must be Kalmarium Services B.V." % rel)
                if n.get("@type") in ("VideoGame", "MobileApplication"):
                    if not str(n.get("@id", "")).endswith("/#app"):
                        bad.append("%s: app node %s without @id https://<host>/#app" % (rel, n.get("name")))
        if d.ld and orgs != 1:
            bad.append("%s: %d Organization nodes, expected 1" % (rel, orgs))
    for rel in ("data/apps.json", "tools/build.py"):
        if legacy in (root / rel).read_text(encoding="utf-8"):
            bad.append("%s: wrong company spelling" % rel)
    ok_or_fail("T14", bad, "About and Press linked on every page; one company spelling; one Organization node with alternateName, @id and legalName; app nodes carry #app ids")


def test_data(root, data):
    bad = []
    for a in data["apps"]:
        for k in ("id", "name", "descriptor", "category", "package", "site", "hook", "bullets", "audience", "price", "offerPrice",
                  "schemaType", "applicationCategory", "accent", "long", "who", "pick", "alt", "aiArt"):
            if k not in a or a[k] in ("", None, []):
                if k == "aiArt" and k in a:
                    continue
                bad.append("%s: field %s missing or empty" % (a.get("id"), k))
        alt = a.get("alt", {})
        if not alt.get("icon") or not alt.get("tile") or len(alt.get("shots", [])) < 1:
            bad.append("%s: alt texts incomplete" % a.get("id"))
        if a.get("accent") and bad_hue(hex_rgb(a["accent"])):
            bad.append("%s: accent in forbidden hue range" % a["id"])
        words = len(a.get("long", "").split())
        if not 70 <= words <= 130:
            bad.append("%s: long copy is %d words (80-120 asked)" % (a["id"], words))
    cats = {c["id"] for c in data["categories"]}
    for c in data["categories"]:
        if not c.get("faq"):
            bad.append("category %s has no FAQ" % c["id"])
    for a in data["apps"]:
        if a["category"] not in cats:
            bad.append("%s: unknown category" % a["id"])
    ok_or_fail("T00", bad, "data/apps.json complete for %d apps in %d categories" % (len(data["apps"]), len(data["categories"])))


def skip_manual():
    rec("SKIP", "T09", "Lighthouse mobile (95/100/100/100, LCP < 1.8 s, CLS < 0.05) needs Chrome DevTools; run it on the live URL")
    rec("SKIP", "T13", "OverWatch: one test visit under kalmarium-hub and Sites score 100 can only be seen in OverWatch after launch")


# ------------------------------------------------------------------ live
UA = {"User-Agent": "Mozilla/5.0 (compatible; kalmarium-hub-check/1.0)"}


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.read(600000)
    except urllib.error.HTTPError as e:
        return e.code, url, b""
    except Exception as e:  # noqa: BLE001
        return 0, url, str(e).encode()


def test_live(root, data, docs):
    bad = []
    targets = [SITE + "/", SITE + "/games/", SITE + "/learning/", SITE + "/tools/", SITE + "/about/", SITE + "/press/",
               SITE + "/privacy-policy.html", SITE + "/img/google-play-badge.png", SITE + "/robots.txt", SITE + "/sitemap.xml", SITE + "/app-ads.txt", SITE + "/og.jpg", SITE + "/assets/site.css",
               SITE + "/assets/site.js", SITE + "/assets/favicon.png", SITE + "/assets/apple-touch-icon.png", SITE + "/brand/dev-icon-512.png"]
    for a in data["apps"]:
        targets += [SITE + "/img/%s/icon.webp" % a["id"], SITE + "/img/%s/tile.webp" % a["id"]]
        if a.get("video"):
            targets += [SITE + "/" + a["video"]["file"], SITE + "/" + a["video"]["poster"]]
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        res = dict(zip(targets, ex.map(lambda u: fetch(u), targets)))
    for u, (st, final, body) in res.items():
        if st != 200:
            bad.append("%s -> HTTP %s %s" % (u, st, body[:60].decode("utf-8", "replace") if st == 0 else ""))
    rec("FAIL" if bad else "PASS", "L01", ("%d hub URLs not HTTP 200" % len(bad)) if bad else "all %d hub URLs return HTTP 200 over HTTPS" % len(targets))
    for b in bad[:12]:
        print("        - " + b)
    # live bytes equal the repo
    diff = []
    compared = 0
    for rel, path in (("index.html", "/"), ("games/index.html", "/games/"), ("learning/index.html", "/learning/"), ("tools/index.html", "/tools/"), ("about/index.html", "/about/"), ("press/index.html", "/press/"), ("privacy-policy.html", "/privacy-policy.html")):
        st, _, body = res.get(SITE + path, (0, "", b""))
        if st == 200 and body.decode("utf-8", "replace").replace("\r\n", "\n") != read(root, rel):
            diff.append(rel)
    rec("FAIL" if diff else "PASS", "L02", ("live pages differ from the repo: %s (deploy not finished?)" % ", ".join(diff)) if diff else "live HTML equals the repo build")
    st, _, body = fetch(SITE + "/no-such-page-" + "x7")
    rec("PASS" if st == 404 and b"Page not found" in body else "FAIL", "L03", "unknown address returns the custom 404 page (HTTP %s)" % st)
    st, _, body = fetch(SITE + "/")
    if st == 200:
        h = Doc(body.decode("utf-8", "replace"))
        rec("PASS" if SITE + "/" == h.link("canonical") else "FAIL", "L04", "live canonical is %s" % h.link("canonical"))
    # app sites and Play listings
    links = []
    for a in data["apps"]:
        links.append((a["name"] + " site", a["site"], None))
        links.append((a["name"] + " Play", "https://play.google.com/store/apps/details?id=%s&hl=en" % a["package"], a["package"]))
    links.append(("Play developer page", data["site"]["playDeveloper"], None))
    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        out = list(ex.map(lambda t: fetch(t[1], 30), links))
    bad = []
    for (label, url, pkg), (st, final, body) in zip(links, out):
        if st != 200:
            bad.append("%s: HTTP %s (%s)" % (label, st, url))
        elif pkg and pkg not in final and pkg.encode() not in body:
            bad.append("%s: response does not mention package %s" % (label, pkg))
    ok_or_fail("L05", bad, "%d app-site and Google Play links return HTTP 200; each Play page names its package id" % len(links))
    ow = Path(r"C:\dev\overwatch")
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if (ow / "scripts" / "check-site.ts").is_file() and npx:
        r = subprocess.run([npx, "tsx", "scripts/check-site.ts", SITE], cwd=str(ow), capture_output=True, text=True, timeout=240)
        out = (r.stdout + r.stderr).strip().splitlines()
        fails = [ln for ln in out if "FAIL" in ln]
        print("        OverWatch check-site output:")
        for ln in out[-25:]:
            print("        | " + ln)
        rec("FAIL" if fails or r.returncode else "PASS", "T01", "OverWatch scripts/check-site.ts on the live URL (%d FAIL lines)" % len(fails))
    else:
        rec("SKIP", "T01", "OverWatch check-site.ts or npx not available; run it by hand from C:\\dev\\overwatch")


def main():
    ap = argparse.ArgumentParser(description="Acceptance tests for the Kalmarium Apps hub")
    ap.add_argument("--live", action="store_true", help="also test https://apps.kalmarium.com and the outbound links")
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--vnu", default=None, help="path to vnu.jar")
    args = ap.parse_args()
    root = Path(args.root)
    if not (root / "data" / "apps.json").is_file():
        print("FAIL  T00  data/apps.json not found")
        return 1
    data = load_data(root)
    test_static_files(root, data)
    test_data(root, data)
    test_build_current(root, data)
    docs = {}
    for rel in PAGES:
        if (root / rel).is_file():
            docs[rel] = Doc(read(root, rel))
        else:
            rec("FAIL", "T00", "%s not found; run tools/build.py" % rel)
    if len(docs) == len(PAGES):
        test_overwatch_replica(root, docs)
        test_validity(root, docs, args.vnu)
        test_links(root, data, docs)
        test_jsonld(root, data, docs)
        test_hue(root)
        test_dashes(root)
        test_third_party(root, docs)
        test_weight(root, data, docs)
        test_a11y(root, docs)
        test_head(root, data, docs)
        test_honesty(root, data, docs)
        test_brand_rules(root, docs)
        skip_manual()
        if args.live:
            test_live(root, data, docs)
    n = lambda s: sum(1 for r in RESULTS if r[0] == s)  # noqa: E731
    print("\n%d PASS, %d FAIL, %d SKIP" % (n("PASS"), n("FAIL"), n("SKIP")))
    return 1 if n("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
