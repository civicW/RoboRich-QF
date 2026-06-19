"""
FRED API 通用拉取器
支持任意 series_id，返回 pandas DataFrame
"""

import requests
import pandas as pd
import yaml
import time
from pathlib import Path


def load_config():
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def fetch_series(series_id: str, limit: int = 100, sort_order: str = "desc") -> pd.DataFrame:
    """
    从 FRED 拉取指定系列数据。
    返回 DataFrame: columns = [date, value]，按日期升序排列。
    """
    cfg = load_config()
    api_key = cfg["fred"]["api_key"]
    base_url = cfg["fred"]["base_url"]

    url = f"{base_url}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "limit": limit,
        "sort_order": sort_order,
    }

    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

    obs = data.get("observations", [])
    df = pd.DataFrame(obs)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_series_info(series_id: str) -> dict:
    """获取 series 元数据（名称、单位、频率等）"""
    cfg = load_config()
    api_key = cfg["fred"]["api_key"]
    base_url = cfg["fred"]["base_url"]

    url = f"{base_url}/series"
    params = {"series_id": series_id, "api_key": api_key, "file_type": "json"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("seriess", [{}])[0]
