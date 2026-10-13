import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
DEV = [("iPhone 16 Pro Safari", 402, 740), ("iPhone 16 Pro app", 402, 820), ("iPhone 16 Pro Max", 440, 860), ("iPhone SE", 375, 550), ("Fold cover Chrome", 412, 780),
       ("Fold cover app", 412, 880), ("Fold open", 884, 900), ("340 phone", 340, 700), ("iPad mini P", 744, 1050), ("iPad 13 L", 1366, 950), ("Phone L", 915, 360)]
SL = ["HDRI", "INSTA", "REF", "VB", "VB PMP", "PHOTOG", "TEXTURES", "GSPLAT", "WITNESS"]
AS = [("ENV", "PHOTOG"), ("ENV", "TEXTURES"), ("ENV", "GSPLAT"), ("ENV", "PLATE"), ("PROP", "PHOTOG"), ("CHAR", "PHOTOG"), ("CHAR", "WSCAN"), ("CHAR", "FACIAL"), ("VEH", "PHOTOG"), ("TILES", "TEXTURES")]
CHK = """() => { const W = document.documentElement.clientWidth, bad = [];
  if (document.documentElement.scrollWidth > W + 1) bad.push('page ' + document.documentElement.scrollWidth);
  document.querySelectorAll('.top .seg, #theme, .top .line, .top .btn, .field, .field input, .field select, .step').forEach(e => {
    if (!e.offsetParent) return; const r = e.getBoundingClientRect(); if (r.right > W + 0.5) bad.push((e.id || e.className) + ' ' + Math.round(r.right)); });
  document.querySelectorAll('.top .btn').forEach(e => { if (e.offsetParent && e.scrollWidth > e.clientWidth + 1) bad.push(e.id + ' clipped'); });
  const cv = document.createElement('canvas').getContext('2d');
  document.querySelectorAll('.field select').forEach(x => { if (!x.offsetParent) return; const cs = getComputedStyle(x); cv.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
    const o = x.options[x.selectedIndex], word = o.dataset.short || o.text;   // the closed box shows the short word; the open list the full name
    if (cv.measureText(word).width * 1.05 + 2 > x.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)) bad.push(x.id + ' word cut'); });
  document.querySelectorAll('.selface').forEach(f => { if (f.offsetParent && f.scrollWidth > f.clientWidth + 1) bad.push('face cut ' + f.textContent); });
  const f = document.getElementById('fields'); if (f.scrollHeight > f.clientHeight + 1) bad.push('scroll ' + (f.scrollHeight - f.clientHeight));
  return bad; }"""
with sync_playwright() as p:
    b = p.chromium.launch(); total = 0; probs = 0
    for name, w, h in DEV:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)   # desktop mode: no auto zoom-out, so overflow shows
        pg = ctx.new_page(); pg.goto(F); time.sleep(0.5); pg.fill("#f-slate", "83A"); pg.dispatch_event("#f-slate", "input")
        out = []
        for t in SL:
            pg.select_option("#f-type", t); time.sleep(0.08); r = pg.evaluate(CHK); total += 1
            if r: probs += 1; out.append(f"{t}: {r}")
        pg.click("#mode-asset")
        for c, a in AS:
            pg.select_option("#f-cat", c); pg.select_option("#f-atype", a); time.sleep(0.08); r = pg.evaluate(CHK); total += 1
            if r: probs += 1; out.append(f"{c}:{a}: {r}")
        print(f"{name} {w}x{h}: " + ("all fit" if not out else " | ".join(out)))
        ctx.close()
    b.close(); print(f"{total - probs}/{total} layouts clean")
