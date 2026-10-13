"""Build BUR Slate from src/bur_slate_src.html.

  python3 src/build_slate.py [--lists <asset_history.json>] [--artifact <out.html>]

Two copies come out:
  1. the web copy (no production lists; installable, offline) -> the repo root: index.html, manifest.webmanifest, sw.js
     (+ the three icons, made only when missing).  Commit and push: GitHub Pages redeploys from main by itself.
  2. the artifact copy (Steve's own, with the production lists built in) -> --artifact, default ../bur_slate_artifact.html
     (outside the repo: never commit it).  Lists come from the kit's config/asset_history.json plus any other JSON file
     with the same keys (--lists a.json,b.json or $BUR_ASSET_HISTORY); without them the artifact copy is skipped.
Placeholders in the source: /*QRLIB*/ (qrcode-generator 1.4.4, MIT, src/qrcode.min.js)  /*LOCATIONS*/  /*CHARACTERS*/  /*PROPS*/.
"""
import json, os, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; SRC = REPO / "src"
args = sys.argv[1:]
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default
lists = opt("--lists", os.environ.get("BUR_ASSET_HISTORY", ""))        # one or more JSON files, comma-separated: union of their lists
art = Path(opt("--artifact", os.environ.get("BUR_SLATE_ARTIFACT", REPO.parent / "bur_slate_artifact.html")))
src = (SRC / "bur_slate_src.html").read_text(encoding="utf-8")
lib = (SRC / "qrcode.min.js").read_text(encoding="utf-8").replace("</", "<\\/")
for ph in ("/*QRLIB*/", "/*LOCATIONS*/", "/*CHARACTERS*/", "/*PROPS*/"):
    assert src.count(ph) == 1, ph
def fill(locs, chs, props):
    return src.replace("/*QRLIB*/", lib).replace("/*LOCATIONS*/", json.dumps(locs)).replace("/*CHARACTERS*/", json.dumps(chs)).replace("/*PROPS*/", json.dumps(props))
# 1. artifact copy (with the production lists)
files = [Path(x) for x in lists.split(",") if x.strip()]
if files and all(f.exists() for f in files):
    h = {}
    for f in files:
        for k, v in json.load(open(f, encoding="utf-8")).items():
            if isinstance(v, list): h[k] = sorted(set(h.get(k, [])) | set(v), key=str.lower)
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text(fill(h.get("locations", []), h.get("characters", []), h.get("props", [])), encoding="utf-8")
    print("artifact copy ->", art, f"({len(h.get('locations', []))} locations, {len(h.get('characters', []))} characters, {len(h.get('props', []))} props)")
else:
    print("no asset_history.json (--lists): artifact copy skipped")
# 2. web copy: no production lists, names learned per phone, installable + offline
release = time.strftime("%Y%m%d-%H%M%S")
web = fill([], [], []).replace("Steve, ", "")
head = '''<title>BUR Slate</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="Slate and QR for on-set data wrangling.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="BUR Slate">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#f5f5f7">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#000000">'''
assert web.count("<title>BUR Slate</title>") == 1
web = web.replace("<title>BUR Slate</title>", head)
web = "<!doctype html>\n<html lang=\"en-GB\">\n<head>\n<meta charset=\"utf-8\">\n" + web
web = web.replace("</style>\n", "</style>\n</head>\n<body>\n", 1)
web += f'''
<script>
  // installable + works with no signal: the service worker keeps a copy on the phone (release {release})
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) navigator.serviceWorker.register("sw.js");
</script>
</body>
</html>
'''
(REPO / "index.html").write_text(web, encoding="utf-8")
(REPO / "manifest.webmanifest").write_text(json.dumps({
    "name": "BUR Slate", "short_name": "BUR Slate", "description": "Slate and QR for on-set data wrangling.",
    "start_url": "./", "scope": "./", "display": "standalone", "orientation": "any",
    "background_color": "#000000", "theme_color": "#000000",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}, indent=2), encoding="utf-8")
(REPO / "sw.js").write_text(f'''// BUR Slate service worker — release {release}
// Opens from the phone's copy straight away (works with no signal) and fetches any new release in the background;
// a new release shows the next time the app is opened.
const CACHE = "bur-slate-{release}";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
self.addEventListener("install", e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); }});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async c => {{
    const hit = await c.match(e.request, {{ ignoreSearch: true }}) || (e.request.mode === "navigate" ? await c.match("index.html") : undefined);
    const net = fetch(e.request).then(r => {{ if (r.ok) c.put(e.request, r.clone()); return r; }}).catch(() => hit);
    return hit || net;
  }}));
}});
''', encoding="utf-8")
# icons (black slate, white BUR, a small QR-style mark): made once, then kept as committed
if not all((REPO / n).exists() for n in ("icon-192.png", "icon-512.png", "apple-touch-icon.png")):
    from PIL import Image, ImageDraw, ImageFont
    def icon(size, path):
        im = Image.new("RGB", (size, size), "#000000"); d = ImageDraw.Draw(im)
        try: f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", int(size * 0.30))
        except OSError: f = ImageFont.load_default(int(size * 0.30))
        w = d.textlength("BUR", font=f); d.text(((size - w) / 2, size * 0.20), "BUR", font=f, fill="#ffffff")
        m = size * 0.06; x0 = size * 0.5 - m * 3.5; y0 = size * 0.60
        for r, row in enumerate(["1110111", "1010001", "1110101", "0001010", "1011110"]):
            for c, v in enumerate(row):
                if v == "1": d.rectangle([x0 + c * m, y0 + r * m, x0 + (c + 1) * m - 1, y0 + (r + 1) * m - 1], fill="#ffffff")
        im.save(path)
    icon(192, REPO / "icon-192.png"); icon(512, REPO / "icon-512.png"); icon(180, REPO / "apple-touch-icon.png")
print("web copy -> repo root | release", release, "| index", len(web) // 1024, "KB")
