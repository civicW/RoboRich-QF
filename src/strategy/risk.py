"""
风险管理模块
- VIX 联动仓位系数
- 最大单票仓位约束
- 止损线判断
"""
import sqlite3
import pandas as pd
from src.data_layer.config import DB_PATH


# ─── 风控参数 ───
MAX_SINGLE_POSITION = 0.20    # 单票最大仓位 20%
STOP_LOSS_PCT = 0.10          # 止损线 -10%（从成本价）

# VIX 分级仓位系数
VIX_TIERS = [
    (15, 1.0),    # VIX < 15 → 满仓
    (20, 0.8),    # 15 ≤ VIX < 20 → 八成仓
    (25, 0.6),    # 20 ≤ VIX < 25 → 六成仓
    (35, 0.4),    # 25 ≤ VIX < 35 → 四成仓
    (float("inf"), 0.2),  # VIX ≥ 35 → 二成仓（极度恐慌）
]


def get_latest_vix() -> float | None:
    """从 macro_data 读取最新 VIX"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT value FROM macro_data WHERE symbol = '^VIX' ORDER BY date DESC LIMIT 1",
        conn,
    )
    conn.close()
    if df.empty:
        return None
    return float(df.iloc[0]["value"])


def vix_position_factor(vix: float | None = None) -> dict:
    """
    根据 VIX 返回仓位系数和说明
    """
    if vix is None:
        vix = get_latest_vix()
    if vix is None:
        return {"factor": 0.8, "vix": None, "reason": "VIX 数据缺失，默认 0.8"}

    for threshold, factor in VIX_TIERS:
        if vix < threshold:
            return {
                "factor": factor,
                "vix": vix,
                "reason": f"VIX {vix:.2f} → 仓位系数 {factor:.0%}",
            }


def position_limit(total_portfolio: float, vix_factor: float = 1.0) -> dict:
    """
    计算单票最大可投金额
    total_portfolio: 总资产（任意货币单位）
    """
    adjusted_max = MAX_SINGLE_POSITION * vix_factor
    max_amount = total_portfolio * adjusted_max
    return {
        "max_single_pct": adjusted_max,
        "max_single_amount": max_amount,
        "reason": f"单票上限 {adjusted_max:.0%}（基础 {MAX_SINGLE_POSITION:.0%} × VIX系数 {vix_factor:.0%}）",
    }


def stop_loss_check(cost_price: float, current_price: float) -> dict:
    """
    判断是否触发止损
    """
    pnl_pct = (current_price - cost_price) / cost_price
    triggered = pnl_pct <= -STOP_LOSS_PCT
    return {
        "triggered": triggered,
        "pnl_pct": pnl_pct,
        "reason": f"成本 {cost_price:.2f} → 现价 {current_price:.2f}（{pnl_pct:+.1%}）{'⚠️ 触发止损' if triggered else ''}",
    }


def get_risk_summary() -> dict:
    """当前市场风险摘要"""
    vix_info = vix_position_factor()
    return {
        "vix": vix_info["vix"],
        "position_factor": vix_info["factor"],
        "max_single_position": MAX_SINGLE_POSITION,
        "stop_loss_pct": STOP_LOSS_PCT,
        "summary": vix_info["reason"],
    }
