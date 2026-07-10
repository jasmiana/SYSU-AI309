"""Output file management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import config


def get_sample_dir(sample_name: str) -> Path:
    """Get/create the output directory for a sample."""
    sample_dir = config.OUTPUT_DIR / sample_name
    sample_dir.mkdir(parents=True, exist_ok=True)
    return sample_dir


def save_svg(sample_name: str, svg_code: str, version: str = "v1") -> Path:
    """Save SVG code to a file."""
    sample_dir = get_sample_dir(sample_name)
    filepath = sample_dir / f"{sample_name}_{version}.svg"
    filepath.write_text(svg_code, encoding="utf-8")
    return filepath


def save_ir(sample_name: str, ir_data: dict[str, Any], ir_type: str) -> Path:
    """Save intermediate representation (Content IR or Layout IR)."""
    sample_dir = get_sample_dir(sample_name)
    filepath = sample_dir / f"{ir_type}_ir.json"
    filepath.write_text(
        json.dumps(ir_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return filepath


def save_generation_metadata(
    sample_name: str, metadata: dict[str, Any]
) -> Path:
    """Save metadata about a generation run."""
    sample_dir = get_sample_dir(sample_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = sample_dir / f"metadata_{timestamp}.json"
    metadata["generated_at"] = datetime.now().isoformat()
    filepath.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return filepath
