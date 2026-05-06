# Agent-Based SOAR Prototype（基于 Agent 架构的自动化安全运营系统）

## 项目概述

本项目是一个**基于 Agent 架构的自动化安全运营（SOAR）原型系统**，模拟了安全分析师处理安全告警的完整自动化流程。系统采用 **Agent 框架**思想，通过一个中央编排器（Orchestrator Agent）协调多个安全工具，按照预定义的 Playbook 自动执行威胁响应。

### 核心流程

```
告警输入 → 威胁情报查询 → 风险评估 → 联动防火墙封禁/监控
```

当安全传感器检测到可疑 IP 活动时，系统自动执行：
1. **威胁情报查询** — 查询 IP 的信誉信息（模拟 VirusTotal/OTX）
2. **风险评估** — 结合情报和告警上下文计算风险分数
3. **决策执行** — 高风险自动封禁，低风险持续监控

## 架构设计

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        前端页面 (HTML+CSS+JS)                     │
│                SOAR Control Room Dashboard                       │
└──────────────────────────┬───────────────────────────────────────┘
                           │ REST API (JSON)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Web 服务层                            │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │ /alerts 路由 │  │  /runs 路由     │  │  后台任务调度器       │  │
│  │ (告警 CRUD)  │  │ (剧本执行管理)   │  │  BackgroundTasks     │  │
│  └──────┬──────┘  └───────┬────────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼──────────────────────┼──────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Agent 编排器（核心）                         │
│                  agents/orchestrator.py                          │
│                                                                  │
│   execute_playbook(run_id) — 安全响应剧本执行引擎                  │
│                                                                  │
│   状态机: queued → running → completed/failed                    │
└───────┬──────────────────────────┬───────────────────────────────┘
        │                          │
        ▼                          ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────┐
│ 威胁情报服务   │   │ 风险评估服务   │   │  防火墙联动服务    │
│ Threat Intel  │──▶│ Risk Assessor │──▶│  Firewall Block   │
│ (模拟)        │   │ (模拟)        │   │  (模拟)           │
└───────────────┘   └───────────────┘   └───────────────────┘
                                                    │
                                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                      SQLite 持久化层                              │
│  表结构: alerts (1) ── N ── runs (1) ── N ── steps              │
└──────────────────────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| **应用入口** | `backend/app/main.py` | FastAPI 应用创建、路由注册、静态文件挂载 |
| **数据模型** | `backend/app/models.py` | Pydantic 请求/响应模型定义 |
| **系统配置** | `backend/app/settings.py` | 集中配置管理（支持环境变量） |
| **持久化层** | `backend/app/storage.py` | SQLite 数据库 CRUD 操作 |
| **Agent 编排器** | `backend/app/agents/orchestrator.py` | **核心** - 自动化剧本执行引擎 |
| **威胁情报** | `backend/app/integrations/threat_intel.py` | IP 信誉查询服务（模拟） |
| **风险评估** | `backend/app/integrations/risk_assessor.py` | 风险评分计算服务（模拟） |
| **防火墙联动** | `backend/app/integrations/firewall.py` | IP 封禁服务（模拟） |
| **告警路由** | `backend/app/routes/alerts.py` | 告警 API 接口 |
| **执行路由** | `backend/app/routes/runs.py` | 剧本执行 API 接口 |
| **启动脚本** | `backend/run.py` | 开发服务器启动入口 |
| **数据导入** | `backend/import_alerts.py` | 样本数据导入工具 |
| **前端页面** | `frontend/` | HTML/CSS/JS 控制台界面 |

### 核心设计思路

#### 1. Agent 架构
Agent 不是单一的 AI 模型，而是一个**任务编排器**。它协调多个安全工具/服务，按照预定义的 Playbook 步骤执行自动化响应。这种设计模式的优势：
- **模块化**：每个安全工具（威胁情报、风险评估、防火墙）都是独立的模块
- **可扩展**：可以轻松添加新的安全工具或步骤
- **可观测**：每一步的执行状态和结果都被记录到数据库

#### 2. Playbook 模式
Playbook（安全剧本）是 SOAR 系统的核心概念，定义了安全事件的处理流程。本系统的 Playbook 包含三个阶段：
```
Phase 1: 威胁情报查询 — 收集上下文信息
Phase 2: 风险评估     — 基于情报做出判断
Phase 3: 决策执行     — 根据结果采取行动
```

#### 3. 异步执行
使用 FastAPI 的 BackgroundTasks 实现异步执行，用户触发剧本后立即获得响应，实际处理在后台进行。前端通过轮询 API 获取实时进度。

#### 4. 状态机管理
```
queued (排队中) → running (执行中) → completed (完成)
                                    → failed (失败)
```
每个状态变更都记录时间戳，形成完整的审计日志。

## 快速开始

### 环境要求
- Python 3.8+
- pip（Python 包管理器）

### 安装步骤

```bash
# 1. 进入项目目录
cd agent_base_SOAR

# 2. 创建虚拟环境（推荐）
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动后端服务
python backend/run.py
```

### 导入样本数据

打开另一个终端窗口：

```bash
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 导入样本告警数据
python backend/import_alerts.py data/alerts.json
```

### 访问前端

在浏览器中打开 `frontend/index.html` 或访问 `http://127.0.0.1:8000`（后端会自动挂载前端）。

### 使用流程

1. 点击 "Import Sample Alerts" 从终端导入样本数据
2. 点击 "Refresh" 按钮加载告警列表
3. 选择一条告警，点击 "Run Playbook" 触发剧本执行
4. 在 "Playbook Runs" 面板中点击运行记录，查看执行详情
5. 观察步骤日志：威胁情报查询 → 风险评估 → 防火墙操作/监控

## API 参考

### 告警管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/alerts` | 创建新告警 |
| GET | `/alerts` | 获取所有告警 |
| GET | `/alerts/{id}` | 获取告警详情 |

### 剧本执行

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/runs` | 触发剧本执行 |
| GET | `/runs` | 获取所有运行记录 |
| GET | `/runs/{id}` | 获取运行详情（含步骤日志） |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |

## 配置说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `SOAR_DB_PATH` | `data/soar.db` | 数据库文件路径（相对于项目根目录） |
| `RISK_BLOCK_THRESHOLD` | `70` | 风险评分阈值（0-100），超过此值自动封禁 |
| `SIMULATED_LATENCY_MS` | `120` | 模拟外部 API 调用延迟（毫秒） |

### 配置示例

```bash
# Windows PowerShell
$env:SOAR_DB_PATH = "data/custom.db"
$env:RISK_BLOCK_THRESHOLD = "80"
$env:SIMULATED_LATENCY_MS = "200"

# Linux/Mac
export SOAR_DB_PATH="data/custom.db"
export RISK_BLOCK_THRESHOLD="80"
export SIMULATED_LATENCY_MS="200"
```

## 扩展指南

### 添加新的威胁情报源

在 `backend/app/integrations/` 下创建新模块，例如 `virus_total.py`：

```python
def lookup(ip: str, latency_ms: int) -> dict:
    # 调用 VirusTotal API 的实现
    return {"source": "VirusTotal", "reputation": ...}
```

### 添加新的 Playbook 步骤

在 `backend/app/agents/orchestrator.py` 的 `execute_playbook()` 函数中添加新步骤：

```python
# 新步骤示例：生成 PDF 报告
step = storage.create_step(run_id, "generate_report", "running")
report = generate_report(alert, intel, risk)
storage.update_step(step["id"], status="completed", detail=report)
```

### 替换为真实 API

将 `threat_intel.py`、`risk_assessor.py`、`firewall.py` 中的模拟逻辑替换为真实 API 调用，移除 `time.sleep()` 即可。

## 许可证

MIT License