"""Basic smoke tests for Phase 1 implementation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Test imports
from src.utils.config import config
from src.utils.file_manager import get_sample_dir
from src.agents.base_agent import extract_json_from_response, strip_svg_markdown
from src.pipeline.ir_schema import validate_content_ir
from src.prompts import get_agent1_prompt, get_agent3_prompt, get_svg_guidelines


def test_config():
    """Test configuration loading."""
    assert config.DEEPSEEK_MODEL is not None
    assert config.MAX_RETRIES == 3
    assert config.OUTPUT_DIR.exists()
    print("✅ config OK")


def test_json_extraction():
    """Test JSON extraction from various formats."""
    # Pure JSON
    assert extract_json_from_response('{"key": "value"}') == {"key": "value"}
    # Markdown code block
    assert extract_json_from_response(
        '```json\n{"a": 1, "b": 2}\n```'
    ) == {"a": 1, "b": 2}
    # Markdown without language
    assert extract_json_from_response(
        '```\n{"x": [1, 2, 3]}\n```'
    ) == {"x": [1, 2, 3]}
    print("✅ JSON extraction OK")


def test_svg_stripping():
    """Test SVG markdown stripping."""
    result = strip_svg_markdown('```svg\n<svg>test</svg>\n```')
    assert result == '<svg>test</svg>'
    result = strip_svg_markdown('<svg xmlns="...">content</svg>')
    assert result.startswith("<svg")
    assert result.endswith("</svg>")
    print("✅ SVG stripping OK")


def test_ir_validation():
    """Test Content IR validation."""
    # Valid minimal IR
    valid_ir = {
        "intent": {"primary_type": "concept_explanation", "confidence": 0.9},
        "entities": [],
        "relations": [],
        "content_summary": {"title": "Test"},
        "knowledge_gap": {"needs_external_knowledge": False},
        "chart_type": {"recommended": "concept_map", "type_confidence": 0.8},
    }
    issues = validate_content_ir(valid_ir)
    assert len(issues) == 0, f"Expected 0 issues, got: {issues}"
    print("✅ IR validation OK")

    # Invalid IR (missing required fields)
    invalid_ir = {"intent": {}}
    issues = validate_content_ir(invalid_ir)
    assert len(issues) > 0
    print("✅ IR validation catches errors OK")


def test_prompts():
    """Test prompt loading."""
    p1 = get_agent1_prompt()
    assert len(p1) > 500
    assert "意图分类" in p1

    p3 = get_agent3_prompt()
    assert len(p3) > 500
    assert "SVG" in p3

    g = get_svg_guidelines()
    assert len(g) > 500
    assert "viewBox" in g

    print("✅ Prompts loaded OK")


def test_file_manager():
    """Test output directory creation."""
    sample_dir = get_sample_dir("test_sample")
    assert sample_dir.exists()
    print("✅ File manager OK")


if __name__ == "__main__":
    print("Running Phase 1 smoke tests...\n")
    test_config()
    test_json_extraction()
    test_svg_stripping()
    test_ir_validation()
    test_prompts()
    test_file_manager()
    print("\n🎉 All Phase 1 basic tests passed!")
