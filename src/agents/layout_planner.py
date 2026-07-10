"""Agent 2: Layout Planner — spatial layout, color scheme, typography planning."""

import logging
from typing import Any

from .base_agent import BaseAgent
from ..prompts import get_agent2_prompt

logger = logging.getLogger(__name__)


class LayoutPlanner(BaseAgent):
    """Agent 2: Converts Content IR into a spatial Layout IR.

    Takes the structured content analysis and plans:
    - Chart type confirmation (from Agent 1 recommendation)
    - Canvas size and background
    - Color scheme selection
    - Typography scaling
    - Section partitioning (proportional layout)
    - Element positioning with size hints
    - Connection arrows and flow directions
    - Natural-language design notes for Agent 3

    Input: {"content_ir": {...Agent 1 output...}}
    Output: LayoutIR (JSON) with chart_type, canvas, color_scheme,
            typography, sections, elements, connections, design_notes.
    """

    def __init__(self, model: str | None = None):
        super().__init__(
            name="LayoutPlanner",
            model=model,
            temperature=0.3,  # Lower temp for deterministic layout planning
            max_tokens=32768,  # Layout IR is very long + thinking tokens consume budget
        )

    def get_system_prompt(self) -> str:
        return get_agent2_prompt()

    def build_user_prompt(self, input_data: dict[str, Any]) -> str:
        content_ir = input_data.get("content_ir", {})

        intent = content_ir.get("intent", {})
        entities = content_ir.get("entities", [])
        relations = content_ir.get("relations", [])
        content_summary = content_ir.get("content_summary", {})
        chart_type = content_ir.get("chart_type", {})

        parts = [
            "## 内容分析结果\n",
            f"### 意图: {intent.get('primary_type', 'unknown')}",
            f"分类理由: {intent.get('reasoning', 'N/A')}",
            "",
            f"### 推荐图表类型: {chart_type.get('recommended', 'unknown')}",
            f"备选: {', '.join(chart_type.get('alternatives', []))}",
            f"类型置信度: {chart_type.get('type_confidence', 0)}",
            "",
            f"### 标题: {content_summary.get('title', '')}",
            f"### 目标受众: {content_summary.get('target_audience', 'general')}",
            f"### 语言: {content_summary.get('language', 'zh')}",
            "",
            "### 关键信息点:",
        ]
        for i, point in enumerate(content_summary.get("key_points", []), 1):
            parts.append(f"{i}. {point}")
        if not content_summary.get("key_points"):
            parts.append("(无关键信息点，请根据标题和意图自行规划)")

        # Pass through knowledge supplement if available (Phase 3)
        knowledge = content_ir.get("knowledge_supplement", "")
        if knowledge:
            parts.append(
                f"\n## 外部知识补充（来自知识检索模块）\n\n{knowledge}"
            )

        if entities:
            parts.append("\n### 核心实体:")
            for e in entities:
                if e.get("importance") in ("primary", "secondary"):
                    parts.append(f"- {e['name']} ({e['type']}, {e.get('role', '')})")

        if relations:
            parts.append("\n### 实体关系:")
            for r in relations:
                quantifier = f" [{r['quantifier']}]" if r.get("quantifier") else ""
                parts.append(
                    f"- {r['source']} --({r['type']})--> {r['target']}{quantifier}"
                )

        parts.append(
            "\n\n现在请基于以上分析结果，输出完整的布局规划 JSON。"
            "记住使用比例布局（百分比），不要输出绝对像素坐标。"
        )

        return "\n".join(parts)

    def plan_layout(self, content_ir: dict[str, Any]) -> dict[str, Any]:
        """Plan spatial layout from Content IR.

        Args:
            content_ir: Agent 1's Content IR output.

        Returns:
            Layout IR dictionary.
        """
        input_data = {"content_ir": content_ir}

        logger.info("Planning layout...")
        result = self.run(input_data)
        logger.info(
            f"Layout planned: chart_type={result.get('chart_type')}, "
            f"sections={len(result.get('sections', []))}, "
            f"elements={len(result.get('elements', []))}"
        )
        return result
