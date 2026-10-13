# BUR Slate

Phone slate for on-set data wrangling: type the slate, show it as big text plus a QR code.

Open https://sb90808.github.io/bur-slate/ once with signal, then Add to Home Screen. After that it works with no signal.
Names you type (locations, props, characters) are remembered on that phone only.

## Source, build and tests (for Steve / Claude sessions)

- `src/bur_slate_src.html` — the one source, with placeholders `/*QRLIB*/ /*LOCATIONS*/ /*CHARACTERS*/ /*PROPS*/`.
- `src/build_slate.py` — builds the web copy into the repo root (commit + push = release; Pages redeploys by itself)
  and, given the kit's `config/asset_history.json`, Steve's artifact copy with the production lists (never commit that).
- `src/tests/` — Playwright checks: slate-line spec, layout on phones/iPads both ways up, Clear/Undo, safe areas, take swipe, fixed top row.
- Steve's own copy is the Claude artifact "BUR Slate"; design notes and the change log are in the Claude project doc `claude/BUR_Slate_Design.md`.
