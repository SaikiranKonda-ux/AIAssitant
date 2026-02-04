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

---

# Critic Agent

## Pattern: Reflection with Bounded Iterations

## Installation

Included with core dependencies.

## Usage

```python
import asyncio
from agents.critic_agent import CriticAgent
from agents.planning_agent import PlanningAgent

async def main():
    planning_agent = PlanningAgent()
    critic_agent = CriticAgent(max_iterations=2)

    plan = await planning_agent.analyze_requirement(
        requirement_text="Add OAuth authentication",
        code_directory="/path/to/project"
    )

    refined_plan, critiques = await critic_agent.review(
        implementation_plan=plan,
        codebase_context=None,
        auto_refine=False
    )

    print(f"Assessment: {critiques[-1].overall_assessment.value}")
    print(f"Concerns: {len(critiques[-1].concerns)}")

asyncio.run(main())
```

## Pattern: Reflection (Max 2-3 Iterations)

### PHASE 1: Evaluation
```
1. evaluate_plan(): LLM analyzes implementation plan
   - Feasibility, completeness, security (OWASP)
   - Performance, best practices, error handling
   - Testing, rollback capability
   - Returns CritiqueFeedback
```

### PHASE 2: Decision
```
2. Assessment Levels:
   - APPROVED: Plan is good, proceed
   - NEEDS_REVISION: Issues found, should refine
   - MAJOR_CONCERNS: Critical problems, must address

3. If APPROVED or max_iterations reached → Return
   Otherwise → Continue to Refinement
```

### PHASE 3: Refinement (Optional)
```
4. HITL: User decides whether to refine
5. refine_plan(): LLM improves plan based on critique
6. Loop back to PHASE 1 (max 2-3 iterations)
```

## Conditional Activation

```python
should_trigger = critic_agent.should_trigger_critique(plan)

# Triggers if:
# - Complexity: MEDIUM or HIGH
# - Affected files: > 5
# - Risks: > 3
```

## Output: CritiqueFeedback

- overall_assessment: APPROVED/NEEDS_REVISION/MAJOR_CONCERNS
- confidence_score: 0.0-1.0
- strengths: Positive aspects
- concerns: Issues with severity (LOW/MEDIUM/HIGH/CRITICAL)
- alternative_approaches: Different solutions with pros/cons
- security_issues: OWASP vulnerabilities
- performance_concerns: Scalability issues
- recommended_changes: Specific improvements

---

# Code Writing Agent

## Pattern: Executor with Safety Mechanisms

## Installation

Included with core dependencies.

## Usage

```python
import asyncio
from agents.code_writing_agent import CodeWritingAgent
from agents.planning_agent import PlanningAgent

async def main():
    planning_agent = PlanningAgent()
    code_agent = CodeWritingAgent(code_directory="/path/to/project")

    plan = await planning_agent.analyze_requirement(
        requirement_text="Add logging middleware",
        code_directory="/path/to/project"
    )

    code_change = await code_agent.execute_plan(
        implementation_plan=plan,
        interactive=True,
        auto_commit=False
    )

    print(code_change.summarize())

asyncio.run(main())
```

## Safety Layers

### 1. Backup Before Modification
```
BackupManager:
- create_backup(): Copy with timestamp + MD5 checksum
- Stores in .code_agent_backups/
- restore_from_backup(): Verified restoration
```

### 2. Syntax Validation
```
SyntaxValidator:
- validate_python(): AST parsing
- validate_json(): JSON parsing
- validate_by_extension(): Route by file type
- Pre-write validation prevents invalid code
```

### 3. User Approval (HITL)
```
Interactive Mode:
- Show file preview (first 500 chars)
- Display syntax errors if any
- Explicit yes/no for each file
- Only apply if all approved
```

### 4. Git Integration
```
GitIntegration:
- stage_files(): Add to git
- commit(): Create commit with SHA
- rollback_to_commit(): Full rollback
- Rollback available if committed
```

## Execution Flow

1. prepare_modification(): For each file
   - Create backup (MODIFY/DELETE only)
   - Validate syntax
   - Return FileModification object

2. HITL Approval Loop (interactive mode)
   - Show diff and preview
   - User approves each file

3. apply_modification(): Execute changes
   - Write files
   - Track created/modified/deleted counts
   - Auto-rollback on error

4. Git Commit (optional)
   - HITL: User chooses whether to commit
   - Auto-commit mode available
   - Returns commit SHA for rollback

## Rollback

```python
# Git-based rollback (preferred)
success = code_agent.rollback(code_change)

# File-based rollback (fallback)
# Automatically attempts if git rollback fails
```

---

# Orchestrator Manager

## Pattern: Magentic-Inspired with Conditional Routing

## Installation

Included with core dependencies.

## Usage

```python
import asyncio
from orchestrator import OrchestratorManager

async def main():
    orchestrator = OrchestratorManager(
        max_rounds=10,
        max_stalls=3
    )

    result = await orchestrator.execute(
        user_requirement="Add user authentication with JWT tokens",
        code_directory="/path/to/project",
        interactive=True
    )

    print(f"Final State: {result.workflow_state.value}")
    print(f"Total Rounds: {result.round_count}")
    print(result.final_output)

asyncio.run(main())
```

## Orchestration Flow

### PHASE 1: Task Classification
```
1. classify_task(): LLM analyzes requirement
   - Returns: task_type, complexity, risk, agent needs
   - Confidence scoring (0.0-1.0)
```

### PHASE 2: Workflow Planning
```
2. plan_workflow_hybrid(): Conditional routing
   
   Rule-Based (80% of cases):
   - HIGH confidence + LOW complexity
   - Fast, deterministic
   - Example: [planning, code_writing]
   
   LLM-Based (20% of cases):
   - LOW confidence or HIGH complexity
   - Flexible, intelligent
   - Example: [research, code_understanding, planning, critic, code_writing]
```

### PHASE 3: Cost Estimation & Approval
```
3. estimate_task_cost(): Calculate time/cost
4. HITL: User approves workflow (interactive mode)
```

### PHASE 4: Workflow Execution
```
5. For each agent in workflow:
   a. Start agent invocation tracking
   b. Execute agent with shared context
   c. Update shared context with results
   d. Check for stall
   e. HITL intervention if stalled (interactive mode)
```

### PHASE 5: Completion
```
6. Set final state (COMPLETED or FAILED)
7. Generate final output summary
```

## Conditional Routing Examples

**Simple (LOW complexity):**
```
Workflow: [planning, code_writing]
Time: 5 min
Cost: $0.18
```

**Medium (MEDIUM complexity):**
```
Workflow: [planning, critic, code_writing]
Time: 10 min
Cost: $0.30
```

**Complex (HIGH complexity or NEW_FEATURE):**
```
Workflow: [research, code_understanding, planning, critic, code_writing]
Time: 15 min
Cost: $0.70
```

## Stall Detection

```
StallDetector checks for:
1. Max stalls limit (default 3)
2. Consecutive agent failures (2+ in last 3)
3. Workflow state repetition (≥5 iterations)
4. Lack of progress (no outputs generated)

Recovery Actions (HITL):
- Continue: Ignore stall, proceed
- Skip: Skip current agent
- Retry: Re-run failed agent
- Abort: Terminate workflow
```

## Shared Context

State passed between all agents:
- requirement_text, code_directory
- task_classification
- research_findings, codebase_context
- implementation_plan, critique_feedback
- code_changes
- conversation_history
- agent_invocations
- workflow_state, round_count, stall_count

## File Structure

```
orchestrator/
  ├── manager.py              # Main orchestrator
  ├── models/
  │   └── task_classification.py
  └── tools/
      ├── task_classifier.py
      ├── workflow_planner.py
      ├── cost_estimator.py
      ├── stall_detector.py
      └── hitl_gates.py
```

---

# Complete Workflow Example

```python
import asyncio
from orchestrator import OrchestratorManager

async def main():
    orchestrator = OrchestratorManager(max_rounds=10, max_stalls=3)
    
    result = await orchestrator.execute(
        user_requirement="Add rate limiting middleware to prevent API abuse",
        code_directory="/path/to/my/api/project",
        interactive=True
    )
    
    if result.workflow_state.value == "COMPLETED":
        print("Success!")
        print(f"Agents used: {[inv.agent_name for inv in result.agent_invocations]}")
        print(f"Total cost: ${result.estimated_cost:.2f}")
        print(result.final_output)
    else:
        print(f"Failed: {result.current_step}")

asyncio.run(main())
```

**Expected Flow:**
1. Classify task → MEDIUM complexity, CODE_MODIFICATION
2. Plan workflow → [planning, critic, code_writing]
3. User approves workflow
4. Planning Agent → Creates implementation plan
5. Critic Agent → Reviews plan (2 iterations, refined)
6. User approves refined plan
7. Code Writing Agent → Modifies files with HITL approval
8. Git commit → User approves commit
9. Complete → Returns CodeChange summary
