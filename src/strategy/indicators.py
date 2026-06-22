"""
技术指标计算模块
- 从 SQLite 读取日K线
- 支持日线/周线聚合
- 输出 DataFrame with MA5/MA20/MA60, RSI14, MACD, ATR
"""
import sqlite3
import pandas as pd
import numpy as np
from src.data_layer.config import DB_PATH


def load_kline(code: str, days: int = 300) -> pd.DataFrame:
    """读取某只股票的日K线，按日期升序"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"""
        SELECT date, open, high, low, close, volume
        FROM kline_daily
        WHERE code = ?
        ORDER BY date ASC
        LIMIT {days}
        """,
        conn,
        params=(code,),
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """日线 → 周线聚合（周五收盘）"""
    weekly = df.resample("W-FRI").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna()
    return weekly


def calc_ma(df: pd.DataFrame, periods: list = [5, 10, 20]) -> pd.DataFrame:
    """计算多周期均线（适用于日线或周线）"""
    for p in periods:
        df[f"ma{p}"] = df["close"].rolling(p).mean()
    return df


def calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI 计算"""
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def calc_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    """MACD 计算，返回 macd_line, signal_line, histogram"""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]
    return df


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ATR 波动率"""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(period).mean()
    return df


def get_indicators(code: str, freq: str = "weekly") -> pd.DataFrame:
    """
    一次性获取某只股票的全部指标
    freq: 'daily' or 'weekly'
    """
    df = load_kline(code, days=300)
    if freq == "weekly":
        df = to_weekly(df)
    df = calc_ma(df, [5, 10, 20])
    df = calc_rsi(df)
    df = calc_macd(df)
    df = calc_atr(df)
    return df
