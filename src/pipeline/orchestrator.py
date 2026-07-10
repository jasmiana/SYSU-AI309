"""Pipeline orchestrator — coordinates multi-agent execution.

Phase 3: Agent 1 → Knowledge Retrieval → Agent 2 → Agent 3 → Agent 4 (with feedback loop)
"""

import time
import logging
from typing import Any

from ..agents.content_analyzer import ContentAnalyzer
from ..agents.layout_planner import LayoutPlanner
from ..agents.svg_coder import SVGCoder
from ..agents.quality_reviewer import QualityReviewer
from ..knowledge.search import retrieve_knowledge
from ..rendering.validator import run_all_checks
from ..utils.logger import PipelineLogger
from ..utils.file_manager import save_svg, save_ir, save_generation_metadata

logger = logging.getLogger(__name__)

# Maximum Agent 4 → Agent 3 feedback rounds
# With thinking mode enabled, each round = 2 extra agent calls (A3 + A4).
# A value of 1 keeps total rounds <= 2 (initial + 1 refinement).
MAX_REFINEMENT_ROUNDS = 1


class Pipeline:
    """Phase 2 full pipeline: 4 agents + rendering validation + feedback loop.

    Pipeline flow:
    1. Agent 1 (ContentAnalyzer) — intent, NER, RE, chart type recommendation
    2. Agent 2 (LayoutPlanner) — proportional layout, color scheme, typography
    3. Agent 3 (SVGCoder) — SVG XML generation
    4. Rendering validation (deterministic checks)
    5. Agent 4 (QualityReviewer) — 6-dimension review
    6. If not passed: Agent 3 regenerates with Agent 4 feedback (up to 2 rounds)
    """

    def __init__(self, model: str | None = None):
        logger.info("Initializing Phase 2 Pipeline (4 agents + validation)...")
        self.agent1 = ContentAnalyzer(model=model)
        self.agent2 = LayoutPlanner(model=model)
        self.agent3 = SVGCoder(model=model)
        self.agent4 = QualityReviewer(model=model)
        logger.info(
            "Agents initialized: ContentAnalyzer + LayoutPlanner + SVGCoder + QualityReviewer"
        )

    def run(
        self,
        user_prompt: str,
        sample_name: str = "sample",
        context: str | None = None,
        svg_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the full Phase 2 pipeline.

        Args:
            user_prompt: Natural language prompt.
            sample_name: Sample identifier for file naming.
            context: Optional additional context.
            svg_spec: Optional SVG specifications.

        Returns:
            Dict with svg_code, content_ir, layout_ir, review_ir,
            refinement_history, file paths, timing.
        """
        plog = PipelineLogger(sample_name)
        overall_start = time.time()

        if svg_spec is None:
            svg_spec = {
                "width": 800,
                "height": "auto",
                "style": "modern_clean",
                "version": "1.1",
                "use_css_animations": False,
            }

        # ═══════════════════════════════════════════════════════════
        # Step 1: Content Analysis
        # ═══════════════════════════════════════════════════════════
        plog.log_agent_start("Agent1:ContentAnalyzer", {"prompt": user_prompt})
        t1 = time.time()
        try:
            content_ir = self.agent1.analyze(user_prompt, context)
        except Exception as e:
            plog.log_error("Agent1:ContentAnalyzer", str(e))
            raise
        d1 = (time.time() - t1) * 1000
        plog.log_agent_output("Agent1:ContentAnalyzer", content_ir, d1)
        save_ir(sample_name, content_ir, "01_content")
        plog.log_info(f"Content IR saved")

        # ═══════════════════════════════════════════════════════════
        # Knowledge Retrieval (Phase 3) — fill knowledge gaps
        # ═══════════════════════════════════════════════════════════
        knowledge_gap = content_ir.get("knowledge_gap", {})
        if knowledge_gap.get("needs_external_knowledge"):
            search_queries = knowledge_gap.get("search_queries", [])
            plog.log_agent_start(
                "KnowledgeRetriever",
                {"queries": search_queries},
            )
            t_k = time.time()
            try:
                knowledge = retrieve_knowledge(search_queries)
            except Exception as e:
                plog.log_error("KnowledgeRetriever", str(e))
                knowledge = {"compiled_knowledge": "", "knowledge_found": False}
            d_k = (time.time() - t_k) * 1000
            plog.log_agent_output(
                "KnowledgeRetriever",
                {
                    "found": knowledge.get("knowledge_found"),
                    "results": len(knowledge.get("search_results", [])),
                },
                d_k,
            )

            # Inject knowledge into Content IR for downstream agents
            if knowledge.get("compiled_knowledge"):
                content_ir["knowledge_supplement"] = knowledge["compiled_knowledge"]
                content_ir["knowledge_sources"] = [
                    {
                        "query": r["query"],
                        "source": r.get("source", "unknown"),
                        "reliability": r.get("reliability", "low"),
                    }
                    for r in knowledge.get("search_results", [])
                ]
                save_ir(sample_name, content_ir, "01_content")
                plog.log_info(
                    f"Knowledge injected: "
                    f"{len(knowledge.get('search_results', []))} sources"
                )
        else:
            plog.log_info("No knowledge gap detected, skipping retrieval")

        # ═══════════════════════════════════════════════════════════
        # Step 2: Layout Planning
        # ═══════════════════════════════════════════════════════════
        plog.log_agent_start("Agent2:LayoutPlanner", {})
        t2 = time.time()
        try:
            layout_ir = self.agent2.plan_layout(content_ir)
        except Exception as e:
            plog.log_error("Agent2:LayoutPlanner", str(e))
            raise
        d2 = (time.time() - t2) * 1000
        plog.log_agent_output("Agent2:LayoutPlanner", layout_ir, d2)
        save_ir(sample_name, layout_ir, "02_layout")
        plog.log_info(f"Layout IR saved")

        # ═══════════════════════════════════════════════════════════
        # Step 3: SVG Generation (with feedback loop)
        # ═══════════════════════════════════════════════════════════
        refinement_history: list[dict] = []
        final_svg = ""
        final_review: dict[str, Any] = {}

        for round_num in range(1, MAX_REFINEMENT_ROUNDS + 2):
            # Build Agent 3 input with review feedback from previous round
            agent3_input = {
                "content_ir": content_ir,
                "layout_ir": layout_ir,
                "svg_spec": svg_spec,
            }

            # If this is a refinement round, add review feedback
            if round_num > 1 and final_review:
                agent3_input["review_feedback"] = {
                    "summary": final_review.get("summary", ""),
                    "suggestions": final_review.get("specific_suggestions", []),
                    "regeneration_focus": final_review.get(
                        "regeneration_focus", []
                    ),
                }
                plog.log_info(
                    f"Refinement round {round_num - 1}: "
                    f"issues={len(final_review.get('specific_suggestions', []))}"
                )

            # Generate SVG
            plog.log_agent_start(
                f"Agent3:SVGCoder (round {round_num})", {}
            )
            t3 = time.time()
            try:
                svg_code = self.agent3.generate(
                    content_ir=content_ir,
                    layout_ir=layout_ir,
                    svg_spec=svg_spec,
                    review_feedback=agent3_input.get("review_feedback"),
                )
            except Exception as e:
                plog.log_error("Agent3:SVGCoder", str(e))
                raise
            d3 = (time.time() - t3) * 1000
            plog.log_agent_output(
                "Agent3:SVGCoder", {"svg_length": len(svg_code)}, d3
            )

            # Save round SVG
            svg_path = save_svg(sample_name, svg_code, version=f"v1_r{round_num}")
            plog.log_info(f"SVG round {round_num} saved to {svg_path}")

            # ═══════════════════════════════════════════════════════
            # Step 4: Rendering Validation (deterministic)
            # ═══════════════════════════════════════════════════════
            plog.log_agent_start("RenderingValidator", {})
            t4 = time.time()
            structured_check = run_all_checks(svg_code)
            d4 = (time.time() - t4) * 1000
            plog.log_agent_output(
                "RenderingValidator",
                {
                    "xml_valid": structured_check.get("xml_valid"),
                    "all_pass": structured_check.get("all_checks_pass"),
                },
                d4,
            )

            # ═══════════════════════════════════════════════════════
            # Step 5: Quality Review
            # ═══════════════════════════════════════════════════════
            plog.log_agent_start(f"Agent4:QualityReviewer (round {round_num})", {})
            t5 = time.time()
            try:
                review = self.agent4.review(
                    svg_code=svg_code,
                    original_prompt=user_prompt,
                    content_ir=content_ir,
                    layout_ir=layout_ir,
                    structured_check=structured_check,
                )
            except Exception as e:
                plog.log_error("Agent4:QualityReviewer", str(e))
                raise
            d5 = (time.time() - t5) * 1000
            plog.log_agent_output(
                "Agent4:QualityReviewer",
                {
                    "pass": review.get("pass"),
                    "score": review.get("overall_score"),
                    "needs_regen": review.get("needs_regeneration"),
                },
                d5,
            )

            # Save review
            save_ir(sample_name, review, f"03_review_r{round_num}")

            # Record refinement history
            refinement_history.append({
                "round": round_num,
                "svg_path": str(svg_path),
                "overall_score": review.get("overall_score"),
                "pass": review.get("pass"),
                "needs_regeneration": review.get("needs_regeneration"),
                "suggestion_count": len(
                    review.get("specific_suggestions", [])
                ),
            })

            final_svg = svg_code
            final_review = review

            # Check if we should stop
            if review.get("pass"):
                plog.log_info(
                    f"✅ Passed on round {round_num} "
                    f"(score: {review.get('overall_score')})"
                )
                break
            elif not review.get("needs_regeneration"):
                plog.log_info(
                    f"⏹ Not regenerating (needs_regeneration=false)"
                )
                break
            else:
                if round_num <= MAX_REFINEMENT_ROUNDS:
                    plog.log_info(
                        f"🔄 Round {round_num} not passed, "
                        f"regenerating with feedback..."
                    )
                else:
                    plog.log_info(
                        f"⏹ Max refinement rounds ({MAX_REFINEMENT_ROUNDS}) "
                        f"reached, using best available version"
                    )

        # ═══════════════════════════════════════════════════════════
        # Save metadata
        # ═══════════════════════════════════════════════════════════
        total_duration = time.time() - overall_start
        metadata = {
            "sample_name": sample_name,
            "user_prompt": user_prompt,
            "total_duration_s": round(total_duration, 2),
            "agent1_duration_ms": round(d1, 1),
            "agent2_duration_ms": round(d2, 1),
            "refinement_rounds": len(refinement_history),
            "final_score": final_review.get("overall_score"),
            "passed": final_review.get("pass"),
            "svg_size_chars": len(final_svg),
            "content_ir_summary": {
                "intent": content_ir.get("intent", {}).get("primary_type"),
                "confidence": content_ir.get("intent", {}).get("confidence"),
                "chart_type": content_ir.get("chart_type", {}).get("recommended"),
                "entities_count": len(content_ir.get("entities", [])),
                "relations_count": len(content_ir.get("relations", [])),
            },
            "refinement_history": refinement_history,
        }
        save_generation_metadata(sample_name, metadata)

        # Save final trace
        trace_path = plog.save_trace()

        return {
            "svg_code": final_svg,
            "content_ir": content_ir,
            "layout_ir": layout_ir,
            "review_ir": final_review,
            "svg_path": str(
                save_svg(sample_name, final_svg, version="v2_final")
            ),
            "trace_path": str(trace_path),
            "duration_s": round(total_duration, 2),
            "refinement_rounds": len(refinement_history),
            "final_score": final_review.get("overall_score"),
            "passed": final_review.get("pass"),
            "metadata": metadata,
        }


def run_sample(
    user_prompt: str,
    sample_name: str,
    model: str | None = None,
    context: str | None = None,
    svg_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience function to run a single sample through Phase 2 pipeline."""
    pipeline = Pipeline(model=model)
    return pipeline.run(
        user_prompt=user_prompt,
        sample_name=sample_name,
        context=context,
        svg_spec=svg_spec,
    )
