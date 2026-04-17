#!/usr/bin/env python3
"""
飞书周报推送脚本
通过 OpenClaw feishu message tool 发送周报到指定群
用法：python scripts/push_weekly_report.py
"""
import sys
import os
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.report import generate_report

FEISHU_CHAT_ID = "oc_c6cb25ea8951dcfc2149bb9857b548f3"


def push_to_feishu(report_text: str):
    """通过 OpenClaw CLI 发送飞书消息"""
    payload = {
        "action": "send",
        "channel": "feishu",
        "target": f"chat:{FEISHU_CHAT_ID}",
        "message": report_text,
    }
    result = subprocess.run(
        ["openclaw", "message", json.dumps(payload)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[Push] 发送失败: {result.stderr}")
    else:
        print(f"[Push] 发送成功")


if __name__ == "__main__":
    print("[Weekly Push] 生成周报...")
    report = generate_report()
    print(report)
    print("[Weekly Push] 推送到飞书群...")
    push_to_feishu(report)
    print("[Weekly Push] 完成")
