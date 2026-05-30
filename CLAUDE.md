# Agent-Based SOAR Prototype

## 项目概述
基于 Agent 架构的自动化安全运营系统 (SOAR)。当安全传感器检测到可疑 IP 时，系统自动执行安全响应 Playbook，支持 AI 增强分析。

## 技术栈
- **后端**: FastAPI + Pydantic + SQLite
- **认证**: JWT (python-jose + bcrypt)
- **AI 引擎**: OpenAI API + 内置 ATT&CK 知识库
- **前端**: 原生 HTML/CSS/JS（暗色主题 Dashboard）
- **Python**: 3.11+

## 项目结构
```
backend/app/
├── main.py              # FastAPI 应用入口
├── models.py            # Pydantic 数据模型
├── settings.py          # 配置管理（环境变量）
├── storage.py           # SQLite 持久化层
├── auth.py              # JWT 认证工具
├── logging_config.py    # 结构化 JSON 日志
├── agents/
│   └── orchestrator.py  # 核心 Playbook 编排引擎（AI 增强）
├── ai/
│   ├── llm_client.py    # LLM API 客户端封装
│   ├── prompts.py       # 安全分析 Prompt 模板
│   ├── analyzer.py      # AI 威胁分析引擎
│   ├── knowledge_base.py# ATT&CK 知识库
│   └── report_generator.py # 自动报告生成
├── integrations/
│   ├── threat_intel.py  # 威胁情报（模拟）
│   ├── risk_assessor.py # 风险评估（规则引擎）
│   └── firewall.py      # 防火墙阻断（模拟）
└── routes/
    ├── alerts.py        # 告警 CRUD API
    ├── runs.py          # Playbook 执行 API
    ├── auth.py          # 认证 API（注册/登录）
    └── knowledge.py     # 知识库搜索 API
```

## 启动方式
```bash
pip install -r requirements.txt
python backend/run.py
python backend/import_alerts.py data/alerts.json

# 运行测试
.venv/Scripts/python -m pytest tests/ -v
```

## API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| POST | /auth/register | 用户注册 |
| POST | /auth/login | 用户登录（获取 JWT） |
| POST | /alerts | 创建告警 |
| GET | /alerts | 列出所有告警 |
| GET | /alerts/{id} | 获取告警详情 |
| POST | /runs | 触发 Playbook 执行 |
| GET | /runs | 列出所有执行记录 |
| GET | /runs/{id} | 获取执行详情（含步骤日志）|
| GET | /knowledge/search?q= | 搜索安全知识库 |

## Playbook 执行步骤
1. **threat_intel** - 威胁情报查询（模拟 VirusTotal/OTX）
2. **risk_assessment** - 风险评估（规则引擎）
3. **ai_analysis** - AI 增强分析（LLM + ATT&CK 知识库，可选）
4. **firewall_block** - 决策执行（高风险自动阻断）
5. **report_generation** - 自动生成事件报告（LLM，可选）

## 数据库 Schema
- `alerts`: 告警表
- `runs`: 执行记录表
- `steps`: 步骤日志表
- `users`: 用户表

## 配置（环境变量）
| 变量 | 默认值 | 说明 |
|------|--------|------|
| SOAR_DB_PATH | data/soar.db | 数据库路径 |
| RISK_BLOCK_THRESHOLD | 70 | 阻断阈值 |
| SIMULATED_LATENCY_MS | 120 | 模拟延迟 |
| JWT_SECRET_KEY | dev-secret-change-me | JWT 密钥 |
| OPENAI_API_KEY | (空) | OpenAI API Key（可选） |
| OPENAI_MODEL | gpt-4o | LLM 模型 |

## 开发约定
- 配置通过环境变量，见 `backend/app/settings.py`
- 模拟集成模块设计为可替换真实 API
- AI 分析为可选增强，无 API key 时自动降级到规则引擎
- 测试使用临时数据库隔离

## Priors

This project uses agent priors (`.claude/priors/`) — persistent knowledge the agent accumulates across sessions.

**Start of every task:** List `.claude/priors/` and read each file's YAML frontmatter (`topic`, `summary`). Load full content only for files relevant to the current task.

**End of every conversation** where you were corrected, discovered something unexpected, or the user provided context you couldn't derive from code: load the `knowledge-extraction` skill from `.claude/skills/` and extract priors.
