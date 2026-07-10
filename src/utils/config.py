"""Configuration management."""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Application configuration loaded from environment variables."""

    # ── DeepSeek API ───────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
    DEEPSEEK_FALLBACK_MODEL: str = os.getenv(
        "DEEPSEEK_FALLBACK_MODEL", "deepseek-v4-flash"
    )
    DEEPSEEK_BASE_URL: str = os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
    )

    # ── Thinking / Reasoning (DeepSeek native) ─────────────────────
    THINKING_ENABLED: bool = os.getenv("THINKING_ENABLED", "true").lower() == "true"
    REASONING_EFFORT: str = os.getenv("REASONING_EFFORT", "high")

    @classmethod
    def get_thinking_config(cls) -> dict:
        """Build the DeepSeek thinking extra_body dict."""
        if not cls.THINKING_ENABLED:
            return {}
        return {
            "thinking": {"type": "enabled"},
            "reasoning_effort": cls.REASONING_EFFORT,
        }

    # ── Pipeline ───────────────────────────────────────────────────
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "8192"))

    # ── Output ─────────────────────────────────────────────────────
    OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"

    # ── Logging ────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = PROJECT_ROOT / "outputs" / "_logs"

    @classmethod
    def validate(cls) -> bool:
        """Check that required configuration is present."""
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. "
                "Copy .env.example to .env and fill in your DeepSeek API key."
            )
        return True


# Singleton
config = Config()
