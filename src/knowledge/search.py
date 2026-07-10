"""Knowledge retrieval — Wikipedia API + local fallback database.

Provides factual knowledge for Agent 1 when the user prompt requires
external information that the LLM may not have (or may hallucinate).
"""

import json
import logging
from pathlib import Path
from typing import Any

try:
    import wikipedia

    _WIKI_AVAILABLE = True
except ImportError:
    _WIKI_AVAILABLE = False

logger = logging.getLogger(__name__)

_FALLBACK_PATH = Path(__file__).parent / "fallback_db.json"


def _load_fallback_db() -> dict[str, Any]:
    """Load the local fallback knowledge database."""
    if _FALLBACK_PATH.exists():
        with open(_FALLBACK_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _match_topic(query: str) -> str | None:
    """Match a search query to a fallback DB topic key.

    Checks the search_queries_mapping first, then falls back to
    substring matching on topic keys.
    """
    db = _load_fallback_db()
    mapping = db.get("search_queries_mapping", {})

    # Direct keyword match
    for keyword, topic_key in mapping.items():
        if keyword.lower() in query.lower():
            return topic_key

    # Substring match on topic names
    topics = db.get("topics", {})
    for topic_key in topics:
        if topic_key.lower().replace("_", " ") in query.lower():
            return topic_key

    return None


def search_wikipedia(query: str, sentences: int = 5) -> dict[str, Any]:
    """Search Wikipedia for a query and return extracted facts.

    Args:
        query: Search query string.
        sentences: Number of summary sentences to fetch.

    Returns:
        {"success": bool, "sources": [...], "extracted_facts": [...], "reliability": str}
    """
    if not _WIKI_AVAILABLE:
        logger.warning("Wikipedia API not installed. Use fallback DB only.")
        return {
            "success": False,
            "sources": [],
            "extracted_facts": [],
            "reliability": "unavailable",
            "error": "wikipedia package not installed",
        }

    try:
        # Set language to Chinese for better results on Chinese queries
        wikipedia.set_lang("zh")

        # Search for pages
        search_results = wikipedia.search(query, results=3)
        if not search_results:
            # Try English fallback
            wikipedia.set_lang("en")
            search_results = wikipedia.search(query, results=3)

        if not search_results:
            return {
                "success": False,
                "sources": [],
                "extracted_facts": [],
                "reliability": "low",
                "error": "No Wikipedia results found",
            }

        facts: list[str] = []
        sources: list[dict] = []

        for title in search_results[:2]:  # Limit to 2 pages
            try:
                page = wikipedia.page(title, auto_suggest=False)
                summary = wikipedia.summary(title, sentences=sentences)
                facts.append(summary)
                sources.append({
                    "title": page.title,
                    "url": page.url,
                    "snippet": summary[:300],
                })
            except (wikipedia.DisambiguationError, wikipedia.PageError) as e:
                logger.debug(f"Wikipedia page error for '{title}': {e}")
                continue

        return {
            "success": len(facts) > 0,
            "sources": sources,
            "extracted_facts": facts,
            "reliability": "medium" if len(facts) > 0 else "low",
        }

    except Exception as e:
        logger.warning(f"Wikipedia search failed: {e}")
        return {
            "success": False,
            "sources": [],
            "extracted_facts": [],
            "reliability": "unavailable",
            "error": str(e),
        }


def retrieve_knowledge(
    search_queries: list[str],
    use_wikipedia: bool = True,
) -> dict[str, Any]:
    """Retrieve external knowledge for detected knowledge gaps.

    Strategy:
    1. Match queries against local fallback DB (fast, reliable)
    2. If no match found, try Wikipedia API
    3. Compile results into a structured knowledge supplement

    Args:
        search_queries: List of search queries from Agent 1's knowledge_gap.
        use_wikipedia: Whether to attempt Wikipedia search.

    Returns:
        Compiled knowledge supplement dict.
    """
    db = _load_fallback_db()
    topics = db.get("topics", {})

    search_results: list[dict] = []
    compiled_parts: list[str] = []

    for query in search_queries:
        # Step 1: Try fallback DB
        topic_key = _match_topic(query)
        if topic_key and topic_key in topics:
            topic_data = topics[topic_key]
            search_results.append({
                "query": query,
                "source": "fallback_db",
                "topic": topic_data.get("topic", topic_key),
                "data": topic_data,
                "reliability": topic_data.get("reliability", "high"),
            })
            # Format knowledge for downstream agents
            compiled_parts.append(_format_topic_knowledge(topic_data))
            logger.info(f"Knowledge: matched '{query}' → fallback DB '{topic_key}'")
            continue

        # Step 2: Try Wikipedia
        if use_wikipedia:
            wiki_result = search_wikipedia(query, sentences=5)
            if wiki_result["success"]:
                search_results.append({
                    "query": query,
                    "source": "wikipedia",
                    "data": wiki_result,
                    "reliability": wiki_result["reliability"],
                })
                compiled_parts.append(
                    f"## Wikipedia 检索: {query}\n\n"
                    + "\n\n".join(wiki_result.get("extracted_facts", []))
                )
                logger.info(f"Knowledge: Wikipedia hit for '{query}'")
                continue

        # Step 3: No results
        logger.warning(f"Knowledge: no results for '{query}'")
        search_results.append({
            "query": query,
            "source": "none",
            "reliability": "unavailable",
        })

    return {
        "search_results": search_results,
        "compiled_knowledge": "\n\n".join(compiled_parts) if compiled_parts else "",
        "knowledge_found": len(compiled_parts) > 0,
    }


def _format_topic_knowledge(topic_data: dict[str, Any]) -> str:
    """Format fallback DB topic data as readable text for downstream agents."""
    topic = topic_data.get("topic", "")

    # Timeline format
    if "key_events" in topic_data:
        lines = [f"## {topic}\n"]
        lines.append(f"来源: {topic_data.get('source', 'unknown')}")
        lines.append("")
        for event in topic_data["key_events"]:
            lines.append(f"- **{event['year']}**: {event['event']}")
        if "narrative" in topic_data:
            lines.append(f"\n概述: {topic_data['narrative']}")
        return "\n".join(lines)

    # Paradigm format (for visualization patterns)
    if "paradigms" in topic_data:
        lines = [f"## {topic}\n"]
        paradigms = topic_data["paradigms"]
        for name, pdata in paradigms.items():
            lines.append(f"### {name}: {pdata.get('description', '')}")
            if "visual_elements" in pdata:
                lines.append("视觉元素:")
                for ve in pdata["visual_elements"]:
                    lines.append(f"  - {ve}")
        if "few_shot_example" in topic_data:
            lines.append(f"\n推荐布局:\n{topic_data['few_shot_example']}")
        return "\n".join(lines)

    # Key concepts format
    if "key_concepts" in topic_data:
        lines = [f"## {topic}\n"]
        for key, value in topic_data["key_concepts"].items():
            if isinstance(value, list):
                lines.append(f"### {key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"  - **{item.get('name', item)}**: {item.get('description', item.get('stage', ''))}")
                    else:
                        lines.append(f"  - {item}")
            elif isinstance(value, str):
                lines.append(f"### {key}: {value}")
        return "\n".join(lines)

    # Generic fallback
    return f"## {topic}\n\n{json.dumps(topic_data, ensure_ascii=False, indent=2)}"
