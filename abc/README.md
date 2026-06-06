# ABC's Start — Local MVP

Single-page Pre-K on-ramp for the 珊蒂美語 classroom.

## What it does

- Plays Track 2 ("The ABC's" — 14 min alphabet song) on a big play button with scrubber
- Shows the Yellow CD 1 / Track 4 alphabet chart (A–Z with pictures)
- A–Z letter strip: tap a letter → that cell pulses on the chart (helps kids find/associate)

## Run it

```bash
cd ~/abc-mvp
python3 -m http.server 8000
# open http://localhost:8000 in any browser
```

Tested in Chrome / Safari mobile. No build step, no backend.

## Files

- `index.html` — page structure
- `styles.css` — kid-friendly, mobile-first
- `app.js` — audio player + letter→chart highlight
- `chart.jpg` — alphabet chart image (extracted from `book.pdf` page 1)
- `track2.mp3` — the ABC song
- `book.pdf` — source PDF (Yellow phonics book, 12 pages)
- `page_1.png` / `chart_raw.png` / `chart_hires.png` — working files for chart extraction

## Next (not built yet)

- Quiz mode: "Which letter is this?" with picture + 4 choices
- Tap-to-hear individual letter sounds (needs individual-letter audio, not in this asset set)
- Sync highlights to the song timeline so the chart auto-pulses letter-by-letter
- PWA manifest + service worker for offline install on parent phones
- Wire onto `*.enlighten-group.com` via the existing tunnel + Nginx

## v0.1 scope (what this is)

Local-only MVP. Hardcoded to the assets Chun shared. No auth, no persistence, no backend.
