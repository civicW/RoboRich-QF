"""
信号生成模块
- 趋势信号：均线金叉/死叉（周线）
- 动量信号：RSI 超买超卖、MACD 背离
- 估值信号：PE/PB 历史分位数
"""
import sqlite3
import pandas as pd
import numpy as np
from src.strategy.indicators import get_indicators
from src.data_layer.config import DB_PATH, WATCHLIST_ALL


# ─── 信号阈值 ───
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 70
PE_HIGH_PCTILE = 80   # PE 超过历史80分位 → 高估
PB_HIGH_PCTILE = 80


def trend_signal(df: pd.DataFrame) -> dict:
    """
    均线趋势信号（周线级别）
    返回: {'signal': 'bullish'|'bearish'|'neutral', 'reason': str}
    """
    if len(df) < 20:
        return {"signal": "neutral", "reason": "数据不足"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # MA5 上穿 MA20 → 金叉
    golden_cross = prev["ma5"] <= prev["ma20"] and last["ma5"] > last["ma20"]
    # MA5 下穿 MA20 → 死叉
    death_cross = prev["ma5"] >= prev["ma20"] and last["ma5"] < last["ma20"]
    # 价格在 MA20 上方 → 多头排列
    above_ma20 = last["close"] > last["ma20"]

    if golden_cross:
        return {"signal": "bullish", "reason": "MA5 上穿 MA20（金叉）"}
    elif death_cross:
        return {"signal": "bearish", "reason": "MA5 下穿 MA20（死叉）"}
    elif above_ma20:
        return {"signal": "bullish", "reason": f"价格在 MA20 上方 ({last['ma20']:.2f})"}
    else:
        return {"signal": "bearish", "reason": f"价格在 MA20 下方 ({last['ma20']:.2f})"}


def momentum_signal(df: pd.DataFrame) -> dict:
    """
    RSI + MACD 动量信号
    """
    if len(df) < 26:
        return {"signal": "neutral", "reason": "数据不足"}

    last = df.iloc[-1]
    prev = df.iloc[-2]
    rsi = last["rsi"]

    signals = []

    # RSI 信号
    if rsi < RSI_OVERSOLD:
        signals.append(f"RSI {rsi:.1f} 超卖（< {RSI_OVERSOLD}）")
        rsi_sig = "bullish"
    elif rsi > RSI_OVERBOUGHT:
        signals.append(f"RSI {rsi:.1f} 超买（> {RSI_OVERBOUGHT}）")
        rsi_sig = "bearish"
    else:
        rsi_sig = "neutral"

    # MACD 信号
    macd_cross_up = prev["macd_line"] <= prev["macd_signal"] and last["macd_line"] > last["macd_signal"]
    macd_cross_down = prev["macd_line"] >= prev["macd_signal"] and last["macd_line"] < last["macd_signal"]

    if macd_cross_up:
        signals.append("MACD 金叉")
        macd_sig = "bullish"
    elif macd_cross_down:
        signals.append("MACD 死叉")
        macd_sig = "bearish"
    else:
        macd_sig = "neutral"
        signals.append(f"MACD hist {last['macd_hist']:.3f}")

    # 综合
    bullish_count = [rsi_sig, macd_sig].count("bullish")
    bearish_count = [rsi_sig, macd_sig].count("bearish")

    if bullish_count > bearish_count:
        overall = "bullish"
    elif bearish_count > bullish_count:
        overall = "bearish"
    else:
        overall = "neutral"

    return {"signal": overall, "reason": " | ".join(signals), "rsi": rsi}


def valuation_signal(code: str) -> dict:
    """
    PE/PB 均值回归估值信号
    - 历史分位数：当前值在历史分布中的位置
    - 均值回归折扣：当前值 vs 历史均值的偏离幅度
    从 daily_snapshot 读取历史数据（每日积累，越久越准）
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT snapshot_date, pe_ratio, pb_ratio FROM daily_snapshot WHERE code = ? ORDER BY snapshot_date ASC",
        conn, params=(code,)
    )
    conn.close()

    if df.empty or df["pe_ratio"].isna().all():
        return {"signal": "neutral", "reason": "无估值数据（需积累历史快照）", "pe_pctile": None, "pb_pctile": None}

    latest_pe = df["pe_ratio"].iloc[-1]
    latest_pb = df["pb_ratio"].iloc[-1]

    # 历史有效值（排除负值/零）
    pe_vals = df["pe_ratio"].dropna()
    pe_vals = pe_vals[pe_vals > 0]
    pb_vals = df["pb_ratio"].dropna()
    pb_vals = pb_vals[pb_vals > 0]

    history_days = len(df)
    reasons = []
    overvalued = False
    undervalued = False

    # ── PE 分析 ──
    pe_pctile = None
    pe_vs_mean = None
    if len(pe_vals) >= 5 and latest_pe > 0:
        pe_mean = pe_vals.mean()
        pe_pctile = (pe_vals < latest_pe).mean() * 100
        pe_vs_mean = (latest_pe - pe_mean) / pe_mean  # 偏离均值百分比

        if pe_pctile > PE_HIGH_PCTILE:
            overvalued = True
            reasons.append(f"PE {latest_pe:.1f}（均值{pe_mean:.1f}，+{pe_vs_mean:.0%}，历史{pe_pctile:.0f}%分位 ⚠️高估）")
        elif pe_pctile < (100 - PE_HIGH_PCTILE):  # 低于20%分位
            undervalued = True
            reasons.append(f"PE {latest_pe:.1f}（均值{pe_mean:.1f}，{pe_vs_mean:.0%}，历史{pe_pctile:.0f}%分位 💡低估）")
        else:
            reasons.append(f"PE {latest_pe:.1f}（均值{pe_mean:.1f}，{pe_vs_mean:+.0%}，历史{pe_pctile:.0f}%分位）")
    elif latest_pe > 0:
        reasons.append(f"PE {latest_pe:.1f}（历史仅{history_days}天，分位待积累）")

    # ── PB 分析 ──
    pb_pctile = None
    if len(pb_vals) >= 5 and latest_pb > 0:
        pb_mean = pb_vals.mean()
        pb_pctile = (pb_vals < latest_pb).mean() * 100
        pb_vs_mean = (latest_pb - pb_mean) / pb_mean

        if pb_pctile > PB_HIGH_PCTILE:
            overvalued = True
            reasons.append(f"PB {latest_pb:.2f}（均值{pb_mean:.2f}，+{pb_vs_mean:.0%}，{pb_pctile:.0f}%分位 ⚠️）")
        elif pb_pctile < (100 - PB_HIGH_PCTILE):
            undervalued = True
            reasons.append(f"PB {latest_pb:.2f}（均值{pb_mean:.2f}，{pb_vs_mean:.0%}，{pb_pctile:.0f}%分位 💡）")
        else:
            reasons.append(f"PB {latest_pb:.2f}（均值{pb_mean:.2f}，{pb_vs_mean:+.0%}，{pb_pctile:.0f}%分位）")
    elif latest_pb > 0:
        reasons.append(f"PB {latest_pb:.2f}（历史{history_days}天，分位待积累）")

    # 高估压制信号，低估加分
    if overvalued:
        signal = "bearish"
    elif undervalued:
        signal = "bullish"
    else:
        signal = "neutral"

    return {
        "signal": signal,
        "reason": " | ".join(reasons) if reasons else f"历史仅{history_days}天，数据积累中",
        "pe_pctile": pe_pctile,
        "pb_pctile": pb_pctile,
        "history_days": history_days,
    }


def analyze_stock(code: str) -> dict:
    """综合分析单只股票，返回完整信号字典"""
    df = get_indicators(code, freq="weekly")
    last = df.iloc[-1]

    trend = trend_signal(df)
    momentum = momentum_signal(df)
    valuation = valuation_signal(code)

    # 综合评分：trend + momentum 各 1 分，估值高分扣 1 分
    score = 0
    if trend["signal"] == "bullish":
        score += 1
    elif trend["signal"] == "bearish":
        score -= 1
    if momentum["signal"] == "bullish":
        score += 1
    elif momentum["signal"] == "bearish":
        score -= 1
    if valuation["signal"] == "bearish":
        score -= 1  # 高估压制
    elif valuation["signal"] == "bullish":
        score += 1  # 低估加分（价值投资信号）

    return {
        "code": code,
        "close": last["close"],
        "rsi": momentum.get("rsi"),
        "score": score,
        "trend": trend,
        "momentum": momentum,
        "valuation": valuation,
    }


def scan_all() -> list[dict]:
    """扫描全部 Watchlist，返回信号列表，按综合评分降序"""
    results = []
    for code in WATCHLIST_ALL:
        try:
            result = analyze_stock(code)
            results.append(result)
        except Exception as e:
            results.append({"code": code, "error": str(e), "score": 0})
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
