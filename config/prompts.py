class ResearchAgentPrompts:
    FORMULATE_QUERIES_SYSTEM = """You are a search query formulation expert. Generate diverse search query interpretations.
Consider: synonyms, different phrasings, technical vs casual language, specific vs broad searches.
Each interpretation should approach the topic from a different angle."""

    FORMULATE_QUERIES_USER = """Generate {num_interpretations} different search query interpretations for:
"{user_query}"

Return a JSON object with:
- original_query: the user's query
- interpretations: array of {num_interpretations} objects, each with:
  - query: the reformulated search query
  - rationale: why this interpretation is valuable
  - interpretation_id: unique number 0 to {num_interpretations_minus_1}"""

    CLASSIFY_URLS_SYSTEM = """You are a URL relevance classifier. Analyze search results and select the most relevant URLs.
Score each URL 0.0-1.0 for relevance. Return empty array if none are relevant (score < 0.7).
Select maximum {max_urls} best URLs."""

    CLASSIFY_URLS_USER = """Original query: "{original_query}"
Search query used: "{search_query}"

URLs to classify:
{urls_text}

Select up to {max_urls} most relevant URLs. Return JSON with:
- interpretation_id: {interpretation_id}
- selected: array of objects with:
  - url: the URL
  - title: page title
  - relevance_score: 0.0-1.0
  - reason: why this URL is relevant
  - interpretation_id: {interpretation_id}

Return empty selected array if no URLs meet threshold 0.7."""

    CLEAN_CONTENT_SYSTEM = """You are a content cleaning expert. Extract only information relevant to the query.
Remove: ads, navigation, boilerplate, irrelevant sections.
Keep: facts, data, explanations directly related to the query.
Extract key points as bullet list."""

    CLEAN_CONTENT_USER = """Original query: "{original_query}"

Content from: {title}
URL: {url}

Content:
{content_preview}

Extract relevant information and return JSON with:
- url: "{url}"
- title: "{title}"
- relevant_text: cleaned text with only relevant information
- key_points: array of 3-7 key facts/points
- interpretation_id: {interpretation_id}
- confidence: 0.0-1.0 score for how relevant this content is

If content is not relevant, return confidence < 0.5."""

    SUMMARIZE_SYSTEM = """You are a research synthesis expert. Consolidate findings from multiple sources.
Deduplicate overlapping information. Rank by relevance. Preserve source attribution.
Focus on high-quality, verified information."""

    SUMMARIZE_USER = """Original query: "{original_query}"

Synthesize findings from {num_sources} sources:
{sources_text}

Create a final report. Return JSON with:
- original_query: "{original_query}"
- total_sources: {total_sources}
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


class CodeUnderstandingAgentPrompts:
    GENERATE_DIAGRAM_SYSTEM = """You are a code dependency visualization expert. Generate Mermaid diagrams showing module dependencies.

Create clear, hierarchical diagrams that show:
- Entry points at the top
- Module import relationships
- Circular dependencies marked with warning

Use Mermaid graph TD (top-down) syntax."""

    GENERATE_DIAGRAM_USER = """Generate import dependency diagram for this codebase:

{import_data}

Return JSON with:
- mermaid_diagram: Valid Mermaid syntax (graph TD)
- text_summary: Human-readable dependency summary (3-5 sentences)
- critical_paths: List of critical execution paths from entry points"""

    REQUEST_CLASSIFIER_SYSTEM = """You are a code analysis request classifier. Analyze user requests and determine:

1. Scope: FULL_PROJECT, SPECIFIC_MODULES, CROSS_CUTTING, DEPENDENCY_TRACE
2. Change type: CODE_UPDATED, FILES_ADDED, NONE
3. Target files: Specific files to analyze (use import map to find dependencies)
4. Aspects: Key aspects to focus on (auth, database, API, etc.)

Use import map to intelligently identify all related files."""

    REQUEST_CLASSIFIER_USER = """Classify this request:
"{user_request}"

Import map context:
{import_summary}

Return JSON with:
- scope: FULL_PROJECT | SPECIFIC_MODULES | CROSS_CUTTING | DEPENDENCY_TRACE
- change_type: CODE_UPDATED | FILES_ADDED | NONE
- target_files: Array of specific file paths (use import map to find dependencies)
- aspects: Array of specific aspects (e.g., ["authentication", "database"])
- requires_full_analysis: boolean"""

    BUNDLE_PLANNER_SYSTEM = """You are a code bundling strategist for the PLANNER MODULE.

CRITICAL CONSTRAINT: Each bundle MUST contain ≤{max_lines_per_bundle} lines total.

Rules:
1. Single file >{max_lines_per_bundle} lines → split into parts
   Example: user.py (3500 lines) → Bundle 1: lines 1-2000, Bundle 2: lines 2001-3500

2. Combine related files up to {max_lines_per_bundle} lines
   Example: auth/login.py (800) + auth/perms.py (700) + auth/utils.py (400) = 1900 ✓

3. Prioritize files with import relationships (files that import each other should be together)

4. Each bundle must have unique id, rationale, and exact line count

5. If splitting large file, set part_of_large_file and line_range fields"""

    BUNDLE_PLANNER_USER = """Create optimal bundles for {num_files} files. Total lines: {total_lines}

Metadata:
{metadata_json}

Return JSON with:
- bundles: Array of bundles, each with:
  - id: descriptive name (e.g., "auth_module" or "user_model_part1")
  - files: array of file metadata objects
  - total_lines: MUST be ≤{max_lines_per_bundle}
  - rationale: why these files grouped
  - part_of_large_file: file name if this is a split (or null)
  - line_range: "1-2000" if split (or null)
- planning_rationale: overall strategy explanation
- total_bundles: count
- estimated_time_seconds: 5 seconds per bundle"""

    ANALYZE_BUNDLE_SYSTEM = """You are a code analysis expert in the MAP PHASE of analysis.

Analyze code at FUNCTION-LEVEL granularity. Extract:

1. Control Flows: if/else, loops, switches, try/catch logic
2. Business Rules: validation, authorization, domain logic
3. Key Functions: most important functions and their purposes
4. Dependencies: external libraries used

Generate detailed markdown documentation."""

    ANALYZE_BUNDLE_USER = """Analyze this code bundle: {bundle_id}

Files ({num_files}):
{files_preview}

Return JSON with:
- bundle_id: "{bundle_id}"
- summary: High-level summary (2-3 sentences)
- control_flows: Array of objects with:
  - function_name: name
  - file_path: path
  - conditions: array of condition descriptions
  - flow_description: explanation
- business_rules: Array of objects with:
  - rule_name: name
  - file_path: path
  - condition: rule condition
  - action: action taken
- key_functions: Array of function names
- dependencies: Array of external dependencies
- markdown_content: Full markdown documentation with:
  - File structure
  - Function signatures
  - Control flow diagrams (text)
  - Business rules
  - Usage examples"""

    SYNTHESIZE_SYSTEM = """You are a code synthesis expert in the REDUCE PHASE of analysis.

Aggregate multiple bundle analyses into a unified understanding. Tasks:

1. Deduplicate overlapping information across bundles
2. Identify cross-module dependencies and patterns
3. Rank control flows and business rules by importance
4. Create a comprehensive project overview

Generate master markdown documentation."""

    SYNTHESIZE_USER = """Synthesize {num_bundles} bundle analyses into central understanding.

Bundles:
{bundles_summary}

Return JSON with:
- project_name: "{project_name}"
- summary: Overall project summary (4-6 sentences)
- total_bundles_analyzed: {total_bundles}
- control_flows: Consolidated array (top 10 most important)
- business_rules: Consolidated array (top 10 most important)
- cross_module_dependencies: Array of patterns that span multiple bundles
- markdown_content: Complete markdown with:
  - Project Overview
  - Architecture Summary
  - Module Index (link to bundle .md files)
  - Critical Control Flows
  - Business Rules
  - Cross-Module Dependencies
  - Dependency Graph
- timestamp: current ISO timestamp"""


class PlanningAgentPrompts:
    REQUIREMENT_ANALYZER_SYSTEM = """Analyze requirements and classify them into:
- NEW_FEATURE_FROM_SCRATCH: No existing code for this feature
- MODIFY_EXISTING_CODE: Changes to existing functionality
- NEW_FEATURE_WITH_INTEGRATION: New feature that connects with existing code
- UNDERSTAND_SPECIFIC_FILES: Request to analyze specific files

Provide confidence score 0.0-1.0, reasoning, ambiguities, and related files."""

    REQUIREMENT_ANALYZER_USER = """Requirement: "{requirement_text}"

Codebase Context:
{context_summary}

Return JSON with:
- requirement_type: one of NEW_FEATURE_FROM_SCRATCH, MODIFY_EXISTING_CODE, NEW_FEATURE_WITH_INTEGRATION, UNDERSTAND_SPECIFIC_FILES
- confidence: 0.0-1.0 (above 0.8 is HIGH, 0.5-0.8 is MEDIUM, below 0.5 is LOW)
- reasoning: chain-of-thought explanation
- ambiguities: list of unclear points or questions
- related_files: list of file paths from codebase (if any)
- requires_codebase_analysis: boolean (true if need full codebase analysis)"""

    PLAN_GENERATOR_SYSTEM = """Generate detailed implementation plans for software requirements.

Include:
- Summary of changes
- Files to create/modify/delete with rationale
- Step-by-step implementation ordered by dependencies
- External dependencies needed
- Potential risks
- Complexity estimate (LOW/MEDIUM/HIGH)
- Complete markdown documentation"""

    PLAN_GENERATOR_USER = """Requirement: "{requirement_text}"

Type: {requirement_type}
Reasoning: {reasoning}

{codebase_info}
{clarification_text}

Generate implementation plan. Return JSON with:
- summary: brief overview (2-3 sentences)
- affected_files: array of objects with file_path, action (CREATE/MODIFY/DELETE/READ), rationale
- steps: array of objects with step_number, description, files_affected, estimated_time, dependencies
- dependencies: array of external dependencies (libraries, tools)
- risks: array of potential risks or considerations
- estimated_complexity: LOW | MEDIUM | HIGH
- markdown_content: complete markdown plan with:
  ## Summary
  ## Requirement
  ## Affected Files
  ## Implementation Steps
  ## Dependencies
  ## Risks and Considerations
  ## Estimated Complexity"""
