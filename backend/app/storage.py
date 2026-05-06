"""
=====  数据持久层（SQLite）  =====

负责所有数据库操作，包括：
1. 数据库初始化（建表）
2. 告警（alerts）的 CRUD
3. 运行记录（runs）的 CRUD
4. 执行步骤（steps）的 CRUD

数据库表结构关系：
  alerts (1) ──── (N) runs (1) ──── (N) steps

每条 run 对应处理一条 alert，
每条 run 包含多个 step（威胁情报→风险评估→防火墙操作）。
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .settings import settings


def _utc_now() -> str:
    """获取当前 UTC 时间的 ISO 8601 格式字符串"""
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> Path:
    """获取数据库文件路径（相对于项目根目录）"""
    return settings.project_root / settings.database_path


def _connect() -> sqlite3.Connection:
    """
    建立数据库连接。

    自动创建数据库文件所在目录，并设置 row_factory 为 sqlite3.Row，
    使得查询结果可以像字典一样通过列名访问。
    """
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    初始化数据库表结构。

    创建三个核心表：
    1. alerts（告警表）：存储安全传感器上报的原始告警
    2. runs（运行表）：存储每次剧本执行的记录
    3. steps（步骤表）：存储每次执行的详细步骤日志
    """
    conn = _connect()
    cursor = conn.cursor()

    # ---- 告警表 ----
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,    -- 自增主键
            ip TEXT NOT NULL,                         -- 源 IP 地址
            source TEXT NOT NULL,                     -- 告警来源（传感器名称）
            description TEXT NOT NULL,                -- 告警描述
            observed_at TEXT NOT NULL,                -- 观测时间
            tags TEXT NOT NULL,                       -- 标签列表（JSON 序列化）
            raw_payload TEXT NOT NULL                 -- 原始告警数据（JSON 格式）
        )
        """
    )

    # ---- 运行记录表 ----
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,    -- 自增主键
            alert_id INTEGER NOT NULL,                -- 关联的告警 ID
            status TEXT NOT NULL,                     -- 运行状态: queued/running/completed/failed
            started_at TEXT,                          -- 开始执行时间
            finished_at TEXT,                         -- 完成时间
            risk_score INTEGER,                       -- 最终风险评分 (0-100)
            decision TEXT,                            -- 最终决策（JSON 格式）
            FOREIGN KEY(alert_id) REFERENCES alerts(id)
        )
        """
    )

    # ---- 执行步骤表 ----
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,    -- 自增主键
            run_id INTEGER NOT NULL,                  -- 关联的运行记录 ID
            name TEXT NOT NULL,                       -- 步骤名称
            status TEXT NOT NULL,                     -- 步骤状态: running/completed/skipped/failed
            started_at TEXT,                          -- 步骤开始时间
            finished_at TEXT,                         -- 步骤完成时间
            detail TEXT,                              -- 步骤执行详情（JSON 格式）
            FOREIGN KEY(run_id) REFERENCES runs(id)
        )
        """
    )

    conn.commit()
    conn.close()


# ==================== 告警（Alerts）操作 ====================


def create_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建一条新告警。

    流程：
    1. 补全默认字段（如 observed_at、tags）
    2. 将完整 payload 序列化为 JSON 存储
    3. 插入数据库并返回完整记录

    Args:
        alert: 告警数据字典

    Returns:
        包含新告警 ID 的完整告警记录
    """
    observed_at = alert.get("observed_at") or _utc_now()
    tags = alert.get("tags") or []
    raw_payload = json.dumps(alert, ensure_ascii=True)
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO alerts (ip, source, description, observed_at, tags, raw_payload)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            alert.get("ip"),
            alert.get("source", "local"),
            alert.get("description", ""),
            observed_at,
            json.dumps(tags, ensure_ascii=True),
            raw_payload,
        ),
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return get_alert(alert_id)


def list_alerts() -> List[Dict[str, Any]]:
    """获取所有告警列表，按 ID 降序排列（最新的在前）"""
    conn = _connect()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    conn.close()
    return [_decode_alert(dict(row)) for row in rows]


def get_alert(alert_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取单条告警记录"""
    conn = _connect()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    conn.close()
    return _decode_alert(dict(row)) if row else None


# ==================== 运行记录（Runs）操作 ====================


def create_run(alert_id: int, status: str = "queued") -> Dict[str, Any]:
    """
    创建新的运行记录。

    当用户点击"Run Playbook"时调用，将告警加入执行队列。

    Args:
        alert_id: 要处理的告警 ID
        status: 初始状态，默认为 "queued"（排队中）
    """
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO runs (alert_id, status, started_at, finished_at, risk_score, decision)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (alert_id, status, None, None, None, None),
    )
    conn.commit()
    run_id = cursor.lastrowid
    conn.close()
    return get_run(run_id)


def update_run(
    run_id: int,
    status: Optional[str] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    risk_score: Optional[int] = None,
    decision: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    更新运行记录状态。

    剧本执行过程中会多次调用此函数来更新进度和结果。

    Args:
        run_id: 运行记录 ID
        status: 新状态（queued/running/completed/failed）
        started_at: 开始时间
        finished_at: 完成时间
        risk_score: 风险评分
        decision: 最终决策（字典或列表会被 JSON 序列化）
    """
    run = get_run(run_id)
    if not run:
        raise ValueError("Run not found")
    serialized_decision = decision
    if isinstance(decision, (dict, list)):
        serialized_decision = json.dumps(decision, ensure_ascii=True)
    updated = {
        "status": status or run["status"],
        "started_at": started_at or run["started_at"],
        "finished_at": finished_at or run["finished_at"],
        "risk_score": risk_score if risk_score is not None else run["risk_score"],
        "decision": serialized_decision if serialized_decision is not None else run["decision"],
    }
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE runs
        SET status = ?, started_at = ?, finished_at = ?, risk_score = ?, decision = ?
        WHERE id = ?
        """,
        (
            updated["status"],
            updated["started_at"],
            updated["finished_at"],
            updated["risk_score"],
            updated["decision"],
            run_id,
        ),
    )
    conn.commit()
    conn.close()
    return get_run(run_id)


def get_run(run_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取单条运行记录"""
    conn = _connect()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    return _decode_run(dict(row)) if row else None


def list_runs() -> List[Dict[str, Any]]:
    """获取所有运行记录，按 ID 降序排列"""
    conn = _connect()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM runs ORDER BY id DESC").fetchall()
    conn.close()
    return [_decode_run(dict(row)) for row in rows]


# ==================== 执行步骤（Steps）操作 ====================


def create_step(run_id: int, name: str, status: str) -> Dict[str, Any]:
    """
    创建新的执行步骤记录。

    每执行一个 playbook 步骤（如威胁情报查询），就会创建一条步骤记录。

    Args:
        run_id: 所属的运行记录 ID
        name: 步骤名称（如 "threat_intel", "risk_assessment", "firewall_block"）
        status: 初始状态（如 "running"）
    """
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO steps (run_id, name, status, started_at, finished_at, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (run_id, name, status, _utc_now(), None, None),
    )
    conn.commit()
    step_id = cursor.lastrowid
    conn.close()
    return get_step(step_id)


def update_step(
    step_id: int,
    status: Optional[str] = None,
    finished_at: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    更新步骤状态和详细信息。

    Args:
        step_id: 步骤记录 ID
        status: 完成状态（completed/skipped/failed）
        finished_at: 完成时间
        detail: 执行详情（如查询结果、封禁结果等）
    """
    step = get_step(step_id)
    if not step:
        raise ValueError("Step not found")
    updated = {
        "status": status or step["status"],
        "finished_at": finished_at or step["finished_at"],
        "detail": json.dumps(detail, ensure_ascii=True)
        if detail is not None
        else step["detail"],
    }
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE steps
        SET status = ?, finished_at = ?, detail = ?
        WHERE id = ?
        """,
        (updated["status"], updated["finished_at"], updated["detail"], step_id),
    )
    conn.commit()
    conn.close()
    return get_step(step_id)


def get_step(step_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取单条步骤记录"""
    conn = _connect()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM steps WHERE id = ?", (step_id,)).fetchone()
    conn.close()
    return _decode_step(dict(row)) if row else None


def list_steps(run_id: int) -> List[Dict[str, Any]]:
    """
    获取指定运行记录的所有步骤。

    Args:
        run_id: 运行记录 ID

    Returns:
        步骤列表，按执行顺序排列
    """
    conn = _connect()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM steps WHERE run_id = ? ORDER BY id ASC", (run_id,)
    ).fetchall()
    conn.close()
    return [_decode_step(dict(row)) for row in rows]


# ==================== JSON 反序列化辅助函数 ====================


def _decode_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    将数据库中存储的 JSON 格式 tags 字段反序列化为 Python 列表。

    SQLite 不支持原生数组类型，所以 tags 以 JSON 字符串或分号分隔的
    字符串形式存储，读取时需要转换回来。
    """
    tags = alert.get("tags")
    if isinstance(tags, str):
        try:
            alert["tags"] = json.loads(tags)
        except json.JSONDecodeError:
            # 兼容旧数据格式：分号分隔的标签
            alert["tags"] = [item.strip() for item in tags.split(";") if item.strip()]
    return alert


def _decode_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """将步骤的 detail 字段从 JSON 字符串反序列化为 Python 对象"""
    detail = step.get("detail")
    if isinstance(detail, str):
        try:
            step["detail"] = json.loads(detail)
        except json.JSONDecodeError:
            step["detail"] = detail
    return step


def _decode_run(run: Dict[str, Any]) -> Dict[str, Any]:
    """将运行记录的 decision 字段从 JSON 字符串反序列化为 Python 对象"""
    decision = run.get("decision")
    if isinstance(decision, str) and decision:
        try:
            run["decision"] = json.loads(decision)
        except json.JSONDecodeError:
            run["decision"] = decision
    return run