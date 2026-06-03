# SOAR — Security Orchestration, Automation & Response

> 基于多 Agent 架构的智能安全运营平台，具备 RAG 知识检索、LangGraph 动态编排、多 Agent 辩论、攻击链重建和 MCP 工具治理能力。

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4-42b883?logo=vuedotjs&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-ff6b35?logo=langchain&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-252%20Passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 项目简介

SOAR 是一个全栈智能安全运营自动化平台。当安全传感器检测到可疑活动时，系统通过 **LangGraph 状态机动态编排** 多个 AI Agent 协作完成威胁分析和响应——不同复杂度的告警走不同的处理路径，而非固定流水线。

### 核心创新（6 大模块）

| 模块 | 解决的问题 | 核心技术 |
|------|-----------|---------|
| **RAG 安全知识库** | 12 条硬编码知识无法覆盖真实场景 | ChromaDB 向量检索 + 完整 MITRE ATT&CK 矩阵（200+ 技术） |
| **LangGraph 动态编排** | 固定流水线无法适应不同告警 | 状态机 + 条件分支 + 迭代精炼 + 执行路径追踪 |
| **多 Agent 辩论** | 单一分析视角容易误判 | 威胁猎人 / 怀疑分析师 / 上下文专家三角色结构化辩论 |
| **Agent 记忆** | 每次分析都从零开始 | 情景记忆 + 分析师反馈 + 阈值自适应校准 |
| **攻击链重建** | 离散告警无法关联为攻击链 | 时间序列分析 + ATT&CK 战术阶段映射 + Kill Chain 检测 |
| **MCP 工具治理** | Agent 可能误触危险操作 | 权限矩阵 + 审计日志 + 角色级工具访问控制 |

---

## 系统架构

```
┌───────────────────────────────────────────────────────────────┐
│                   Vue 3 前端 (Vite + Pinia)                    │
│  Dashboard │ Alerts │ Workbench │ Graph │ Simulator │ Settings │
└──────────────────────────┬────────────────────────────────────┘
                           │ REST API (JWT 认证)
┌──────────────────────────▼────────────────────────────────────┐
│                     FastAPI 后端                               │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           LangGraph 动态编排引擎                         │   │
│  │  gather_intel ──→ analyze_threat ──→ execute_response   │   │
│  │       │               ↕                    │            │   │
│  │       └→ synthesize   deep_analysis (循环) ┘            │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌─────────────────┐  ┌─────────────┐  ┌──────────────┐      │
│  │ 多 Agent 辩论    │  │ Agent 记忆   │  │ 攻击链重建   │      │
│  │ 猎人⟷怀疑⟷专家  │  │ 情景+反馈   │  │ 时间+战术    │      │
│  └─────────────────┘  └─────────────┘  └──────────────┘      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  RAG 知识库 (ChromaDB)  │  知识图谱 (networkx)         │   │
│  │  MCP 工具治理           │  Agent 记忆 (SQLite)          │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              安全工具集成层                              │   │
│  │  VirusTotal │ AbuseIPDB │ 防火墙 │ 邮件 │ Slack │ DNS  │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ AI/LLM   │  │  SQLite  │  │  JWT     │                    │
│  │ 多模型   │  │  存储    │  │  认证    │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
└───────────────────────────────────────────────────────────────┘
```

---

## 核心功能

### RAG 安全知识库
- 基于 ChromaDB 的向量语义检索，覆盖完整 MITRE ATT&CK Enterprise 矩阵
- 12 个安全事件案例语料库（暴力破解、DNS 隧道、APT 活动等）
- 混合检索：向量相似度 + 关键词匹配加权融合
- 分析时自动检索相关技术 + 相似历史事件

### LangGraph 动态编排
- 3 种编排模式：**classic**（固定 8 步）/ **adaptive**（模板选择）/ **langgraph**（动态路由）
- 高置信度告警走短路径（3 步快速响应），低置信度走深度路径（含循环迭代）
- 条件路由：根据 AI 分析置信度动态决定下一步
- 执行路径追踪：每条告警记录实际走过的节点序列

### 多 Agent 辩论系统
- **威胁猎人**：激进解读，关注 IOC 和 TTP
- **怀疑分析师**：保守解读，寻找合法解释
- **上下文专家**：中立分析，关注环境因素
- 三轮辩论：独立分析 → 交叉质疑 → 主持人综合裁决
- 共识评分：量化 Agent 间的一致程度

### Agent 记忆与反馈闭环
- 情景记忆：存储每次处理的告警特征、分析结果
- 分析师反馈：确认 / 推翻裁决 + 原因
- 阈值校准：根据误报率自动调整 Playbook 阻断阈值
- 相似事件检索：处理新告警时检索历史相似事件

### 攻击链自动重建
- 按源 IP 聚合告警 → 时间排序 → ATT&CK 战术映射 → 进展验证
- 2 个 APT 模拟场景：横向移动攻击链、供应链攻击链
- 战术阶段评分：验证是否符合 Kill Chain 自然进展
- 时间关联评分：评估告警间的时序紧密度

### MCP 工具协议与治理
- 7 个安全工具注册为 MCP 工具（VT、AbuseIPDB、WHOIS、DNS、防火墙、知识库、知识图谱）
- 权限矩阵：情报 Agent 只能查询，响应 Agent 才能封锁
- 审计日志：记录每次工具调用的调用者、输入、输出、成功/失败

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+（前端构建）
- Git

### 1. 克隆并安装

```bash
git clone https://github.com/ZeDoq/SOAR.git
cd SOAR

# 后端
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
cd ..
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少设置 JWT_SECRET_KEY 为随机字符串
# 生成方法: python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. 开发模式运行

```bash
# 终端 1：后端 API
python backend/run.py

# 终端 2：前端开发服务器
cd frontend && npm run dev
```

浏览器访问 **http://localhost:5173**

### 4. Docker 部署（生产环境）

```bash
cp .env.example .env
# 编辑 .env 填写生产配置
docker compose up -d
```

浏览器访问 **http://localhost:8000**

---

## Playbook 执行流程（LangGraph 模式）

```
告警接入 → gather_intel（情报收集）
              │
              ├─ 高置信度恶意 → synthesize_decision → execute_response
              │
              └─ 不确定 → analyze_threat
                              │
                              ├─ 置信度 ≥ 0.8 → execute_response
                              │
                              └─ 置信度 < 0.5 → deep_analysis（最多 3 轮）
                                                  │
                                                  └─ execute_response
                                                        │
                                                  审计日志 + 报告
```

---

## API 参考

### 认证
```
POST /auth/register    用户注册
POST /auth/login       登录获取 JWT
```

### 核心接口
```
POST /alerts           接入告警（传感器接口，无需认证）
GET  /alerts           告警列表

POST /runs             触发 Playbook（mode: classic|adaptive|langgraph）
GET  /runs             执行记录列表
GET  /runs/{id}        执行详情（含步骤日志）
GET  /runs/langgraph/graph  编排流程图（Mermaid 格式）
```

### 六大创新模块接口
```
# RAG 知识库
GET  /knowledge/search?q=    RAG 语义检索 ATT&CK 知识
GET  /knowledge/rag/status   RAG 引擎状态
POST /knowledge/rag/reload   重新加载知识库

# 多 Agent 辩论
GET  /debates                辩论记录列表
POST /debates/run/{alert_id} 执行多 Agent 辩论

# Agent 记忆
POST /feedback/{run_id}      提交分析师反馈
GET  /feedback/stats         反馈统计
GET  /feedback/memory/stats  记忆统计

# 攻击链
GET  /chains                 所有攻击链
GET  /chains/{ip}            指定 IP 的攻击链

# MCP 工具治理
GET  /mcp/tools              工具注册表
GET  /mcp/governance         权限矩阵
GET  /mcp/audit              审计日志
POST /mcp/call               执行工具（带权限检查）

# 知识图谱
GET  /graph                  图谱数据
GET  /graph/clusters         IP 聚类
GET  /graph/techniques       ATT&CK 技术频率

# 攻击模拟器
GET  /simulator/scenarios    场景列表（8 个场景）
POST /simulator/run/{name}   执行模拟场景
```

---

## 测试

```bash
# 运行全部测试（252 个）
python -m pytest tests/ -v

# 按模块运行
python -m pytest tests/test_rag_engine.py -v           # RAG 知识库（18 个）
python -m pytest tests/test_langgraph_orchestrator.py -v  # LangGraph 编排（14 个）
python -m pytest tests/test_debate.py -v               # 多 Agent 辩论（10 个）
python -m pytest tests/test_memory.py -v               # Agent 记忆（9 个）
python -m pytest tests/test_chain_detector.py -v       # 攻击链重建（12 个）
python -m pytest tests/test_mcp.py -v                  # MCP 治理（25 个）
```

测试覆盖：252 个测试，20 个测试文件，覆盖全部模块。

---

## 项目结构

```
SOAR/
├── backend/
│   ├── app/
│   │   ├── agents/              # Agent 系统
│   │   │   ├── orchestrator.py            # 经典编排器
│   │   │   ├── adaptive_orchestrator.py   # 自适应编排器
│   │   │   ├── langgraph_orchestrator.py  # LangGraph 动态编排
│   │   │   ├── state.py                   # 编排状态定义
│   │   │   ├── nodes/                     # LangGraph 节点
│   │   │   ├── debate/                    # 多 Agent 辩论系统
│   │   │   ├── intelligence_agent.py      # 情报 Agent
│   │   │   ├── analysis_agent.py          # 分析 Agent
│   │   │   └── response_agent.py          # 响应 Agent
│   │   ├── ai/                  # AI 引擎
│   │   │   ├── llm_client.py              # 多模型客户端
│   │   │   ├── analyzer.py                # 威胁分析
│   │   │   ├── rag_engine.py              # RAG 向量检索
│   │   │   ├── knowledge_base.py          # ATT&CK 知识库
│   │   │   ├── attack_data_loader.py      # ATT&CK 数据加载
│   │   │   └── incident_corpus.py         # 安全事件语料
│   │   ├── graph/               # 知识图谱
│   │   │   ├── knowledge_graph.py         # 图引擎
│   │   │   ├── chain_detector.py          # 攻击链检测
│   │   │   └── temporal_reasoning.py      # 时间推理
│   │   ├── memory/              # Agent 记忆
│   │   │   ├── episodic_memory.py         # 情景记忆
│   │   │   └── feedback_loop.py           # 反馈闭环
│   │   ├── mcp/                 # MCP 工具协议
│   │   │   ├── server.py                  # MCP 服务端
│   │   │   ├── tool_registry.py           # 工具注册
│   │   │   ├── governance.py              # 权限治理
│   │   │   └── audit.py                   # 审计日志
│   │   ├── integrations/        # 安全工具集成
│   │   ├── ingestion/           # 告警接入
│   │   ├── routes/              # API 端点（14 个路由）
│   │   ├── simulator/           # 攻击模拟器（8 个场景）
│   │   └── ...
│   └── run.py
├── frontend/                    # Vue 3 + Vite SPA
│   └── src/
│       ├── views/               # 10 个页面
│       ├── components/          # UI 组件
│       ├── stores/              # Pinia 状态管理
│       └── i18n/                # 中英文双语
├── tests/                       # 252 个测试（20 个文件）
├── Dockerfile                   # 多阶段构建
├── docker-compose.yml
├── requirements.txt
└── .env.example                 # 配置模板
```

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端 | FastAPI + Pydantic | REST API + 自动校验 |
| 数据库 | SQLite | 零配置持久化 |
| 向量库 | ChromaDB | RAG 语义检索 |
| 编排 | LangGraph | 状态机动态编排 |
| 认证 | JWT + bcrypt | Token 认证 |
| AI/LLM | OpenAI SDK（多提供商） | 威胁分析 + 报告生成 |
| 图谱 | networkx | 内存知识图谱 |
| 前端 | Vue 3 + Vite + Pinia | 响应式 SPA |
| 可视化 | vis-network + Chart.js | 图谱 + 图表 |
| 国际化 | vue-i18n | 中英文双语 |
| 部署 | Docker + Docker Compose | 容器化部署 |

---

## 配置说明

LLM 通过网页端 **Settings** 页面配置，支持：

| 提供商 | API 地址 | 推荐模型 |
|--------|----------|----------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4.1`、`o4-mini` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-max` |
| 自定义 | 任意 OpenAI 兼容 URL | 任意模型 |

完整环境变量参见 `.env.example`。

---

## 许可证

MIT License. 详见 [LICENSE](LICENSE)。

---

## 致谢

- [MITRE ATT&CK](https://attack.mitre.org/) — 威胁分类框架
- [LangGraph](https://langchain-ai.github.io/langgraph/) — 状态机编排框架
- [ChromaDB](https://www.trychroma.com/) — 向量数据库
- [VirusTotal](https://www.virustotal.com/) — 威胁情报 API
- [AbuseIPDB](https://www.abuseipdb.com/) — IP 滥用数据库
- [FastAPI](https://fastapi.tiangolo.com/) — Python Web 框架
- [Vue.js](https://vuejs.org/) — 前端框架
