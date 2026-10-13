import os
from pathlib import Path
import sys, time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
DEV = [("Fold cover Chrome", 412, 780), ("Fold cover app", 412, 880), ("iPhone 16 Pro Safari", 402, 740), ("iPhone 16 Pro app", 402, 820), ("iPhone SE", 375, 550),
       ("iPhone 16 Pro Max", 440, 860), ("340 phone", 340, 700), ("Fold open", 884, 900), ("iPad mini P", 744, 1050), ("iPad 13 P", 1024, 1290), ("iPad 13 L", 1366, 950),
       ("Phone L", 915, 360), ("iPhone L", 874, 370), ("Fold app L", 960, 412)]
SL = ["HDRI", "INSTA", "REF", "VB", "VB PMP", "PHOTOG", "TEXTURES", "GSPLAT", "WITNESS"]
AS = [("ENV", "PHOTOG"), ("ENV", "TEXTURES"), ("ENV", "GSPLAT"), ("ENV", "PLATE"), ("PROP", "PHOTOG"), ("CHAR", "PHOTOG"), ("CHAR", "WSCAN"), ("CHAR", "FACIAL"), ("VEH", "PHOTOG"), ("TILES", "TEXTURES")]
INFO = """() => { const f = document.getElementById('fields'), t = document.getElementById('top'), cs = getComputedStyle(document.documentElement);
  const rects = ['seg','preview','acts','clear','theme','dnu','show'].map(id => { const e = id === 'seg' ? t.querySelector('.seg') : document.getElementById(id); const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)].join(','); });
  const clipped = [...document.querySelectorAll('#acts .btn')].filter(b => !b.hidden && b.scrollWidth > b.clientWidth + 1).map(b => b.id);
  return { tu: cs.getPropertyValue('--tu'), u: cs.getPropertyValue('--u'), h: t.offsetHeight, scroll: f.scrollHeight - f.clientHeight, sig: t.offsetHeight + '|' + rects.slice(0, 5).join('|'), clipped }; }"""
FD = "/tmp/bur_slate_fonts/"
ROBOTO = None
if "roboto" in sys.argv:   # Android's font, so the widths match the Fold
    css = "".join(f"@font-face{{font-family:Roboto;font-weight:{w};src:url(file://{FD}roboto-latin-{f}-normal.woff2)}}" for w, f in [(400, 400), (500, 500), (600, 700), (700, 700)]) + ":root{--font-ui:Roboto,sans-serif !important}"
    ROBOTO = "document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=" + repr(css) + ";document.head.appendChild(s);});"
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in DEV:
        ctx = b.new_context(viewport={"width": w, "height": h}); pg = ctx.new_page()
        if ROBOTO: pg.add_init_script(ROBOTO)
        pg.goto(F); time.sleep(0.5)
        pg.fill("#f-slate", "90"); pg.dispatch_event("#f-slate", "input"); pg.locator("#f-slate").blur()
        sigs = set(); rows = []
        for t in SL:
            pg.select_option("#f-type", t); time.sleep(0.05); r = pg.evaluate(INFO); sigs.add(r["sig"]); rows.append((t, r))
        pg.click("#mode-asset")
        for c, a in AS:
            pg.select_option("#f-cat", c); pg.select_option("#f-atype", a); time.sleep(0.05); r = pg.evaluate(INFO); sigs.add(r["sig"]); rows.append((c + ":" + a, r))
        scrolls = [f"{k} {r['scroll']}" for k, r in rows if r["scroll"] > 1]
        clip = [f"{k} {r['clipped']}" for k, r in rows if r["clipped"]]
        us = sorted(float(r["u"]) for k, r in rows)
        ok = len(sigs) == 1 and not scrolls and not clip; bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {name} {w}x{h}: tu {rows[0][1]['tu']} top {rows[0][1]['h']}px ({round(100*rows[0][1]['h']/h)}%) | top layouts {len(sigs)} | fields u {us[0]:.2f}-{us[-1]:.2f}"
              + (f" | SCROLL {scrolls}" if scrolls else "") + (f" | CLIPPED {clip}" if clip else ""))
        ctx.close()
    b.close()
print("ALL SAME" if not bad else f"{bad} screens with problems")
