import os
from pathlib import Path
import time, cv2
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
ok = []; errs = []
def check(name, cond, info=""):
    ok.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name, info)
def qr(pg, tag):
    path = f"/tmp/bur_slate_shots/swipe_{tag}.png"; pg.screenshot(path=path); d, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(path)); return d
def touch_swipe(pg, cdp, x0, y0, x1, y1, steps=8, dur=0.25):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        time.sleep(dur / steps)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / steps, "y": y0 + (y1 - y0) * i / steps}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); time.sleep(0.15)
def tap(cdp, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(0.04)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
LINE = "() => document.getElementById('slateText').textContent.replace(/\\n/g, ' ')"
def strip(pg):
    return pg.evaluate("() => { const r = document.getElementById('tkline').getBoundingClientRect(), h = document.getElementById('slateText').parentElement.getBoundingClientRect(); return [h.left, h.right, r.top, r.bottom]; }")
def setup(pg, kind):
    if kind == "WITNESS":
        pg.click("#mode-slate"); pg.select_option("#f-type", "WITNESS"); pg.fill("#f-slate", "90"); pg.fill("#f-focal", "50")
    elif kind == "PLATE":
        pg.click("#mode-asset"); pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PLATE"); pg.fill("#f-loc", "North Tunnel"); pg.fill("#f-spec", "doorway"); pg.fill("#f-focal", "24")
    elif kind == "FACIAL":
        pg.click("#mode-asset"); pg.select_option("#f-cat", "CHAR"); pg.select_option("#f-atype", "FACIAL"); pg.fill("#f-char", "Guard 1"); pg.fill("#f-stunt", "John Smith"); pg.fill("#f-focal", "50")
    pg.fill("#f-take", "1"); pg.dispatch_event("#f-take", "input"); pg.locator("#f-take").blur(); time.sleep(0.3)
    pg.click("#show"); time.sleep(0.4)
with sync_playwright() as p:
    b = p.chromium.launch()
    for dev, w, h in [("Fold portrait", 412, 880), ("Fold landscape", 960, 412)]:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); cdp = ctx.new_cdp_session(pg)
        pg.goto(F); time.sleep(0.4); pg.evaluate("localStorage.clear()"); pg.reload(); time.sleep(0.4)
        for kind in ["WITNESS", "PLATE", "FACIAL"]:
            setup(pg, kind)
            l0 = pg.evaluate(LINE); x0, x1, t, bt = strip(pg); y = (t + bt) / 2; cx = (x0 + x1) / 2; span = (x1 - x0) * 0.6
            touch_swipe(pg, cdp, cx + span / 2, y, cx - span / 2, y + 6)
            l1 = pg.evaluate(LINE); q = qr(pg, f"{dev[:4]}_{kind}_r")
            check(f"{dev} {kind}: swipe right to left -> next take", "TK2" in l1 and q.endswith("TK2"), f"{l0!r} -> {l1!r} | QR {q!r}")
            touch_swipe(pg, cdp, cx - span / 2, y, cx + span / 2, y - 6)
            l2 = pg.evaluate(LINE); check(f"{dev} {kind}: swipe left to right -> take back", "TK1" in l2 and qr(pg, f"{dev[:4]}_{kind}_l").endswith("TK1"), l2)
            touch_swipe(pg, cdp, cx - span / 2, y, cx + span / 2, y)
            check(f"{dev} {kind}: never below take 1", "TK1" in pg.evaluate(LINE), pg.evaluate(LINE))
            if kind == "WITNESS":
                x0, x1, t, bt = strip(pg); y = (t + bt) / 2
                for _ in range(3): touch_swipe(pg, cdp, cx + span / 2, y, cx - span / 2, y)
                check(f"{dev}: three swipes right to left -> TK4", "TK4" in pg.evaluate(LINE), pg.evaluate(LINE))
                x0, x1, t, bt = strip(pg); y = (t + bt) / 2
                touch_swipe(pg, cdp, cx, y - 5, cx + 20, y + 140)
                check(f"{dev}: up/down drag in the strip does nothing", "TK4" in pg.evaluate(LINE))
                touch_swipe(pg, cdp, cx - 15, y, cx + 15, y)
                check(f"{dev}: short nudge does nothing", "TK4" in pg.evaluate(LINE))
                top = pg.evaluate("() => document.getElementById('slateText').getBoundingClientRect().top")
                if t - top > 40:
                    touch_swipe(pg, cdp, cx - span / 2, top + 10, cx + span / 2, top + 10)
                    check(f"{dev}: swipe on another line does nothing", "TK4" in pg.evaluate(LINE))
                tap(cdp, cx, y); time.sleep(0.1); tap(cdp, cx, y); time.sleep(0.7)
                check(f"{dev}: double-tap on the text half stays on the slate", pg.is_visible("#stage"))
            qb = pg.locator("#qrHalf").bounding_box(); qx, qy = qb["x"] + qb["width"] / 2, qb["y"] + qb["height"] / 2
            tap(cdp, qx, qy); time.sleep(0.12); tap(cdp, qx, qy); time.sleep(0.8)
            check(f"{dev} {kind}: double-tap QR goes back", pg.is_visible("#editor") and not pg.is_visible("#stage"))
            exp = "4" if kind == "WITNESS" else "1"
            check(f"{dev} {kind}: form shows the swiped take", pg.input_value("#f-take") == exp and f"TK{exp}" in pg.inner_text("#preview"), pg.input_value("#f-take"))
        # no swipe where there is no take
        pg.click("#mode-slate"); pg.select_option("#f-type", "REF"); pg.fill("#f-slate", "90"); pg.dispatch_event("#f-slate", "input"); time.sleep(0.2); pg.click("#show"); time.sleep(0.4)
        l0 = pg.evaluate(LINE); r = pg.evaluate("() => document.getElementById('slateText').getBoundingClientRect()") 
        touch_swipe(pg, cdp, r["x"] + 10, r["y"] + r["height"] / 2, r["x"] + r["width"] - 10, r["y"] + r["height"] / 2)
        check(f"{dev}: Ref has no swipe", pg.evaluate(LINE) == l0 and not pg.evaluate("() => !!document.getElementById('tkline')"), l0)
        qb = pg.locator("#qrHalf").bounding_box(); qx, qy = qb["x"] + qb["width"] / 2, qb["y"] + qb["height"] / 2
        tap(cdp, qx, qy); time.sleep(0.12); tap(cdp, qx, qy); time.sleep(0.8)
        pg.click("#dnu"); time.sleep(0.4); r = pg.evaluate("() => document.getElementById('slateText').getBoundingClientRect()")
        touch_swipe(pg, cdp, r["x"] + 10, r["y"] + r["height"] / 2, r["x"] + r["width"] - 10, r["y"] + r["height"] / 2)
        check(f"{dev}: DO NOT USE has no swipe", pg.evaluate(LINE) == "DO NOT USE")
        ctx.close()
    b.close()
check("No page errors", not errs, errs)
print(f"\n{sum(ok)}/{len(ok)} passed")
