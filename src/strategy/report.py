"""
周报生成 + 飞书推送
格式：市场风险概览 → 板块强弱 → 个股信号 → 调仓建议
"""
from datetime import datetime
from src.strategy.signals import scan_all
from src.strategy.risk import get_risk_summary
from src.strategy.sector_rank import sector_rank


SIGNAL_EMOJI = {
    "bullish": "🟢",
    "bearish": "🔴",
    "neutral": "⚪",
}


def generate_report() -> str:
    """生成 Markdown 格式周报"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. 风险摘要
    risk = get_risk_summary()
    vix_str = f"{risk['vix']:.2f}" if risk["vix"] else "N/A"

    # 2. 板块强弱
    rank_df = sector_rank(weeks=4)

    # 3. 个股信号
    signals = scan_all()

    lines = []
    lines.append(f"# 📊 RoboRich 周报 · {now}")
    lines.append("")

    # 风控
    lines.append("## 🛡️ 市场风险")
    lines.append(f"- VIX：**{vix_str}**")
    lines.append(f"- 仓位系数：**{risk['position_factor']:.0%}**（{risk['summary']}）")
    lines.append(f"- 单票上限：{risk['max_single_position']:.0%}  |  止损线：{risk['stop_loss_pct']:.0%}")
    lines.append("")

    # 板块强弱
    lines.append("## 🔄 板块相对强弱（4周）")
    lines.append("| 排名 | 标的 | 板块 | 4周涨幅 |")
    lines.append("|------|------|------|---------|")
    for _, row in rank_df.iterrows():
        lines.append(f"| {int(row['rank'])} | {row['code']} | {row['sector']} | {row['return_4w_pct']} |")
    lines.append("")

    # 个股信号
    lines.append("## 📈 个股信号")
    for s in signals:
        if "error" in s:
            lines.append(f"- **{s['code']}** ⚠️ {s['error']}")
            continue
        t_emoji = SIGNAL_EMOJI.get(s["trend"]["signal"], "⚪")
        m_emoji = SIGNAL_EMOJI.get(s["momentum"]["signal"], "⚪")
        rsi_str = f"RSI {s['rsi']:.1f}" if s["rsi"] else ""
        val_reason = s["valuation"]["reason"]
        score_str = f"综合评分 {s['score']:+d}"
        lines.append(
            f"### {t_emoji} {s['code']}  ·  收 {s['close']:.2f}  ·  {score_str}"
        )
        lines.append(f"- 趋势：{t_emoji} {s['trend']['reason']}")
        lines.append(f"- 动量：{m_emoji} {s['momentum']['reason']}")
        lines.append(f"- 估值：{val_reason}")
        lines.append("")

    # 调仓建议
    lines.append("## 💡 调仓建议")
    strong_buy = [s for s in signals if s.get("score", 0) >= 2]
    reduce = [s for s in signals if s.get("score", 0) <= -2]

    if strong_buy:
        lines.append("**可加仓（综合评分 ≥ +2）：**")
        for s in strong_buy:
            lines.append(f"- {s['code']} 评分 {s['score']:+d}，注意单票不超 {risk['max_single_position']:.0%}")
    else:
        lines.append("**无强力买入信号**")

    if reduce:
        lines.append("**建议减仓/止损观察（综合评分 ≤ -2）：**")
        for s in reduce:
            lines.append(f"- {s['code']} 评分 {s['score']:+d}，确认是否触发止损线")
    else:
        lines.append("**无需强制减仓**")

    lines.append("")
    lines.append(f"---")
    lines.append(f"*由 RoboRich-QF 自动生成 · {now}*")

    return "\n".join(lines)


def print_report():
    """打印报告到终端"""
    report = generate_report()
    print(report)
    return report
