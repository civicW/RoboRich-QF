"""
行业/板块相对强弱排名
基于过去 N 周的涨幅排名
"""
import pandas as pd
from src.strategy.indicators import get_indicators
from src.data_layer.config import WATCHLIST_US, WATCHLIST_HK

# 板块分组（手动映射）
SECTOR_MAP = {
    "US.NVDA": "科技/芯片",
    "US.GOOG": "科技/互联网",
    "US.AAPL": "科技/消费电子",
    "US.TSLA": "新能源/汽车",
    "US.SPY":  "大盘/指数",
    "US.QQQ":  "科技/指数",
    "HK.00700": "科技/互联网",
    "HK.09988": "电商/零售",
    "HK.03690": "科技/电商",
}


def calc_momentum_return(code: str, weeks: int = 4) -> dict:
    """计算过去 N 周涨幅"""
    try:
        df = get_indicators(code, freq="weekly")
        if len(df) < weeks + 1:
            return {"code": code, "return": None, "error": "数据不足"}
        recent = df["close"].iloc[-1]
        past = df["close"].iloc[-(weeks + 1)]
        ret = (recent - past) / past
        return {
            "code": code,
            "sector": SECTOR_MAP.get(code, "其他"),
            "return_4w": ret,
            "close": recent,
        }
    except Exception as e:
        return {"code": code, "error": str(e), "return_4w": None}


def sector_rank(weeks: int = 4) -> pd.DataFrame:
    """
    全部标的按 4 周涨幅排名
    返回 DataFrame，降序
    """
    all_codes = WATCHLIST_US + WATCHLIST_HK
    rows = [calc_momentum_return(code, weeks) for code in all_codes]
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["return_4w"])
    df = df.sort_values("return_4w", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df["return_4w_pct"] = df["return_4w"].map(lambda x: f"{x:+.1%}")
    return df
