# AI Assistant Agents

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

---

# Code Understanding Agent

## Pattern: Planner-Executor with Map-Reduce Concurrent Orchestration

## Installation

```bash
pip install openai pydantic
```

## Usage

```python
import asyncio
from agents.code_understanding_agent import CodeUnderstandingAgent

async def main():
    agent = CodeUnderstandingAgent(
        max_concurrent_bundles=5,
        max_lines_per_bundle=2000
    )

    result = await agent.analyze(
        project_path="/path/to/your/project",
        user_request="Understand authentication module"
    )

    print(f"Project: {result.project_name}")
    print(f"Summary: {result.summary}")
    print(f"Bundles analyzed: {result.total_bundles_analyzed}")

asyncio.run(main())
```

## Architecture: Planner-Executor + Map-Reduce

### PLANNER MODULE
```
1. imports_understanding (cached or generated)
2. file_search (intelligent, uses imports)
3. request_classifier (LLM: scope determination)
4. user_permission_gate (>20 files)
5. create_metadata (file stats)
6. bundle_planner (LLM: ≤2000 lines per bundle)
```

### EXECUTOR MODULE - MAP PHASE
```
Parallel bundle processing:
- read_bundle (concurrent)
- analyze_bundle (LLM, batched 5 at a time)
```

### EXECUTOR MODULE - REDUCE PHASE
```
- synthesize (LLM: aggregate all bundles)
- write central_understanding.md
```

## Supported File Types

```python
.py    → Extract imports (AST parsing)
.ipynb → Code cells only
.toml  → All lines
.yml   → All lines
.sql   → All lines
```

## Output Structure

```
project_root/
  └── agent_knowledge/
      ├── imports_understanding.md
      ├── bundle_auth_module.md
      ├── bundle_database.md
      ├── central_understanding.md
```

## Key Features

**Intelligent Bundling**
- LLM enforces 2000-line constraint
- Groups related files by imports
- Splits large files into parts

**User Control**
- Permission gate for >20 Python files
- Shows estimated time & cost
- Cancel before analysis starts

**Function-Level Analysis**
- Control flows (if/else, loops)
- Business rules (validation, auth)
- Cross-module dependencies

## File Structure

```
agents/
  └── code_understanding_agent/
      ├── agent.py                    # Planner-Executor orchestrator
      ├── tools/
      │   ├── extract_imports.py      # AST parsing
      │   ├── generate_diagram.py     # LLM: Mermaid diagrams
      │   ├── file_search.py          # Filter by imports
      │   ├── request_classifier.py   # LLM: scope detection
      │   ├── create_metadata.py      # File stats
      │   ├── bundle_planner.py       # LLM: 2000-line bundles
      │   ├── read_bundle.py          # File I/O
      │   ├── analyze_bundle.py       # LLM: function analysis
      │   ├── synthesize.py           # LLM: aggregation
      │   └── write_markdown.py       # .md file writer
      └── models/
          └── schemas.py              # Pydantic models
```

---

# Planning Agent

## Pattern: Sequential Workflow + Handoff + Human-in-the-Loop (HITL)

## Installation

```bash
pip install openai pydantic
```

## Usage

```python
import asyncio
from agents.planning_agent import PlanningAgent

async def main():
    agent = PlanningAgent()

    plan = await agent.analyze_requirement(
        requirement_text="Add user authentication with OAuth",
        code_directory="/path/to/your/project"
    )

    print(f"Requirement: {plan.requirement_text}")
    print(f"Type: {plan.requirement_type}")
    print(f"Affected files: {len(plan.affected_files)}")
    print(f"Steps: {len(plan.steps)}")

asyncio.run(main())
```

## Architecture: Sequential + Handoff + HITL

### PHASE 1: Codebase Context
```
1. load_codebase_context (loads agent_knowledge/)
2. [HANDOFF] Trigger CodeUnderstandingAgent if needed
3. [HITL] User confirms to run analysis
```

### PHASE 2: Requirement Classification
```
4. requirement_analyzer (LLM: classify requirement)
   - NEW_FEATURE_FROM_SCRATCH
   - MODIFY_EXISTING_CODE
   - NEW_FEATURE_WITH_INTEGRATION
   - UNDERSTAND_SPECIFIC_FILES
5. [HITL] ambiguity_resolver (interactive prompts)
```

### PHASE 3: Planning
```
6. [HITL] discussion_facilitator (for new features)
7. plan_generator (LLM: detailed implementation plan)
8. write_markdown (save to agent_planning/)
```

## Requirement Types

**NEW_FEATURE_FROM_SCRATCH**
- No existing code for this feature
- Requires architecture discussion
- Interactive tech stack choices

**MODIFY_EXISTING_CODE**
- Changes to existing functionality
- Identifies affected files
- Plans refactoring steps

**NEW_FEATURE_WITH_INTEGRATION**
- New feature connecting to existing code
- Maps integration points
- Plans compatibility changes

**UNDERSTAND_SPECIFIC_FILES**
- Analysis request for specific files
- Handoff to CodeUnderstandingAgent
- No implementation planning

## Output Structure

```
project_root/
  └── agent_planning/
      ├── requirements/
      │   └── requirement_<hash>.md
      ├── classifications/
      │   └── classification_<hash>.md
      └── plans/
          └── plan_<hash>.md
```

## Key Features

**Interactive Ambiguity Resolution**
- LLM identifies unclear points
- Chain-of-thought reasoning displayed
- User provides clarifications inline

**Handoff Mechanism**
- Detects missing agent_knowledge/
- Triggers CodeUnderstandingAgent
- Waits for codebase analysis completion

**Context-Aware Planning**
- Reuses imports_understanding.md
- References central_understanding.md
- Plans based on existing architecture

## File Structure

```
agents/
  └── planning_agent/
      ├── agent.py                         # Sequential orchestrator
      ├── tools/
      │   ├── requirement_analyzer.py      # LLM: classification
      │   ├── ambiguity_resolver.py        # HITL: interactive
      │   ├── codebase_context_manager.py  # Load agent_knowledge/
      │   ├── plan_generator.py            # LLM: implementation plan
      │   └── discussion_facilitator.py    # HITL: new feature dialog
      └── models/
          └── schemas.py                   # Pydantic models
```
