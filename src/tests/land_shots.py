import os
from pathlib import Path
import sys, time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
OUT = "/tmp/bur_slate_shots/"
DEV = [("fold_chrome", 915, 360), ("iphone_safari", 874, 370), ("fold_app", 960, 412)]
SL = ["HDRI", "REF", "VB", "VB PMP", "PHOTOG", "TEXTURES", "WITNESS"]
AS = [("ENV", "PHOTOG"), ("ENV", "TEXTURES"), ("ENV", "PLATE"), ("PROP", "PHOTOG"), ("CHAR", "FACIAL"), ("TILES", "TEXTURES")]
INFO = """() => { const f = document.getElementById('fields'), t = document.getElementById('top');
  return { u: getComputedStyle(document.documentElement).getPropertyValue('--u'), top: Math.round(t.offsetHeight), scroll: f.scrollHeight - f.clientHeight,
           cols: getComputedStyle(f).gridTemplateColumns.split(' ').length }; }"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in DEV:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
        pg = ctx.new_page(); pg.goto(F); time.sleep(0.4); pg.fill("#f-slate", "83A"); pg.dispatch_event("#f-slate", "input")
        for t in SL:
            pg.select_option("#f-type", t); time.sleep(0.1); i = pg.evaluate(INFO); print(name, t, i)
            pg.screenshot(path=OUT + f"{name}_{t.replace(' ', '')}.png")
        pg.click("#mode-asset")
        for c, a in AS:
            pg.select_option("#f-cat", c); pg.select_option("#f-atype", a); time.sleep(0.1); i = pg.evaluate(INFO); print(name, c, a, i)
            pg.screenshot(path=OUT + f"{name}_{c}_{a}.png")
        ctx.close()
    b.close()
