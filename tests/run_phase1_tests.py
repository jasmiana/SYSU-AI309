"""Phase 1 smoke tests — run this script directly to verify the implementation."""

import sys
import os
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

# -- Test 1: Imports ----------------------------------------------------
print("=" * 60)
print("TEST 1: Module Imports")
print("=" * 60)

from src.utils.config import config
print(f"  Model: {config.DEEPSEEK_MODEL}")
print(f"  Max retries: {config.MAX_RETRIES}")
print(f"  Output dir: {config.OUTPUT_DIR}")
print("  ✅ Config loaded")

from src.utils.logger import PipelineLogger
plog = PipelineLogger("test_sample")
print("  ✅ PipelineLogger created")

from src.utils.file_manager import get_sample_dir, save_svg, save_ir
print("  ✅ File manager imported")

from src.agents.base_agent import extract_json_from_response, strip_svg_markdown
print("  ✅ Base agent utilities imported")

from src.pipeline.ir_schema import validate_content_ir, CONTENT_IR_SCHEMA
print("  ✅ IR schema imported")

from src.prompts import get_agent1_prompt, get_agent3_prompt, get_svg_guidelines
print("  ✅ Prompts loader imported")

# -- Test 2: JSON Extraction --------------------------------------------
print("\n" + "=" * 60)
print("TEST 2: JSON Extraction from LLM Responses")
print("=" * 60)

tests = [
    ('{"key": "value"}', {"key": "value"}),
    ('```json\n{"a": 1, "b": 2}\n```', {"a": 1, "b": 2}),
    ('```\n{"x": [1, 2, 3]}\n```', {"x": [1, 2, 3]}),
]
for raw, expected in tests:
    result = extract_json_from_response(raw)
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  ✅ {raw[:40]}... → {result}")

# -- Test 3: SVG Stripping ----------------------------------------------
print("\n" + "=" * 60)
print("TEST 3: SVG Markdown Stripping")
print("=" * 60)

result = strip_svg_markdown('```svg\n<svg>hello</svg>\n```')
assert result == '<svg>hello</svg>', f"Got: {result}"
print(f"  ✅ Markdown SVG → {result}")

result = strip_svg_markdown('<svg xmlns="x">content</svg>')
assert result == '<svg xmlns="x">content</svg>', f"Got: {result}"
print(f"  ✅ Bare SVG → {result}")

# -- Test 4: IR Validation ----------------------------------------------
print("\n" + "=" * 60)
print("TEST 4: Content IR Validation")
print("=" * 60)

valid_ir = {
    "intent": {"primary_type": "concept_explanation", "confidence": 0.9},
    "entities": [],
    "relations": [],
    "content_summary": {"title": "Test Title"},
    "knowledge_gap": {"needs_external_knowledge": False},
    "chart_type": {"recommended": "concept_map", "type_confidence": 0.8},
}
issues = validate_content_ir(valid_ir)
assert len(issues) == 0, f"Expected 0 issues, got: {issues}"
print(f"  ✅ Valid IR passes validation")

invalid_ir = {"intent": {}}
issues = validate_content_ir(invalid_ir)
assert len(issues) > 0
print(f"  ✅ Invalid IR caught with {len(issues)} issues: {issues}")

# -- Test 5: Prompts Loading --------------------------------------------
print("\n" + "=" * 60)
print("TEST 5: System Prompts")
print("=" * 60)

p1 = get_agent1_prompt()
assert len(p1) > 500, f"Agent1 prompt too short: {len(p1)}"
assert "意图分类" in p1
print(f"  ✅ Agent 1 prompt: {len(p1)} chars")

p3 = get_agent3_prompt()
assert len(p3) > 500, f"Agent3 prompt too short: {len(p3)}"
assert "SVG" in p3
print(f"  ✅ Agent 3 prompt: {len(p3)} chars")

g = get_svg_guidelines()
assert len(g) > 500, f"SVG guidelines too short: {len(g)}"
assert "viewBox" in g
print(f"  ✅ SVG guidelines: {len(g)} chars")

# -- Test 6: File Manager -----------------------------------------------
print("\n" + "=" * 60)
print("TEST 6: Output File Management")
print("=" * 60)

sample_dir = get_sample_dir("test_sample")
assert sample_dir.exists()
print(f"  ✅ Sample dir: {sample_dir}")

# Test SVG save
test_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#fff"/></svg>'
svg_path = save_svg("test_sample", test_svg, "test")
assert svg_path.exists()
print(f"  ✅ SVG saved: {svg_path}")

# Test IR save
test_ir = {"test": True, "data": [1, 2, 3]}
ir_path = save_ir("test_sample", test_ir, "content")
assert ir_path.exists()
print(f"  ✅ IR saved: {ir_path}")

# -- Summary ------------------------------------------------------------
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print("\n  🎉 All Phase 1 tests passed!\n")
print("  Next steps:")
print("    1. Create .env file with DEEPSEEK_API_KEY")
print("    2. Run: python main.py --sample sample4  (single test)")
print("    3. Run: python main.py                     (all 5 samples)")
print()
