from pathlib import Path
import lightkurve as lk

CACHE = Path(__file__) .resolve().parent.parent / "data"

def get_lightcurve(tic, sector=None, max_sectors=2):
    """Holt eine SPOC-2min-Lichtkurve. Cache liegt in data/."""
    CACHE.mkdir(exist_ok=True)
    search = lk.search_lightcurve(
            f"TIC {tic}", author="SPOC", exptime=120, sector=sector
    )
    if len(search) == 0:
        return None
    lcs = search[:max_sectors].download_all(download_dir=str(CACHE))
    lc = lcs.stitch()
    return lc.remove_nans().normalize()
