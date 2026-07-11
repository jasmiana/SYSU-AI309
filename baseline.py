#!/usr/bin/env python3
"""Baseline: single-shot SVG generation with deepseek-v4-flash.

No multi-agent pipeline, no IR, no validation, no feedback loop.
Just one system prompt + one user prompt → SVG output.

Usage:
    python baseline.py                  # Run all 5 samples
    python baseline.py --sample sample4 # Run a single sample
    python baseline.py --list           # List available samples
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
BASELINE_MODEL = "deepseek-v4-flash"
OUTPUT_DIR = PROJECT_ROOT / "outputs_baseline"

# ---------------------------------------------------------------------------
# System prompt (lean — no CoT, no IR, just SVG generation rules)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
你是一个 SVG 信息图生成器。用户会用中文描述需求，你直接输出完整的 SVG 代码。

## 核心规则

### XML 正确性（最高优先级）
1. 根元素：`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 H">`
2. 所有标签必须正确闭合，属性用引号包围
3. 颜色必须用十六进制（如 #4A90D9），禁止用颜色名称
4. 在 `<defs>` 中定义渐变、滤镜、箭头标记

### 布局
- 画布宽 800px，高度自适应（建议 900-1400）
- 四周留白 ≥ 40px，元素间距 ≥ 16px
- 标题使用渐变背景横幅（高 70-90px）
- 信息卡片用圆角矩形 + 柔和阴影

### 文本
- 中文：`font-family="system-ui, 'Microsoft YaHei', sans-serif"`
- 标题 28-36px bold，小节标题 20-24px，正文 14-16px

### 设计
- 根据内容选择合适的图表类型（流程图/柱状图/时间线/架构图/概念图）
- 色彩和谐、层次分明、留白充足
- 装饰适度，不喧宾夺主

## 输出要求
直接输出 `<svg>` 开头、`</svg>` 结尾的完整 XML。不要 markdown 代码块，不要任何解释文字。"""

# ---------------------------------------------------------------------------
# 5 mandatory test samples (same as main.py)
# ---------------------------------------------------------------------------

SAMPLES = {
    "sample1": {
        "name": "sample1_llm_principles",
        "prompt": "绘制白色背景的SVG信息图解释大语言模型的基本原理",
        "description": "大语言模型的基本原理（概念解释 → 架构图）",
    },
    "sample2": {
        "name": "sample2_word_embedding",
        "prompt": "绘制白色背景的SVG信息图，通俗易懂地解释词向量（Word Embedding）的基本概念",
        "description": "词向量的基本概念（科普教学 → 概念图）",
    },
    "sample3": {
        "name": "sample3_sysu_history",
        "prompt": "绘制白色背景的SVG信息图，展示中山大学的发展历程",
        "description": "中山大学的发展历程（历史叙述 → 时间线）",
    },
    "sample4": {
        "name": "sample4_coffee_chain",
        "prompt": "绘制 SVG 流程图，展示从一颗咖啡豆到一杯咖啡的完整生产链（种植、采摘、烘焙、研磨、冲煮）",
        "description": "咖啡生产链流程图（流程展示 → 流程图）",
    },
    "sample5": {
        "name": "sample5_video_comparison",
        "prompt": "绘制白色背景的SVG信息图，对比以下数据：YouTube has 10 times more videos than TikTok, TikTok has 2 times more than Kuaishou",
        "description": "YouTube/TikTok/Kuaishou 视频数量对比（数据对比 → 柱状图）",
    },
}

# ---------------------------------------------------------------------------
# Utility: extract clean SVG from LLM response
# ---------------------------------------------------------------------------

def extract_svg(text: str) -> str:
    """Extract clean SVG from LLM output (strip markdown wrappers)."""
    text = text.strip()

    # Remove markdown code blocks
    for pattern in [r"```xml\s*\n", r"```svg\s*\n", r"```html\s*\n", r"```\s*\n"]:
        text = re.sub(pattern, "", text)
    text = text.replace("```", "")

    # Find <svg>...</svg>
    svg_start = text.find("<svg")
    svg_end = text.find("</svg>")

    if svg_start == -1:
        if "<svg" in text.lower():
            svg_start = text.lower().find("<svg")
        else:
            return text.strip()

    if svg_end == -1:
        return text[svg_start:].strip()

    return text[svg_start : svg_end + len("</svg>")].strip()


# ---------------------------------------------------------------------------
# Core: single-shot generation
# ---------------------------------------------------------------------------

def generate_svg(prompt: str, client: OpenAI) -> tuple[str, float, int]:
    """Make one LLM call and return (svg_code, duration_s, token_count)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    t0 = time.time()
    response = client.chat.completions.create(
        model=BASELINE_MODEL,
        messages=messages,
        temperature=0.5,
        max_tokens=16384,
        timeout=300,
        extra_body={"thinking": {"type": "disabled"}},
    )
    elapsed = time.time() - t0

    raw = response.choices[0].message.content or ""
    token_count = response.usage.total_tokens if response.usage else 0
    svg = extract_svg(raw)

    return svg, elapsed, token_count


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_sample(sample_id: str, client: OpenAI) -> dict:
    """Run baseline on a single sample."""
    info = SAMPLES[sample_id]
    print(f"\n{'─'*50}")
    print(f"[{sample_id}] {info['description']}")
    print(f"Prompt: {info['prompt']}")

    svg, elapsed, tokens = generate_svg(info["prompt"], client)

    # Save
    out_dir = OUTPUT_DIR / info["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / f"{info['name']}_baseline.svg"
    svg_path.write_text(svg, encoding="utf-8")

    # Basic XML validation
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(svg)
        xml_ok = True
    except Exception:
        xml_ok = False

    status = "OK" if xml_ok else "XML_INVALID"
    print(f"  → {status} | {elapsed:.1f}s | {len(svg)} chars | {tokens} tokens")
    print(f"  → saved: {svg_path}")

    return {
        "sample": sample_id,
        "name": info["name"],
        "status": status,
        "duration_s": round(elapsed, 1),
        "svg_chars": len(svg),
        "tokens": tokens,
        "xml_valid": xml_ok,
        "svg_path": str(svg_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Baseline single-shot SVG generation")
    parser.add_argument("--sample", type=str, default=None, help="Run a specific sample (sample1-sample5)")
    parser.add_argument("--list", action="store_true", help="List available samples")
    args = parser.parse_args()

    if args.list:
        print("Available samples:")
        for sid, info in SAMPLES.items():
            print(f"  {sid}: {info['description']}")
        return

    # Validate API key
    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY not set. Please configure .env file.")
        sys.exit(1)

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    print(f"Baseline: model={BASELINE_MODEL}, single-shot (no multi-agent)")

    if args.sample:
        if args.sample not in SAMPLES:
            print(f"Unknown sample: {args.sample}. Available: {', '.join(SAMPLES)}")
            return
        results = [run_sample(args.sample, client)]
    else:
        results = [run_sample(sid, client) for sid in SAMPLES]

    # Summary
    print(f"\n{'='*50}")
    print("BASELINE SUMMARY")
    print(f"{'='*50}")
    total_time = sum(r["duration_s"] for r in results)
    ok_count = sum(1 for r in results if r["xml_valid"])
    print(f"Model: {BASELINE_MODEL}")
    print(f"Total: {len(results)} samples | {ok_count}/{len(results)} XML valid | {total_time:.1f}s total")
    for r in results:
        icon = "[OK]" if r["xml_valid"] else "[FAIL]"
        print(f"  {icon} {r['sample']}: {r['duration_s']}s | {r['svg_chars']} chars | {r['tokens']} tokens")

    # Save summary JSON
    summary_path = OUTPUT_DIR / f"baseline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps({
            "model": BASELINE_MODEL,
            "results": results,
            "total_duration_s": round(total_time, 1),
            "xml_valid_count": ok_count,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSummary saved: {summary_path}")


if __name__ == "__main__":
    main()
