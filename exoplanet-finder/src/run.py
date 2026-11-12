from download import get_lightcurve
from search import run_bls

TARGETS = [100100827, 261136679]

for tic in TARGETS:
    lc = get_lightcurve(tic)
    if lc is None:
        print(f"TIC {tic}: keine Daten")
        continue
    print(f"TIC {tic}:", run_bls(lc))
