from typing import Annotated
from duckduckgo_search import DDGS
from ..models.schemas import SearchResults, URLResult


def search_web(
    query: Annotated[str, "Search query to execute"],
    interpretation_id: Annotated[int, "Interpretation ID this search belongs to"],
    max_results: Annotated[int, "Maximum number of results to return"] = 10
) -> SearchResults:
    """
    Search the web using DuckDuckGo and return structured results
    """
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)

        urls = []
        for result in results:
            url_result = URLResult(
                url=result.get('href', ''),
                title=result.get('title', ''),
                snippet=result.get('body', ''),
                interpretation_id=interpretation_id
            )
            urls.append(url_result)

        return SearchResults(
            interpretation_id=interpretation_id,
            query=query,
            urls=urls
        )
    except Exception as e:
        return SearchResults(
            interpretation_id=interpretation_id,
            query=query,
            urls=[]
        )
