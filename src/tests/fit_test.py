import os
from pathlib import Path
import time, re, sys
from playwright.sync_api import sync_playwright
F = "file://" + os.environ.get("BUR_SLATE_HTML", str(Path(__file__).resolve().parents[3] / "bur_slate_artifact.html"))
CHECK = re.search(r'CHECK = """(.*?)"""', open("/home/claude/portrait_test2.py").read(), re.S).group(1)
DEVICES = [("Fold cover", 412, 820, 2.6), ("Fold open", 884, 900, 2.6), ("iPhone 15", 393, 660, 3), ("iPhone SE", 375, 550, 2),
           ("iPad mini P", 744, 1050, 2), ("iPad mini L", 1133, 680, 2), ("iPad 11 P", 834, 1120, 2), ("iPad 11 L", 1194, 760, 2),
           ("iPad 13 P", 1024, 1290, 2), ("iPad 13 L", 1366, 950, 2), ("Phone L", 915, 360, 2.6)]
CONFIGS = [("slate", "HDRI"), ("slate", "REF"), ("slate", "VB"), ("slate", "PHOTOG"), ("slate", "WITNESS"),
           ("asset", "ENV:PHOTOG"), ("asset", "ENV:PLATE"), ("asset", "PROP:PHOTOG"), ("asset", "CHAR:FACIAL"), ("asset", "CHAR:WSCAN")]
shots = set(sys.argv[1:])
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h, dpr in DEVICES:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(F); time.sleep(0.8)
        pg.fill("#f-slate", "83A"); pg.dispatch_event("#f-slate", "input")
        row = []
        for mode, t in CONFIGS:
            if mode == "slate":
                pg.click("#mode-slate"); pg.select_option("#f-type", t)
            else:
                c, at = t.split(":"); pg.click("#mode-asset"); pg.select_option("#f-cat", c); pg.select_option("#f-atype", at)
            time.sleep(0.15)
            u = float(pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--u')"))
            sc = pg.evaluate("(() => { const f = document.getElementById('fields'); return f.scrollHeight - f.clientHeight; })()")
            used = pg.evaluate("(() => { const f = document.getElementById('fields'); const kids = [...f.children].filter(k => k.offsetParent); const last = Math.max(...kids.map(k => k.getBoundingClientRect().bottom)); return Math.round(100 * last / window.innerHeight); })()")
            bad = pg.evaluate(CHECK)
            row.append(f"{t.split(':')[-1][:6]} u{u:.2f} fill{used}%" + (f" SCROLL{sc}" if sc > 1 else "") + (f" BAD{bad}" if bad else ""))
            key = f"{name}|{t}"
            if key in shots: pg.screenshot(path=f"/tmp/bur_slate_shots/fit_{name.replace(' ', '_')}_{t.replace(':', '_')}.png")
        print(f"{name} {w}x{h}: " + " · ".join(row) + (f" ERR {errs}" if errs else ""))
        ctx.close()
    b.close()
