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

from .routes import alerts, auth, chains, debates, feedback, graph, knowledge, mcp_routes, models, runs, simulator, sources
from .storage import init_db
from .logging_config import setup_logging
from .ingestion.manager import start_configured_sources, stop_all_sources

from contextlib import asynccontextmanager
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时启动告警源、知识图谱和RAG知识库，关闭时停止。"""
    start_configured_sources()
    # 初始化知识图谱
    try:
        from .graph.knowledge_graph import graph
        from .graph.populator import populate_from_database, populate_techniques
        populate_techniques(graph)
        populate_from_database(graph)
    except Exception:
        pass  # graph 模块不可用时静默跳过
    # 初始化 RAG 知识库
    try:
        from .ai.attack_data_loader import load_attack_data
        from .ai.incident_corpus import load_incident_corpus
        load_attack_data()
        load_incident_corpus()
    except Exception:
        pass  # RAG 模块不可用时静默跳过
    # 注册 MCP 工具
    try:
        from .integrations.mcp_tools import register_all_tools
        register_all_tools()
    except Exception:
        pass  # MCP 模块不可用时静默跳过
    yield
    stop_all_sources()


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
    app = FastAPI(title="Agent-Based SOAR Prototype", version="0.1.0", lifespan=lifespan)
    setup_logging()

    # ---- CORS 配置 ----
    # 生产环境应通过环境变量 CORS_ORIGINS 指定允许的来源
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000")
    allowed_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- 初始化数据库 ----
    init_db()

    # ---- 注册 API 路由 ----
    app.include_router(alerts.router)     # 告警相关接口（CRUD）
    app.include_router(runs.router)       # 剧本执行相关接口
    app.include_router(auth.router)       # 认证接口
    app.include_router(knowledge.router)  # 知识库接口
    app.include_router(sources.router)    # 告警源管理接口
    app.include_router(graph.router)      # 知识图谱接口
    app.include_router(simulator.router)  # 攻击模拟器接口
    app.include_router(models.router)     # 模型提供商管理接口
    app.include_router(debates.router)    # 多 Agent 辩论接口
    app.include_router(feedback.router)   # 反馈与记忆接口
    app.include_router(chains.router)     # 攻击链接口
    app.include_router(mcp_routes.router) # MCP 工具协议接口

    # ---- 健康检查 ----
    # 必须在静态文件挂载之前注册，否则会被 "/" 静态挂载拦截
    @app.get("/health")
    def health() -> dict:
        """健康检查端点，用于监控系统运行状态"""
        return {"status": "ok"}

    # ---- 挂载前端静态文件 ----
    # Vite 构建输出目录
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dir.exists():
        # 将静态文件挂载到根路径，支持 HTML5 History 模式
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


# 创建全局应用实例，供 uvicorn 导入使用
app = create_app()

if __name__ == "__main__":
    """直接运行时启动开发服务器"""
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)