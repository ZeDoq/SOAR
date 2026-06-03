"""Security analysis prompt templates."""

import json

SYSTEM_ANALYST = """你是一名资深网络安全分析师，精通 MITRE ATT&CK 框架和威胁情报分析。
你的任务是分析安全事件并提供结构化的研判结果。
请始终用中文回答，JSON 格式输出。"""


def build_analysis_prompt(alert: dict, intel: dict, context: str = "") -> str:
    """Build the threat analysis prompt."""
    prompt = f"""请分析以下安全事件：

## 告警信息
- 源 IP: {alert.get('ip')}
- 来源: {alert.get('source')}
- 描述: {alert.get('description')}
- 标签: {', '.join(alert.get('tags', []))}
- 观测时间: {alert.get('observed_at', '未知')}

## 威胁情报
- 信誉: {intel.get('reputation')}
- 置信度: {intel.get('confidence')}
- 信号值: {intel.get('signal')}
- 来源: {', '.join(intel.get('sources', []))}"""

    if context:
        prompt += f"\n\n## 相关知识库检索结果\n{context}"

    prompt += """

请以 JSON 格式返回分析结果：
{
    "threat_level": "malicious | suspicious | benign | false_positive",
    "attack_technique": "MITRE ATT&CK 技术名称（如有）",
    "attack_tactic": "ATT&CK 战术阶段（如初始访问、执行、持久化等）",
    "impact_assessment": "影响范围评估",
    "recommended_actions": ["推荐处置措施1", "推荐措施2"],
    "additional_intel_needed": ["需要额外收集的情报"],
    "confidence": 0.0-1.0,
    "reasoning": "分析推理过程"
}"""
    return prompt


def build_rag_enhanced_prompt(alert: dict, intel: dict, rag_context: dict) -> str:
    """Build analysis prompt with RAG-enhanced context.

    rag_context from knowledge_base.get_rich_context() includes:
    - techniques: list of matched ATT&CK techniques
    - incidents: list of similar past incidents
    - context_text: formatted context string
    """
    prompt = f"""请分析以下安全事件：

## 告警信息
- 源 IP: {alert.get('ip')}
- 来源: {alert.get('source')}
- 描述: {alert.get('description')}
- 标签: {', '.join(alert.get('tags', []))}
- 观测时间: {alert.get('observed_at', '未知')}

## 威胁情报
- 信誉: {intel.get('reputation')}
- 置信度: {intel.get('confidence')}
- 信号值: {intel.get('signal')}
- 来源: {', '.join(intel.get('sources', []))}"""

    # Add RAG-retrieved ATT&CK techniques
    techniques = rag_context.get("techniques", [])
    if techniques:
        prompt += "\n\n## MITRE ATT&CK 知识库检索结果\n"
        for t in techniques:
            prompt += f"- [{t['id']}] {t['name']} (战术: {t['tactic']})\n"
            prompt += f"  {t['description'][:200]}\n"

    # Add similar past incidents
    incidents = rag_context.get("incidents", [])
    if incidents:
        prompt += "\n## 相似历史安全事件\n"
        for inc in incidents:
            prompt += f"- [{inc['attack_type']}] {inc['description'][:200]}\n"

    prompt += """

请以 JSON 格式返回分析结果：
{
    "threat_level": "malicious | suspicious | benign | false_positive",
    "attack_technique": "MITRE ATT&CK 技术名称（如有）",
    "attack_tactic": "ATT&CK 战术阶段（如初始访问、执行、持久化等）",
    "impact_assessment": "影响范围评估",
    "recommended_actions": ["推荐处置措施1", "推荐措施2"],
    "additional_intel_needed": ["需要额外收集的情报"],
    "confidence": 0.0-1.0,
    "reasoning": "分析推理过程"
}"""
    return prompt


def build_report_prompt(alert: dict, intel: dict, risk: dict, decision: dict) -> str:
    """Build the auto-report generation prompt."""
    return f"""请根据以下安全事件处置记录，生成一份专业的事件调查报告。

## 事件信息
- 告警 IP: {alert.get('ip')}
- 来源: {alert.get('source')}
- 描述: {alert.get('description')}
- 标签: {', '.join(alert.get('tags', []))}

## 威胁情报
- 信誉: {intel.get('reputation')} (置信度: {intel.get('confidence')})

## 风险评估
- 风险评分: {risk.get('risk_score')}/100
- 评估依据: {risk.get('rationale')}

## 处置决策
- 动作: {decision.get('action')}
- 详情: {json.dumps(decision.get('detail', {}), ensure_ascii=False)}

请生成 Markdown 格式的报告，包含以下章节：
1. 事件概述
2. 威胁分析
3. 影响评估
4. 处置措施
5. 后续建议"""
