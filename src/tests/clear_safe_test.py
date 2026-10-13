import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
ok = []; errs = []
def check(name, cond, info=""):
    ok.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name, info)
with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------- Clear + Undo ----------
    ctx = b.new_context(viewport={"width": 412, "height": 880}, device_scale_factor=2, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(F); time.sleep(0.4)
    pg.evaluate("localStorage.clear()"); pg.reload(); time.sleep(0.4)
    pg.select_option("#f-type", "REF"); pg.fill("#f-slate", "83A"); pg.fill("#f-slate2", "40A 40B"); pg.fill("#f-spec", "chrome ball")
    for _ in range(3): pg.click("[data-step=f-pos][data-d='1']")
    pg.click("#f-add"); pg.dispatch_event("#f-slate", "input"); time.sleep(0.1)
    before = pg.inner_text("#preview")
    check("Filled before clear", "83A + 40A + 40B / REF / CHROME BALL POS 4 / ADD" in before, before)
    pg.select_option("#f-type", "VB"); pg.fill("#f-spec", "full room"); pg.dispatch_event("#f-spec", "input")
    pg.select_option("#f-type", "REF"); time.sleep(0.1)
    # Clear sits beside the theme button, same row
    cb, tb = pg.locator("#clear").bounding_box(), pg.locator("#theme").bounding_box()
    check("Clear beside theme button", abs(cb["y"] - tb["y"]) < 6 and cb["x"] < tb["x"], (cb, tb))
    pg.click("#clear"); time.sleep(0.15)
    vals = pg.evaluate("() => ['f-slate','f-slate2','f-spec','f-pos','f-take'].map(i => document.getElementById(i).value).concat([document.getElementById('f-add').checked, document.getElementById('f-type').value])")
    check("Clear empties fields, pos/take 1, ADD off, type kept", vals == ["", "", "", "1", "1", False, "REF"], vals)
    check("Toast shows with Undo", pg.is_visible("#toast") and pg.is_visible("#toast-undo"))
    pg.select_option("#f-type", "VB"); time.sleep(0.05)
    check("Other types' specifics cleared too", pg.input_value("#f-spec") == "", pg.input_value("#f-spec"))
    pg.select_option("#f-type", "REF"); time.sleep(0.05)
    pg.click("#toast-undo"); time.sleep(0.15)
    after = pg.inner_text("#preview")
    check("Undo restores everything", after == before, after)
    pg.select_option("#f-type", "VB"); time.sleep(0.05)
    check("Undo restores other types' specifics", pg.input_value("#f-spec").upper() == "FULL ROOM", pg.input_value("#f-spec"))
    check("Toast gone after Undo", not pg.is_visible("#toast"))
    # clear in asset mode keeps the mode + category
    pg.click("#mode-asset"); pg.select_option("#f-cat", "CHAR"); pg.select_option("#f-atype", "FACIAL"); pg.fill("#f-char", "Guard 2"); pg.fill("#f-stunt", "John Smith")
    pg.click("[data-step=f-take][data-d='1']"); pg.click("#clear"); time.sleep(0.15)
    a = pg.evaluate("() => [document.getElementById('mode-asset').getAttribute('aria-pressed'), document.getElementById('f-cat').value, document.getElementById('f-atype').value, document.getElementById('f-char').value, document.getElementById('f-stunt').value, document.getElementById('f-take').value, document.getElementById('f-date').value.length]")
    check("Asset clear: mode/category/type kept, names gone, take 1, date today", a == ["true", "CHAR", "FACIAL", "", "", "1", 6], a)
    time.sleep(6.5)
    check("Toast hides by itself", not pg.is_visible("#toast"))
    pg.reload(); time.sleep(0.4)
    check("Cleared state survives reload", pg.input_value("#f-char") == "" and pg.input_value("#f-take") == "1")
    # ADD: label first, box after it, away from the +
    pg.click("#mode-slate"); pg.select_option("#f-type", "REF"); time.sleep(0.1)
    lb, ab, plus = pg.locator("#w-add label").bounding_box(), pg.locator("#f-add").bounding_box(), pg.locator("[data-step=f-pos][data-d='1']").bounding_box()
    check("ADD: text first, tick box after it", lb["x"] + lb["width"] <= ab["x"] + 1, (lb, ab))
    check("ADD box not right next to +", ab["x"] - (plus["x"] + plus["width"]) > 40 or abs(ab["y"] - plus["y"]) > 30, (plus, ab))
    # the words hug the tick box (Steve, 13 Oct evening: "closer to the tick box")
    tx = pg.evaluate("() => { const l = document.querySelector('#w-add label'), r = document.createRange(); r.selectNodeContents(l); const t = r.getBoundingClientRect(), b = document.getElementById('f-add').getBoundingClientRect(); return [Math.round(b.left - t.right), getComputedStyle(l).textAlign]; }")
    check("ADD words sit right by the tick box", 0 <= tx[0] <= 20 and tx[1] == "right", tx)
    ctx.close()
    # ---------- safe areas (iPhone 16 Pro on its side: Dynamic Island 62px, home bar 21px) ----------
    SAFE = ":root{--sal:62px !important;--sar:62px !important;--sab:21px !important}"
    cases = [("S", "VB PMP", None), ("S", "TEXTURES", None), ("S", "WITNESS", None), ("S", "HDRI", None), ("A", "ENV", "TEXTURES"), ("A", "ENV", "PLATE")]
    for w, h in [(874, 402), (874, 370)]:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=3)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(F); time.sleep(0.4); pg.add_style_tag(content=SAFE)
        for m, x, y in cases:
            if m == "S":
                pg.click("#mode-slate"); pg.select_option("#f-type", x); pg.fill("#f-slate", "112BX")
                if pg.is_visible("#f-spec"): pg.fill("#f-spec", "smashed cabinet wide angle")
                if pg.is_visible("#f-focal"): pg.fill("#f-focal", "35")
                pg.dispatch_event("#f-spec", "input")
            else:
                pg.click("#mode-asset"); pg.select_option("#f-cat", x); pg.select_option("#f-atype", y)
                pg.fill("#f-loc", "Old Station Yard"); pg.dispatch_event("#f-loc", "input"); pg.fill("#f-spec", "smashed cabinet"); pg.dispatch_event("#f-spec", "input")
                pg.locator("#f-spec").blur(); time.sleep(0.25)
            time.sleep(0.1); pg.click("#show"); time.sleep(0.3)
            r = pg.evaluate("""() => { const t = document.getElementById('slateText'), rg = document.createRange(); rg.selectNodeContents(t); const b = rg.getBoundingClientRect();
                const q = document.getElementById('qrHalf'); const qb = q.hidden ? null : document.getElementById('qrBox').getBoundingClientRect();
                return { l: b.left, r: b.right, t: b.top, b: b.bottom, q: qb && [qb.left, qb.right, qb.bottom], text: t.textContent, W: innerWidth, H: innerHeight }; }""")
            good = r["l"] >= 62 and r["r"] <= r["W"] - 62 and r["b"] <= r["H"] - 21 and r["t"] >= 0 and (not r["q"] or (r["q"][0] >= 62 and r["q"][1] <= r["W"] - 62 and r["q"][2] <= r["H"] - 21))
            check(f"{w}x{h} {m}:{x}{'/' + y if y else ''} slate clear of the island", good, f"text {round(r['l'])}-{round(r['r'])} qr {r['q'] and [round(v) for v in r['q']]} | {r['text']!r}")
            pg.screenshot(path=f"/tmp/bur_slate_shots/safe_{h}_{x}{y or ''}.png".replace(" ", ""))
            pg.dblclick("#stage"); time.sleep(0.7)
        # form clear of the island too
        bad = pg.evaluate("() => [...document.querySelectorAll('.top .seg, .top .line, .top .btn, .field')].filter(e => e.offsetParent).filter(e => { const r = e.getBoundingClientRect(); return r.left < 61.5 || r.right > innerWidth - 61.5; }).map(e => e.id || e.className)")
        check(f"{w}x{h} form clear of the island", not bad, bad[:4])
        ctx.close()
    b.close()
check("No page errors", not errs, errs)
print(f"\n{sum(ok)}/{len(ok)} passed")
