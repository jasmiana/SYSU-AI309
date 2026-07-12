"""Agent 4: Quality Reviewer — multi-dimension review with iterative feedback."""

import json
import logging
from typing import Any

from .base_agent import BaseAgent
from ..prompts import get_agent4_prompt

logger = logging.getLogger(__name__)


class QualityReviewer(BaseAgent):
    """Agent 4: Reviews generated SVG across 7 dimensions.

    Provides structured feedback with:
    - Per-dimension scores and issues
    - Overall pass/fail decision
    - Specific, actionable suggestions (with priorities)
    - Concise summary for Agent 3 regeneration

    The review input includes the structured_check report from the
    rendering validation module, so Agent 4 has deterministic data
    about syntax, bounds, overlaps, and contrast before making its
    qualitative assessment.

    Input: {
        "svg_code": "...",
        "original_prompt": "...",
        "content_ir": {...},
        "layout_ir": {...},
        "structured_check": {...}
    }
    Output: ReviewIR with pass, scores, suggestions, summary.
    """

    def __init__(self, model: str | None = None):
        super().__init__(
            name="QualityReviewer",
            model=model,
            temperature=0.2,  # Low temp for consistent, objective review
            max_tokens=16384,  # Full SVG + structured check + IRs can be long
        )

    def get_system_prompt(self) -> str:
        return get_agent4_prompt()

    def build_user_prompt(self, input_data: dict[str, Any]) -> str:
        svg_code = input_data.get("svg_code", "")
        original_prompt = input_data.get("original_prompt", "")
        content_ir = input_data.get("content_ir", {})
        layout_ir = input_data.get("layout_ir", {})
        structured_check = input_data.get("structured_check", {})

        # Send full SVG — truncation causes false positives when Agent 4
        # can't see the complete bar chart / layout structure
        svg_preview = svg_code

        parts = [
            "## 审查任务\n",
            f"原始提示词: {original_prompt}",
            "",
            "## 1. 结构化检查报告（程序自动检测）\n",
            json.dumps(structured_check, ensure_ascii=False, indent=2),
            "",
            "## 2. 内容分析结果（Content IR）\n",
            f"标题: {content_ir.get('content_summary', {}).get('title', '')}",
        ]

        for i, point in enumerate(
            content_ir.get("content_summary", {}).get("key_points", []), 1
        ):
            parts.append(f"  {i}. {point}")

        parts.append(
            f"\n意图: {content_ir.get('intent', {}).get('primary_type', '')}"
        )
        parts.append(
            f"推荐图表: {content_ir.get('chart_type', {}).get('recommended', '')}"
        )

        # Key entities for content accuracy check
        entities = content_ir.get("entities", [])
        if entities:
            parts.append("\n关键实体:")
            for e in entities:
                if e.get("importance") in ("primary", "secondary"):
                    parts.append(f"  - {e['name']}")

        parts.append(
            f"\n## 3. 布局规划（Layout IR）\n"
            f"图表类型: {layout_ir.get('chart_type', '')}\n"
            f"画布: {layout_ir.get('canvas', {})}\n"
            f"区域数: {len(layout_ir.get('sections', []))}\n"
            f"元素数: {len(layout_ir.get('elements', []))}\n"
        )

        parts.append(
            f"\n## 4. SVG 代码（前 3000 字符）\n```xml\n{svg_preview}\n```"
        )

        parts.append(
            "\n\n请基于以上所有信息，按照你的 6 个审查维度逐一评估，"
            "输出完整的 JSON 审查结果。"
        )

        return "\n".join(parts)

    def review(
        self,
        svg_code: str,
        original_prompt: str,
        content_ir: dict[str, Any],
        layout_ir: dict[str, Any],
        structured_check: dict[str, Any],
    ) -> dict[str, Any]:
        """Review SVG quality across all dimensions.

        Args:
            svg_code: The generated SVG XML.
            original_prompt: The original user prompt.
            content_ir: Agent 1's Content IR.
            layout_ir: Agent 2's Layout IR.
            structured_check: Deterministic validation report.

        Returns:
            Review IR with pass/fail, scores, suggestions.
        """
        input_data = {
            "svg_code": svg_code,
            "original_prompt": original_prompt,
            "content_ir": content_ir,
            "layout_ir": layout_ir,
            "structured_check": structured_check,
        }

        logger.info("Reviewing SVG...")
        result = self.run(input_data)
        logger.info(
            f"Review: pass={result.get('pass')}, "
            f"score={result.get('overall_score')}, "
            f"needs_regeneration={result.get('needs_regeneration')}"
        )
        return result
