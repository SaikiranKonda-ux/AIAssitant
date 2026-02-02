import sys
from pathlib import Path
from typing import Annotated
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config.prompts import ResearchAgentPrompts
from agents.research_agent.models.schemas import QueryFormulations, SearchInterpretation


def formulate_queries(
    user_query: Annotated[str, "Original user query to reformulate"],
    azure_client: Annotated[AzureOpenAI, "Azure OpenAI client instance"],
    deployment_name: Annotated[str, "Azure OpenAI deployment name"],
    num_interpretations: Annotated[int, "Number of interpretations to generate"] = 3
) -> QueryFormulations:
    system_prompt = ResearchAgentPrompts.FORMULATE_QUERIES_SYSTEM

    user_prompt = ResearchAgentPrompts.FORMULATE_QUERIES_USER.format(
        num_interpretations=num_interpretations,
        user_query=user_query,
        num_interpretations_minus_1=num_interpretations-1
    )

    response = azure_client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7
    )

    import json
    result = json.loads(response.choices[0].message.content)

    interpretations = []
    for i, interp in enumerate(result.get("interpretations", [])):
        interpretations.append(SearchInterpretation(
            query=interp.get("query", ""),
            rationale=interp.get("rationale", ""),
            interpretation_id=i
        ))

    return QueryFormulations(
        original_query=user_query,
        interpretations=interpretations
    )
