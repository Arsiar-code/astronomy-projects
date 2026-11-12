import sqlite3
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA / "results.db"


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
    return con


def already_done(con, tic):
    row = con.execute("SELECT 1 FROM results WHERE tic = ?", (tic,)).fetchone()
    return row is not None


def save(con, tic, status, res=None, n_sectors=None, plot_path=None):
    res = res or {}
    con.execute(
        "INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            tic, status,
            res.get("period"), res.get("depth"), res.get("t0"),
            res.get("duration"), res.get("snr"),
            n_sectors, res.get("n_transits"),
            plot_path, datetime.now().isoformat(timespec="seconds"),
        ),
    )
    con.commit()
