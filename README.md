# SOAR — Security Orchestration, Automation & Response

> AI 驱动的安全运营自动化平台，支持多 Agent 协作、实时威胁情报、自适应 Playbook 执行和知识图谱可视化。

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4-42b883?logo=vuedotjs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-164%20Passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 项目简介

SOAR 是一个全栈安全运营自动化平台，模拟资深安全分析师处理威胁告警的完整流程 —— 但完全自动化。当安全传感器检测到可疑活动时，系统自动编排多步响应：查询威胁情报、执行 AI 驱动的风险分析、采取遏制措施、生成事件报告。

系统同时支持**经典线性 Playbook** 和 **AI 自适应 Playbook**（根据攻击类型自动选择响应策略）。

### 解决什么问题？

安全运营中心（SOC）面临告警疲劳 —— 每天数千条告警，分析师人手不足。SOAR 自动化了分诊和响应流程：

```
告警接入 → 威胁情报 → 风险评估 → AI 分析 → 遏制处置 → 通知 → 报告
```

每个步骤独立可配，外部服务不可用时优雅降级，并产生结构化审计日志。

---

## 核心功能

### 多模型 AI 引擎
- 支持 **DeepSeek、OpenAI GPT-4.1、通义千问 Qwen3、MiMo** 及任何 OpenAI 兼容 API
- 网页端一键配置模型，支持连通性测试和自动获取模型列表
- AI 威胁分析 + MITRE ATT&CK 技术映射
- 自动生成 Markdown 事件报告
- 无 LLM 时自动降级为规则引擎

### 自适应 Playbook 系统
- **7 套 Playbook 模板**，根据攻击类型自动选择：
  - 暴力破解 → 激进阻断（阈值 60）
  - 端口扫描 → 监控为主（阈值 75）
  - 数据外泄 → 立即遏制（阈值 50）
  - 钓鱼 → 报告为主（不封防火墙）
  - DDoS → 快速响应（阈值 40）
- 多 Agent 架构：情报 Agent → 分析 Agent → 响应 Agent
- 每个 Agent 记录推理过程，决策完全透明

### 实时威胁情报
- **VirusTotal** IP 信誉查询（免费版：4 次/分钟）
- **AbuseIPDB** 滥用评分（免费版：1000 次/天）
- 多源聚合，取最差信誉评分
- WHOIS + DNS 网络侦察

### 自动告警接入
- **Syslog** UDP 监听器（RFC 3164）
- **Wazuh** API 轮询
- **Suricata** EVE JSON 日志 Tail
- 统一管理器：启动/停止/状态查询

### 安全知识图谱
- 基于 networkx 的内存图结构（IP、告警、ATT&CK 技术、风险等级）
- 自动关联检测：共享技术的 IP 之间建立连接
- IP 聚类分析：识别攻击活动
- 最短路径分析：可视化攻击链

### 安全加固
- 全端点 JWT 认证保护
- SSRF 防护（阻止访问内网地址）
- API Key 加密存储 + 响应脱敏
- 登录速率限制（5 分钟 10 次）
- IP 地址、URL、密码等输入校验
- CORS 限制来源

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                 Vue 3 前端 (Vite + Pinia)                    │
│  态势大屏 │ 告警管理 │ 调查工作台 │ 知识图谱 │ 攻击模拟 │ 模型配置 │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JWT 认证)
┌────────────────────────┴────────────────────────────────────┐
│                    FastAPI 后端                               │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 经典     │  │ 自适应   │  │  多      │  │  知识    │    │
│  │ 编排器   │  │ 编排器   │  │  Agent   │  │  图谱    │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘    │
│       │              │              │                         │
│  ┌────┴──────────────┴──────────────┴───────────────────┐   │
│  │              集成层                                    │   │
│  │  威胁情报 │ 风险引擎 │ 防火墙 │ 通知 │ 侦察          │   │
│  │  Syslog   │ Wazuh    │ Suricata                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ AI/LLM   │  │  SQLite  │  │  JWT     │                  │
│  │ 多模型   │  │  存储    │  │  认证    │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

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

浏览器访问 **http://localhost:8000** — 前端由 FastAPI 自动构建并服务。

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `JWT_SECRET_KEY` | *(自动生成)* | JWT 签名密钥 — **生产环境必须设置** |
| `SOAR_DB_PATH` | `data/soar.db` | SQLite 数据库路径 |
| `RISK_BLOCK_THRESHOLD` | `70` | 自动阻断风险阈值 (0-100) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | 允许的跨域来源（逗号分隔） |
| `OPENAI_API_KEY` | *(空)* | 备用 LLM 密钥（推荐通过网页配置） |
| `VIRUSTOTAL_API_KEY` | *(空)* | VirusTotal API 密钥 |
| `ABUSEIPDB_API_KEY` | *(空)* | AbuseIPDB API 密钥 |
| `SMTP_HOST/PORT/USER/PASSWORD` | *(空)* | 邮件通知配置 |
| `SLACK_WEBHOOK_URL` | *(空)* | Slack Webhook 地址 |

### 模型提供商配置

LLM 通过网页端 **Settings** 页面配置（非环境变量），支持：

| 提供商 | API 地址 | 推荐模型 |
|--------|----------|----------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat`、`deepseek-reasoner` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4.1`、`gpt-4.1-mini`、`o4-mini` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-max`、`qwen-plus`、`qwen3-235b-a22b` |
| 自定义 | 任意 OpenAI 兼容 URL | 任意模型 |

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
GET  /alerts/{id}      告警详情

POST /runs             触发 Playbook（mode: classic|adaptive）
GET  /runs             执行记录列表
GET  /runs/{id}        执行详情（含步骤日志）
```

### AI 与情报
```
GET  /knowledge/search?q=    搜索 ATT&CK 知识库
GET  /models                 已配置的模型列表
POST /models                 添加模型提供商
POST /models/fetch-available 获取提供商可用模型列表
POST /models/{id}/test       测试连通性
```

### 基础设施
```
GET  /sources                告警源状态
POST /sources/{name}/start   启动告警源 (syslog/wazuh/suricata)
POST /sources/{name}/stop    停止告警源

GET  /graph                  知识图谱数据
GET  /graph/clusters         IP 聚类
GET  /graph/techniques       ATT&CK 技术频率
POST /graph/rebuild          重建图谱

GET  /simulator/scenarios    攻击场景列表
POST /simulator/run/{name}   执行模拟场景
```

---

## Playbook 执行流程

```
┌─────────────┐
│  告警输入    │ ← 传感器 / Syslog / Wazuh / Suricata / API
└──────┬──────┘
       ▼
┌──────────────┐     ┌─────────────────────┐
│ Playbook     │────▶│ 模板选择            │ ← 仅自适应模式
│ 选择器       │     │ (7 种攻击模式)      │
└──────┬──────┘     └─────────────────────┘
       ▼
┌──────────────┐
│  情报 Agent  │ ← VirusTotal + AbuseIPDB + WHOIS + DNS
└──────┬──────┘
       ▼
┌──────────────┐
│  分析 Agent  │ ← 规则引擎 + LLM (DeepSeek/GPT/Qwen)
│              │   + MITRE ATT&CK 知识库
└──────┬──────┘
       ▼
┌──────────────┐
│  响应 Agent  │ ← 防火墙阻断 + 邮件 + Slack + 报告生成
└──────┬──────┘
       ▼
┌──────────────┐
│  审计日志    │ ← 完整决策链路 + Agent 推理记录
└──────────────┘
```

---

## 测试

```bash
# 运行全部测试（164 个）
.venv/Scripts/python -m pytest tests/ -v

# 运行指定测试文件
.venv/Scripts/python -m pytest tests/test_orchestrator.py -v
```

测试覆盖：
- API 端点（认证、CRUD、权限控制）
- Playbook 编排（经典 + 自适应）
- 多 Agent 系统（情报、分析、响应）
- 知识图谱操作
- 威胁情报聚合
- 攻击模拟器场景
- 输入校验与安全控制

---

## 项目结构

```
SOAR/
├── backend/
│   ├── app/
│   │   ├── agents/           # 多 Agent 系统
│   │   │   ├── orchestrator.py          # 经典 8 步 Playbook
│   │   │   ├── adaptive_orchestrator.py # 自适应 Playbook
│   │   │   ├── intelligence_agent.py    # 情报 + 侦察
│   │   │   ├── analysis_agent.py        # 风险 + AI 分析
│   │   │   ├── response_agent.py        # 处置 + 通知
│   │   │   └── playbook_selector.py     # 7 套攻击模板
│   │   ├── ai/               # AI/LLM 引擎
│   │   │   ├── llm_client.py           # 多模型客户端
│   │   │   ├── analyzer.py             # 威胁分析
│   │   │   ├── knowledge_base.py       # ATT&CK 知识库
│   │   │   └── report_generator.py     # 报告生成
│   │   ├── graph/            # 知识图谱
│   │   │   └── knowledge_graph.py      # networkx 图引擎
│   │   ├── ingestion/        # 告警源接入
│   │   │   ├── syslog_listener.py      # UDP Syslog
│   │   │   ├── wazuh_client.py         # Wazuh API
│   │   │   └── suricata_tail.py        # EVE JSON Tail
│   │   ├── integrations/     # 外部服务连接器
│   │   │   ├── threat_intel.py         # VT + AbuseIPDB
│   │   │   ├── risk_assessor.py        # 风险评分
│   │   │   ├── recon.py               # WHOIS + DNS
│   │   │   ├── notify_email.py        # 邮件通知
│   │   │   └── notify_slack.py        # Slack 通知
│   │   ├── routes/           # API 端点（10 个路由）
│   │   ├── simulator/        # 攻击模拟器
│   │   ├── auth.py           # JWT + bcrypt 认证
│   │   ├── storage.py        # SQLite 存储层
│   │   ├── settings.py       # 环境配置
│   │   └── main.py           # FastAPI 应用入口
│   └── run.py
├── frontend/                 # Vue 3 + Vite SPA
│   └── src/
│       ├── views/            # 10 个页面视图
│       ├── components/       # 可复用 UI 组件
│       ├── stores/           # Pinia 状态管理
│       ├── i18n/             # 中英文双语
│       └── api/              # Axios HTTP 客户端
├── tests/                    # 164 个测试用例（18 个文件）
├── Dockerfile                # 多阶段构建
├── docker-compose.yml        # 生产部署配置
└── .env.example              # 配置模板
```

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端 | FastAPI + Pydantic | REST API + 自动校验 |
| 数据库 | SQLite | 零配置持久化 |
| 认证 | JWT + bcrypt | Token 认证 |
| AI/LLM | OpenAI SDK（多提供商） | 威胁分析 + 报告生成 |
| 图谱 | networkx | 内存知识图谱 |
| 前端 | Vue 3 + Vite + Pinia | 响应式 SPA |
| 图表 | Chart.js + 自定义 SVG | 风险分布 + 动作图表 |
| 可视化 | vis-network | 交互式知识图谱 |
| 国际化 | vue-i18n | 中英文双语 |
| HTTP | httpx | 外部 API 调用 |
| 部署 | Docker + Docker Compose | 容器化生产部署 |

---

## 应用场景

### SOC 分析师工作台
- 赛博朋克风格实时告警监控大屏
- 一键执行 Playbook，实时查看步骤进度
- AI 驱动的威胁分析 + ATT&CK 技术映射
- 知识图谱可视化攻击关联

### 自动化事件响应
- Syslog/SIEM 集成自动接入告警
- 根据攻击类型自适应选择 Playbook
- 高风险事件自动防火墙阻断
- 邮件 + Slack 关键事件通知

### 安全测试与培训
- 6 种内置攻击模拟场景（暴力破解、端口扫描、DDoS、钓鱼、数据外泄、横向移动）
- 多模型 AI 对比测试（同一告警用 DeepSeek / GPT / Qwen 分析）
- 完整决策审计链路 + Agent 推理日志

---

## 许可证

MIT License. 详见 [LICENSE](LICENSE)。

---

## 致谢

- [MITRE ATT&CK](https://attack.mitre.org/) — 威胁分类框架
- [VirusTotal](https://www.virustotal.com/) — 威胁情报 API
- [AbuseIPDB](https://www.abuseipdb.com/) — IP 滥用数据库
- [FastAPI](https://fastapi.tiangolo.com/) — Python Web 框架
- [Vue.js](https://vuejs.org/) — 前端框架
- [networkx](https://networkx.org/) — 图分析库
