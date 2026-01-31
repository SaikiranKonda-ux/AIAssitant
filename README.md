# Multi-Interpretation Research Agent

## Installation

```bash
pip install openai ddgs requests beautifulsoup4 pydantic
```

## Setup

Set environment variables:

```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

## Usage

```python
import asyncio
from agents.research_agent import ResearchAgent

async def main():
    agent = ResearchAgent(
        num_interpretations=3,
        max_urls_per_interpretation=2,
        confidence_threshold=0.7
    )

    report = await agent.research("Your research query here")

    print(f"Query: {report.original_query}")
    print(f"Sources: {report.total_sources}")
    for result in report.results:
        print(f"\n{result.title}")
        print(f"Summary: {result.summary}")

asyncio.run(main())
```

## Architecture

```
ResearchAgent (Orchestrator)
  ↓
Tools:
  - formulate_queries (LLM) → 3-5 interpretations
  - search_web (DDGS) → 10 URLs per interpretation
  - classify_urls (LLM) → 0-2 best URLs per interpretation
  - fetch_content (BeautifulSoup) → extract page content
  - clean_content (LLM) → remove noise
  - summarize (LLM) → final report
```

## Pipeline Flow

1. **Query Formulation**: Generate 3-5 search interpretations
2. **Parallel Search**: Search all interpretations concurrently (DDGS)
3. **LLM Classification**: Select 0-2 best URLs per interpretation
4. **Dynamic Fetch**: Fetch only selected URLs (variable count)
5. **Parallel Cleaning**: Remove noise from all fetched content
6. **Summarization**: Consolidate findings with deduplication

## File Structure

```
agents/
  └── research_agent/
      ├── agent.py                    # Main orchestrator
      ├── tools/
      │   ├── formulate_queries.py    # LLM-powered
      │   ├── search_web.py           # DDGS
      │   ├── classify_urls.py        # LLM-powered
      │   ├── fetch_content.py        # BeautifulSoup
      │   ├── clean_content.py        # LLM-powered
      │   └── summarize.py            # LLM-powered
      └── models/
          └── schemas.py              # Pydantic models
config/
  └── azure_config.py                 # Azure OpenAI setup
```
