# RoboRich-QF — 量化投资 Agent 框架

> 自动化宏观看盘 + 自上而下投资框架，目标：周级量化投资 Agent

---

## 项目进度

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| 数据层 MVP | ✅ 完成 | futu-api + SQLite + yfinance 日K/快照/宏观采集 |
| M0 | ✅ 完成 | GDPC1 拉取验证（FRED API） |
| M1 | ✅ 完成 | 全量20个宏观指标批量拉取 + SQLite存储 + 信号引擎 |
| M2 | 🚧 待做 | SP500 vs GDP 四分法相关性计算（复现69.04%胜率） |

---

## 当前宏观信号快照（2026-06-15）

| 指标 | 数值 | 状态 |
|------|------|------|
| 收益率曲线 (2Y-10Y) | +0.40pp | NORMAL（无衰退信号）|
| HY 信用利差 | 278bp | 正常（< 400bp 阈值）|
| VIX | 19.4 | 平稳 |
| 实际利率 | 2.16% | 政策偏紧 |
| 通胀预期 | 2.31% | 温和 |

**当前综合偏差信号：Long S&P 500**

---

## 目录结构

```
RoboRich-QF/
├── src/data_layer/           # 数据层 MVP（futu-api + yfinance）
│   ├── config.py             # 配置（OpenD地址、Watchlist、宏观指标）
│   ├── db.py                 # SQLite schema + upsert
│   ├── futu_client.py        # Futu OpenD 连接封装
│   ├── collectors/
│   │   ├── kline.py          # 日K线采集（250天）
│   │   ├── snapshot.py       # 市场快照采集
│   │   └── macro.py          # 宏观数据（VIX/TNX/DX-Y）
│   └── scheduler.py          # APScheduler 定时任务
├── scripts/
│   ├── run_daily.py          # 手动触发全量采集
│   └── check_db.py           # 数据库状态检查
├── fetchers/
│   └── fred.py               # FRED API 封装（GDP/利率/利差等20+指标）
├── macro-dashboard/
│   ├── fetchers/
│   │   └── macro_fetch.py    # M1 信号引擎主脚本
│   └── m0_verify.py          # M0 GDPC1 验证
├── gdp_verify.py             # M0 验证脚本
├── config.yaml.example       # 配置模板（复制为 config.yaml 填入 API key）
├── requirements.txt          # Python 依赖
└── README.md
```

---

## 快速开始

### 数据层（futu + yfinance）

```bash
pip install -r requirements.txt
# 启动 Futu OpenD，确保监听 127.0.0.1:11111
python scripts/run_daily.py   # 手动全量采集
python scripts/check_db.py    # 查看数据库状态
python -m src.data_layer.scheduler  # 定时调度（每天17:00 HKT）
```

### 宏观信号引擎（FRED API）

```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 FRED API key
# 申请：https://fred.stlouisfed.org/docs/api/api_key.html

python macro-dashboard/fetchers/macro_fetch.py  # 拉取全量指标 + 输出信号
python gdp_verify.py                            # M0 GDP 验证
```

---

## 数据表

| 表名 | 说明 |
|------|------|
| kline_daily | 日K线（OHLCV） |
| daily_snapshot | 实时快照（价格/PE/PB） |
| macro_data | 宏观指标（VIX/美债/美元） |
| observations | FRED 原始时序数据 |
| derived | 派生信号（曲线形态/利差状态等） |

---

## 技术栈

- Python 3（标准库为主，无重依赖）
- futu-api + APScheduler（行情采集）
- yfinance（美股宏观）
- FRED API（GDP/利率/利差等官方数据）
- SQLite（本地存储）

## Watchlist

- 美股：NVDA, GOOG, AAPL, TSLA, SPY, QQQ
- 港股：00700, 09988, 03690
- 宏观：^VIX, ^TNX, DX-Y.NYB
