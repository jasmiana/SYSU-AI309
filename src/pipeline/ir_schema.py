"""IR (Intermediate Representation) Schema definitions.

Defines the expected JSON schemas for inter-agent communication.
Used for validation and documentation purposes.
"""

from typing import Any


# ── Content IR (Agent 1 output) ──────────────────────────────────────

CONTENT_IR_SCHEMA: dict[str, Any] = {
    "intent": {
        "primary_type": "string (concept_explanation | 科普 | process_flow | data_comparison | timeline | architecture_diagram)",
        "secondary_type": "string | null",
        "confidence": "float (0.0-1.0)",
        "reasoning": "string",
    },
    "entities": [
        {
            "name": "string",
            "type": "string (person | organization | location | term | number | date)",
            "role": "string (subject | object | attribute | relation)",
            "importance": "string (primary | secondary | context)",
        }
    ],
    "relations": [
        {
            "type": "string (comparison | hierarchy | sequence | causality | temporal)",
            "source": "string",
            "target": "string",
            "description": "string",
            "quantifier": "string | null",
        }
    ],
    "content_summary": {
        "title": "string",
        "key_points": ["string"],
        "target_audience": "string (general | technical | academic)",
        "language": "string (zh | en | mixed)",
    },
    "knowledge_gap": {
        "needs_external_knowledge": "boolean",
        "search_queries": ["string"],
        "fallback_knowledge": "string | null",
    },
    "chart_type": {
        "recommended": "string (flowchart | bar_chart | timeline | architecture_diagram | concept_map | comparison_chart | process_diagram)",
        "alternatives": ["string"],
        "type_confidence": "float (0.0-1.0)",
    },
}

# ── Layout IR (Agent 2 output, Phase 2) ──────────────────────────────

LAYOUT_IR_SCHEMA: dict[str, Any] = {
    "chart_type": "string",
    "canvas": {
        "width": "int",
        "height": "int",
        "background": "string (hex color or gradient)",
    },
    "color_scheme": {
        "name": "string",
        "primary": "string (#hex)",
        "secondary": "string (#hex)",
        "accent": "string (#hex)",
        "background": "string (#hex)",
        "text_primary": "string (#hex)",
        "text_secondary": "string (#hex)",
        "palette": ["string (#hex)"],
        "rationale": "string",
    },
    "typography": {
        "title_size": "int (px)",
        "heading_size": "int (px)",
        "body_size": "int (px)",
        "label_size": "int (px)",
        "font_family": "string",
    },
    "sections": [
        {
            "id": "string",
            "type": "string (title | content_block | diagram | chart | timeline | footer)",
            "position": {
                "x_pct": "float (0-100)",
                "y_pct": "float (0-100)",
                "width_pct": "float (0-100)",
                "height_pct": "float (0-100)",
            },
            "visual_weight": "string (primary | secondary | tertiary)",
        }
    ],
    "elements": [
        {
            "id": "string",
            "type": "string (rect | rounded_rect | circle | text_block | arrow | icon ...)",
            "label": "string",
            "color": "string",
            "relative_position": {
                "x_offset_pct": "float",
                "y_offset_pct": "float",
            },
            "size_hint": {
                "min_width": "int",
                "min_height": "int",
                "aspect_ratio": "float | null",
            },
        }
    ],
    "connections": [
        {
            "id": "string",
            "type": "string (arrow | line | curve | dashed)",
            "from_element": "string",
            "to_element": "string",
            "direction": "string (top-to-bottom | left-to-right | ...)",
            "label": "string | null",
        }
    ],
    "design_notes": "string",
}

# ── Review IR (Agent 4 output, Phase 2) ──────────────────────────────

REVIEW_IR_SCHEMA: dict[str, Any] = {
    "pass": "boolean",
    "overall_score": "float (0-10)",
    "dimensions": {
        "syntax": {"score": "float", "pass": "boolean", "issues": ["string"]},
        "layout": {"score": "float", "pass": "boolean", "issues": ["string"]},
        "content_accuracy": {"score": "float", "pass": "boolean", "issues": ["string"]},
        "chart_type_appropriateness": {"score": "float", "pass": "boolean", "issues": ["string"]},
        "information_completeness": {"score": "float", "pass": "boolean", "issues": ["string"]},
        "aesthetics": {"score": "float", "pass": "boolean", "issues": ["string"]},
    },
    "needs_regeneration": "boolean",
    "regeneration_focus": ["string"],
    "specific_suggestions": [
        {
            "target": "string",
            "issue": "string",
            "suggestion": "string",
            "priority": "string (critical | high | medium | low)",
        }
    ],
    "summary": "string",
}


def validate_content_ir(data: dict[str, Any]) -> list[str]:
    """Validate Content IR structure. Returns list of issues (empty if valid)."""
    issues = []

    # Required top-level keys
    required_keys = [
        "intent", "entities", "relations",
        "content_summary", "knowledge_gap", "chart_type"
    ]
    for key in required_keys:
        if key not in data:
            issues.append(f"Missing required key: '{key}'")

    # Intent validation
    intent = data.get("intent", {})
    if not intent.get("primary_type"):
        issues.append("Missing intent.primary_type")
    if "confidence" not in intent:
        issues.append("Missing intent.confidence")

    # Content summary validation
    cs = data.get("content_summary", {})
    if not cs.get("title"):
        issues.append("Missing content_summary.title")

    return issues
