import numpy as np


def mask_edges(lc, gap=0.5, trim=0.5):
    """Entfernt Daten kurz vor und nach jeder Lücke sowie am Anfang und Ende."""
    t = lc.time.value
    keep = ((t - t[0]) > trim) & ((t[-1] - t) > trim)
    for i in np.where(np.diff(t) > gap)[0]:
        keep &= ~((t > t[i] - trim) & (t < t[i + 1] + trim))
    return lc[keep]

def run_bls(lc, pmin=0.5, pmax=15, n=50000):
    lc = mask_edges(lc)
    flat = lc.flatten(window_length=901).remove_outliers(sigma_upper=4)
    pg = flat.to_periodogram(
        method="bls",
        period=np.linspace(pmin, pmax, n),
        duration=[0.04, 0.08, 0.12, 0.2],
    )
    period = float(pg.period_at_max_power.value)
    t = flat.time.value
    res = {
        "period": period,
        "depth": float(pg.depth_at_max_power),
        "t0": float(pg.transit_time_at_max_power.value),
        "duration": pg.duration_at_max_power.value,
        "snr": float(pg.max_power / np.nanstd(pg.power)),
        "n_transits": int((t.max() - t.min()) / period),
    }
    return res, flat, pg
