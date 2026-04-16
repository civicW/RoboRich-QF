# RoboRich - 量化投资数据层

## 技术栈

- Python 3 + futu-api + SQLite + yfinance
- APScheduler 定时采集

## 前置条件

1. 安装依赖：`pip install -r requirements.txt`
2. 启动 Futu OpenD，确保监听 `127.0.0.1:11111`

## 快速开始

```bash
# 手动执行一次全量采集（K线 + 快照 + 宏观）
python scripts/run_daily.py

# 查看数据库状态
python scripts/check_db.py

# 启动定时调度（每天 17:00 HKT 自动采集）
python -m src.data_layer.scheduler
```

## 目录结构

```
data/               SQLite 数据库存放目录
src/data_layer/
  config.py         配置（OpenD地址、Watchlist、宏观指标）
  db.py             数据库初始化 + upsert 函数
  futu_client.py    Futu OpenD 连接封装
  collectors/
    kline.py        日K线采集（250天）
    snapshot.py     市场快照采集
    macro.py        宏观数据采集（VIX/TNX/DX-Y）
  scheduler.py      APScheduler 定时任务
scripts/
  run_daily.py      手动触发全量采集
  check_db.py       数据库状态检查
```

## 数据表

| 表名 | 说明 |
|------|------|
| kline_daily | 日K线（OHLCV） |
| daily_snapshot | 实时快照（价格/PE/PB） |
| macro_data | 宏观指标（VIX/美债/美元） |

## Watchlist

- 美股：NVDA, GOOG, AAPL, TSLA, SPY, QQQ
- 港股：00700, 09988, 03690
- 宏观：^VIX, ^TNX, DX-Y.NYB
