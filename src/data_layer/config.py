import os

# ── OpenD 连接 ──
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111

# ── 数据库 ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "roborich.db")

# ── 美股 Watchlist ──
WATCHLIST_US = [
    "US.NVDA",
    "US.GOOG",
    "US.AAPL",
    "US.TSLA",
    "US.SPY",
    "US.QQQ",
]

# ── 港股 Watchlist ──
WATCHLIST_HK = [
    "HK.00700",
    "HK.09988",
    "HK.03690",
]

# ── 宏观指标 (yfinance) ──
MACRO_SYMBOLS = [
    "^VIX",
    "^TNX",
    "DX-Y.NYB",
]

# ── 全部股票 ──
WATCHLIST_ALL = WATCHLIST_US + WATCHLIST_HK
