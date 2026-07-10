"""Agent 1: Content Analyzer — semantic analysis, NER, RE, intent classification."""

import logging
from typing import Any

from .base_agent import BaseAgent
from ..prompts import get_agent1_prompt

logger = logging.getLogger(__name__)


class ContentAnalyzer(BaseAgent):
    """Agent 1: Analyzes user prompt and extracts structured information.

    Performs:
    - Intent classification (with confidence score)
    - Named entity recognition (NER)
    - Relation extraction (RE)
    - Knowledge gap detection
    - Chart type recommendation

    Input: {"user_prompt": "...", "context": "..." | null}
    Output: ContentIR (JSON) with intent, entities, relations, chart_type, etc.
    """

    def __init__(self, model: str | None = None):
        super().__init__(
            name="ContentAnalyzer",
            model=model,
            temperature=0.3,  # Lower temperature for more consistent analysis
        )

    def get_system_prompt(self) -> str:
        return get_agent1_prompt()

    def build_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Format the user prompt for analysis."""
        prompt = input_data.get("user_prompt", "")
        context = input_data.get("context", "")

        parts = [f"## 用户提示词\n\n{prompt}"]
        if context:
            parts.append(f"\n## 上下文信息\n\n{context}")

        parts.append(
            "\n\n请按照你的 Chain-of-Thought 分析步骤，"
            "输出完整的结构化 JSON 分析结果。"
        )
        return "\n".join(parts)

    def analyze(self, user_prompt: str, context: str | None = None) -> dict[str, Any]:
        """Analyze a user prompt and return Content IR.

        Args:
            user_prompt: The natural language prompt from the user.
            context: Optional additional context.

        Returns:
            Content IR dictionary with intent, entities, relations, etc.
        """
        input_data = {"user_prompt": user_prompt}
        if context:
            input_data["context"] = context

        logger.info(f"Analyzing prompt: {user_prompt[:80]}...")
        result = self.run(input_data)
        logger.info(
            f"Analysis complete: type={result.get('intent', {}).get('primary_type')}, "
            f"entities={len(result.get('entities', []))}, "
            f"relations={len(result.get('relations', []))}"
        )
        return result
