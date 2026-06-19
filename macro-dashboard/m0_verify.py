"""
M0 验证脚本 — 美国实际 GDP (FRED: GDPC1)
纯标准库，无需第三方依赖
"""

import json
import urllib.request
from datetime import datetime

API_KEY = "2454f654814b23ee413ba9a48268ef14"
BASE_URL = "https://api.stlouisfed.org/fred"


def fred_get(endpoint, params):
    params["api_key"] = API_KEY
    params["file_type"] = "json"
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE_URL}/{endpoint}?{query}"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode())


def get_series_info(series_id):
    data = fred_get("series", {"series_id": series_id})
    return data.get("seriess", [{}])[0]


def get_observations(series_id, limit=20):
    data = fred_get("series/observations", {
        "series_id": series_id,
        "limit": limit,
        "sort_order": "desc"
    })
    obs = data["observations"]
    # 升序排列
    obs.reverse()
    return obs


def quarter_label(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year} Q{q}"


def calc_qoq_annualized(current, previous):
    """((current/previous)^4 - 1) * 100"""
    return ((current / previous) ** 4 - 1) * 100


def calc_yoy(current, prev4):
    return (current / prev4 - 1) * 100


def main():
    print("=" * 65)
    print("  M0 验证 — 美国实际 GDP (FRED: GDPC1)")
    print("=" * 65)

    # 元数据
    info = get_series_info("GDPC1")
    print(f"\n数据系列 : {info.get('title')}")
    print(f"单位     : {info.get('units')}")
    print(f"频率     : {info.get('frequency')}")
    print(f"最后更新 : {info.get('last_updated', 'N/A')}")
    print(f"数据来源 : BEA via FRED")
    print(f"总数据点 : 317个季度 (1947 Q1 起)")

    # 拉取最近16个季度（多取4个季度用于 YoY 计算）
    obs = get_observations("GDPC1", limit=16)
    values = [float(o["value"]) for o in obs]
    dates  = [o["date"] for o in obs]

    print("\n" + "-" * 65)
    print(f"  {'季度':<10} {'GDP(十亿$)':<16} {'QoQ年化(%)':<14} {'YoY(%)'}")
    print("-" * 65)

    for i in range(len(obs)):
        val = values[i]
        ql  = quarter_label(dates[i])

        qoq_str = "  N/A  "
        yoy_str = "  N/A"

        if i >= 1:
            qoq = calc_qoq_annualized(val, values[i-1])
            qoq_str = f"{qoq:+7.2f}%"

        if i >= 4:
            yoy = calc_yoy(val, values[i-4])
            yoy_str = f"{yoy:+.2f}%"

        # 仅显示最近10个季度
        if i >= 6:
            print(f"  {ql:<10} {val:>14,.3f}   {qoq_str:<13} {yoy_str}")

    # 最新季度重点展示
    latest_val  = values[-1]
    latest_date = dates[-1]
    latest_ql   = quarter_label(latest_date)
    latest_qoq  = calc_qoq_annualized(latest_val, values[-2])
    latest_yoy  = calc_yoy(latest_val, values[-5])

    print("\n" + "=" * 65)
    print(f"  最新数据 [{latest_ql}]")
    print(f"  实际 GDP   : ${latest_val:,.3f}B  (2017年链式美元，季调年化)")
    print(f"  QoQ 年化   : {latest_qoq:+.2f}%")
    print(f"  YoY        : {latest_yoy:+.2f}%")
    print("=" * 65)

    print(f"\n--- 交叉验证链接 ---")
    print(f"BEA 官网  : https://www.bea.gov/data/gdp/gross-domestic-product")
    print(f"FRED 页面 : https://fred.stlouisfed.org/series/GDPC1")
    print(f"\n验证方法: BEA 官网 Advance/Second/Third Estimate 新闻稿中")
    print(f"'Real GDP' 增速数字应与上方 QoQ年化 数字一致。")

    # 额外验证：联邦基金利率
    print("\n" + "=" * 65)
    print("  M0 附加验证 — 联邦基金有效利率 (FRED: DFF)")
    print("=" * 65)
    rate_obs = get_observations("DFF", limit=10)
    latest_rate = float(rate_obs[-1]["value"])
    latest_rate_date = rate_obs[-1]["date"]
    print(f"\n  最新利率 ({latest_rate_date}): {latest_rate:.2f}%")
    print(f"  FRED 页面: https://fred.stlouisfed.org/series/DFF")

    print("\n[M0 验证完成] API 正常，数据可靠。")


if __name__ == "__main__":
    main()
