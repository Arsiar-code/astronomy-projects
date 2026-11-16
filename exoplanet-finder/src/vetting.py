import numpy as np

VAR_LIMIT = 0.25

def get_phase(time, period, t0):
    """Zeit seit dem nächsten Transit, im Bereich -P/2 bis +P/2."""
    return (time - t0 + 0.5 * period) % period - 0.5 * period

def robust_sigma(x):
    """Streuung, die von einzelnen Ausreissern kaum beeinflusst wird."""
    return 1.4826 * np.nanmedian(np.abs(x - np.nanmedian(x)))

def transit_snr(flux, intransit):
    inside = flux[intransit]
    outside = flux[~intransit]
    if len(inside) == 0 or len(outside) == 0:
        return np.nan, np.nan
    depth = np.nanmedian(outside) - np.nanmedian(inside)
    sigma = robust_sigma(outside)
    return depth, depth / sigma * np.sqrt(len(inside))

def oot_variability(phase, flux, period, duration, depth, nbins=50):
    """Wie stark schwankt der Stern ausserhalb des Transits, relativ zur Transittiefe?"""
    if not depth > 0:
        return np.nan
    edges = np.linspace(-period / 2, period / 2, nbins + 1)
    idx = np.clip(np.digitize(phase, edges) - 1, 0, nbins - 1)

    medians = []
    for b in range(nbins):
        center = 0.5 * (edges[b] + edges[b + 1])
        if abs(center) < 0.75 * duration:
            continue
        sel = flux[idx == b]
        if len(sel) > 10:
            medians.append(np.nanmedian(sel))

    if len(medians) < 5:
        return np.nan
    return np.std(medians) / depth

def vet(flat, res):
    t = flat.time.value
    f = flat.flux.value
    ok = np.isfinite(t) & np.isfinite(f)
    t, f = t[ok], f[ok]

    P, t0, dur = res["period"], res["t0"], res["duration"]
    phase = get_phase(t, P, t0)
    intransit = np.abs(phase) < dur / 2

    depth, snr_real = transit_snr(f, intransit)
    ratio = oot_variability(phase, f, P, dur, depth)

    return {
        "snr_real": float(snr_real),
        "oot_ratio": float(ratio),
        "flag_variable": None if np.isnan(ratio) else int(ratio > VAR_LIMIT),
    }
