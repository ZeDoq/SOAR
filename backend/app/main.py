"""
=====  Agent-Based SOAR 系统入口  =====

FastAPI 应用主入口。负责：
1. 创建 FastAPI 应用实例
2. 注册所有路由（alerts、runs）
3. 挂载前端静态文件
4. 初始化 SQLite 数据库

系统架构概览：
  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
  │  前端页面    │────▶│  FastAPI     │────▶│  SQLite 数据库 │
  │ (HTML+JS)   │◀────│  REST API    │◀────│  (持久化)     │
  └─────────────┘     └──────┬───────┘     └──────────────┘
                             │
                    ┌────────▼────────┐
                    │   Agent 编排器    │
                    │  (Orchestrator)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │ 威胁情报  │  │ 风险评估  │  │ 防火墙封禁│
       │ Threat   │  │ Risk     │  │ Firewall │
       │ Intel    │  │ Assessor │  │ Block    │
       └──────────┘  └──────────┘  └──────────┘
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import alerts, runs
from .storage import init_db


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例。

    执行流程：
    1. 实例化 FastAPI，设置标题和版本号
    2. 添加 CORS 中间件，允许跨域请求（开发环境）
    3. 初始化 SQLite 数据库表结构
    4. 注册 alerts（告警）和 runs（运行记录）路由
    5. 挂载前端静态文件目录
    6. 添加 /health 健康检查端点
    """
    app = FastAPI(title="Agent-Based SOAR Prototype", version="0.1.0")

    # ---- CORS 配置 ----
    # 允许所有来源的跨域请求，方便前后端分离开发
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- 初始化数据库 ----
    init_db()

    # ---- 注册 API 路由 ----
    app.include_router(alerts.router)  # 告警相关接口（CRUD）
    app.include_router(runs.router)    # 剧本执行相关接口

    # ---- 挂载前端静态文件 ----
    # 从当前文件位置向上两级找到 frontend 目录
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.exists():
        # 将静态文件挂载到根路径，支持 HTML5 History 模式
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    @app.get("/health")
    def health() -> dict:
        """健康检查端点，用于监控系统运行状态"""
        return {"status": "ok"}

    return app


# 创建全局应用实例，供 uvicorn 导入使用
app = create_app()

if __name__ == "__main__":
    """直接运行时启动开发服务器"""
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)