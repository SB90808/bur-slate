# BUR Slate — phone slate app: what it is, how it works, where everything lives

Written 13 Oct 2026. The kit side (how the sort kit reads these slates) is in the Claude project's status doc.

## 1. Purpose

A phone page the wranglers hold up instead of the BIG app slate: the slate line as big text plus a QR code holding `BUR:` + the line.
The sort kit (v1.9.27 on Ramses and Cleopatra) reads the QR first — exact, nothing to misread — and falls back to the text.
iPhone and Android, portrait or landscape, works with no signal once opened.

## 2. Where everything lives

| Thing | Where |
|---|---|
| Steve's own copy (production lists built in) | a Claude artifact "BUR Slate" (private; the link is in the Claude project doc) |
| Wranglers' copy (no production lists) | https://sb90808.github.io/bur-slate/ — GitHub repo **SB90808/bur-slate**, Pages from `main` / root. Claude GitHub App is installed on this repo only (`add_repo` SB90808/bur-slate in a session, then clone, commit as Steven Barham, push). The Pages API is blocked through the session proxy; pushing to main redeploys by itself (check `gh api repos/SB90808/bur-slate/actions/runs`) |
| Source | `src/bur_slate_src.html` in the repo — ONE source with placeholders `/*QRLIB*/ /*LOCATIONS*/ /*CHARACTERS*/ /*PROPS*/` |
| Build | `src/build_slate.py` — web copy into the repo root (index.html, manifest.webmanifest, sw.js; icons kept as committed) and, given the kit's `config/asset_history.json` (`--lists`), the artifact copy (`--artifact <path>`, never commit it) |
| QR library | `src/qrcode.min.js` = qrcode-generator 1.4.4 (Kazuhiko Arase, MIT), inlined at build |
| Tests | `src/tests/` (Playwright Chromium + OpenCV QR decode; `src/tests/README.md`) |
| Production lists | the kit's `config/asset_history.json` (locations / characters / props, union of the drives) + a second JSON file with the production's fixed characters — both kept off this repo |

Release = edit `src/bur_slate_src.html` → `python3 src/build_slate.py --lists … --artifact …` → run the tests → republish the artifact (same path or `url`) → commit the repo root files → push. Phones that installed the web copy fetch the new release in the background and show it the next time the app is opened.

## 3. The screen

**Form** (editor) — top section + fields + the slate screen behind it.

Top section, one row, the same size for every type (Steve, 13 Oct: "this top area should be uniform across all types… I really want it on one row at the top"):
`DO NOT USE` at the left edge · `Slate | Asset` centred on the page (the two side columns share the width equally) · `Clear` `◐` (light/dark) at the right edge (Steve, 13 Oct evening; landscape: DO NOT USE · toggle · line · Clear · ◐) — then the slate line box (two lines tall in portrait, one in landscape; text centred, wraps and shrinks so the whole line is always visible; no "text + QR" tag (Steve, 13 Oct evening) — only "↳ what is missing" when something is) — then `TK +1 & Show` / `POS +1 & Show` and `Show` (Show alone fills the row when there is no +1).

Fields under the separator (what shows depends on mode + type — §4). Slate and Type (Category and Type in Asset) are always side by side; `+ Slates` straight under them; Specific / Location / Character / Prop name / Real name always full width; small fields (Pos, Positions in folder, Date, Focal, Take, ADD) share a row. ADD = label first, then a tick box the size of the + button (not next to the +).

**First open** (nothing saved on the phone yet): Slate mode, type Ref, the slate box empty — no example slate anywhere; only `+ Slates` keeps its `40A 40B 40C` placeholder (Steve, 13 Oct evening: "clear all slate samples, may be confusing"). After that the app picks up exactly where it was left (§6).

**Slate screen** — text left / QR right (portrait: text top / QR bottom); HDRI, Insta360 and DO NOT USE are text only (full screen). Text is laid out by trying line breaks (at most 4) for the biggest size that fits; QR as big as its half allows. Double-tap the QR (anywhere when there is no QR) goes back to the form — the form ignores touches for 0.5 s so the second tap never opens a box. Screen kept awake; full screen in Android browser tabs. Everything inside the phone's safe area (iPhone Dynamic Island / home bar): `--sat/--sar/--sab/--sal` from `env(safe-area-inset-*)`, viewport-fit=cover.

**Take swipe** (Witness, ENV Plate, CHAR Facial): on the slate screen, a horizontal swipe on the TK line's strip (the line's band across the text half, 35 % of its height above and below) — **right to left = next take, left to right = take back** (never below 1; reversed to this on 13 Oct at Steve's request). Needs ≥ max(40 px, 12 % of the half) mostly sideways within 1 s; QR, form and saved state follow; a swipe never counts towards the double-tap.

**Clear** (top row): empties slate, + slates, every type's specific, location, character, prop, real name, focal; pos / take / positions back to 1; ADD off; date today. Keeps Slate/Asset, the types picked, learned names and the theme. "Cleared — Undo" for 6 s. Decided 13 Oct evening: fields only — Clear never resets the mode or the type.

**Look**: Graphite (Steve chose it from five Apple-clean schemes, 13 Oct): neutral greys, Show = solid white on dark / black on light, red only for DO NOT USE, the phone's system font. Light/dark toggle (follows the phone until chosen, remembered) — **light mode = white slate, black text**; the QR is always black on white. No "On the slate" tip.

## 4. Modes, types and what they show

Slate mode (Type drop-down): HDRI · Insta360 · Ref · VB · VB PMP · Photog · Textures · Gsplat · Witness.
Asset mode: Category ENV / PROP / CHAR / VEH / TILES, then Type per category — ENV: Photog, Textures, Gsplat, Plate (witcam); PROP: Photog, Textures; CHAR: Photog, Wrangler scan, Facial (witcam); VEH / TILES: Photog, Textures.

**Drop-down names** (Steve, 13 Oct evening): the open list shows the full name, for reading in the app only — Ref → *Reference Stills*, Photog → *Photogrammetry*, Gsplat → *GaussianSplat* (Slate and Asset Type lists); Category → *Environment / Prop / Character / Vehicle / Tiles*. The closed box keeps the short word exactly as before (Ref, Photog, Gsplat, ENV…), and the slate line, QR and kit naming are untouched. How: each `<option>` text is the full name with `data-short` holding the short word; the select sits in a `.selwrap` with its own text transparent, and a `.selface` span (pointer-events none) shows the short word over it, refreshed by `faceSelects()` in `refreshFields`. `selectFits` and width_test measure the short word, so sizing is unchanged.

| Type | Fields | Line (QR payload = `BUR:` + line) |
|---|---|---|
| HDRI | Specific (optional), Pos, Positions in folder 1–10 | `83A / [SPEC ]POS 1` or `POS 1-10` — **text only** (QR does not survive the fisheye) |
| Insta360 | — | `83A` — text only |
| Ref | + Slates, Specific (optional), Pos, ADD | `83A[ + 40A + 40B] / REF[ / SPEC[ POS n]][ / ADD]` |
| VB, VB PMP | Specific (optional), Pos | `83A / VB / [SPEC ]POS n` |
| Photog | Specific (required), Pos (set) | `83A / PHOTOG / SPEC[ POS n]` |
| Textures | Specific (required) | `83A / TEXTURES / SPEC` |
| Gsplat | Specific (required), Pos | `83A / GSPLAT / [SPEC ]POS n` |
| Witness | Focal, Take | `83A / [50MM / ]TK1` |
| ENV / VEH / TILES Photog, Textures, Gsplat | Location (type or pick), Specific (required; Gsplat adds Pos) | `ENV / LOCATION / PHOTOG / SPEC`, Gsplat tail `[SPEC ]POS n` |
| ENV Plate (witcam) | Location, Specific (required), Focal, Take | `ENV / LOCATION / SPECIFIC / [24MM / ]TK1` |
| PROP Photog, Textures | Prop name (type or pick), Specific (optional) | `PROP / NAME / PHOTOG[ / SPEC]` |
| CHAR Photog | Character (type or pick), Specific (required) | `CHAR / NAME / PHOTOG / SPEC` |
| CHAR Wrangler scan | Character | `CHAR / NAME / WSCAN` |
| CHAR Facial (witcam) | Character, Real name, Date (yymmdd, today by default), Focal, Take | `NAME - REAL NAME / [50MM / ]261013 / TK1` |

Rules Steve set: `+ Slates` (shared capture — every word another slate, each filed a plain copy) only for Ref and Insta360; HDRI, Witness, VB, VB PMP, Photog, Textures, Gsplat are slate-specific. Each type keeps its own Specific (per `S:type` or `A:cat:type`), never shared. "Stunt name" is called **Real name**. Only the fields on screen count towards the line. Everything typed is upper-cased; Location / Character / Prop name offer names as you type (production list + names this phone has shown; × forgets a learned one; a new location is fine — the kit flags it CHECK). Small grey help line per type (dropped first on a short screen).

## 5. Sizing (how it fits any phone or iPad)

Every size is a multiple of a CSS variable. `--tu` sizes the top section: worked out once per screen size / way up / safe insets (cached by `screenKey`, redone when fonts load) as Witness's own fitted size, then limited to what fits the one row with the longest button label showing (`topFits`: nothing past the edge, nothing overlapping, no label cut); landscape also keeps the top to a quarter of the height. Measured with Android's Roboto: Fold cover ≈ 1.19, iPhone 16 Pro ≈ 1.17 (about the size the Ref form used to get).
`--u` sizes the fields: a binary search for the biggest size at which the fields fit without scrolling (pass 2 locks the column count), capped at the screen's short side / 300 (Fold ≈ 1.37, iPhone ≈ 1.34 — where Steve signed off "textures text too big" fix) and 2.4 on iPads; never below 0.8 portrait / 0.75 landscape (typed text never under 16 px, so iOS never zooms); a drop-down word must always show in full. Fields' side margins follow `--tu` so the left edges line up with the top. Resizes are ignored while a box has focus (the keyboard must never shrink the form); with the keyboard up the fields scroll so the box being typed in sits above it.

## 6. Storage on the phone (localStorage)

`bur-slate-v2` — mode, every field, ADD, per-type specifics (`specs`); `bur-slate-theme` — light / dark once chosen; `bur-slate-names` — learned locations / props / characters (per phone, max 300 each). Nothing leaves the phone; the web copy carries no production names (Steve: "take the lists out"); `noindex` for search engines.

## 7. Tests (all in `src/tests/`, all passing 13 Oct)

spec_test (60 line/QR checks incl. light-mode white slate, QR decode, first-open Slate / Ref with an empty slate box and the + Slates example kept, full names in the open lists with the short word in the closed box) · width_test (209 layouts on 11 screens — 3 known: "Facial (witcam)" cut on a 340 px phone, no real device) · fit_test (reads its CHECK snippet from `/home/claude/portrait_test2.py`, a file outside the repo — fails with FileNotFoundError in a fresh container until that snippet is moved in) · acts_test · iphone_test (sizes + picker steady) · back_test (double-tap, type-or-pick) · spec_mem_test (per-type specifics survive reload) · clear_safe_test (Clear / Undo / ADD order / Dynamic Island, 28) · swipe_test (45, real touch events, portrait + landscape) · top_const_test (top identical across 19 types on 14 screens; `roboto` arg for Android widths) · web_test (install, service worker, offline reload with QR, learned names). Not possible from the container: a real phone — Steve checks the Fold 8 and a wrangler's iPhone 16 Pro.

## 8. Decisions log (Steve, 13 Oct 2026, in order)

Prop name pop-up broken → type-or-pick, new names allowed · Location type-or-pick · + Slates hidden for the slate-specific types · double-tap the QR itself to go back, never a stray text box · fields fill the screen, auto-size for any phone / iPad · light mode · Slate and Type always side by side, + Slates under · HDRI optional Specific, positions in folder up to 10 · slate line always fully visible · white slate in light mode · five Apple-clean schemes → Graphite · "On the slate" tip removed · ADD box the size of the + button · Stunt name → Real name · each type its own Specific · shared with the wranglers: lists out, free GitHub Pages (SB90808) · iPhone 16 Pro spacing / Textures text too big → size cap · kit taught white slates, QR, sideways slates, asset order (v1.9.26 / 27) · Clear button with reset to 1 · landscape uniform, specifics full width · ADD text before the box · Dynamic Island cut-off fixed · take swipe on witcam slates (all three witcam types, TK-line strip) · top section one row, one size for every type (Ref-ish size; Witness size would not fit one row) · DO NOT USE up beside Clear · swipe direction reversed (right-to-left = next take) · (evening) Clear = fields only, mode and type stay · first install opens on Slate / Ref, then picks up where it was left · no example slate anywhere (`83A` placeholder and pre-fill gone); only + Slates keeps its example · drop-downs: full names in the open list (Reference Stills, Photogrammetry, GaussianSplat; Environment, Prop, Character, Vehicle, Tiles), closed box stays as it was · slate line box: tag gone, text centred · top row: DO NOT USE at the left edge, Slate | Asset centred on the page, Clear + light/dark at the right edge.

## 9. Open / ideas not asked for yet

fit_test's CHECK snippet to move into the repo · wrangler docs (Quick Look v5.1, handout v11) do not mention BUR Slate / QR / white slates · SB 3TB kit still v1.9.21 · witcam QR test clip (BlackMagic + GoPro) still to shoot.
