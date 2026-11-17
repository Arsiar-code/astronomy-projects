import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"
DB = DATA / "results.db"
FLAGS = ["flag_variable", "flag_oddeven", "flag_secondary", "flag_edge"]

st.set_page_config(page_title="Exoplanet Finder", layout="wide")
st.title("Exoplanet Finder")

@st.cache_data(ttl=30)
def load():
    con = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM results", con)
    con.close()
    return df

df = load()
if df.empty:
    st.warning("Die Datenbank ist noch leer.")
    st.stop()

versions = sorted(df["pipeline_version"].dropna().unique(), reverse=True)
version = st.sidebar.selectbox("Pipeline-Version", versions)
df = df[df["pipeline_version"] == version]

ok = df[df["status"] == "ok"].copy()
ok["clean"] = (ok[FLAGS] == 0).all(axis=1)
ok["klasse"] = ok["clean"].map({True: "sauber", False: "markiert"})
ok["depth_ppm"] = ok["depth"] * 1e6

# Übersicht
st.header("Übersicht")
cols = st.columns(4)
cols[0].metric("Sterne gesamt", len(df))
cols[1].metric("Erfolgreich", len(ok))
cols[2].metric("Fehler", int((df["status"] == "error").sum()))
cols[3].metric("Sauber (alle Tests bestanden)", int(ok["clean"].sum()))

st.subheader("Wo fallen die Sterne durch?")
funnel = pd.Series({
    "variable": int((ok["flag_variable"] == 1).sum()),
    "Odd/Even": int((ok["flag_oddeven"] == 1).sum()),
    "Sekundärminimum": int((ok["flag_secondary"] == 1).sum()),
    "Rand / wenige Transits": int((ok["flag_edge"] == 1).sum()),
    "sauber": int(ok["clean"].sum()),
})
st.bar_chart(funnel)
st.caption("Ein Stern kann mehrere Flags haben, die Balken addieren sich deshalb nicht zu Gesamtzahl.")

# Tabelle
st.header("Tabelle")
only_clean = st.sidebar.checkbox("Nur saubere Sterne", value=False)
min_snr = st.sidebar.slider("Minimales echtes SNR", 0.0, 30.0, 0.0, 0.5)

view = ok.copy()
if only_clean:
    view = view[view["clean"]]
view = view[view["snr_real"].fillna(0) >= min_snr]
view = view.sort_values("snr_real", ascending=False)

show = ["tic", "period", "depth_ppm", "snr_real", "n_transits", "oot_ratio"] + FLAGS
st.dataframe(view[show], use_container_width=True, hide_index=True)

# Streudiagramm
st.header("Periode gegen Tiefe")
st.scatter_chart(ok, x="period", y="depth_ppm", color="klasse")
st.caption("Häufungen am rechten Rand (um 13 bis 15 Tage) sind ein Warnzeichen für Artefakte.")

# Detail
st.header("Einzelner Stern")
if view.empty:
    st.info("Kein Stern passt zu den Filtern.")
else:
    tic = st.selectbox("TIC", view["tic"].tolist())
    row = view[view["tic"] == tic].iloc[0]
    left, right = st.columns([3, 1])
    img = DATA / str(row["plot_path"])
    if img.exists():
        left.image(str(img))
    else:
        left.warning("Kein Plot gefunden.")
    right.write(f"Periode: {row['period']:.4f} d")
    right.write(f"Tiefe: {row['depth_ppm']:,0f} ppm")
    right.write(f"Echtes SNR: {row['snr_real']:.1f}")
    right.write(f"Transits: {row['n_transits']}")
    for f in FLAGS:
        v = row[f]
        right.write(f"{f}: " + ("unbekannt" if pd.isna(v) else ("JA" if v == 1 else "nein")))
