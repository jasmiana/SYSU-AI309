#!/usr/bin/env python3
"""NER/RE evaluation script — compares Agent 1 predictions against ground truth.

Evaluates entity extraction (NER) and relation extraction (RE) for all 5
mandatory test samples, computing Precision, Recall, and F1 at the
per-sample, micro-average, and macro-average levels.

Ground truth files: tests/ground_truth/sample{1-5}_gt.json
Prediction files:   outputs/{sample_name}/01_content_ir.json

Usage:
    python tests/evaluate_ner_re.py
    python tests/evaluate_ner_re.py --sample sample1      # single sample
    python tests/evaluate_ner_re.py --verbose             # show TP/FP/FN details
"""

import json
import sys
from pathlib import Path
from typing import Any


# -- Paths ---------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
GT_DIR = PROJECT_ROOT / "tests" / "ground_truth"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Map ground-truth sample IDs to output directory names
SAMPLE_ID_TO_DIR: dict[str, str] = {
    "sample1": "sample1_llm_principles",
    "sample2": "sample2_word_embedding",
    "sample3": "sample3_sysu_history",
    "sample4": "sample4_coffee_chain",
    "sample5": "sample5_video_comparison",
}


# -- Helpers --------------------------------------------------------------

def _norm(s: str) -> str:
    """Normalize a string for entity name comparison."""
    return s.strip().lower()


def _norm_triple(rel: dict[str, Any]) -> tuple[str, str, str]:
    """Normalize a relation into a canonical (source, target, type) triple."""
    return (
        _norm(rel.get("source", "")),
        _norm(rel.get("target", "")),
        _norm(rel.get("type", "")),
    )


# -- Evaluation functions -------------------------------------------------

def evaluate_entities(
    pred_entities: list[dict],
    gt_entities: list[dict],
) -> dict[str, Any]:
    """Compute entity-level Precision, Recall, F1.

    Matching rule: entity name, case-insensitive, whitespace-trimmed.

    Returns:
        Dict with precision, recall, f1, tp, fp, fn lists, and counts.
    """
    pred_names: set[str] = set()
    pred_name_map: dict[str, dict] = {}  # normed_name → original entity
    for e in pred_entities:
        n = _norm(e.get("name", ""))
        if n:
            pred_names.add(n)
            pred_name_map[n] = e

    gt_names: set[str] = set()
    gt_name_map: dict[str, dict] = {}
    for e in gt_entities:
        n = _norm(e.get("name", ""))
        if n:
            gt_names.add(n)
            gt_name_map[n] = e

    tp_names = pred_names & gt_names
    fp_names = pred_names - gt_names
    fn_names = gt_names - pred_names

    tp_count = len(tp_names)
    fp_count = len(fp_names)
    fn_count = len(fn_names)

    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp_count": tp_count,
        "fp_count": fp_count,
        "fn_count": fn_count,
        "tp": sorted(tp_names),
        "fp": sorted(fp_names),
        "fn": sorted(fn_names),
    }


def evaluate_relations(
    pred_relations: list[dict],
    gt_relations: list[dict],
) -> dict[str, Any]:
    """Compute relation-level Precision, Recall, F1.

    Matching rule: (source, target, type) triple comparison,
    case-insensitive, whitespace-trimmed.

    The quantifier field is NOT used for matching (Agent 1 may phrase the
    same quantifier differently, e.g., "10 times more" vs "10x").

    Returns:
        Dict with precision, recall, f1, tp, fp, fn lists, and counts.
    """
    pred_triples: set[tuple[str, str, str]] = set()
    for r in pred_relations:
        pred_triples.add(_norm_triple(r))

    gt_triples: set[tuple[str, str, str]] = set()
    for r in gt_relations:
        gt_triples.add(_norm_triple(r))

    tp_triples = pred_triples & gt_triples
    fp_triples = pred_triples - gt_triples
    fn_triples = gt_triples - pred_triples

    tp_count = len(tp_triples)
    fp_count = len(fp_triples)
    fn_count = len(fn_triples)

    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # Convert triples back to readable strings
    def _triple_to_str(t: tuple[str, str, str]) -> str:
        return f"({t[0]} --[{t[2]}]--> {t[1]})"

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp_count": tp_count,
        "fp_count": fp_count,
        "fn_count": fn_count,
        "tp": sorted(_triple_to_str(t) for t in tp_triples),
        "fp": sorted(_triple_to_str(t) for t in fp_triples),
        "fn": sorted(_triple_to_str(t) for t in fn_triples),
    }


# -- Main evaluation ------------------------------------------------------

def load_ground_truth(sample_id: str) -> dict[str, Any]:
    """Load a ground truth annotation file."""
    gt_path = GT_DIR / f"{sample_id}_gt.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {gt_path}")
    with open(gt_path, encoding="utf-8") as f:
        return json.load(f)


def load_prediction(sample_id: str) -> dict[str, Any] | None:
    """Load Agent 1's Content IR prediction file. Returns None if not found."""
    dir_name = SAMPLE_ID_TO_DIR.get(sample_id, sample_id)
    ir_path = OUTPUTS_DIR / dir_name / "01_content_ir.json"
    if not ir_path.exists():
        return None
    with open(ir_path, encoding="utf-8") as f:
        return json.load(f)


def run_evaluation(
    sample_ids: list[str] | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Evaluate NER and RE for the specified sample IDs.

    Args:
        sample_ids: List of sample IDs to evaluate. None = all 5.
        verbose: If True, print TP/FP/FN details for each sample.

    Returns:
        Full evaluation results dict.
    """
    if sample_ids is None:
        sample_ids = [f"sample{i}" for i in range(1, 6)]

    per_sample: dict[str, dict] = {}

    # Accumulators for micro-average
    ner_tp_total, ner_fp_total, ner_fn_total = 0, 0, 0
    re_tp_total, re_fp_total, re_fn_total = 0, 0, 0

    for sid in sample_ids:
        print(f"\n{'─'*60}")
        print(f"[{sid}]")
        print(f"{'─'*60}")

        # Load data
        try:
            gt = load_ground_truth(sid)
        except FileNotFoundError as e:
            print(f"  [WARN] {e}")
            continue

        pred = load_prediction(sid)
        if pred is None:
            print(f"  [WARN] Prediction file not found for {sid}, skipping.")
            continue

        gt_entities: list[dict] = gt.get("ground_truth_entities", [])
        gt_relations: list[dict] = gt.get("ground_truth_relations", [])
        pred_entities: list[dict] = pred.get("entities", [])
        pred_relations: list[dict] = pred.get("relations", [])

        print(f"  Prompt: {gt.get('prompt', 'N/A')[:80]}...")
        print(f"  GT entities: {len(gt_entities)}, GT relations: {len(gt_relations)}")
        print(f"  Pred entities: {len(pred_entities)}, Pred relations: {len(pred_relations)}")

        # Evaluate
        ner_result = evaluate_entities(pred_entities, gt_entities)
        re_result = evaluate_relations(pred_relations, gt_relations)

        # Print results
        print(f"  NER — P: {ner_result['precision']:.3f}, "
              f"R: {ner_result['recall']:.3f}, "
              f"F1: {ner_result['f1']:.3f} "
              f"(TP={ner_result['tp_count']}, FP={ner_result['fp_count']}, FN={ner_result['fn_count']})")
        print(f"  RE  — P: {re_result['precision']:.3f}, "
              f"R: {re_result['recall']:.3f}, "
              f"F1: {re_result['f1']:.3f} "
              f"(TP={re_result['tp_count']}, FP={re_result['fp_count']}, FN={re_result['fn_count']})")

        # Verbose details
        if verbose:
            if ner_result["fp"]:
                print(f"  [FP] NER False Positives (hallucinated): {ner_result['fp']}")
            if ner_result["fn"]:
                print(f"  [FN] NER False Negatives (missed): {ner_result['fn']}")
            if re_result["fp"]:
                print(f"  [FP] RE False Positives: {re_result['fp']}")
            if re_result["fn"]:
                print(f"  [FN] RE False Negatives: {re_result['fn']}")

        # Accumulate for micro-average
        ner_tp_total += ner_result["tp_count"]
        ner_fp_total += ner_result["fp_count"]
        ner_fn_total += ner_result["fn_count"]
        re_tp_total += re_result["tp_count"]
        re_fp_total += re_result["fp_count"]
        re_fn_total += re_result["fn_count"]

        per_sample[sid] = {
            "ner": ner_result,
            "re": re_result,
        }

    # Compute micro-average
    ner_micro_p = ner_tp_total / (ner_tp_total + ner_fp_total) if (ner_tp_total + ner_fp_total) > 0 else 0.0
    ner_micro_r = ner_tp_total / (ner_tp_total + ner_fn_total) if (ner_tp_total + ner_fn_total) > 0 else 0.0
    ner_micro_f1 = (
        2 * ner_micro_p * ner_micro_r / (ner_micro_p + ner_micro_r)
        if (ner_micro_p + ner_micro_r) > 0
        else 0.0
    )

    re_micro_p = re_tp_total / (re_tp_total + re_fp_total) if (re_tp_total + re_fp_total) > 0 else 0.0
    re_micro_r = re_tp_total / (re_tp_total + re_fn_total) if (re_tp_total + re_fn_total) > 0 else 0.0
    re_micro_f1 = (
        2 * re_micro_p * re_micro_r / (re_micro_p + re_micro_r)
        if (re_micro_p + re_micro_r) > 0
        else 0.0
    )

    # Compute macro-average
    n_samples = len(per_sample)
    ner_macro_p = sum(r["ner"]["precision"] for r in per_sample.values()) / n_samples if n_samples > 0 else 0.0
    ner_macro_r = sum(r["ner"]["recall"] for r in per_sample.values()) / n_samples if n_samples > 0 else 0.0
    ner_macro_f1 = sum(r["ner"]["f1"] for r in per_sample.values()) / n_samples if n_samples > 0 else 0.0

    re_macro_p = sum(r["re"]["precision"] for r in per_sample.values()) / n_samples if n_samples > 0 else 0.0
    re_macro_r = sum(r["re"]["recall"] for r in per_sample.values()) / n_samples if n_samples > 0 else 0.0
    re_macro_f1 = sum(r["re"]["f1"] for r in per_sample.values()) / n_samples if n_samples > 0 else 0.0

    # -- Print summary table ----------------------------------------------
    print(f"\n{'='*80}")
    print("SUMMARY: NER / RE Evaluation Results")
    print(f"{'='*80}")

    # Table header
    header = (
        f"{'Sample':<22s} │ {'NER P':>6s} {'NER R':>6s} {'NER F1':>6s} │ "
        f"{'RE P':>6s} {'RE R':>6s} {'RE F1':>6s} │ "
        f"{'NER TP/FP/FN':<18s} │ {'RE TP/FP/FN':<18s}"
    )
    print(header)
    print("─" * len(header))

    sample_labels = {
        "sample1": "sample1 (LLM原理)",
        "sample2": "sample2 (词向量)",
        "sample3": "sample3 (SYSU历史)",
        "sample4": "sample4 (咖啡链)",
        "sample5": "sample5 (数据对比)",
    }

    for sid in sample_ids:
        if sid not in per_sample:
            continue
        r = per_sample[sid]
        ner = r["ner"]
        re = r["re"]
        label = sample_labels.get(sid, sid)
        ner_counts = f"{ner['tp_count']}/{ner['fp_count']}/{ner['fn_count']}"
        re_counts = f"{re['tp_count']}/{re['fp_count']}/{re['fn_count']}"
        print(
            f"{label:<22s} │ {ner['precision']:6.3f} {ner['recall']:6.3f} {ner['f1']:6.3f} │ "
            f"{re['precision']:6.3f} {re['recall']:6.3f} {re['f1']:6.3f} │ "
            f"{ner_counts:<18s} │ {re_counts:<18s}"
        )

    print("─" * len(header))
    print(
        f"{'Micro Avg':<22s} │ {ner_micro_p:6.3f} {ner_micro_r:6.3f} {ner_micro_f1:6.3f} │ "
        f"{re_micro_p:6.3f} {re_micro_r:6.3f} {re_micro_f1:6.3f}"
    )
    print(
        f"{'Macro Avg':<22s} │ {ner_macro_p:6.3f} {ner_macro_r:6.3f} {ner_macro_f1:6.3f} │ "
        f"{re_macro_p:6.3f} {re_macro_r:6.3f} {re_macro_f1:6.3f}"
    )
    print(f"{'='*80}")

    return {
        "per_sample": per_sample,
        "micro_avg": {
            "ner": {"precision": round(ner_micro_p, 4), "recall": round(ner_micro_r, 4), "f1": round(ner_micro_f1, 4)},
            "re": {"precision": round(re_micro_p, 4), "recall": round(re_micro_r, 4), "f1": round(re_micro_f1, 4)},
        },
        "macro_avg": {
            "ner": {"precision": round(ner_macro_p, 4), "recall": round(ner_macro_r, 4), "f1": round(ner_macro_f1, 4)},
            "re": {"precision": round(re_macro_p, 4), "recall": round(re_macro_r, 4), "f1": round(re_macro_f1, 4)},
        },
    }


# -- CLI ------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate Agent 1 NER/RE against ground truth annotations",
    )
    parser.add_argument(
        "--sample", type=str, default=None,
        help="Evaluate a single sample (e.g., sample1). Omit for all 5.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show TP/FP/FN entity/relation details.",
    )
    parser.add_argument(
        "--json", type=str, default=None,
        help="Export full results to a JSON file.",
    )
    args = parser.parse_args()

    sample_ids = [args.sample] if args.sample else None
    results = run_evaluation(sample_ids=sample_ids, verbose=args.verbose)

    if args.json:
        output_path = Path(args.json)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults exported to: {output_path}")
