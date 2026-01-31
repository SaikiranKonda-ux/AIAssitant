from typing import Annotated, List
from datetime import datetime
from openai import AzureOpenAI
from ..models.schemas import CleanedContent, FinalReport, ResearchResult


def summarize(
    cleaned_contents: Annotated[List[CleanedContent], "List of cleaned content to summarize"],
    original_query: Annotated[str, "Original user query"],
    azure_client: Annotated[AzureOpenAI, "Azure OpenAI client instance"],
    confidence_threshold: Annotated[float, "Minimum confidence for inclusion"] = 0.7
) -> FinalReport:
    """
    Consolidate all research findings into a final report with deduplication
    """
    filtered_contents = [c for c in cleaned_contents if c.confidence >= confidence_threshold]

    if not filtered_contents:
        return FinalReport(
            original_query=original_query,
            total_sources=0,
            results=[],
            timestamp=datetime.now().isoformat(),
            confidence_threshold=confidence_threshold
        )

    sources_text = ""
    for i, content in enumerate(filtered_contents):
        sources_text += f"\nSource {i+1}:\n"
        sources_text += f"Title: {content.title}\n"
        sources_text += f"URL: {content.url}\n"
        sources_text += f"Key Points: {', '.join(content.key_points[:3])}\n"
        sources_text += f"Confidence: {content.confidence}\n"

    system_prompt = """You are a research synthesis expert. Consolidate findings from multiple sources.
Deduplicate overlapping information. Rank by relevance. Preserve source attribution.
Focus on high-quality, verified information."""

    user_prompt = f"""Original query: "{original_query}"

Synthesize findings from {len(filtered_contents)} sources:
{sources_text}

Create a final report. Return JSON with:
- original_query: "{original_query}"
- total_sources: {len(filtered_contents)}
- results: array of objects (one per source after deduplication), each with:
  - url: source URL
  - title: page title
  - summary: concise summary of this source's contribution
  - key_facts: array of 3-5 unique facts from this source
  - confidence: original confidence score
  - interpretation_source: which search interpretation found this
- timestamp: current timestamp
- confidence_threshold: {confidence_threshold}

Deduplicate information across sources. Rank by relevance."""

    response = azure_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    import json
    result = json.loads(response.choices[0].message.content)

    results = []
    for item in result.get("results", []):
        results.append(ResearchResult(
            url=item.get("url", ""),
            title=item.get("title", ""),
            summary=item.get("summary", ""),
            key_facts=item.get("key_facts", []),
            confidence=item.get("confidence", 0.0),
            interpretation_source=item.get("interpretation_source", "")
        ))

    return FinalReport(
        original_query=original_query,
        total_sources=len(filtered_contents),
        results=results,
        timestamp=datetime.now().isoformat(),
        confidence_threshold=confidence_threshold
    )
