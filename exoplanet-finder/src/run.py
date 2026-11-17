import vetting

import traceback
from pathlib import Path

import db
from download import get_lightcurve
from search import run_bls
from plots import save_plot


LIMIT = 50
FORCE = False
TARGET_FILE = Path(__file__).resolve().parent.parent / "data" / "targets.txt"
TARGETS = [int(x) for x in TARGET_FILE.read_text().split()][:LIMIT]

con = db.connect()

for tic in TARGETS:
    if not FORCE and db.already_done(con, tic):
        print(f"TIC {tic}: schon in der DB, übersprungen")
        continue
    try:
        lc, n_sectors = get_lightcurve(tic)
        if lc is None:
            db.save(con, tic, "no data")
            print(f"TIC {tic}: keine Daten")
            continue
        res, flat, pg = run_bls(lc)
        res.update(vetting.vet(flat, res))
        plot = save_plot(tic, flat, pg, res)
        db.save(con, tic, "ok", res, n_sectors, plot)
        print(f"TIC {tic}: P={res['period']:.4f} d, SNR={res['snr']:.1f}")
    except Exception:
        db.save(con, tic, "error")
        traceback.print_exc()
