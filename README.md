# Les disques de Christophe Brault

Static site listing Christophe Brault's album picks — twenty per year from 1964 to 2004, each year with its introductory text, plus the "liste cachée" of compilations — with links to Deezer, Spotify or YouTube.

Styled with the bzhmacro house kit (`assets/bzh.css`, vendored fallback). No build step: Vercel serves `index.html` as is.

## Layout

- `index.html` — generated page (do not hand-edit; regenerate with `pipeline/gen.py`)
- `data/albums.json` — the dataset: years → blurb + ranked items → albums with Deezer/Spotify/YouTube links
- `assets/` — bzhmacro stylesheet fallback, logo, `brault.css` (site-specific classes)
- `pipeline/` — how the data was made

## Pipeline

1. `ocr/ocr_raw.json` — OCR of the page photos. `parse.py` → `years_ocr.json` (blurb + 20 raw lines per year).
2. The OCR merged the bold artist and italic album title. `resolve_split.py` splits them using Deezer artist matches; `overrides.py` holds the hand-checked fixes.
3. Six years (1966, 1968, 1979, 1984, 1986, 1994) and the last page of the hidden list had no OCR; they were transcribed from the photos into `manual/`. The hidden list is structured in `hidden.py`.
4. `build_data.py` resolves each album on Deezer (queries cached in `dzcache.json`; run `dzfetch.py` from a UK/FR connection — Deezer search results depend on the caller's country). `spotify_hits.txt` adds exact Spotify links for some albums absent from Deezer. Everything else falls back to Spotify/YouTube search links.
5. `gen.py data/albums.json index.html` renders the page.

To fix a wrong link, edit `overrides.py` / `spotify_hits.txt` / the `DENY` set in `build_data.py`, rerun steps 4–5 and push.
