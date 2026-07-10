"""Prompt templates for all agents.

Each agent's system prompt is stored in a separate .txt file for easy editing
and version control. The prompts are loaded at runtime.
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    """Load a prompt template from file."""
    filepath = _PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")
    return filepath.read_text(encoding="utf-8")


def get_agent1_prompt() -> str:
    """Get Agent 1 (Content Analyzer) system prompt."""
    return load_prompt("agent1_system.txt")


def get_agent2_prompt() -> str:
    """Get Agent 2 (Layout Planner) system prompt."""
    return load_prompt("agent2_system.txt")


def get_agent3_prompt() -> str:
    """Get Agent 3 (SVG Coder) system prompt."""
    return load_prompt("agent3_system.txt")


def get_agent4_prompt() -> str:
    """Get Agent 4 (Quality Reviewer) system prompt."""
    return load_prompt("agent4_system.txt")


def get_svg_guidelines() -> str:
    """Get SVG design guidelines."""
    return load_prompt("svg_guidelines.txt")
