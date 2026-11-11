# K-Beauty Trade Catalog

Buyer-facing catalog of Korean beauty brands. Static site for GitHub Pages: `index.html` + `data/catalog.json`.

- Live (GitHub Pages): https://rigeltop-byte.github.io/kbeauty-catalog/ — public repo `rigeltop-byte/kbeauty-catalog`, branch `main`, folder `/ (root)`
- Local preview: `python3 -m http.server 8000` then open http://localhost:8000
- Deploy: GitHub → Settings → Pages → Deploy from branch `main`, folder `/ (root)`
- Images: `tools/make_thumbs.py` (+ `tools/cutout.swift` for macOS Vision cutouts) → `tools/apply_images.py`; navigation groups: `tools/enrich.py`; brand highlight cards: `tools/apply_brands.py` (data in `handoff/brand-highlights/`); texture & review insights: `tools/apply_insights.py` (data in `handoff/review-insights/`)
- Handoff notes (Korean): see `HANDOFF.md`

Internal price sheets and supply prices are never stored in this repository.
