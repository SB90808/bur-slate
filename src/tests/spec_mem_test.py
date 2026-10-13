import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
def setv(pg, id, v): pg.fill("#" + id, v); pg.dispatch_event("#" + id, "input")
def line(pg): return pg.eval_on_selector("#preview .lt", "p => p.firstChild && p.firstChild.nodeType === 3 ? p.firstChild.textContent.trim() : ''")
ok = True
def chk(name, cond, info):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + "  [" + info + "]")
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 412, "height": 820}, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(F); time.sleep(0.6)
    setv(pg, "f-slate", "83A")
    pg.select_option("#f-type", "VB"); setv(pg, "f-spec", "full room")
    pg.select_option("#f-type", "PHOTOG"); chk("Photog starts empty", pg.input_value("#f-spec") == "", pg.input_value("#f-spec"))
    setv(pg, "f-spec", "smashed lights")
    pg.select_option("#f-type", "TEXTURES"); chk("Textures starts empty", pg.input_value("#f-spec") == "", pg.input_value("#f-spec"))
    setv(pg, "f-spec", "wall")
    pg.select_option("#f-type", "VB"); chk("VB keeps its own", pg.input_value("#f-spec") == "FULL ROOM" or pg.input_value("#f-spec").upper() == "FULL ROOM", line(pg))
    pg.select_option("#f-type", "PHOTOG"); chk("Photog keeps its own", pg.input_value("#f-spec").upper() == "SMASHED LIGHTS", line(pg))
    pg.press("#f-spec", "Enter"); time.sleep(0.5)                      # show -> saved
    pg.select_option("#f-type", "TEXTURES") if False else None
    pg.dblclick("#qrHalf"); time.sleep(0.7)
    pg.select_option("#f-type", "TEXTURES"); chk("Textures keeps its own", pg.input_value("#f-spec").upper() == "WALL", line(pg))
    pg.select_option("#f-type", "REF"); chk("Ref empty (never typed)", pg.input_value("#f-spec") == "", line(pg))
    pg.click("#mode-asset"); pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PHOTOG"); time.sleep(0.1)
    chk("Asset ENV Photog separate from slate Photog", pg.input_value("#f-spec") == "", pg.input_value("#f-spec"))
    setv(pg, "f-spec", "smashed cabinet")
    pg.select_option("#f-atype", "TEXTURES"); chk("ENV Textures separate", pg.input_value("#f-spec") == "", pg.input_value("#f-spec"))
    pg.select_option("#f-atype", "PHOTOG"); chk("ENV Photog keeps its own", pg.input_value("#f-spec").upper() == "SMASHED CABINET", pg.input_value("#f-spec"))
    pg.reload(); time.sleep(0.6)
    chk("After reload: ENV Photog still there", pg.input_value("#f-spec").upper() == "SMASHED CABINET", line(pg))
    pg.click("#mode-slate"); pg.select_option("#f-type", "VB"); chk("After reload: VB still its own", pg.input_value("#f-spec").upper() == "FULL ROOM", line(pg))
    pg.select_option("#f-type", "PHOTOG"); chk("After reload: Photog still its own", pg.input_value("#f-spec").upper() == "SMASHED LIGHTS", line(pg))
    chk("No page errors", not errs, "; ".join(errs))
    b.close()
print("ALL PASS" if ok else "SOMETHING FAILED")
