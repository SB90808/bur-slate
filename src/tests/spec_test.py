import os
from pathlib import Path
import time, cv2
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
results = []
def check(name, ok, info=""):
    results.append((name, bool(ok), info)); print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""))
def line(pg): return pg.eval_on_selector("#preview .lt", "p => p.firstChild ? (p.firstChild.nodeType === 3 ? p.firstChild.textContent : '') : ''").strip()
def vis(pg, id): return pg.eval_on_selector("#" + id, "e => !e.hidden && e.offsetParent !== null")
def setv(pg, id, v): pg.fill("#" + id, v); pg.dispatch_event("#" + id, "input")
def qr(pg, tag):
    pg.screenshot(path=f"/tmp/bur_slate_shots/spec_{tag}.png"); d, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(f"/tmp/bur_slate_shots/spec_{tag}.png")); return d
def back(pg):
    t = "#stage" if pg.eval_on_selector("#qrHalf", "e => e.hidden") else "#qrHalf"
    xy = pg.eval_on_selector(t, "e => { const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    pg.touchscreen.tap(*xy); time.sleep(0.12); pg.touchscreen.tap(*xy); time.sleep(0.7)
PAIR = """([a, b]) => { const x = document.getElementById(a).getBoundingClientRect(), y = document.getElementById(b).getBoundingClientRect(); return Math.abs(x.top - y.top) < 1 && x.right <= y.left; }"""
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 412, "height": 820}, device_scale_factor=2.6, is_mobile=True, has_touch=True, color_scheme="dark")
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(F); time.sleep(0.8)
    check("Opens in Slate mode", pg.get_attribute("#mode-slate", "aria-pressed") == "true")
    check("Phone's own font, Graphite dark colours", "-apple-system" in pg.eval_on_selector("#f-slate", "e => getComputedStyle(e).fontFamily")
          and pg.eval_on_selector("#editor", "e => getComputedStyle(e).backgroundColor") == "rgb(0, 0, 0)"
          and pg.eval_on_selector("#show", "e => getComputedStyle(e).backgroundColor") == "rgb(245, 245, 247)"
          and pg.eval_on_selector("#dnu", "e => getComputedStyle(e).color") == "rgb(255, 69, 58)")
    check("No 'On the slate' tip", "double-tap" not in pg.inner_text("#fields"))
    setv(pg, "f-slate", "83a")
    types = ["HDRI", "INSTA", "REF", "VB", "VB PMP", "PHOTOG", "TEXTURES", "GSPLAT", "WITNESS"]
    side, plus = [], {}
    for t in types:
        pg.select_option("#f-type", t); time.sleep(0.1)
        side.append(pg.evaluate(PAIR, ["f-slate", "f-type"])); plus[t] = vis(pg, "w-slate2")
    check("Slate and Type side by side in every type", all(side))
    check("+ Slates only on Insta360 and Ref", [t for t in types if plus[t]] == ["INSTA", "REF"], ", ".join(t for t in types if plus[t]))
    pg.select_option("#f-type", "REF"); time.sleep(0.1)
    under = pg.evaluate("() => { const s = document.getElementById('f-type').getBoundingClientRect(), w = document.getElementById('w-slate2').getBoundingClientRect(); return w.top > s.bottom && w.top - s.bottom < 40; }")
    check("+ Slates sits straight under Slate / Type", under)
    setv(pg, "f-slate2", "40a 40b 40c"); time.sleep(0.1)
    check("+ Slates: each word is a slate", line(pg) == "83A + 40A + 40B + 40C / REF", line(pg))
    pg.select_option("#f-type", "HDRI"); time.sleep(0.1)
    check("Hidden + Slates never reaches the line (HDRI)", line(pg) == "83A / POS 1", line(pg))
    pg.select_option("#f-type", "REF"); setv(pg, "f-slate2", ""); pg.tap("#f-add"); time.sleep(0.1)
    check("Ref ADD", line(pg) == "83A / REF / ADD", line(pg))
    sz = pg.evaluate("() => { const a = document.getElementById('f-add').getBoundingClientRect(), b = document.querySelector('[data-step=\"f-pos\"][data-d=\"1\"]').getBoundingClientRect(); return [a.width, a.height, b.width, b.height]; }")
    check("ADD box same size as the + button", abs(sz[0] - sz[2]) < 1 and abs(sz[1] - sz[3]) < 1, f"{sz[0]:.0f}x{sz[1]:.0f} vs {sz[2]:.0f}x{sz[3]:.0f}")
    pg.tap("#f-add")
    # HDRI
    pg.select_option("#f-type", "HDRI"); time.sleep(0.1)
    check("HDRI has an optional Specific", vis(pg, "w-spec") and "optional" in pg.text_content("#l-spec").lower())
    setv(pg, "f-spec", "robot mark"); check("HDRI specific in the line", line(pg) == "83A / ROBOT MARK POS 1", line(pg))
    opts = pg.eval_on_selector_all("#f-npos option", "os => os.map(o => +o.value)")
    pg.select_option("#f-npos", "10"); time.sleep(0.1)
    check("HDRI positions in folder go to 10", opts == list(range(1, 11)) and line(pg) == "83A / ROBOT MARK POS 1-10", line(pg))
    pg.select_option("#f-npos", "1"); setv(pg, "f-spec", "")
    pg.press("#f-slate", "Enter"); time.sleep(0.6)
    check("HDRI shows text only (no QR)", pg.eval_on_selector("#qrHalf", "e => e.hidden") and not pg.eval_on_selector("#stage", "e => e.hidden"))
    check("Enter shows the slate and drops the keyboard", pg.evaluate("document.activeElement === document.body"))
    back(pg)
    pg.select_option("#f-type", "INSTA"); time.sleep(0.1); check("Insta360 line", line(pg) == "83A", line(pg))
    pg.tap("#show"); time.sleep(0.5); check("Insta360 text only", pg.eval_on_selector("#qrHalf", "e => e.hidden")); back(pg)
    # slate-specific types
    pg.select_option("#f-type", "VB"); setv(pg, "f-spec", "full room"); pg.click('[data-step="f-pos"][data-d="1"]'); time.sleep(0.1)
    check("VB line", line(pg) == "83A / VB / FULL ROOM POS 2", line(pg))
    pg.select_option("#f-type", "VB PMP"); time.sleep(0.1); check("VB PMP starts with its own (empty) specific", pg.input_value("#f-spec") == "")
    setv(pg, "f-spec", "full room"); check("VB PMP line", line(pg) == "83A / VB PMP / FULL ROOM POS 2", line(pg))
    pg.select_option("#f-type", "PHOTOG"); setv(pg, "f-spec", "smashed lights"); check("Photog line", line(pg) == "83A / PHOTOG / SMASHED LIGHTS POS 2", line(pg))
    pg.select_option("#f-type", "TEXTURES"); setv(pg, "f-spec", "wall"); check("Textures line", line(pg) == "83A / TEXTURES / WALL", line(pg))
    pg.select_option("#f-type", "GSPLAT"); setv(pg, "f-spec", "statue"); check("Gsplat line", line(pg) == "83A / GSPLAT / STATUE POS 2", line(pg))
    pg.click('[data-step="f-pos"][data-d="-1"]')
    pg.select_option("#f-type", "WITNESS"); time.sleep(0.1)
    check("Witness keeps Focal and Take", vis(pg, "w-focal") and vis(pg, "w-take"))
    setv(pg, "f-focal", "50"); check("Witness line", line(pg) == "83A / 50MM / TK1", line(pg))
    pg.tap("#show"); time.sleep(0.6)
    st = pg.evaluate("() => { const t = document.getElementById('slateText').parentElement.getBoundingClientRect(), q = document.getElementById('qrHalf').getBoundingClientRect(); return [t.bottom <= q.top + 1, getComputedStyle(document.getElementById('stage')).backgroundColor]; }")
    check("Portrait: text on top, QR below", st[0])
    check("Witness QR reads", qr(pg, "wit_p") == "BUR:83A / 50MM / TK1")
    check("Dark mode slate: white on black", st[1] == "rgb(0, 0, 0)" and pg.eval_on_selector("#slateText", "e => getComputedStyle(e).color") == "rgb(255, 255, 255)")
    xy = pg.eval_on_selector("#slateText", "e => { const r = e.parentElement.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    pg.touchscreen.tap(*xy); time.sleep(0.12); pg.touchscreen.tap(*xy); time.sleep(0.6)
    check("Double-tap on the text does not leave the slate", not pg.eval_on_selector("#stage", "e => e.hidden"))
    back(pg)
    check("Double-tap the QR goes back, no text box opens", pg.eval_on_selector("#stage", "e => e.hidden") and pg.evaluate("document.activeElement === document.body"))
    pg.tap("#bump"); time.sleep(0.6); check("TK +1 & Show", qr(pg, "bump") == "BUR:83A / 50MM / TK2"); back(pg)
    pg.tap("#dnu"); time.sleep(0.5)
    check("DO NOT USE: text only", pg.eval_on_selector("#qrHalf", "e => e.hidden") and pg.text_content("#slateText").replace("\n", " ") == "DO NOT USE"); back(pg)
    # assets
    pg.tap("#mode-asset"); time.sleep(0.2)
    cats = []
    for c in ["ENV", "PROP", "CHAR", "VEH", "TILES"]:
        pg.select_option("#f-cat", c); time.sleep(0.1); cats.append(pg.evaluate(PAIR, ["f-cat", "f-atype"]))
    check("Category and Type side by side in every category", all(cats))
    pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PHOTOG"); setv(pg, "f-spec", "smashed cabinet")
    pg.fill("#f-loc", ""); pg.tap("#f-loc"); pg.keyboard.type("museum"); time.sleep(0.2)
    sug = pg.eval_on_selector_all("#loc-sugg button", "bs => bs.map(b => b.textContent)")
    pg.tap("#loc-sugg button >> nth=0"); time.sleep(0.3)
    check("Location: pick from the list as you type", sug and line(pg) == f"ENV / {sug[0]} / PHOTOG / SMASHED CABINET", line(pg))
    pg.tap("#f-loc"); pg.fill("#f-loc", ""); pg.keyboard.type("north tunnel"); time.sleep(0.2)
    check("Location: type a new one", line(pg) == "ENV / NORTH TUNNEL / PHOTOG / SMASHED CABINET" and "New location" in pg.text_content("#loc-sugg"), line(pg))
    pg.select_option("#f-atype", "PLATE"); setv(pg, "f-take", "1"); setv(pg, "f-loc", "old station yard"); setv(pg, "f-spec", "guard element"); setv(pg, "f-focal", "24")
    check("ENV plate line (with focal)", line(pg) == "ENV / OLD STATION YARD / GUARD ELEMENT / 24MM / TK1", line(pg))
    pg.tap("#show"); time.sleep(0.6); check("ENV plate QR reads", qr(pg, "plate") == "BUR:ENV / OLD STATION YARD / GUARD ELEMENT / 24MM / TK1"); back(pg)
    pg.select_option("#f-cat", "PROP"); pg.select_option("#f-atype", "PHOTOG"); setv(pg, "f-spec", "")
    pg.fill("#f-name", ""); pg.tap("#f-name"); pg.keyboard.type("golden scarab"); time.sleep(0.2)
    check("Prop: any new name types freely", line(pg) == "PROP / GOLDEN SCARAB / PHOTOG", line(pg))
    pg.fill("#f-name", ""); pg.keyboard.type("museum"); time.sleep(0.2); pg.tap("#name-sugg button >> nth=0"); time.sleep(0.3)
    check("Prop: known names offered as you type", line(pg).startswith("PROP / ") and "MUSEUM" in line(pg), line(pg))
    pg.select_option("#f-cat", "CHAR"); pg.select_option("#f-atype", "WSCAN"); time.sleep(0.1)
    setv(pg, "f-char", "guard 1"); check("Character WSCAN (typed name)", line(pg) == "CHAR / GUARD 1 / WSCAN", line(pg))
    pg.select_option("#f-atype", "FACIAL"); setv(pg, "f-char", "guard 1"); setv(pg, "f-stunt", "john smith"); setv(pg, "f-date", "261013"); setv(pg, "f-focal", "")
    check("Facial capture line", line(pg) == "GUARD 1 - JOHN SMITH / 261013 / TK1", line(pg))
    check("Facial capture says Real name", pg.text_content("label[for=f-stunt]") == "Real name" and "real name" in pg.text_content("#note"))
    # long line wraps and shrinks to stay fully visible
    pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PLATE"); setv(pg, "f-loc", "old station yard outside the main gate"); setv(pg, "f-spec", "guard running left to right")
    check("Long slate line fully visible in the top box", pg.eval_on_selector("#preview", "p => { const cs = getComputedStyle(p); return p.firstElementChild.offsetHeight <= p.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) + 1; }"))
    # light mode
    pg.tap("#theme"); time.sleep(0.3)
    check("Light mode Graphite colours", pg.eval_on_selector("#editor", "e => getComputedStyle(e).backgroundColor") == "rgb(245, 245, 247)"
          and pg.eval_on_selector("#show", "e => getComputedStyle(e).backgroundColor") == "rgb(29, 29, 31)")
    pg.tap("#show"); time.sleep(0.6)
    check("Light mode slate: black on white", pg.eval_on_selector("#stage", "e => getComputedStyle(e).backgroundColor") == "rgb(255, 255, 255)"
          and pg.eval_on_selector("#slateText", "e => getComputedStyle(e).color") == "rgb(0, 0, 0)")
    check("QR reads on the white slate", qr(pg, "white").startswith("BUR:ENV / OLD STATION YARD OUTSIDE"))
    back(pg); pg.reload(); time.sleep(0.6)
    check("Theme remembered after reload", pg.eval_on_selector("#editor", "e => getComputedStyle(e).backgroundColor") == "rgb(245, 245, 247)")
    check("No page errors", not errs, "; ".join(errs))
    ctx.close()
    # landscape: text left, QR right
    ctx = b.new_context(viewport={"width": 904, "height": 412}, device_scale_factor=2.6, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); pg.goto(F); time.sleep(0.6)
    setv(pg, "f-slate", "83A"); pg.select_option("#f-type", "REF"); setv(pg, "f-spec", ""); pg.tap("#show"); time.sleep(0.6)
    lr = pg.evaluate("() => { const t = document.getElementById('slateText').parentElement.getBoundingClientRect(), q = document.getElementById('qrHalf').getBoundingClientRect(); return t.right <= q.left + 1 && Math.abs(t.width - q.width) < 2; }")
    check("Landscape: text left half, QR right half", lr)
    check("Landscape QR reads", qr(pg, "land") == "BUR:83A / REF")
    b.close()
print(f"\n{sum(r[1] for r in results)}/{len(results)} passed")
