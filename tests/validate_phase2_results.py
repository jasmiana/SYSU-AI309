"""Validate Phase 2 generation results and print a summary."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

outputs = Path("outputs")
results = []

for d in sorted(outputs.iterdir()):
    if not d.is_dir() or d.name.startswith("_"):
        continue

    # Validate SVG
    svg_files = sorted(d.glob("*v3_final.svg"))
    svg_status = "no SVG found"
    svg_short = "NO_SVG"
    svg_size = 0
    elements: dict[str, int] | None = None
    for svg in svg_files:
        try:
            tree = ET.parse(str(svg))
            root = tree.getroot()
            ns = "http://www.w3.org/2000/svg"
            elements = {
                "rects": len(root.findall(f".//{{{ns}}}rect")),
                "texts": len(root.findall(f".//{{{ns}}}text")),
                "paths": len(root.findall(f".//{{{ns}}}path")),
                "circles": len(root.findall(f".//{{{ns}}}circle")),
            }
            svg_size = svg.stat().st_size / 1024
            vb = root.get("viewBox", "N/A")
            svg_status = f"VALID, {svg_size:.1f}KB, viewBox={vb}"
            svg_short = "VALID"
        except ET.ParseError as e:
            svg_status = f"PARSE ERROR: {e}"
            svg_short = "PARSE_ERR"

    # Read metadata
    meta_files = sorted(d.glob("metadata_*.json"))
    meta = {}
    if meta_files:
        with open(str(meta_files[-1]), encoding="utf-8") as f:
            meta = json.load(f)

    # Read content IR
    content_ir = {}
    content_ir_file = d / "01_content_ir.json"
    if content_ir_file.exists():
        with open(str(content_ir_file), encoding="utf-8") as f:
            content_ir = json.load(f)

    ir_summary = content_ir.get("content_ir_summary", {}) or {}
    intent = ir_summary.get("intent") or content_ir.get("intent", {}).get("primary_type", "?")
    chart = ir_summary.get("chart_type") or content_ir.get("chart_type", {}).get("recommended", "?")
    key_points = content_ir.get("content_summary", {}).get("key_points", [])

    results.append({
        "name": d.name,
        "svg": svg_status,
        "svg_short": svg_short,
        "score": meta.get("final_score", "?"),
        "passed": meta.get("passed", False),
        "rounds": meta.get("refinement_rounds", 0),
        "duration": meta.get("total_duration_s", 0),
        "intent": intent,
        "chart": chart,
        "key_points_count": len(key_points),
        "elements": elements,
    })

print("=" * 70)
print("PHASE 2 GENERATION RESULTS SUMMARY")
print("=" * 70)
print(f"{'Sample':<25} {'SVG':<10} {'Score':<6} {'Pass':<6} {'Rnd':<4} {'Dur':<8} {'Intent':<22} {'Chart'}")
print("-" * 70)
for r in results:
    dur_str = f"{r['duration']:.0f}s" if r["duration"] else "?"
    svg_col = r.get("svg_short", "?")
    print(f"{r['name']:<25} {svg_col:<10} {r['score']:<6} {str(r['passed']):<6} {r['rounds']:<4} {dur_str:<8} {r['intent']:<22} {r['chart']}")

print("-" * 70)
avg_score = sum(r["score"] for r in results if isinstance(r["score"], (int, float))) / max(len(results), 1)
pass_count = sum(1 for r in results if r["passed"])
print(f"Average score: {avg_score:.1f}, Passed: {pass_count}/{len(results)}")

for r in results:
    elems = r["elements"] or {}
    print(f"\n{r['name']}: {r['svg']}, key_points={r['key_points_count']}, elements={elems}")
