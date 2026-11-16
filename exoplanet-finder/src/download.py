import time
from pathlib import Path

import lightkurve as lk
from astroquery.exceptions import RemoteServiceError
from astroquery.mast import Observations

Observations.TIMEOUT = 60
CACHE = Path(__file__) .resolve().parent.parent / "data"

RETRY_ERRORS = (OSError, RemoteServiceError)

def retry(func, tries=3, wait=30):
    """Ruft func() bis zu `tries`-mal auf. Pausen: 30 s, 60 s, ..."""
    for attempt in range(1, tries + 1):
        try:
            return func()
        except RETRY_ERRORS as e:
            if attempt == tries:
                raise
            pause = wait * attempt
            print(f" {type(e).__name__}, Versuch {attempt}/{tries}, warte {pause} s")
            time.sleep(pause)

def pick_sectors(sectors, n=2):
    """Findet n direkt aufeinanderfolgende Sektoren, sonst den ersten allein."""
    s = sorted(set(sectors))
    for i in range(len(s) - n + 1):
        block = s[i:i + n]
        if block[-1] - block[0] == n - 1:
            return block
        return s[:1]

def get_lightcurve(tic, max_sectors=2):
    """Gibt (Lichtkurve, Anzahl Sektoren) zurück, oder (None, 0)."""
    CACHE.mkdir(exist_ok=True)
    search = retry(
            lambda: lk.search_lightcurve(f"TIC {tic}", author="SPOC", exptime=120)
    )
    if len(search) == 0:
        return None, 0

    sectors = [int(s) for s in search.table["sequence_number"]]
    wanted = pick_sectors(sectors, max_sectors)
    mask = [s in wanted for s in sectors]
    lcs = retry(lambda: search[mask].download_all(download_dir=str(CACHE)))
    
    lc = lcs.stitch()
    return lc.remove_nans().normalize(), len(lcs)
