#!/usr/bin/env python3
"""Main entry point for the Multi-Agent SVG Generation System.

Phase 2: Agent 1 → Agent 2 → Agent 3 → Agent 4 (with feedback loop)

Usage:
    python main.py                          # Run all 5 samples
    python main.py --sample sample1         # Run a single sample
    python main.py --sample sample1 --model deepseek-v4-pro
    python main.py --list                   # List available samples
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import config
from src.pipeline.orchestrator import Pipeline


# ── Five mandatory test samples ────────────────────────────────────────

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


def run_all_samples(model: str | None = None) -> None:
    """Run pipeline on all 5 mandatory test samples."""
    pipeline = Pipeline(model=model)

    results = {}
    for sample_id, sample_info in SAMPLES.items():
        print(f"\n{'='*60}")
        print(f"Running: {sample_info['description']}")
        print(f"Prompt: {sample_info['prompt']}")
        print(f"{'='*60}")

        try:
            result = pipeline.run(
                user_prompt=sample_info["prompt"],
                sample_name=sample_info["name"],
            )
            results[sample_id] = {
                "status": "success",
                "svg_path": result["svg_path"],
                "duration_s": result["duration_s"],
                "score": result["final_score"],
                "refinement_rounds": result["refinement_rounds"],
                "metadata": result["metadata"],
            }
            print(f"✅ Success! SVG saved to: {result['svg_path']}")
            print(f"   Duration: {result['duration_s']:.1f}s")
            print(f"   Score: {result['final_score']}, Rounds: {result['refinement_rounds']}")
            print(f"   Intent: {result['metadata']['content_ir_summary']['intent']}")
            print(f"   Chart type: {result['metadata']['content_ir_summary']['chart_type']}")

        except Exception as e:
            results[sample_id] = {
                "status": "failed",
                "error": str(e),
            }
            print(f"❌ Failed: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    print(f"Total: {len(results)}, Success: {success_count}, Failed: {len(results) - success_count}")
    for sid, r in results.items():
        status_icon = "✅" if r["status"] == "success" else "❌"
        if r["status"] == "success":
            print(f"  {status_icon} {sid}: {r['svg_path']} ({r['duration_s']}s)")
        else:
            print(f"  {status_icon} {sid}: {r['error']}")


def run_single_sample(sample_id: str, model: str | None = None) -> None:
    """Run pipeline on a single sample."""
    if sample_id not in SAMPLES:
        print(f"Unknown sample: {sample_id}")
        print(f"Available: {', '.join(SAMPLES.keys())}")
        return

    sample_info = SAMPLES[sample_id]
    pipeline = Pipeline(model=model)

    print(f"Running: {sample_info['description']}")
    print(f"Prompt: {sample_info['prompt']}")

    result = pipeline.run(
        user_prompt=sample_info["prompt"],
        sample_name=sample_info["name"],
    )

    print(f"\n✅ Success!")
    print(f"   SVG: {result['svg_path']}")
    print(f"   Trace: {result['trace_path']}")
    print(f"   Duration: {result['duration_s']:.1f}s")
    print(f"   Refinement rounds: {result['refinement_rounds']}")
    print(f"   Final score: {result['final_score']}")
    print(f"   Passed: {result['passed']}")
    print(f"   Intent: {result['metadata']['content_ir_summary']['intent']}")
    print(f"   Chart type: {result['metadata']['content_ir_summary']['chart_type']}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent SVG Generation System (Phase 2)",
    )
    parser.add_argument(
        "--sample",
        type=str,
        default=None,
        help="Run a specific sample (sample1-sample5). Omit to run all.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Model override (default: {config.DEEPSEEK_MODEL})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available samples and exit.",
    )

    args = parser.parse_args()

    if args.list:
        print("Available samples:")
        for sid, info in SAMPLES.items():
            print(f"  {sid}: {info['description']}")
        return

    # Validate API configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please create a .env file with your ANTHROPIC_API_KEY.")
        print("See .env.example for reference.")
        sys.exit(1)

    if args.sample:
        run_single_sample(args.sample, model=args.model)
    else:
        run_all_samples(model=args.model)


if __name__ == "__main__":
    main()
