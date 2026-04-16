"""APScheduler 定时任务：每天 17:00 HKT 触发全量采集。"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .db import init_db
from .collectors.kline import collect_kline
from .collectors.snapshot import collect_snapshot
from .collectors.macro import collect_macro


def run_daily():
    """全量采集：K线 + 快照 + 宏观。"""
    print("=" * 50)
    print("[Scheduler] 开始全量采集")
    print("=" * 50)

    init_db()

    print("\n--- 1/3 K线日线采集 ---")
    collect_kline()

    print("\n--- 2/3 市场快照采集 ---")
    collect_snapshot()

    print("\n--- 3/3 宏观数据采集 ---")
    collect_macro()

    print("\n" + "=" * 50)
    print("[Scheduler] 全量采集完成")
    print("=" * 50)


def start_scheduler():
    """启动定时调度器，每天 17:00 HKT 执行。"""
    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=17, minute=0, timezone="Asia/Hong_Kong")
    scheduler.add_job(run_daily, trigger, id="daily_collect", name="每日全量采集")

    print("[Scheduler] 定时任务已启动，每天 17:00 HKT 执行全量采集")
    print("[Scheduler] 按 Ctrl+C 退出")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[Scheduler] 已停止")


if __name__ == "__main__":
    start_scheduler()
