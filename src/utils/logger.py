"""Logging system with structured JSON output for report generation."""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import config


class PipelineLogger:
    """Structured logger that records the full pipeline execution for reports."""

    def __init__(self, sample_name: str):
        self.sample_name = sample_name
        self.log_dir = config.LOG_DIR / sample_name
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Standard Python logger
        self._logger = logging.getLogger(f"pipeline.{sample_name}")
        self._logger.setLevel(getattr(logging, config.LOG_LEVEL))
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
            )
            self._logger.addHandler(handler)

        # Structured execution trace
        self.trace: list[dict] = []
        self.start_time = datetime.now()

    def log_agent_start(self, agent_name: str, input_data: dict[str, Any]) -> None:
        """Record agent invocation start."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "agent_start",
            "agent": agent_name,
            "input_summary": _summarize(input_data),
        }
        self.trace.append(entry)
        self._logger.info(f"[{agent_name}] Starting...")

    def log_agent_output(self, agent_name: str, output: Any, duration_ms: float) -> None:
        """Record agent output."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "agent_output",
            "agent": agent_name,
            "duration_ms": round(duration_ms, 1),
            "output_summary": _summarize(output),
        }
        self.trace.append(entry)
        self._logger.info(f"[{agent_name}] Completed in {duration_ms:.0f}ms")

    def log_error(self, agent_name: str, error: str) -> None:
        """Record an error."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "agent": agent_name,
            "error": error,
        }
        self.trace.append(entry)
        self._logger.error(f"[{agent_name}] Error: {error}")

    def log_info(self, message: str) -> None:
        """Record a general info message."""
        self._logger.info(message)

    def save_trace(self) -> Path:
        """Save the full execution trace as JSON."""
        trace_path = self.log_dir / "trace.json"
        trace_path.write_text(
            json.dumps(
                {
                    "sample": self.sample_name,
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "total_duration_s": (
                        datetime.now() - self.start_time
                    ).total_seconds(),
                    "events": self.trace,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return trace_path


def _summarize(data: Any, max_length: int = 200) -> Any:
    """Create a short summary of data for logging."""
    if isinstance(data, str):
        return data[:max_length] + ("..." if len(data) > max_length else "")
    if isinstance(data, dict):
        return {k: _summarize(v, max_length // 4) for k, v in data.items()}
    if isinstance(data, list):
        if len(data) > 3:
            return [_summarize(x, max_length // 4) for x in data[:3]] + ["..."]
        return [_summarize(x, max_length // 4) for x in data]
    return data
