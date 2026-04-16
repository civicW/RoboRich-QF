#!/usr/bin/env python3
"""检查数据库状态：各表行数 + 最新 kline 数据。"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_layer.config import DB_PATH


def check_db():
    if not os.path.exists(DB_PATH):
        print(f"[Check] 数据库不存在: {DB_PATH}")
        print("[Check] 请先运行 python scripts/run_daily.py")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print("=" * 60)

    # 各表行数
    for table in ["kline_daily", "daily_snapshot", "macro_data"]:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"\n[{table}] 共 {count} 条记录")
        except Exception as e:
            print(f"\n[{table}] 查询失败: {e}")

    # 最新 kline 数据
    print("\n" + "-" * 60)
    print("最新 kline_daily 数据（每只股票最新一条）:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT code, date, open, high, low, close, volume
            FROM kline_daily
            WHERE id IN (
                SELECT MAX(id) FROM kline_daily GROUP BY code
            )
            ORDER BY code
        """)
        rows = cursor.fetchall()
        if rows:
            print(f"{'代码':<12} {'日期':<12} {'开':<10} {'高':<10} {'低':<10} {'收':<10} {'成交量'}")
            for row in rows:
                print(f"{row[0]:<12} {row[1]:<12} {row[2]:<10.2f} {row[3]:<10.2f} {row[4]:<10.2f} {row[5]:<10.2f} {row[6]}")
        else:
            print("（暂无数据）")
    except Exception as e:
        print(f"查询失败: {e}")

    # 最新 macro 数据
    print("\n" + "-" * 60)
    print("最新 macro_data 数据:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT symbol, date, value
            FROM macro_data
            WHERE id IN (
                SELECT MAX(id) FROM macro_data GROUP BY symbol
            )
            ORDER BY symbol
        """)
        rows = cursor.fetchall()
        if rows:
            print(f"{'指标':<15} {'日期':<12} {'值'}")
            for row in rows:
                print(f"{row[0]:<15} {row[1]:<12} {row[2]:.4f}")
        else:
            print("（暂无数据）")
    except Exception as e:
        print(f"查询失败: {e}")

    conn.close()


if __name__ == "__main__":
    check_db()
