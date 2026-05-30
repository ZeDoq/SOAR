# SOAR — Security Orchestration, Automation & Response

AI 驱动的安全运营自动化平台。当安全传感器检测到可疑活动时，系统自动执行威胁情报查询、风险分析、遏制处置和事件报告生成。

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4-42b883?logo=vuedotjs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-164_Passed-brightgreen)

---

## 功能特性

### 安全运营核心
- **多 Agent 协作** — 情报 Agent、分析 Agent、响应 Agent 分工协作
- **自适应 Playbook** — 7 套模板根据攻击类型自动选择响应策略
- **AI 威胁分析** — 支持 DeepSeek / GPT / Qwen / MiMo 等多模型，自动映射 MITRE ATT&CK 技术
- **知识图谱** — networkx 内存图，IP/告警/技术关联分析和聚类检测

### 威胁情报与侦察
- VirusTotal + AbuseIPDB IP 信誉查询（多源聚合）
- WHOIS + DNS 网络侦察
- 模拟引擎兜底（无 API Key 时自动使用）

### 告警接入
- Syslog UDP 监听（RFC 3164）
- Wazuh API 轮询
- Suricata EVE JSON 日志 Tail

### 通知与报告
- 邮件（SMTP）+ Slack Webhook 通知
- AI 自动生成 Markdown 事件报告

### 攻击模拟
- 6 种预定义场景：暴力破解、端口扫描、DDoS、钓鱼、数据外泄、横向移动

---

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+

### 开发模式

```bash
# 克隆项目
git clone https://github.com/ZeDoq/SOAR.git
cd SOAR

# 后端
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd frontend && npm install && cd ..

# 配置
cp .env.example .env
# 编辑 .env，至少设置 JWT_SECRET_KEY

# 启动（两个终端）
python backend/run.py            # 终端 1：API 服务 (8000)
cd frontend && npm run dev       # 终端 2：前端开发 (5173)
```

浏览器访问 **http://localhost:5173**

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env

docker compose up -d
```

浏览器访问 **http://localhost:8000**

---

## 配置说明

复制 `.env.example` 为 `.env`，主要配置项：

| 变量 | 说明 |
|------|------|
| `JWT_SECRET_KEY` | JWT 密钥（必须修改） |
| `SOAR_DB_PATH` | 数据库路径 |
| `RISK_BLOCK_THRESHOLD` | 自动阻断阈值（默认 70） |
| `VIRUSTOTAL_API_KEY` | VirusTotal 密钥 |
| `ABUSEIPDB_API_KEY` | AbuseIPDB 密钥 |
| `SMTP_*` | 邮件通知配置 |
| `SLACK_WEBHOOK_URL` | Slack Webhook |

AI 模型通过网页端 **Settings** 页面配置，支持 DeepSeek、OpenAI、通义千问等。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Pydantic + SQLite |
| AI | OpenAI SDK（多提供商）+ networkx 知识图谱 |
| 前端 | Vue 3 + Vite + Pinia |
| 部署 | Docker + Docker Compose |

---

## 项目结构

```
SOAR/
├── backend/app/
│   ├── agents/           # 多 Agent 系统 + 自适应编排器
│   ├── ai/               # AI/LLM 引擎 + 知识库
│   ├── graph/            # 知识图谱 (networkx)
│   ├── ingestion/        # 告警源接入 (Syslog/Wazuh/Suricata)
│   ├── integrations/     # 威胁情报 + 通知 + 侦察
│   ├── routes/           # API 端点
│   └── simulator/        # 攻击模拟器
├── frontend/src/         # Vue 3 SPA
│   ├── views/            # 页面（仪表盘/告警/工作台/图谱/模拟器/配置）
│   ├── components/       # 组件（图表/AI 卡片/实时数据流）
│   └── stores/           # Pinia 状态管理
├── tests/                # 164 个测试用例
├── Dockerfile            # 多阶段构建
└── docker-compose.yml
```

---

## 许可证

MIT License
