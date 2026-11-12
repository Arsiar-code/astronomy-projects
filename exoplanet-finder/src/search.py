import numpy as np

def run_bls(lc, pmin=0.5, pmax=15, n=30000):
    flat = lc.flatten(window_length=901).remove_outliers(sigma_upper=4)
    pg = flat.to_periodogram(
        method="bls",
        period=np.linspace(pmin, pmax, n),
        duration=[0.04, 0.08, 0.12, 0.2],
    )
    return {
        "period": pg.period_at_max_power.value,
        "depth": float(pg.depth_at_max_power),
        "t0": float(pg.transit_time_at_max_power.value),
        "duration": pg.duration_at_max_power.value
        "snr": float(pg.max_power / np.nanstd(pg.power)),
    }
