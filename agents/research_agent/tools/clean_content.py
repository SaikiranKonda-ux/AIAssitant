from typing import Annotated
from openai import AzureOpenAI
from ..models.schemas import FetchedContent, CleanedContent


def clean_content(
    fetched_content: Annotated[FetchedContent, "Fetched content to clean"],
    original_query: Annotated[str, "Original user query for filtering relevance"],
    azure_client: Annotated[AzureOpenAI, "Azure OpenAI client instance"]
) -> CleanedContent:
    """
    Use LLM to remove noise and extract only relevant information from content
    """
    if not fetched_content.success or not fetched_content.content:
        return CleanedContent(
            url=fetched_content.url,
            title=fetched_content.title,
            relevant_text="",
            key_points=[],
            interpretation_id=fetched_content.interpretation_id,
            confidence=0.0
        )

    content_preview = fetched_content.content[:4000]

    system_prompt = """You are a content cleaning expert. Extract only information relevant to the query.
Remove: ads, navigation, boilerplate, irrelevant sections.
Keep: facts, data, explanations directly related to the query.
Extract key points as bullet list."""

    user_prompt = f"""Original query: "{original_query}"

Content from: {fetched_content.title}
URL: {fetched_content.url}

Content:
{content_preview}

Extract relevant information and return JSON with:
- url: "{fetched_content.url}"
- title: "{fetched_content.title}"
- relevant_text: cleaned text with only relevant information
- key_points: array of 3-7 key facts/points
- interpretation_id: {fetched_content.interpretation_id}
- confidence: 0.0-1.0 score for how relevant this content is

If content is not relevant, return confidence < 0.5."""

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

    return CleanedContent(
        url=fetched_content.url,
        title=fetched_content.title,
        relevant_text=result.get("relevant_text", ""),
        key_points=result.get("key_points", []),
        interpretation_id=fetched_content.interpretation_id,
        confidence=result.get("confidence", 0.0)
    )
