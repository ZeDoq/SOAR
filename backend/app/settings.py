"""
=====  系统配置  =====

集中管理所有可配置参数，支持通过环境变量覆盖默认值。
这种设计遵循 12-Factor App 的"配置与代码分离"原则。
"""

import os
from pathlib import Path


class Settings:
    """
    系统配置类。

    使用示例：
        settings = Settings()
        # 可通过环境变量覆盖默认配置：
        # $env:SOAR_DB_PATH = "data/custom.db"        # Windows PowerShell
        # export SOAR_DB_PATH="data/custom.db"         # Linux/Mac
    """

    def __init__(self) -> None:
        # ---- 项目根目录 ----
        # 通过当前文件位置向上推算，确保路径在任何工作目录下都正确
        self.project_root = Path(__file__).resolve().parents[2]

        # ---- 数据库路径 ----
        # 环境变量: SOAR_DB_PATH
        # 默认: data/soar.db
        # 相对于项目根目录
        self.database_path = os.getenv("SOAR_DB_PATH", "data/soar.db")

        # ---- 风险等级阻断阈值 ----
        # 环境变量: RISK_BLOCK_THRESHOLD
        # 默认: 70
        # 取值范围: 0-100
        # 当风险评估分数 >= 此值时，自动触发防火墙封禁动作
        self.risk_block_threshold = int(os.getenv("RISK_BLOCK_THRESHOLD", "70"))

        # ---- 模拟延迟（毫秒） ----
        # 环境变量: SIMULATED_LATENCY_MS
        # 默认: 120
        # 用于模拟真实外部 API 调用的网络延迟
        self.simulated_latency_ms = int(os.getenv("SIMULATED_LATENCY_MS", "120"))


# 全局单例配置实例
# 其他模块通过 from .settings import settings 来使用
settings = Settings()