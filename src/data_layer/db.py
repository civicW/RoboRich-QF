import sqlite3
import os
from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kline_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            market TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            turnover REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            market TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            last_price REAL,
            change_rate REAL,
            volume INTEGER,
            turnover REAL,
            pe_ratio REAL,
            pb_ratio REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, snapshot_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] 数据库初始化完成")


def upsert_kline(code: str, market: str, date: str,
                 open_: float, high: float, low: float, close: float,
                 volume: int, turnover: float):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO kline_daily
           (code, market, date, open, high, low, close, volume, turnover)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (code, market, date, open_, high, low, close, volume, turnover),
    )
    conn.commit()
    conn.close()


def upsert_snapshot(code: str, market: str, snapshot_date: str,
                    last_price: float, change_rate: float,
                    volume: int, turnover: float,
                    pe_ratio: float, pb_ratio: float):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO daily_snapshot
           (code, market, snapshot_date, last_price, change_rate,
            volume, turnover, pe_ratio, pb_ratio)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (code, market, snapshot_date, last_price, change_rate,
         volume, turnover, pe_ratio, pb_ratio),
    )
    conn.commit()
    conn.close()


def upsert_macro(symbol: str, date: str, value: float):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO macro_data (symbol, date, value)
           VALUES (?, ?, ?)""",
        (symbol, date, value),
    )
    conn.commit()
    conn.close()
