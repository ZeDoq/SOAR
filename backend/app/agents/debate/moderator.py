"""Debate moderator that synthesizes final verdict from agent discussions."""

import json
import logging
from typing import List, Dict, Any, Optional

from ...ai.llm_client import chat_json

logger = logging.getLogger(__name__)

MODERATOR_SYSTEM = (
    "你是一名安全运营中心(SOC)的高级分析师，负责主持一场关于安全告警的辩论。\n"
    "三位分析师（威胁猎人、怀疑分析师、上下文专家）已经各自给出了分析。\n"
    "你的任务是：\n"
    "1. 综合所有分析师的观点\n"
    "2. 识别共识点和分歧点\n"
    "3. 给出你的最终裁决\n"
    "4. 评估整体置信度\n\n"
    "请用 JSON 格式回答：\n"
    '{"final_verdict": "malicious|suspicious|benign|false_positive", '
    '"final_confidence": 0.0-1.0, '
    '"key_arguments_for": ["支持恶意判定的关键论据"], '
    '"key_arguments_against": ["反对恶意判定的关键论据"], '
    '"consensus_points": ["所有分析师一致认同的要点"], '
    '"resolution_of_disagreements": "如何解决分歧", '
    '"final_reasoning": "最终推理过程", '
    '"recommended_actions": ["推荐处置措施"]}'
)


def synthesize(
    alert: dict,
    intel: dict,
    agent_verdicts: List[dict],
    consensus: dict,
) -> Optional[dict]:
    """Use LLM to synthesize a final verdict from debate results.

    Args:
        alert: The alert being analyzed
        intel: Threat intelligence data
        agent_verdicts: List of verdict dicts from each agent
        consensus: Consensus metrics from compute_consensus()

    Returns:
        Synthesized verdict dict or None if LLM unavailable.
    """
    # Build the moderator prompt
    prompt = f"""请综合以下辩论结果，给出最终裁决。

## 告警信息
- IP: {alert.get('ip')}
- 描述: {alert.get('description')}
- 标签: {', '.join(alert.get('tags', []))}

## 威胁情报
- 信誉: {intel.get('reputation', 'unknown')}
- 置信度: {intel.get('confidence', 0)}

## 各分析师的裁决
"""
    for v in agent_verdicts:
        prompt += f"\n### {v.get('agent_name', 'Unknown')} ({v.get('persona', '')})\n"
        prompt += f"- 裁决: {v.get('verdict')}\n"
        prompt += f"- 置信度: {v.get('confidence', 0)}\n"
        prompt += f"- 推理: {v.get('reasoning', 'N/A')}\n"
        # Include persona-specific fields
        if v.get("iocs"):
            prompt += f"- 发现的 IOC: {', '.join(v['iocs'])}\n"
        if v.get("legitimate_explanations"):
            prompt += f"- 合法解释: {', '.join(v['legitimate_explanations'])}\n"
        if v.get("context_factors"):
            prompt += f"- 上下文因素: {', '.join(str(f) for f in v['context_factors'])}\n"

    prompt += f"""
## 共识指标
- 一致度: {consensus.get('agreement_score', 0)}
- 共识裁决: {consensus.get('consensus_verdict', 'unknown')}
- 是否全体一致: {consensus.get('is_unanimous', False)}
- 分歧: {json.dumps(consensus.get('disagreements', []), ensure_ascii=False)}

请给出你的最终综合裁决。"""

    result = chat_json(MODERATOR_SYSTEM, prompt)
    return result
