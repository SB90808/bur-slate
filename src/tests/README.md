# BUR Slate tests (Playwright + OpenCV, run in Claude's cloud container)

    pip install playwright opencv-python-headless pillow && playwright install chromium   # once
    python3 src/build_slate.py --lists <kit>/config/asset_history.json --artifact ../bur_slate_artifact.html
    mkdir -p /tmp/bur_slate_shots
    for t in spec_test width_test fit_test acts_test iphone_test back_test spec_mem_test clear_safe_test swipe_test top_const_test; do python3 src/tests/$t.py; done
    (cd <repo> && python3 -m http.server 8811 &) ; python3 src/tests/web_test.py      # the web copy: install, offline, learned names

Page under test: $BUR_SLATE_HTML (default ../bur_slate_artifact.html beside the repo — the copy WITH the production lists,
which spec_test / back_test need). `top_const_test.py roboto` measures with Android's font (put the @fontsource/roboto
woff2 files in /tmp/bur_slate_fonts/). land_shots.py / top_shots.py only take screenshots for a look.
