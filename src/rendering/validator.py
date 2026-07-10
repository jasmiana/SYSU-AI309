"""SVG rendering validation — deterministic checks on generated SVG.

Provides structured check reports for Agent 4's review process.
Checks: XML syntax, coordinate bounds, element overlap, color contrast.
"""

import re
import logging
import xml.etree.ElementTree as ET
from typing import Any

logger = logging.getLogger(__name__)

# SVG namespace
SVG_NS = "http://www.w3.org/2000/svg"


def _parse_coord(value: str | None) -> float | None:
    """Parse a coordinate value (with optional 'px' suffix)."""
    if value is None:
        return None
    value = str(value).strip().rstrip("px")
    try:
        return float(value)
    except ValueError:
        return None


def _parse_viewbox(svg_root: ET.Element) -> tuple[float, float, float, float]:
    """Extract viewBox as (x, y, w, h)."""
    vb = svg_root.get("viewBox", "0 0 800 1200")
    parts = vb.split()
    if len(parts) >= 4:
        return (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
    return (0, 0, 800, 1200)


def validate_svg_syntax(svg_code: str) -> dict[str, Any]:
    """Check SVG XML well-formedness.

    Returns:
        {"valid": bool, "errors": [str]}
    """
    try:
        ET.fromstring(svg_code)
        return {"xml_valid": True, "xml_errors": []}
    except ET.ParseError as e:
        return {"xml_valid": False, "xml_errors": [str(e)]}


def check_bounds(svg_code: str) -> dict[str, Any]:
    """Check that all positioned elements stay within viewBox.

    Returns:
        {"ok": bool, "out_of_bounds": [{"element": tag, "attr": attr, "value": val}]}
    """
    try:
        root = ET.fromstring(svg_code)
    except ET.ParseError:
        return {"ok": False, "out_of_bounds": [{"error": "XML parse failed"}]}

    _, _, vb_w, vb_h = _parse_viewbox(root)
    out_of_bounds: list[dict] = []

    # Coordinate attributes to check
    coord_attrs = ["x", "y", "cx", "cy", "x1", "y1", "x2", "y2"]
    # Attributes that hold width/height
    size_attrs = ["width", "height", "r"]

    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        # Check coordinate attributes
        for attr in coord_attrs:
            val = _parse_coord(elem.get(attr))
            if val is not None:
                if attr in ("x", "cx", "x1", "x2") and (val < 0 or val > vb_w + 50):
                    out_of_bounds.append({
                        "element": tag,
                        "attribute": attr,
                        "value": val,
                        "limit": vb_w,
                        "issue": f"{attr} = {val} out of viewBox width {vb_w}",
                    })
                if attr in ("y", "cy", "y1", "y2") and (val < 0 or val > vb_h + 50):
                    out_of_bounds.append({
                        "element": tag,
                        "attribute": attr,
                        "value": val,
                        "limit": vb_h,
                        "issue": f"{attr} = {val} out of viewBox height {vb_h}",
                    })

    return {
        "bounds_check_ok": len(out_of_bounds) == 0,
        "out_of_bounds_count": len(out_of_bounds),
        "out_of_bounds": out_of_bounds[:10],  # cap at 10
    }


def check_overlaps(svg_code: str) -> dict[str, Any]:
    """Detect potential text/text or text/rect overlaps.

    Uses simplified bounding-box estimation (does not do full layout engine).

    Returns:
        {"ok": bool, "overlaps": [{"elem1": id, "elem2": id}]}
    """
    try:
        root = ET.fromstring(svg_code)
    except ET.ParseError:
        return {"overlap_check_ok": False, "overlaps": [{"error": "XML parse failed"}]}

    overlaps: list[dict] = []
    boxes: list[dict] = []

    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        eid = elem.get("id", "")

        x = _parse_coord(elem.get("x", "0"))
        y = _parse_coord(elem.get("y", "0"))
        w = _parse_coord(elem.get("width", "0"))
        h = _parse_coord(elem.get("height", "0"))

        if tag in ("rect", "text") and x is not None and y is not None:
            if w and h and w > 0 and h > 0:
                boxes.append({
                    "id": eid,
                    "tag": tag,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "x2": x + w,
                    "y2": y + h,
                })

    # Simple pairwise overlap detection (O(n^2), n is small for SVG)
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            b1, b2 = boxes[i], boxes[j]
            # Check if bboxes overlap
            if (
                b1["x"] < b2["x2"]
                and b1["x2"] > b2["x"]
                and b1["y"] < b2["y2"]
                and b1["y2"] > b2["y"]
            ):
                overlaps.append({
                    "elem1": f"{b1['tag']}#{b1['id']}" if b1["id"] else b1["tag"],
                    "elem2": f"{b2['tag']}#{b2['id']}" if b2["id"] else b2["tag"],
                    "region": f"({b1['x']},{b1['y']})-({b2['x']},{b2['y']})",
                })

    # Filter: exclude containment overlaps where one rect fully contains another
    # (e.g., chart background containing bars — this is normal layout)
    def _is_containment(b1, b2) -> bool:
        """Check if b1 fully contains b2 or vice versa."""
        return (
            (b1["x"] <= b2["x"] and b1["y"] <= b2["y"]
             and b1["x2"] >= b2["x2"] and b1["y2"] >= b2["y2"])
            or
            (b2["x"] <= b1["x"] and b2["y"] <= b1["y"]
             and b2["x2"] >= b1["x2"] and b2["y2"] >= b1["y2"])
        )

    real_overlaps = []
    for overlap in overlaps:
        # Find the original boxes
        b1_data = next((b for b in boxes if (b["tag"] + ("#" + b["id"] if b["id"] else "")) == overlap["elem1"]), None)
        b2_data = next((b for b in boxes if (b["tag"] + ("#" + b["id"] if b["id"] else "")) == overlap["elem2"]), None)
        if b1_data and b2_data and _is_containment(b1_data, b2_data):
            continue  # Skip containment overlaps
        real_overlaps.append(overlap)

    significant = real_overlaps[:10]  # cap

    return {
        "overlap_check_ok": len(significant) <= 2,  # Allow up to 2 minor overlaps
        "overlap_count": len(significant),
        "overlaps": significant,
    }


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) == 6:
        try:
            return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
        except ValueError:
            return None
    return None


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.0."""
    def channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(c1: str, c2: str) -> float | None:
    """Calculate WCAG contrast ratio between two hex colors."""
    rgb1 = _hex_to_rgb(c1)
    rgb2 = _hex_to_rgb(c2)
    if not rgb1 or not rgb2:
        return None
    l1 = _relative_luminance(*rgb1)
    l2 = _relative_luminance(*rgb2)
    lighter, darker = (l1, l2) if l1 > l2 else (l2, l1)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(svg_code: str) -> dict[str, Any]:
    """Check text-background color contrast against WCAG AA.

    Extracts fill colors from <text> elements and compares with
    the SVG background or surrounding rect fills.

    Returns:
        {"ok": bool, "low_contrast": [{"text": str, "ratio": float}]}
    """
    # Common text colors found in the SVG
    text_color_pattern = re.findall(
        r'<text[^>]*fill="([^"]+)"[^>]*>', svg_code
    )
    # Background colors
    bg_color_pattern = re.findall(
        r'fill="(#[0-9A-Fa-f]{6})"', svg_code
    )

    low_contrast: list[dict] = []

    # Check text against white background (most common)
    default_bg = "#FFFFFF"
    for tc in set(text_color_pattern):
        if tc.startswith("#"):
            ratio = _contrast_ratio(tc, default_bg)
            if ratio is not None and ratio < 3.0:  # WCAG AA large text minimum
                low_contrast.append({
                    "text_color": tc,
                    "background": default_bg,
                    "contrast_ratio": round(ratio, 2),
                    "wcag_aa_pass": ratio >= 4.5,
                    "wcag_aa_large_pass": ratio >= 3.0,
                })

    return {
        "contrast_check_ok": len(low_contrast) == 0,
        "low_contrast_count": len(low_contrast),
        "low_contrast": low_contrast[:10],
    }


def run_all_checks(svg_code: str) -> dict[str, Any]:
    """Run all deterministic validation checks on SVG code.

    This is the main entry point — called by the pipeline orchestrator
    before passing data to Agent 4.

    Args:
        svg_code: Complete SVG XML string.

    Returns:
        Structured check report dictionary.
    """
    logger.info("Running structured validation checks...")

    syntax = validate_svg_syntax(svg_code)
    bounds = check_bounds(svg_code) if syntax["xml_valid"] else {
        "bounds_check_ok": False, "error": "Skipped due to XML parse error"
    }
    overlaps = check_overlaps(svg_code) if syntax["xml_valid"] else {
        "overlap_check_ok": False, "error": "Skipped due to XML parse error"
    }
    contrast = check_contrast(svg_code) if syntax["xml_valid"] else {
        "contrast_check_ok": False, "error": "Skipped due to XML parse error"
    }

    report = {
        **syntax,
        **bounds,
        **overlaps,
        **contrast,
        "all_checks_pass": (
            syntax["xml_valid"]
            and bounds.get("bounds_check_ok", False)
            and overlaps.get("overlap_check_ok", False)
            and contrast.get("contrast_check_ok", False)
        ),
    }

    logger.info(
        f"Validation: xml={syntax['xml_valid']}, "
        f"bounds={bounds.get('bounds_check_ok')}, "
        f"overlaps={overlaps.get('overlap_check_ok')}, "
        f"contrast={contrast.get('contrast_check_ok')}"
    )

    return report
