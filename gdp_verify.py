"""
GDP 拉取器 + 验证
使用 FRED: GDPC1 (Real GDP, 季调，年化十亿美元)
"""

import pandas as pd
from fetchers.fred import fetch_series, fetch_series_info


SERIES_ID = "GDPC1"


def get_gdp(quarters: int = 12) -> pd.DataFrame:
    """
    拉取最近 N 个季度的实际 GDP 数据，并计算：
    - qoq_annualized: 季环比年化增速 (%)
    - yoy: 同比增速 (%)
    """
    df = fetch_series(SERIES_ID, limit=quarters + 4, sort_order="asc")
    df = df.tail(quarters + 1).reset_index(drop=True)

    # QoQ annualized: ((current/prev)^4 - 1) * 100
    df["qoq_annualized"] = ((df["value"] / df["value"].shift(1)) ** 4 - 1) * 100

    # YoY: ((current/prev_4q) - 1) * 100
    df["yoy"] = (df["value"] / df["value"].shift(4) - 1) * 100

    df = df.tail(quarters).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("M0 验证 — 美国实际 GDP (FRED: GDPC1)")
    print("=" * 60)

    info = fetch_series_info(SERIES_ID)
    print(f"\n数据系列: {info.get('title')}")
    print(f"单位    : {info.get('units')}")
    print(f"频率    : {info.get('frequency')}")
    print(f"最后更新: {info.get('last_updated')}")
    print(f"数据来源: {info.get('source', 'BEA via FRED')}")

    df = get_gdp(quarters=10)

    print("\n最近10个季度实际 GDP:\n")
    print(f"{'季度':<12} {'GDP(十亿美元)':<18} {'QoQ年化(%)':<15} {'YoY(%)'}")
    print("-" * 60)
    for _, row in df.iterrows():
        quarter_str = f"{row['date'].year} Q{(row['date'].month - 1) // 3 + 1}"
        gdp_val = f"{row['value']:,.3f}"
        qoq = f"{row['qoq_annualized']:+.2f}%" if pd.notna(row['qoq_annualized']) else "N/A"
        yoy = f"{row['yoy']:+.2f}%" if pd.notna(row['yoy']) else "N/A"
        print(f"{quarter_str:<12} {gdp_val:<18} {qoq:<15} {yoy}")

    print("\n--- 交叉验证 ---")
    latest = df.iloc[-1]
    q_str = f"{latest['date'].year} Q{(latest['date'].month - 1) // 3 + 1}"
    print(f"最新季度: {q_str}")
    print(f"  GDP:    ${latest['value']:,.3f}B (2017年链式美元)")
    print(f"  QoQ年化: {latest['qoq_annualized']:+.2f}%")
    print(f"  YoY:    {latest['yoy']:+.2f}%")
    print(f"\n请对照 BEA 官网验证: https://www.bea.gov/data/gdp/gross-domestic-product")
    print(f"FRED 页面: https://fred.stlouisfed.org/series/GDPC1")
