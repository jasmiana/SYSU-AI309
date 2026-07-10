"""Agent 3: SVG Coder — generates SVG XML code from content analysis."""

import logging
from typing import Any

from .base_agent import BaseAgent, strip_svg_markdown
from ..prompts import get_agent3_prompt, get_svg_guidelines

logger = logging.getLogger(__name__)


class SVGCoder(BaseAgent):
    """Agent 3: Generates SVG XML code from structured content.

    Takes Content IR (and optionally Layout IR) and produces complete,
    valid SVG code. In Phase 1, this agent works directly with Agent 1's
    Content IR output (no intermediate Layout IR from Agent 2).

    Input: Content IR + SVG spec
    Output: Raw SVG XML string
    """

    def __init__(self, model: str | None = None):
        super().__init__(
            name="SVGCoder",
            model=model,
            temperature=0.5,  # Slightly higher for creative visual design
            max_tokens=32768,  # SVG code + thinking tokens (thinking mode consumes budget)
        )

    def get_system_prompt(self) -> str:
        base_prompt = get_agent3_prompt()
        guidelines = get_svg_guidelines()
        return f"{base_prompt}\n\n## SVG 设计规范参考\n\n{guidelines}"

    def build_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Build a rich prompt for SVG generation from Content IR + Layout IR."""
        content_ir = input_data.get("content_ir", {})
        layout_ir = input_data.get("layout_ir", {})
        svg_spec = input_data.get("svg_spec", {})
        review_feedback = input_data.get("review_feedback")

        content_summary = content_ir.get("content_summary", {})
        chart_type = content_ir.get("chart_type", {})

        parts = [
            "## 生成任务\n",
            f"根据以下分析结果生成 SVG 信息图。",
            "",
            f"### 标题: {content_summary.get('title', '信息图')}",
            f"### 目标受众: {content_summary.get('target_audience', 'general')}",
            f"### 语言: {content_summary.get('language', 'zh')}",
            "",
            "### 关键信息点:",
        ]

        for i, point in enumerate(content_summary.get("key_points", []), 1):
            parts.append(f"{i}. {point}")

        # ── Layout IR integration ──────────────────────────
        if layout_ir:
            parts.append(f"\n## 布局规范（来自 Layout Planner）\n")
            parts.append(f"- 图表类型: {layout_ir.get('chart_type', 'unknown')}")
            canvas = layout_ir.get("canvas", {})
            parts.append(
                f"- 画布: {canvas.get('width', 800)} × {canvas.get('height', 'auto')}"
            )

            color = layout_ir.get("color_scheme", {})
            if color:
                parts.append(
                    f"\n### 配色方案: {color.get('name', '')}"
                )
                parts.append(
                    f"- 主色: {color.get('primary')}, "
                    f"辅色: {color.get('secondary')}, "
                    f"强调色: {color.get('accent')}"
                )
                parts.append(f"- 背景: {color.get('background')}")
                parts.append(f"- 配色理由: {color.get('rationale', '')}")

            typo = layout_ir.get("typography", {})
            if typo:
                parts.append(
                    f"\n### 排版: 标题 {typo.get('title_size', 28)}px, "
                    f"小节 {typo.get('heading_size', 22)}px, "
                    f"正文 {typo.get('body_size', 15)}px"
                )

            sections = layout_ir.get("sections", [])
            if sections:
                parts.append(f"\n### 空间分区 ({len(sections)} 个区域):")
                for s in sections:
                    pos = s.get("position", {})
                    parts.append(
                        f"- {s['id']} ({s.get('type')}): "
                        f"x={pos.get('x_pct')}% y={pos.get('y_pct')}% "
                        f"w={pos.get('width_pct')}% h={pos.get('height_pct')}% "
                        f"[{s.get('visual_weight', '')}]"
                    )

            elements = layout_ir.get("elements", [])
            if elements:
                parts.append(f"\n### 元素清单 ({len(elements)} 个):")
                for e in elements[:15]:  # limit for prompt size
                    parts.append(
                        f"- {e['id']} ({e.get('type')}): "
                        f"\"{e.get('label', '')}\" "
                        f"[{e.get('importance', '')}]"
                    )
                if len(elements) > 15:
                    parts.append(f"  ... ({len(elements) - 15} more)")

            connections = layout_ir.get("connections", [])
            if connections:
                parts.append(f"\n### 连接关系 ({len(connections)} 条):")
                for c in connections[:10]:
                    parts.append(
                        f"- {c['from_element']} --({c.get('direction')})--> "
                        f"{c['to_element']} [{c.get('type')}]"
                    )

            design_notes = layout_ir.get("design_notes", "")
            if design_notes:
                parts.append(f"\n### 设计指导:\n{design_notes}")

        # Add relations and entities from Content IR (for context)
        entities = content_ir.get("entities", [])
        if entities:
            parts.append("\n## 关键实体（用于内容准确性检查）:")
            for e in entities:
                if e.get("importance") in ("primary", "secondary"):
                    parts.append(f"- {e['name']} ({e['type']})")

        relations = content_ir.get("relations", [])
        if relations:
            parts.append("\n## 实体关系:")
            for r in relations:
                quantifier = f" [{r['quantifier']}]" if r.get("quantifier") else ""
                parts.append(f"- {r['source']} --({r['type']})--> {r['target']}{quantifier}")

        # Add canvas and style hints
        parts.append("\n## 设计参数\n")
        parts.append(f"- 画布: {svg_spec.get('width', 800)} × {svg_spec.get('height', '自适应')}")

        # ── Review feedback (for refinement rounds) ────────
        if review_feedback:
            parts.append("\n## ⚠️ 修改要求（上一轮审核反馈）\n")
            parts.append(f"### 问题总结: {review_feedback.get('summary', '')}")
            parts.append(f"### 需要重点改进的维度: {review_feedback.get('regeneration_focus', [])}")
            suggestions = review_feedback.get("suggestions", [])
            if suggestions:
                parts.append("\n### 具体修改建议:")
                for s in suggestions:
                    parts.append(
                        f"- [{s.get('priority', 'medium')}] {s.get('target')}: "
                        f"{s.get('issue')} → {s.get('suggestion')}"
                    )
            parts.append(
                "\n请在原有 SVG 基础上，按照以上反馈进行修改。"
                "重点关注 critical 和 high 优先级的问题。"
            )

        parts.append(
            "\n\n现在请生成完整的 SVG 代码。记住：直接输出 <svg> 开始、"
            "</svg> 结束的完整 XML，不要用 markdown 代码块包裹。"
        )

        return "\n".join(parts)

    def generate(
        self,
        content_ir: dict[str, Any],
        svg_spec: dict[str, Any] | None = None,
        layout_ir: dict[str, Any] | None = None,
        review_feedback: dict[str, Any] | None = None,
    ) -> str:
        """Generate SVG code from Content IR and Layout IR.

        Args:
            content_ir: Agent 1's Content IR output.
            svg_spec: Optional SVG specifications.
            layout_ir: Agent 2's Layout IR output (Phase 2).
            review_feedback: Agent 4's review feedback for refinement.

        Returns:
            Clean SVG XML string.
        """
        if svg_spec is None:
            svg_spec = {
                "width": 800,
                "height": "auto",
                "style": "modern_clean",
                "version": "1.1",
                "use_css_animations": False,
            }

        input_data = {
            "content_ir": content_ir,
            "layout_ir": layout_ir or {},
            "svg_spec": svg_spec,
        }
        if review_feedback:
            input_data["review_feedback"] = review_feedback

        logger.info("Generating SVG code...")
        raw_svg = self.run_raw(input_data)
        clean_svg = strip_svg_markdown(raw_svg)
        logger.info(f"SVG generated: {len(clean_svg)} chars")
        return clean_svg
