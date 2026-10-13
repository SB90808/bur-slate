# Source

`bur_slate_src.html` is the page before the build step. The build fills four placeholders:

- `/*QRLIB*/` — qrcode-generator 1.4.4 (MIT), `qrcode.min.js`, with `</` escaped as `<\/`
- `/*LOCATIONS*/`, `/*CHARACTERS*/`, `/*PROPS*/` — JSON arrays of names offered as you type; empty (`[]`) in this public version, so every phone learns its own

It then adds the `<head>` (manifest, icons, `noindex`, theme colours), the service-worker registration, and writes `index.html`, `manifest.webmanifest`, `sw.js` and the icons to the site root.
