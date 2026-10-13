import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 412, "height": 915}, device_scale_factor=2.6, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(F); time.sleep(0.6)
    # + Slates visibility per type
    vis = {}
    for t in ["HDRI", "INSTA", "REF", "VB", "VB PMP", "PHOTOG", "TEXTURES", "GSPLAT", "WITNESS"]:
        pg.select_option("#f-type", t); time.sleep(0.05); vis[t] = not pg.eval_on_selector("#w-slate2", "e => e.hidden")
    print("+ slates shown:", vis)
    # hidden + slates value is ignored
    pg.select_option("#f-type", "REF"); pg.fill("#f-slate", "83A"); pg.fill("#f-slate2", "40A"); pg.dispatch_event("#f-slate2", "input")
    print("ref line:", pg.text_content("#preview"))
    pg.select_option("#f-type", "WITNESS"); time.sleep(0.1); print("witness line:", pg.text_content("#preview"))
    # double-tap back, in portrait: QR is the bottom half
    pg.select_option("#f-type", "REF"); time.sleep(0.1); pg.tap("#show"); time.sleep(0.6)
    qr = pg.eval_on_selector("#qrHalf", "e => { const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    tx = pg.eval_on_selector("#slateText", "e => { const r = e.parentElement.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    pg.touchscreen.tap(*tx); time.sleep(0.12); pg.touchscreen.tap(*tx); time.sleep(0.7)
    print("double-tap on text half -> still on slate:", not pg.eval_on_selector("#stage", "e => e.hidden"))
    # tap where a form text box will be after the swap
    for trial in range(5):
        pg.touchscreen.tap(*qr); time.sleep(0.12); pg.touchscreen.tap(*qr); time.sleep(0.7)
        back = pg.eval_on_selector("#stage", "e => e.hidden")
        ae = pg.evaluate("document.activeElement && (document.activeElement.id || document.activeElement.tagName)")
        hit = pg.evaluate(f"(() => {{ const e = document.elementFromPoint({qr[0]}, {qr[1]}); return e && (e.id || e.className || e.tagName); }})()")
        print(f"trial {trial}: back to form: {back} | focused: {ae} | form element under finger: {hit}")
        pg.tap("#show"); time.sleep(0.6)
    # text-only (HDRI): double-tap anywhere
    pg.dblclick("#qrHalf") if False else None
    pg.touchscreen.tap(*qr); time.sleep(0.12); pg.touchscreen.tap(*qr); time.sleep(0.7)
    pg.select_option("#f-type", "HDRI"); pg.tap("#show"); time.sleep(0.6)
    pg.touchscreen.tap(*tx); time.sleep(0.12); pg.touchscreen.tap(*tx); time.sleep(0.7)
    print("hdri double-tap anywhere -> form:", pg.eval_on_selector("#stage", "e => e.hidden"), "| focused:", pg.evaluate("document.activeElement.id || document.activeElement.tagName"))
    # location: pick or type
    pg.tap("#mode-asset"); pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PHOTOG"); pg.fill("#f-loc", ""); pg.tap("#f-loc"); time.sleep(0.2)
    n_all = pg.eval_on_selector_all("#loc-sugg button", "es => es.length")
    first = pg.eval_on_selector("#loc-sugg button", "e => e.textContent") if n_all else ""; part = first.split(" ")[-1].lower()[:5]   # a word of the first built-in name
    pg.keyboard.type(part); time.sleep(0.2)
    print("locations on focus:", n_all, f"| {part!r}:", len(pg.eval_on_selector_all("#loc-sugg button", "es => es.map(e => e.textContent)")), "offered")
    pg.tap("#loc-sugg button >> nth=0"); time.sleep(0.3); pg.fill("#f-spec", "smashed cabinet"); pg.dispatch_event("#f-spec", "input")
    print("picked:", pg.text_content("#preview"))
    pg.tap("#f-loc"); pg.fill("#f-loc", ""); pg.keyboard.type("north tunnel"); time.sleep(0.2)
    print("new loc hint:", pg.eval_on_selector_all("#loc-sugg > *", "es => es.map(e => e.textContent)"))
    pg.screenshot(path="/tmp/bur_slate_shots/loc_new.png")
    pg.keyboard.press("Enter"); time.sleep(0.6); print("new loc slate:", repr(pg.text_content("#slateText")))
    print("errors:", errs)
    b.close()
