import sqlite3
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA / "results.db"
PIPELINE_VERSION = 2

NEW_COLUMNS = {
    "pipeline_version": "INTEGER",
    "snr_real": "REAL",
    "flag_variable": "INTEGER",
    "flag_oddeven": "INTEGER",
    "flag_secondary": "INTEGER",
    "flag_edge": "INTEGER",
    "npz_path": "TEXT",
    "oot_ratio": "REAL",
    "oddeven_sig": "REAL",
    "sec_ratio": "REAL",
}


def connect():
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS results (
            tic         INTEGER PRIMARY KEY,
            status      TEXT NOT NULL,      -- ok / no_data / error
            period      REAL,
            depth       REAL,
            t0          REAL,
            duration    REAL,
            snr         REAL,
            n_sectors   INTEGER,
            n_transits  INTEGER,
            plot_path   TEXT,
            run_date    TEXT
        )
    """)
    have = {row[1] for row in con.execute("PRAGMA table_info(results)")}
    for name, typ in NEW_COLUMNS.items():
        if name not in have:
            con.execute(f"ALTER TABLE results ADD COLUMN {name} {typ}")
    con.commit()
    return con


def already_done(con, tic):
    row = con.execute(
        "SELECT 1 FROM results WHERE tic = ? " 
        "AND status IN ('ok', 'no_data') AND pipeline_version = ?",
        (tic, PIPELINE_VERSION),
    ).fetchone()
    return row is not None


def save(con, tic, status, res=None, n_sectors=None, plot_path=None):
    row = dict(res or {})
    row.update(
        tic=tic,
        status=status,
        n_sectors=n_sectors,
        plot_path=plot_path,
        pipeline_version=PIPELINE_VERSION,
        run_date=datetime.now().isoformat(timespec="seconds"),
    )
    cols = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    con.execute(
            f"INSERT OR REPLACE INTO results ({cols}) VALUES ({marks})",
            list(row.values()),
    )
    con.commit()
