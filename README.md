# daily-frame

One picture a day for the TV screensaver (Lumen, "Our pictures").

- `frames/` the pictures, numbered `001-name.webp`, 1672 x 941, WebP quality 95. They are shown in number order, one a day.
- `tools/daily.py` and `.github/workflows/daily.yml` pick the next one every day and write `latest.webp`, `manifest.json` and `state.json`.
- To add pictures: convert with `cwebp -q 95 -m 6 -resize 1672 941 in.png -o frames/214-name.webp`. They come after the ones already shown.
- The TV reads `https://flatwhiteflow.github.io/daily-frame/manifest.json` (GitHub Pages from `main`, root).
