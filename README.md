# daily-frame

One picture a day, for the TV screensaver (Lumen, "Our pictures") and the website "Two of a Kind".

- `frames/` the pictures, numbered `001-name.webp`, 1672 x 941, WebP quality 95. They are shown in number order, one a day.
- `.github/workflows/daily.yml` runs `tools/daily.py` every night (00:10 UTC, Dublin date). It copies the next frame to `latest.webp`
  and writes `manifest.json` (the TV), `history.json` (the website: every day shown so far) and `state.json`. It also makes the small
  archive copy in `thumbs/` (640 px wide) for any frame that has none yet.
- To add pictures: convert with `cwebp -q 95 -m 6 -resize 1672 941 in.png -o frames/214-name.webp`. They come after the ones already shown.
- The TV reads `manifest.json` and the website reads `history.json`, both from GitHub Pages (`main`, root), served at https://daily.fabiopetriccione.com (`CNAME`). The old `flatwhiteflow.github.io/daily-frame` address redirects there.

## The website

`index.html`, `site.css`, `site.js`: one screen with today's picture in a frame (black, oak, walnut or white, picked with the swatches at
the top; `?frame=oak` in a link), and four corner links: the wordmark (back to today), Archive, the title and countdown, About.
The archive lists only days before today: a picture appears there once the next one has replaced it. Each past day has its own link,
`#YYYY-MM-DD`; arrow keys step through the days. `?look=open` shows the pictures without a frame, straight on their own cream.

- `assets/two-of-a-kind.svg` is the wordmark, traced from the lettering printed on the frames.
- `fonts/` holds Outfit and Instrument Serif (SIL Open Font License), self-hosted.
- To try it locally: `python3 -m http.server 8642`, then open `http://127.0.0.1:8642/`. `?preview` adds a made-up 52-day history
  (`preview/history.json`, not committed) to see a full archive.
