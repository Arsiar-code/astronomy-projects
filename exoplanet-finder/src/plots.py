import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from db import DATA

PLOTS = DATA / "plots"


def _binned(x,y, lo, hi, nbins):
    edges = np.linspace(lo, hi, nbins + 1)
    centers = 0.5 * (edges[1:] + edges[:-1])
    med = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (x >= a) & (x < b)
        med.append(np.nanmedian(y[m]) if m.any() else np.nan)
    return centers, np.array(med)


def save_plot(tic, flat, pg, res):
    PLOTS.mkdir(parents=True, exist_ok=True)
    P, dur = res["period"], res["duration"]

    folded = flat.fold(period=P, epoch_time=res["t0"])
    x = folded.time.value
    y = folded.flux.value

    fig, ax = plt.subplots(1, 3, figsize=(16, 4))

    ax[0].plot(pg.period.value, pg.power.value, lw=0.6)
    ax[0].axvline(P, color="r", alpha=0.4)
    ax[0].set(title="BLS-Periodogramm", xlabel="Periode [d]", ylabel="Power")

    ax[1].plot(x, y, ".", ms=1, alpha=0.3)
    bx, by = _binned(x, y, -P / 2, P / 2, 200)
    ax[1].plot(bx, by, "r-", lw=1)
    ax[1].set(title=f"Gefaltet, P = {P:.4f} d", xlabel="Zeit seit Transit [d]",
              ylabel="Normierter Fluss")

    w = max(3 * dur, 0.1)
    m = (x > -w) & (x < w)
    ax[2].plot(x[m], y[m], ".", ms=2, alpha=0.3)
    bx, by = _binned(x, y, -w, w, 60)
    ax[2].plot(bx, by, "r-o", ms=3, lw=1)
    ax[2].set(title="Transit (Zoom)", xlabel="Zeit seit Transit [d]")

    fig.suptitle(f"TIC {tic} | Tiefe {res['depth']*1e6:.0f} ppm | "
                 f"SNR~{res['snr']:.1f} | ~{res['n_transits']} Transits")
    fig.tight_layout()

    path = PLOTS / f"TIC{tic}.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return f"plots/TIC{tic}.png"
