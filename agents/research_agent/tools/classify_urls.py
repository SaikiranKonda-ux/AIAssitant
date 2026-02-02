import sys
from pathlib import Path
from typing import Annotated, List
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config.prompts import ResearchAgentPrompts
from agents.research_agent.models.schemas import SearchResults, ClassifiedURLs, ClassifiedURL


def classify_urls(
    search_results: Annotated[SearchResults, "Search results to classify"],
    original_query: Annotated[str, "Original user query for relevance assessment"],
    azure_client: Annotated[AzureOpenAI, "Azure OpenAI client instance"],
    deployment_name: Annotated[str, "Azure OpenAI deployment name"],
    max_urls: Annotated[int, "Maximum URLs to select"] = 2
) -> ClassifiedURLs:
    if not search_results.urls:
        return ClassifiedURLs(
            interpretation_id=search_results.interpretation_id,
            selected=[]
        )

    urls_text = ""
    for i, url in enumerate(search_results.urls):
        urls_text += f"\n{i+1}. Title: {url.title}\n   URL: {url.url}\n   Snippet: {url.snippet}\n"

    system_prompt = ResearchAgentPrompts.CLASSIFY_URLS_SYSTEM.format(max_urls=max_urls)

    user_prompt = ResearchAgentPrompts.CLASSIFY_URLS_USER.format(
        original_query=original_query,
        search_query=search_results.query,
        urls_text=urls_text,
        max_urls=max_urls,
        interpretation_id=search_results.interpretation_id
    )

    response = azure_client.chat.completions.create(
        model=deployment_name,
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
