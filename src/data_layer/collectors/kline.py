"""K线日线采集：通过 Futu OpenD 拉取最近 250 个交易日的日K线。"""

from datetime import datetime, timedelta
from typing import List, Optional
from futu import RET_OK, KLType

from ..futu_client import get_quote_ctx
from ..db import upsert_kline
from ..config import WATCHLIST_ALL


def collect_kline(code_list: Optional[List[str]] = None):
    code_list = code_list or WATCHLIST_ALL
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    try:
        with get_quote_ctx() as ctx:
            for code in code_list:
                market = code.split(".")[0]
                try:
                    ret, data, _ = ctx.request_history_kline(
                        code, start=start, end=end, ktype=KLType.K_DAY, max_count=250
                    )
                    if ret != RET_OK:
                        print(f"[Kline] {code} 拉取失败: {data}")
                        continue

                    count = 0
                    for _, row in data.iterrows():
                        upsert_kline(
                            code=code,
                            market=market,
                            date=row["time_key"][:10],
                            open_=row["open"],
                            high=row["high"],
                            low=row["low"],
                            close=row["close"],
                            volume=int(row["volume"]),
                            turnover=float(row["turnover"]),
                        )
                        count += 1
                    print(f"[Kline] {code} 写入 {count} 条日K线")
                except Exception as e:
                    print(f"[Kline] {code} 采集异常: {e}")
    except Exception as e:
        print(f"[Kline] Futu 连接失败，跳过K线采集: {e}")
