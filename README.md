# Astronomy Projects

Automated search for exoplanet candidates in public TESS light curves, built as a data pipeline on a self-hosted Linux server.

**Status:** work in progress. The core pipeline runs and has been validated on known planets. Vetting, dashboard and automation are under development.

## What is this about?

The TESS space telescope measures the brightness of millions of stars. When a planet passes in front of its star, the star dims slightly (a *transit*), and this repeats periodically. This project automatically searches for such periodic dips and then checks whether they can really be a planet or a false positive (eclipsing binary, variable star, instrumental systematics).

## How the pipeline works

```
Target list → Download → Clean → BLS search → Plot → SQLite
```

1. **Target list** (`targets.py`): Stars with 2-minute SPOC data from the TESS Input Catalog, filtered by brightness, size and temperature. Known TOIs and confirmed planets are removed, so the search only covers stars where nothing has been flagged yet.
2. **Download** (`download.py`): Light curves from the MAST archive (via `lightkurve`), cached locally. Only directly consecutive sectors are combined.
3. **Cleaning and search** (`search.py`): Remove NaNs and outliers, filter out slow stellar variability, then run a *Box Least Squares* (BLS) search for periodic, box-shaped dips.
4. **Plots** (`plots.py`): BLS periodogram, phase-folded light curve and transit zoom for each star.
5. **Storage** (`db.py`): Results go into SQLite. Each row records the pipeline version that produced it. Stars that are already processed are skipped, failed ones are retried automatically.

## Validation

Before searching new stars, the pipeline was tested on systems with known planets:

| Star | Recovered period | Literature |
|---|---|---|
| WASP-18 (TIC 100100827) | 0.9414 d | WASP-18 b, approx. 0.94 d |
| π Mensae (TIC 261136679) | 6.268 d | π Men c, approx. 6.27 d |

![WASP-18 b, phase-folded light curve](exoplanet-finder/docs/wasp18b.png)

## A false positive that shows why vetting matters

In early runs, TIC 375034557 stood out with a strong signal (P ≈ 0.84 d). The folded curve, however, is a smooth wave rather than a box, so this is a variable star and not a transit. Cases like this are exactly what the vetting step is meant to reject automatically.

## Project status

- [x] Linux server (Ubuntu, Hyper-V), SSH access, Git/GitHub
- [x] Modular pipeline: download, cleaning, BLS search
- [x] Validation on WASP-18 b and π Men c
- [x] SQLite storage with versioning and migration
- [x] Per-star plot generation
- [x] Target list excluding known TOIs
- [ ] Vetting: out-of-transit variability, odd/even test, secondary eclipse, edge flags, proper transit SNR
- [ ] Streamlit dashboard (overview, table, per-star detail page)
- [ ] Retry and timeout handling for MAST queries
- [ ] Nightly automated runs (cron)
- [ ] Docker Compose, GitHub Actions (linting, tests)
- [ ] Later: migration to k3s, further astronomy projects sharing a common module

## Known limitations

- The current SNR is a rough approximation (peak periodogram power relative to its scatter), not a true transit SNR.
- The search uses only two consecutive sectors per star. Very long periods and single transits are not covered.
- Without vetting, most detections are false positives. A detection is a lead, not a finding.

## Installation

```bash
git clone git@github.com:YOUR-USERNAME/astronomy-projects.git
cd astronomy-projects/exoplanet-finder
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

```bash
# 1. Generate the target list (takes a few minutes)
python src/targets.py

# 2. Run the pipeline
python src/run.py

# 3. Inspect the results
sqlite3 data/results.db "SELECT tic, period, snr FROM results WHERE status='ok' ORDER BY snr DESC LIMIT 10;"
```

Plots are written to `exoplanet-finder/data/plots/`. The `data/` folder is not part of the repository.

## Project structure

```
astronomy-projects/
└── exoplanet-finder/
    ├── requirements.txt
    ├── docs/              example plots
    └── src/
        ├── targets.py     target list from TIC, excluding TOIs
        ├── download.py    fetch and cache light curves
        ├── search.py      cleaning and BLS search
        ├── plots.py       periodogram, folded curve, zoom
        ├── db.py          SQLite storage
        ├── run.py         run the pipeline over the target list
        └── test_known.py  validation on WASP-18 b
```

## Tech stack

Python, lightkurve, astropy, astroquery, NumPy, matplotlib, pandas, SQLite, Git, Linux (Ubuntu Server).

## Data and acknowledgements

Data comes from the Transiting Exoplanet Survey Satellite (TESS) and is provided by the Mikulski Archive for Space Telescopes (MAST). The TOI list and planet catalog come from the NASA Exoplanet Archive. The analysis uses `lightkurve` and `astropy`.

## Author

Arsiar-Code | Aleksander P.
