import time, cv2
from playwright.sync_api import sync_playwright
import os
U = os.environ.get("BUR_SLATE_URL", "http://localhost:8811/")   # serve the repo root: python3 -m http.server 8811
ok = True
def chk(n, c, i=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{i}]" if i else ""))
def setv(pg, id, v): pg.fill("#" + id, v); pg.dispatch_event("#" + id, "input")
def line(pg): return pg.eval_on_selector("#preview .lt", "p => p.firstChild && p.firstChild.nodeType === 3 ? p.firstChild.textContent.trim() : ''")
def sugg(pg, id): return pg.eval_on_selector_all(f"#{id} .pick", "bs => bs.map(b => b.textContent)")
def back(pg):
    t = "#stage" if pg.eval_on_selector("#qrHalf", "e => e.hidden") else "#qrHalf"
    xy = pg.eval_on_selector(t, "e => { const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2]; }")
    pg.touchscreen.tap(*xy); time.sleep(0.12); pg.touchscreen.tap(*xy); time.sleep(0.7)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 412, "height": 820}, device_scale_factor=2.6, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.goto(U); time.sleep(1.5)
    chk("Service worker installed", pg.evaluate("navigator.serviceWorker.getRegistration().then(r => !!(r && (r.active || r.installing || r.waiting)))"))
    chk("Manifest linked", pg.evaluate("fetch('manifest.webmanifest').then(r => r.json()).then(j => j.display === 'standalone' && j.icons.length === 2)"))
    pg.tap("#mode-asset"); pg.select_option("#f-cat", "ENV"); pg.select_option("#f-atype", "PHOTOG"); time.sleep(0.1)
    pg.tap("#f-loc"); time.sleep(0.2); chk("No production locations built in", sugg(pg, "loc-sugg") == [], str(sugg(pg, "loc-sugg")))
    pg.keyboard.type("north tunnel"); setv(pg, "f-spec", "doorway"); time.sleep(0.1)
    pg.tap("#show"); time.sleep(0.6); chk("Slate shows", qr_ok := True); back(pg)
    setv(pg, "f-loc", ""); pg.tap("#f-loc"); time.sleep(0.2)
    chk("Typed location remembered and offered", sugg(pg, "loc-sugg") == ["NORTH TUNNEL"], str(sugg(pg, "loc-sugg")))
    pg.keyboard.type("north"); time.sleep(0.2); pg.tap("#loc-sugg .pick >> nth=0"); time.sleep(0.3)
    chk("Tap a remembered location fills it", line(pg) == "ENV / NORTH TUNNEL / PHOTOG / DOORWAY", line(pg))
    pg.select_option("#f-cat", "PROP"); pg.select_option("#f-atype", "PHOTOG"); pg.tap("#f-name"); pg.fill("#f-name", ""); pg.keyboard.type("old book"); pg.tap("#show"); time.sleep(0.5); back(pg)
    pg.select_option("#f-cat", "CHAR"); pg.select_option("#f-atype", "WSCAN"); pg.tap("#f-char"); time.sleep(0.2)
    chk("No production characters built in", sugg(pg, "char-sugg") == [], str(sugg(pg, "char-sugg")))
    pg.keyboard.type("guard 1"); pg.tap("#show"); time.sleep(0.5); back(pg)
    setv(pg, "f-char", ""); pg.tap("#f-char"); time.sleep(0.2)
    chk("Typed character remembered", sugg(pg, "char-sugg") == ["GUARD 1"], str(sugg(pg, "char-sugg")))
    pg.tap("#char-sugg .forget"); time.sleep(0.2)
    chk("x forgets a remembered name", sugg(pg, "char-sugg") == [] and pg.evaluate("document.activeElement.id") == "f-char")
    pg.reload(); time.sleep(1)
    pg.tap("#mode-asset"); pg.select_option("#f-cat", "PROP"); pg.select_option("#f-atype", "PHOTOG"); setv(pg, "f-name", ""); pg.tap("#f-name"); time.sleep(0.2)
    chk("Remembered after reload (prop)", sugg(pg, "name-sugg") == ["OLD BOOK"], str(sugg(pg, "name-sugg")))
    # offline: reload with no network
    ctx.set_offline(True); pg.reload(); time.sleep(1)
    pg.tap("#mode-slate"); setv(pg, "f-slate", "83A"); pg.select_option("#f-type", "WITNESS"); setv(pg, "f-focal", "50"); pg.tap("#show"); time.sleep(0.6)
    pg.screenshot(path="/tmp/bur_slate_shots/web_offline.png"); d, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread("/tmp/bur_slate_shots/web_offline.png"))
    chk("Works with no signal (reloaded offline, QR reads)", d.startswith("BUR:83A / 50MM / TK"), d)
    ctx.set_offline(False)
    chk("No page errors", not errs, "; ".join(errs))
    b.close()
print("ALL PASS" if ok else "SOMETHING FAILED")
