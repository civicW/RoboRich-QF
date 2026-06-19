"""
宏观指标批量拉取 — 纯标准库，无依赖
按"自上而下"传导链分层：L1债券 → L2股市 → L3同步 → L4滞后
"""

import json
import urllib.request
import sqlite3
import os
from datetime import datetime, timedelta

API_KEY = "2454f654814b23ee413ba9a48268ef14"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "macro.db")

# ─── 指标清单（按传导链分层）────────────────────────────────────────────
INDICATORS = {
    # L1 — 债券市场（最领先，9-12月）
    "DGS2":          ("L1", "2Y国债收益率",          "%"),
    "DGS5":          ("L1", "5Y国债收益率",          "%"),
    "DGS10":         ("L1", "10Y国债收益率",         "%"),
    "DGS30":         ("L1", "30Y国债收益率",         "%"),
    "T10Y2Y":        ("L1", "10Y-2Y利差(倒挂信号)",  "pp"),
    "DFII10":        ("L1", "10Y实际利率(TIPS)",     "%"),
    "T10YIE":        ("L1", "10Y盈亏平衡通胀预期",   "%"),
    "BAMLH0A0HYM2":  ("L1", "高收益债信用利差(HY)",  "%"),
    "BAMLC0A0CM":    ("L1", "投资级信用利差(IG)",    "%"),

    # L2 — 股市（领先 ~6月）
    "SP500":         ("L2", "S&P 500指数",           "pt"),
    "VIXCLS":        ("L2", "VIX恐慌指数",           "pt"),

    # L3 — 同步指标
    "DFF":           ("L3", "联邦基金利率",           "%"),
    "CPIAUCSL":      ("L3", "CPI(同比)",             "index"),
    "PCEPILFE":      ("L3", "核心PCE",               "index"),
    "INDPRO":        ("L3", "工业产出指数",           "index"),
    "RSXFS":         ("L3", "零售销售(扣汽车)",       "M$"),
    "M2SL":          ("L3", "M2货币供应",             "B$"),

    # L4 — 滞后（最终验证）
    "GDPC1":         ("L4", "实际GDP",               "B$"),
    "UNRATE":        ("L4", "失业率",                "%"),
    "PAYEMS":        ("L4", "非农就业",               "K"),
}


def fred_fetch(series_id: str, limit: int = 20) -> list[dict]:
    """从FRED拉取最近N条观测，返回 [{date, value}, ...]"""
    url = (
        f"{FRED_BASE}?series_id={series_id}"
        f"&api_key={API_KEY}&file_type=json"
        f"&limit={limit}&sort_order=desc"
    )
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    obs = [
        {"date": o["date"], "value": float(o["value"])}
        for o in data["observations"]
        if o["value"] not in (".", "")
    ]
    return sorted(obs, key=lambda x: x["date"])


def init_db(db_path: str = DB_PATH):
    """初始化 SQLite，创建表"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            series_id  TEXT NOT NULL,
            date       TEXT NOT NULL,
            value      REAL NOT NULL,
            layer      TEXT,
            label      TEXT,
            unit       TEXT,
            fetched_at TEXT,
            PRIMARY KEY (series_id, date)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS derived (
            metric     TEXT NOT NULL,
            date       TEXT NOT NULL,
            value      REAL NOT NULL,
            note       TEXT,
            fetched_at TEXT,
            PRIMARY KEY (metric, date)
        )
    """)
    conn.commit()
    return conn


def save_obs(conn, series_id, records, layer, label, unit):
    now = datetime.utcnow().isoformat()
    conn.executemany(
        "INSERT OR REPLACE INTO observations VALUES (?,?,?,?,?,?,?)",
        [(series_id, r["date"], r["value"], layer, label, unit, now)
         for r in records],
    )
    conn.commit()


def compute_yield_curve(conn):
    """计算收益率曲线形态（NORMAL/FLAT/INVERTED）"""
    c = conn.cursor()
    result = {}
    for sid in ("DGS2", "DGS5", "DGS10", "DGS30"):
        row = c.execute(
            "SELECT date, value FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 1",
            (sid,)
        ).fetchone()
        if row:
            result[sid] = {"date": row[0], "value": row[1]}

    if "DGS2" in result and "DGS10" in result:
        spread_2_10 = result["DGS10"]["value"] - result["DGS2"]["value"]
        if spread_2_10 > 0.1:
            shape = "NORMAL"
        elif spread_2_10 < -0.1:
            shape = "INVERTED ⚠️"
        else:
            shape = "FLAT"
        result["shape"] = shape
        result["spread_2_10"] = spread_2_10
        # 保存派生指标
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO derived VALUES (?,?,?,?,?)",
            ("spread_2_10", result["DGS10"]["date"], spread_2_10, shape, now)
        )
        conn.commit()
    return result


def fetch_all(verbose: bool = True) -> dict:
    """拉取所有指标，写入DB，返回汇总"""
    conn = init_db()
    summary = {}

    for series_id, (layer, label, unit) in INDICATORS.items():
        try:
            records = fred_fetch(series_id, limit=20)
            save_obs(conn, series_id, records, layer, label, unit)
            latest = records[-1]
            summary[series_id] = {
                "layer": layer, "label": label, "unit": unit,
                "date": latest["date"], "value": latest["value"]
            }
            if verbose:
                print(f"  ✓ [{layer}] {series_id:<18} {label:<20}  "
                      f"{latest['value']:>10.3f} {unit}  @ {latest['date']}")
        except Exception as e:
            print(f"  ✗ [{layer}] {series_id:<18} 失败: {e}")
            summary[series_id] = {"error": str(e)}

    # 计算派生指标
    curve = compute_yield_curve(conn)
    if "shape" in curve:
        print(f"\n  📊 收益率曲线形态: {curve['shape']}")
        print(f"     2Y-10Y利差: {curve['spread_2_10']:+.2f}pp")

    conn.close()
    return summary


def print_dashboard(summary: dict):
    """打印当前宏观仪表盘快照"""
    layers = {"L1": "债券市场（最领先）", "L2": "股市（领先~6月）",
              "L3": "同步指标", "L4": "滞后指标（验证用）"}

    print("\n" + "="*65)
    print("  宏观仪表盘快照")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print("="*65)

    for layer, layer_name in layers.items():
        items = [(sid, v) for sid, v in summary.items()
                 if isinstance(v, dict) and v.get("layer") == layer and "error" not in v]
        if not items:
            continue
        print(f"\n  ── {layer} {layer_name}")
        for sid, v in items:
            print(f"     {sid:<18} {v['label']:<22}  {v['value']:>10.3f} {v['unit']}")

    # 信号判断
    t10y2y = summary.get("T10Y2Y", {})
    hy = summary.get("BAMLH0A0HYM2", {})
    vix = summary.get("VIXCLS", {})
    gdp_signal = "📈 扩张"

    print("\n" + "-"*65)
    print("  宏观信号")
    if t10y2y.get("value") is not None:
        spread = t10y2y["value"]
        if spread < -0.1:
            print(f"  ⚠️  收益率曲线倒挂 ({spread:+.2f}pp) — 衰退预警")
            gdp_signal = "⚠️ 衰退风险"
        else:
            print(f"  ✅  收益率曲线正常 ({spread:+.2f}pp)")
    if hy.get("value") is not None:
        hy_val = hy["value"] * 100  # 转为bp
        flag = "⚠️ 偏宽" if hy_val > 400 else "✅ 正常"
        print(f"  {flag}  HY信用利差: {hy_val:.0f}bp")
    if vix.get("value") is not None:
        vix_val = vix["value"]
        flag = "⚠️ 高恐慌" if vix_val > 25 else "✅ 平稳"
        print(f"  {flag}  VIX: {vix_val:.1f}")
    print(f"\n  🎯 当前GDP方向预测: {gdp_signal}")
    print(f"  🎯 交易偏差: {'Long S&P 500' if '扩张' in gdp_signal else 'Long-Short 对冲'}")
    print("="*65)


if __name__ == "__main__":
    print("正在拉取所有宏观指标...\n")
    summary = fetch_all(verbose=True)
    print_dashboard(summary)
