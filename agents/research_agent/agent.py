import asyncio
import sys
from pathlib import Path
from typing import List, Optional
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.azure_config import AzureOpenAIConfig
from agents.research_agent.models.schemas import (
    QueryFormulations,
    SearchResults,
    ClassifiedURLs,
    FetchedContent,
    CleanedContent,
    FinalReport
)
from agents.research_agent.tools import (
    formulate_queries,
    search_web,
    classify_urls,
    fetch_content,
    clean_content,
    summarize
)


class ResearchAgent:
    """
    Multi-Interpretation Research Agent with Dynamic Structured Outputs
    Orchestrates deterministic workflow: formulate -> search -> classify -> fetch -> clean -> summarize
    """

    def __init__(
        self,
        azure_config: Optional[AzureOpenAIConfig] = None,
        num_interpretations: int = 3,
        max_urls_per_interpretation: int = 2,
        confidence_threshold: float = 0.7
    ):
        self.config = azure_config or AzureOpenAIConfig()
        self.num_interpretations = num_interpretations
        self.max_urls_per_interpretation = max_urls_per_interpretation
        self.confidence_threshold = confidence_threshold

        config_dict = self.config.get_client_config()
        self.azure_client = AzureOpenAI(
            api_key=config_dict["api_key"],
            api_version=config_dict["api_version"],
            azure_endpoint=config_dict["endpoint"]
        )

    async def research(self, user_query: str) -> FinalReport:
        """
        Execute full research pipeline
        """
        print(f"\n🔍 Starting research for: '{user_query}'")

        formulations = self._formulate_queries(user_query)
        print(f"✓ Generated {len(formulations.interpretations)} interpretations")

        search_results = await self._parallel_search(formulations)
        print(f"✓ Searched {len(search_results)} interpretations, found {sum(len(sr.urls) for sr in search_results)} total URLs")

        classified_results = await self._parallel_classify(search_results, user_query)
        total_selected = sum(len(cr.selected) for cr in classified_results)
        print(f"✓ Classified URLs, selected {total_selected} relevant URLs")

        if total_selected == 0:
            print("✗ No relevant URLs found")
            return FinalReport(
                original_query=user_query,
                total_sources=0,
                results=[],
                timestamp="",
                confidence_threshold=self.confidence_threshold
            )

        fetched_contents = await self._parallel_fetch(classified_results)
        print(f"✓ Fetched {len(fetched_contents)} pages")

        cleaned_contents = await self._parallel_clean(fetched_contents, user_query)
        print(f"✓ Cleaned {len(cleaned_contents)} contents")

        final_report = self._summarize_findings(cleaned_contents, user_query)
        print(f"✓ Generated final report with {len(final_report.results)} sources")

        return final_report

    def _formulate_queries(self, user_query: str) -> QueryFormulations:
        """
        Step 1: Generate 3-5 search interpretations
        """
        return formulate_queries(
            user_query=user_query,
            azure_client=self.azure_client,
            num_interpretations=self.num_interpretations
        )

    async def _parallel_search(self, formulations: QueryFormulations) -> List[SearchResults]:
        """
        Step 2: Search all interpretations in parallel
        """
        tasks = []
        for interp in formulations.interpretations:
            task = asyncio.to_thread(
                search_web,
                query=interp.query,
                interpretation_id=interp.interpretation_id,
                max_results=10
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def _parallel_classify(
        self,
        search_results: List[SearchResults],
        original_query: str
    ) -> List[ClassifiedURLs]:
        """
        Step 3: Classify URLs in parallel (LLM picks 0-2 best per interpretation)
        """
        tasks = []
        for sr in search_results:
            task = asyncio.to_thread(
                classify_urls,
                search_results=sr,
                original_query=original_query,
                azure_client=self.azure_client,
                max_urls=self.max_urls_per_interpretation
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def _parallel_fetch(self, classified_results: List[ClassifiedURLs]) -> List[FetchedContent]:
        """
        Step 4: Fetch content from selected URLs (dynamic count)
        """
        tasks = []
        for classified in classified_results:
            for url_obj in classified.selected:
                task = asyncio.to_thread(
                    fetch_content,
                    url=url_obj.url,
                    title=url_obj.title,
                    interpretation_id=url_obj.interpretation_id
                )
                tasks.append(task)

        if not tasks:
            return []

        return await asyncio.gather(*tasks)

    async def _parallel_clean(
        self,
        fetched_contents: List[FetchedContent],
        original_query: str
    ) -> List[CleanedContent]:
        """
        Step 5: Clean content in parallel (LLM removes noise)
        """
        tasks = []
        for content in fetched_contents:
            if content.success:
                task = asyncio.to_thread(
                    clean_content,
                    fetched_content=content,
                    original_query=original_query,
                    azure_client=self.azure_client
                )
                tasks.append(task)

        if not tasks:
            return []

        return await asyncio.gather(*tasks)

    def _summarize_findings(
        self,
        cleaned_contents: List[CleanedContent],
        original_query: str
    ) -> FinalReport:
        """
        Step 6: Consolidate findings into final report
        """
        return summarize(
            cleaned_contents=cleaned_contents,
            original_query=original_query,
            azure_client=self.azure_client,
            confidence_threshold=self.confidence_threshold
        )


async def main():
    """
    Example usage of ResearchAgent
    """
    agent = ResearchAgent(
        num_interpretations=3,
        max_urls_per_interpretation=2,
        confidence_threshold=0.7
    )

    report = await agent.research("Microsoft Agent Framework latest features")

    print("\n" + "="*80)
    print("FINAL RESEARCH REPORT")
    print("="*80)
    print(f"\nQuery: {report.original_query}")
    print(f"Sources analyzed: {report.total_sources}")
    print(f"Timestamp: {report.timestamp}")
    print(f"\nResults:")

    for i, result in enumerate(report.results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Summary: {result.summary}")
        print(f"   Key Facts:")
        for fact in result.key_facts:
            print(f"     - {fact}")


if __name__ == "__main__":
    asyncio.run(main())
