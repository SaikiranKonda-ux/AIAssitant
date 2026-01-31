from typing import Annotated, List
from openai import AzureOpenAI
from ..models.schemas import SearchResults, ClassifiedURLs, ClassifiedURL


def classify_urls(
    search_results: Annotated[SearchResults, "Search results to classify"],
    original_query: Annotated[str, "Original user query for relevance assessment"],
    azure_client: Annotated[AzureOpenAI, "Azure OpenAI client instance"],
    max_urls: Annotated[int, "Maximum URLs to select"] = 2
) -> ClassifiedURLs:
    """
    Use LLM to classify and select the most relevant URLs from search results
    """
    if not search_results.urls:
        return ClassifiedURLs(
            interpretation_id=search_results.interpretation_id,
            selected=[]
        )

    urls_text = ""
    for i, url in enumerate(search_results.urls):
        urls_text += f"\n{i+1}. Title: {url.title}\n   URL: {url.url}\n   Snippet: {url.snippet}\n"

    system_prompt = """You are a URL relevance classifier. Analyze search results and select the most relevant URLs.
Score each URL 0.0-1.0 for relevance. Return empty array if none are relevant (score < 0.7).
Select maximum {max_urls} best URLs."""

    user_prompt = f"""Original query: "{original_query}"
Search query used: "{search_results.query}"

URLs to classify:
{urls_text}

Select up to {max_urls} most relevant URLs. Return JSON with:
- interpretation_id: {search_results.interpretation_id}
- selected: array of objects with:
  - url: the URL
  - title: page title
  - relevance_score: 0.0-1.0
  - reason: why this URL is relevant
  - interpretation_id: {search_results.interpretation_id}

Return empty selected array if no URLs meet threshold 0.7."""

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

    selected = []
    for item in result.get("selected", [])[:max_urls]:
        selected.append(ClassifiedURL(
            url=item.get("url", ""),
            title=item.get("title", ""),
            relevance_score=item.get("relevance_score", 0.0),
            reason=item.get("reason", ""),
            interpretation_id=search_results.interpretation_id
        ))

    return ClassifiedURLs(
        interpretation_id=search_results.interpretation_id,
        selected=selected
    )
