import os
from pathlib import Path
import time, sys
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
O = "/tmp/bur_slate_shots/"
FD = "/tmp/bur_slate_fonts/"
css = "".join(f"@font-face{{font-family:Roboto;font-weight:{w};src:url(file://{FD}roboto-latin-{f}-normal.woff2)}}" for w, f in [(400, 400), (500, 500), (600, 700), (700, 700)]) + ":root{--font-ui:Roboto,sans-serif !important}"
INIT = "document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=" + repr(css) + ";document.head.appendChild(s);});"
from PIL import Image
def sheet(names, out, scale=1):
    ims = [Image.open(O + n) for n in names]; W = sum(i.width + 10 for i in ims); H = max(i.height for i in ims)
    c = Image.new("RGB", (W, H), "#c00"); x = 0
    for i in ims: c.paste(i, (x, 0)); x += i.width + 10
    if scale != 1: c = c.resize((int(c.width * scale), int(c.height * scale)))
    c.save(O + out)
with sync_playwright() as p:
    b = p.chromium.launch()
    for tag, w, h in [("P", 412, 780), ("L", 960, 412)]:
        ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme="dark"); pg = ctx.new_page(); pg.add_init_script(INIT); pg.goto(F); time.sleep(0.5)
        names = []
        pg.fill("#f-slate", "90")
        for t in ["WITNESS", "REF", "TEXTURES"]:
            pg.select_option("#f-type", t)
            if t == "WITNESS": pg.fill("#f-focal", "50")
            pg.dispatch_event("#f-slate", "input"); pg.locator("#f-slate").blur(); time.sleep(0.15); pg.screenshot(path=O + f"t{tag}_{t}.png"); names.append(f"t{tag}_{t}.png")
        pg.click("#mode-asset"); pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PHOTOG"); time.sleep(0.15); pg.screenshot(path=O + f"t{tag}_ENV.png"); names.append(f"t{tag}_ENV.png")
        sheet(names, f"top_{tag}.png", 1 if tag == "P" else 0.5)
        ctx.close()
    b.close()
