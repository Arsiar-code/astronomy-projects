import numpy as np

VAR_LIMIT = 0.25

PMAX = 15
ODD_EVEN_SIG = 3.0
ODD_EVEN_FRAC = 0.25
SEC_FRAC = 0.5
SEC_SNR = 3.0
MIN_TRANSITS = 3

def odd_even(time, flux, period, t0, intransit):
    """Vergleicht die Tiefe der geraden und ungeraden Transits."""
    epoch = np.round((time - t0) / period).astype(int)
    outside = flux[~intransit]
    base = np.nanmedian(outside)
    sigma = robust_sigma(outside)

    depths, errs = [], []
    for parity in (0, 1):
        sel = intransit & (epoch % 2 == parity)
        n = sel.sum()
        if n < 5:
            return np.nan, np,nan
        depths.append(base - np.nanmedian(flux[sel]))
        errs.append(sigma / np.sqrt(n))

    diff = abs(depths[0] - depths[1])
    sig = diff / np.sqrt(errs[0] ** 2 + errs[1] ** 2)
    biggest = max(depths)
    rel = diff / biggest if biggest > 0 else np.nan
    return sig, rel

def secondary(time, flux, period, t0, dur):
    """Misst die Tiefe bei Phase 0.5."""
    phase2 = get_phase(time, period, t0 + 0.5 * period)
    insec = np.abs(phase2) < dur / 2
    return transit_snr(flux, insec)

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
    
    sig, rel = odd_even(t, f, P, t0, intransit)
    d2, snr2 = secondary(t, f, P, t0, dur)
    sec_ratio = d2 / depth if depth > 0 else np.nan

    epoch = np.round((t - t0) / P).astype(int)
    n_obs = len(np.unique(epoch[intransit]))

    def flag(cond, *vals):
        """None, wenn ein Wert nicht berechenbar war, sonst 0 oder 1."""
        return None if any(np.isnan(v) for v in vals) else int(cond)

    return {
        "snr_real": float(snr_real),
        "oot_ratio": float(ratio),
        "oddeven_sig": float(sig),
        "sec_ratio": float(sec_ratio),
        "n_transits": n_obs,
        "flag_variable": flag(ratio > VAR_LIMIT, ratio),
        "flag_oddeven": flag(sig > ODD_EVEN_SIG and rel > ODD_EVEN_FRAC, sig, rel),
        "flag_secondary": flag(sec_ratio > SEC_FRAC and snr2 > SEC_SNR, sec_ratio, snr2),
        "flag_edge": int(n_obs < MIN_TRANSITS or P > 0.9 * PMAX),
    }
