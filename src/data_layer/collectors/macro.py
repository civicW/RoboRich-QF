"""宏观数据采集：通过 yfinance 拉取 VIX / 美债收益率 / 美元指数。"""

from typing import List, Optional
import yfinance as yf

from ..db import upsert_macro
from ..config import MACRO_SYMBOLS


def collect_macro(symbols: Optional[List[str]] = None):
    symbols = symbols or MACRO_SYMBOLS

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if hist.empty:
                print(f"[Macro] {symbol} 无数据")
                continue

            count = 0
            for date, row in hist.iterrows():
                upsert_macro(
                    symbol=symbol,
                    date=str(date.date()),
                    value=float(row["Close"]),
                )
                count += 1
            print(f"[Macro] {symbol} 写入 {count} 条数据")
        except Exception as e:
            print(f"[Macro] {symbol} 采集异常: {e}")
