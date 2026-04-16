"""实时快照采集：通过 Futu OpenD 批量拉取市场快照。"""

from datetime import datetime
from typing import List, Optional
from futu import RET_OK

from ..futu_client import get_quote_ctx
from ..db import upsert_snapshot
from ..config import WATCHLIST_ALL


def collect_snapshot(code_list: Optional[List[str]] = None):
    code_list = code_list or WATCHLIST_ALL
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        with get_quote_ctx() as ctx:
            ret, data = ctx.get_market_snapshot(code_list)
            if ret != RET_OK:
                print(f"[Snapshot] 批量拉取失败: {data}")
                return

            count = 0
            for _, row in data.iterrows():
                code = row["code"]
                market = code.split(".")[0]
                try:
                    upsert_snapshot(
                        code=code,
                        market=market,
                        snapshot_date=today,
                        last_price=float(row.get("last_price", 0)),
                        change_rate=float(row.get("price_spread", 0)),
                        volume=int(row.get("volume", 0)),
                        turnover=float(row.get("turnover", 0)),
                        pe_ratio=float(row.get("pe_ttm_ratio", 0)),
                        pb_ratio=float(row.get("pb_ratio", 0)),
                    )
                    count += 1
                except Exception as e:
                    print(f"[Snapshot] {code} 写入异常: {e}")

            print(f"[Snapshot] 写入 {count} 条快照数据")
    except Exception as e:
        print(f"[Snapshot] Futu 连接失败，跳过快照采集: {e}")
