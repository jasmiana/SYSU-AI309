"""Base agent class with DeepSeek API abstraction, retry logic, and JSON parsing.

DeepSeek API is OpenAI-compatible, so we use the openai SDK with a custom
base_url pointing to https://api.deepseek.com .
"""

import json
import re
import time
import logging
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from ..utils.config import config

logger = logging.getLogger(__name__)


class LLMCallError(Exception):
    """Raised when an LLM API call fails after all retries."""


def extract_json_from_response(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response text.

    Handles:
    - Pure JSON: '{"key": "value"}'
    - Markdown code block: '```json\\n{...}\\n```'
    - Markdown without lang: '```\\n{...}\\n```'
    - Text with embedded JSON: finds first '{' and last '}'
    """
    text = text.strip()

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    code_block_pattern = r"```(?:json)?\s*\n(.*?)\n```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Fallback: find first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]

        # Fix common LLM JSON issues
        # 1. Remove trailing commas before } or ]
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
        # 2. Remove single-line comments
        candidate = re.sub(r"//[^\n]*", "", candidate)

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Last resort: try to find balanced braces
        try:
            balanced = _extract_balanced_json(text, first_brace)
            if balanced:
                balanced = re.sub(r",\s*([}\]])", r"\1", balanced)
                return json.loads(balanced)
        except json.JSONDecodeError:
            pass

        # Desperate: try to fix truncated JSON by closing unclosed strings/brackets
        try:
            fixed = _fix_truncated_json(text[first_brace:last_brace + 1])
            if fixed:
                fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
                return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract valid JSON from LLM response:\n{text[:500]}..."
    )


def _fix_truncated_json(text: str) -> str | None:
    """Attempt to fix JSON truncated by token limits.

    Tries: closing unclosed strings, adding missing closing braces.
    """
    # If the last non-whitespace character before end is a letter/digit/comma,
    # the JSON was likely truncated mid-string or mid-value.
    # Try closing any open string and adding missing }] pairs.
    result = text.rstrip()

    # Count unclosed braces/brackets
    open_braces = result.count("{") - result.count("}")
    open_brackets = result.count("[") - result.count("]")
    in_string = False
    escape_next = False
    for ch in result:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string

    # Close unclosed string
    if in_string:
        result += '"'

    # Close unclosed braces/brackets
    result += "]" * open_brackets
    result += "}" * open_braces

    if result != text.rstrip():
        return result
    return None


def _extract_balanced_json(text: str, start: int) -> str | None:
    """Extract JSON by tracking balanced braces from a given start position."""
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def strip_svg_markdown(text: str) -> str:
    """Clean SVG code from LLM response, removing markdown wrappers.

    Returns clean SVG code starting with <svg> and ending with </svg>.
    """
    text = text.strip()

    # Remove markdown code blocks
    for pattern in [
        r"```xml\s*\n", r"```svg\s*\n", r"```html\s*\n", r"```\s*\n"
    ]:
        text = re.sub(pattern, "", text)
    text = text.replace("```", "")

    # Find SVG content
    svg_start = text.find("<svg")
    svg_end = text.find("</svg>")

    if svg_start == -1:
        if "<svg" in text.lower():
            svg_start = text.lower().find("<svg")
        else:
            return text

    if svg_end == -1:
        return text[svg_start:]

    return text[svg_start : svg_end + len("</svg>")]


class BaseAgent(ABC):
    """Abstract base for all pipeline agents.

    Uses DeepSeek API via OpenAI-compatible SDK.

    Provides:
    - OpenAI client initialized with DeepSeek base URL
    - Retry logic with exponential backoff (max 3 attempts)
    - Structured JSON output parsing
    - Timeout handling
    - Execution time tracking
    """

    def __init__(
        self,
        name: str,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ):
        self.name = name
        self.model = model or config.DEEPSEEK_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens or config.MAX_TOKENS

        if not config.DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY not configured. "
                "Set it in .env file or environment variable."
            )

        self.client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...

    def build_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Build the user prompt from input data.

        Override in subclasses for custom formatting.
        """
        return json.dumps(input_data, ensure_ascii=False, indent=2)

    def call_llm(
        self,
        user_message: str,
        system_prompt: str | None = None,
        expect_json: bool = True,
    ) -> str:
        """Call the DeepSeek API with retry logic.

        Args:
            user_message: The user message/prompt.
            system_prompt: Optional system prompt override.
            expect_json: If True, instruct the model to output raw JSON.

        Returns:
            The model's text response.

        Raises:
            LLMCallError: If all retry attempts fail.
        """
        system = system_prompt or self.get_system_prompt()

        if expect_json:
            system += (
                "\n\nIMPORTANT: Output ONLY valid JSON. "
                "No markdown, no explanations outside the JSON."
            )

        # Build messages in OpenAI format (system as a message role)
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]

        last_error = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"[{self.name}] Attempt {attempt}/{config.MAX_RETRIES}"
                )
                start_time = time.time()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    extra_body=config.get_thinking_config(),
                )

                elapsed = time.time() - start_time
                text = response.choices[0].message.content or ""
                logger.debug(
                    f"[{self.name}] Response received in {elapsed:.1f}s "
                    f"({len(text)} chars)"
                )
                return text

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.name}] API error (attempt {attempt}): {e}"
                )
                if attempt < config.MAX_RETRIES:
                    delay = 2 ** attempt  # exponential backoff: 2, 4, 8 seconds
                    logger.info(f"[{self.name}] Retrying in {delay}s...")
                    time.sleep(delay)

        raise LLMCallError(
            f"[{self.name}] Failed after {config.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent: call LLM and parse structured output.

        If JSON parsing fails, retries once with a stronger instruction
        to output complete, valid JSON (no truncation).

        Args:
            input_data: Agent-specific input data.

        Returns:
            Parsed JSON output as dict.
        """
        user_message = self.build_user_prompt(input_data)
        system_prompt = self.get_system_prompt()

        raw_response = self.call_llm(
            user_message=user_message,
            system_prompt=system_prompt,
            expect_json=True,
        )

        try:
            return extract_json_from_response(raw_response)
        except ValueError as e:
            logger.warning(
                f"[{self.name}] JSON parsing failed (attempt 1): {e}. "
                f"Retrying with stricter JSON instruction..."
            )

            # Retry: add explicit anti-truncation instruction
            retry_system = system_prompt + (
                "\n\nCRITICAL: Your previous output was not valid JSON. "
                "The JSON was likely truncated (cut off before closing). "
                "Output COMPLETE, well-formed JSON with all braces and "
                "quotes properly closed. Double-check the final } is present. "
                "Keep design_notes under 200 characters to avoid truncation."
            )
            try:
                raw_response2 = self.call_llm(
                    user_message=user_message,
                    system_prompt=retry_system,
                    expect_json=True,
                )
                return extract_json_from_response(raw_response2)
            except ValueError as e2:
                logger.error(
                    f"[{self.name}] JSON parsing failed after retry: {e2}"
                )
                return {
                    "parse_error": str(e2),
                    "raw_response": raw_response2,
                }

    def run_raw(self, input_data: dict[str, Any]) -> str:
        """Execute the agent and return raw text (no JSON parsing).

        Use this for agents that output SVG code instead of JSON.

        Args:
            input_data: Agent-specific input data.

        Returns:
            Raw text response from the LLM.
        """
        user_message = self.build_user_prompt(input_data)
        system_prompt = self.get_system_prompt()

        # Add instruction to output raw SVG without markdown wrapping
        system_prompt += (
            "\n\nCRITICAL: Output ONLY the raw SVG code. "
            "No markdown code blocks, no explanations, no ```svg tags. "
            "Start directly with <svg> and end with </svg>."
        )

        return self.call_llm(
            user_message=user_message,
            system_prompt=system_prompt,
            expect_json=False,
        )
