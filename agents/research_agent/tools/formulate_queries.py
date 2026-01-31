from typing import Annotated
from openai import AzureOpenAI
from ..models.schemas import QueryFormulations, SearchInterpretation


def formulate_queries(
    user_query: Annotated[str, "Original user query to reformulate"],
    azure_client: Annotated[AzureOpenAI, "Azure OpenAI client instance"],
    num_interpretations: Annotated[int, "Number of interpretations to generate"] = 3
) -> QueryFormulations:
    """
    Generate 3-5 different search query interpretations using LLM
    """
    system_prompt = """You are a search query formulation expert. Generate diverse search query interpretations.
Consider: synonyms, different phrasings, technical vs casual language, specific vs broad searches.
Each interpretation should approach the topic from a different angle."""

    user_prompt = f"""Generate {num_interpretations} different search query interpretations for:
"{user_query}"

Return a JSON object with:
- original_query: the user's query
- interpretations: array of {num_interpretations} objects, each with:
  - query: the reformulated search query
  - rationale: why this interpretation is valuable
  - interpretation_id: unique number 0 to {num_interpretations-1}"""

    response = azure_client.chat.completions.create(
        model="gpt-4",
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
