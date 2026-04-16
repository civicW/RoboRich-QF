#!/usr/bin/env python3
"""手动触发一次全量采集（K线 + 快照 + 宏观）。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_layer.scheduler import run_daily

if __name__ == "__main__":
    run_daily()
