import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in [("iPhone 16 Pro Safari", 402, 740), ("iPhone 16 Pro home-screen app", 402, 820), ("iPhone SE Safari", 375, 550)]:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=3, is_mobile=True, has_touch=True, color_scheme="dark")
        pg = ctx.new_page(); pg.goto(F); time.sleep(0.6)
        pg.fill("#f-slate", "83A"); pg.dispatch_event("#f-slate", "input")
        rows = []
        for t in ["HDRI", "REF", "VB", "PHOTOG", "TEXTURES", "WITNESS"]:
            pg.select_option("#f-type", t); time.sleep(0.15)
            r = pg.evaluate("""() => ({u: +getComputedStyle(document.documentElement).getPropertyValue('--u'),
                minFont: Math.min(...[...document.querySelectorAll('.field input:not([type=checkbox]), .field select')].filter(e => e.offsetParent).map(e => parseFloat(getComputedStyle(e).fontSize))),
                wide: document.documentElement.scrollWidth > innerWidth || [...document.querySelectorAll('.top *, .field')].some(e => e.offsetParent && e.getBoundingClientRect().right > innerWidth + 0.5)})""")
            rows.append(f"{t} u{r['u']:.2f} min font {r['minFont']:.0f}px" + (" OFF-SCREEN" if r["wide"] else ""))
        # an open drop-down (iOS picker) shrinks the visible area: the form must not re-size under it
        pg.select_option("#f-type", "TEXTURES"); time.sleep(0.15)
        u0 = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--u')")
        pg.focus("#f-type"); pg.set_viewport_size({"width": w, "height": int(h * 0.6)}); time.sleep(0.4)
        u1 = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--u')")
        pg.evaluate("document.activeElement.blur()"); pg.set_viewport_size({"width": w, "height": h}); time.sleep(0.4)
        u2 = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--u')")
        print(f"{name}: " + " | ".join(rows) + f" || picker open: u {u0.strip()} -> {u1.strip()} (steady: {u0 == u1}), closed -> {u2.strip()}")
        if name.startswith("iPhone 16 Pro Safari"):
            pg.select_option("#f-type", "WITNESS"); time.sleep(0.2); pg.screenshot(path="/tmp/bur_slate_shots/ip16_witness.png")
            pg.select_option("#f-type", "TEXTURES"); time.sleep(0.2); pg.screenshot(path="/tmp/bur_slate_shots/ip16_textures.png")
        ctx.close()
    b.close()
