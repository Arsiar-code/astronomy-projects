import numpy as np
import lightkurve as lk

TIC = "TIC 100100827"

search = lk.search_lightcurve(TIC, author="SPOC", exptime=120)
print(search)

lc = search[0].download().remove_nans().normalize()
lc = lc.flatten(window_length=901)

pg = lc.to_periodogram(
        method="bls",
        period=np.linspace(0.5, 10, 20000),
        duration=[0.05, 0.1, 0.15],
)
print("Periode:", pg.period_at_max_power)
print("Tiefe:  ", pg.depth_at_max_power)
print("TO;     ", pg.transit_time_at_max_power)
