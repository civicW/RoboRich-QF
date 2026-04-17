#!/usr/bin/env python3
"""
每周触发入口 — 生成并推送周报
用法：python scripts/run_weekly.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.report import print_report

if __name__ == "__main__":
    print("=" * 60)
    print("[Weekly] 开始生成周报...")
    print("=" * 60)
    report = print_report()
    print("=" * 60)
    print("[Weekly] 完成")
