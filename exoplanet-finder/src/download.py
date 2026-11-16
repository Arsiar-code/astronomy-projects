from pathlib import Path
import lightkurve as lk

CACHE = Path(__file__) .resolve().parent.parent / "data"


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
    search = lk.search_lightcurve(
            f"TIC {tic}", author="SPOC", exptime=120
    )
    if len(search) == 0:
        return None, 0

    sectors = [int(s) for s in search.table["sequence_number"]]
    wanted = pick_sectors(sectors, max_sectors)
    mask = [s in wanted for s in sectors]
    lcs = search[mask].download_all(download_dir=str(CACHE))
    
    lc = lcs.stitch()
    return lc.remove_nans().normalize(), len(lcs)
