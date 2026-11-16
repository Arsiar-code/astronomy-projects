from io import StringIO

import pandas as pd
import requests
from astroquery.mast import Catalogs, Observations

from db import DATA

SECTOR = 69
TMAG_MAX = 12.0
RAD_MAX = 1.3
TEFF_RANGE = (3000, 6500)
OUT = DATA / "targets.txt"

TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"


def tap(query):
    r = requests.get(TAP, params={"query": query, "format": "csv"}, timeout=120)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))


def known_tics():
    """Alle Sterne, die schon als TOI oder bekannter Planet geführt werden."""
    toi = tap("select distinct tid from toi")
    ps = tap("select distinct tic_id from pscomppars where tic_id is not null")
    ids = set(toi["tid"].dropna().astype(int))
    ids |= {int(str(s).replace("TIC", "").strip()) for s in ps["tic_id"].dropna()}
    return ids


def sector_tics(sector):
    """Sterne mit SPOC-2-Minuten-Lichtkurve in diesem Sektor."""
    obs = Observations.query_criteria(
            obs_collection="TESS",
            provenance_name="SPOC",
            dataproduct_type="timeseries",
            sequence_number=sector,
    ).to_pandas()
    obs = obs[(obs["t_exptime"] - 120).abs() < 1]
    return sorted({int(str(t).replace("TIC", "").strip()) for t in obs["target_name"]})


def tic_properties(ids, chunk=1000):
    parts = []
    for i in range(0, len(ids), chunk):
        part = Catalogs.query_criteria(catalog="Tic", ID=ids[i:i + chunk])
        parts.append(part.to_pandas())
        print(f" TIC-Abfrage {min(i + chunk, len(ids))}/{len(ids)}")
    return pd.concat(parts, ignore_index=True)


def main():
    print(f"Sektor {SECTOR}: suche 2-Minuten-Sterne ...")
    ids = sector_tics(SECTOR)
    print(f" {len(ids)} Sterne mit Daten")

    print("Hole Sterneigenschaften aus dem TIC ...")
    df = tic_properties(ids)
    df = df[
        (df["Tmag"] <= TMAG_MAX)
        & (df["rad"] <= RAD_MAX)
        & (df["Teff"].between(*TEFF_RANGE))
    ]
    print(f" {len(df)} nach Helligkeits-/Grössen-Filter")

    print("Ziehe TOIs und bekannte Planeten ab ...")
    known = known_tics()
    df = df[~df["ID"].astype(int).isin(known)].sort_values("Tmag")
    print(f" {len(df)} übrig ({len(known)} bekannte Sterne in der Abzugsliste)")

    DATA.mkdir(exist_ok=True)
    OUT.write_text("\n".join(str(int(i)) for i in df["ID"]) + "\n")
    print(f"Gespeichert: {OUT}")


if __name__ == "__main__":
    main()
