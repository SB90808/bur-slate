import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
CHK = """() => { const W = document.documentElement.clientWidth; const bad = [];
  document.querySelectorAll('.top .btn, .top .seg, .top .line').forEach(e => { if (e.offsetParent === null) return; const r = e.getBoundingClientRect();
    if (r.right > W - 1 || r.left < 0) bad.push((e.id || e.className) + ' off-screen');
    if (e.scrollWidth > e.clientWidth + 1 && !e.classList.contains('line')) bad.push((e.id || e.className) + ' text clipped'); });
  return bad; }"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in [("Fold cover", 412, 820), ("iPhone SE", 375, 550), ("iPhone 15", 393, 660), ("narrow 340", 340, 700), ("iPad mini P", 744, 1050), ("iPad 13 L", 1366, 950), ("Phone L", 915, 360)]:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); pg.goto(F); time.sleep(0.5); pg.fill("#f-slate", "83A"); pg.dispatch_event("#f-slate", "input")
        out = []
        for t in ["HDRI", "REF", "WITNESS", "PHOTOG"]:
            pg.select_option("#f-type", t); time.sleep(0.1)
            u = float(pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--u')"))
            out.append(f"{t} u{u:.2f} {pg.evaluate(CHK) or 'ok'}")
            if name == "Fold cover" and t == "REF": pg.screenshot(path="/tmp/bur_slate_shots/acts_fold.png")
            if name == "narrow 340" and t == "WITNESS": pg.screenshot(path="/tmp/bur_slate_shots/acts_340.png")
        print(name, " | ".join(out)); ctx.close()
    b.close()
