"""
=====  告警数据导入工具  =====

用于将 JSON/CSV 格式的样本告警数据导入到 SOAR 系统数据库中。

用法：
    # 导入 JSON 格式告警
    python backend/import_alerts.py data/alerts.json

    # 导入 CSV 格式告警
    python backend/import_alerts.py data/alerts.csv

数据格式要求（JSON）：
    [
        {
            "ip": "185.199.109.153",
            "source": "sensor-alpha",
            "description": "Repeated login failures from new ASN",
            "observed_at": "2026-05-07T08:12:40Z",
            "tags": ["auth", "bruteforce"]
        },
        ...
    ]

数据格式要求（CSV）：
    ip,source,description,observed_at,tags
    185.199.109.153,sensor-alpha,Repeated login failures...,2026-05-07T08:12:40Z,"auth;bruteforce"
"""

import csv
import json
import sys
from typing import Dict, Any, Iterable

from app.storage import create_alert, init_db


def _normalize_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    标准化告警数据格式。

    处理导入数据中的常见问题：
    1. tags 字段可能是字符串或列表，统一转为列表
    2. 补全缺失的必填字段默认值

    Args:
        payload: 原始告警数据

    Returns:
        标准化后的告警字典
    """
    tags = payload.get("tags", [])
    if isinstance(tags, str):
        # 兼容 CSV 格式：分号或逗号分隔的标签字符串 → 列表
        tags = [item.strip() for item in tags.replace(",", ";").split(";") if item.strip()]
    return {
        "ip": payload.get("ip", "0.0.0.0"),
        "source": payload.get("source", "local"),
        "description": payload.get("description", ""),
        "observed_at": payload.get("observed_at"),
        "tags": tags,
    }


def _read_json(path: str) -> Iterable[Dict[str, Any]]:
    """读取 JSON 格式的告警文件"""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    # 兼容单个对象和对象数组两种格式
    if isinstance(data, list):
        return data
    return [data]


def _read_csv(path: str) -> Iterable[Dict[str, Any]]:
    """读取 CSV 格式的告警文件"""
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def main() -> None:
    """主入口：解析命令行参数并执行数据导入"""
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python backend/import_alerts.py data/alerts.json")

    path = sys.argv[1]

    # 根据文件扩展名选择解析方式
    if path.lower().endswith(".csv"):
        rows = _read_csv(path)
    else:
        rows = _read_json(path)

    count = len(rows)

    # 初始化数据库并导入数据
    init_db()
    for row in rows:
        record = _normalize_alert(row)
        create_alert(record)

    print(f"Imported {count} alerts")


if __name__ == "__main__":
    main()