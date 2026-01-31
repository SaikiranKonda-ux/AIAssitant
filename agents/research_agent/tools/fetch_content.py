from typing import Annotated
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..models.schemas import FetchedContent


def fetch_webpage_text(url: str) -> str:
    """
    Fetch and extract clean text from a webpage
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)

    except Exception as e:
        return f"Error fetching content: {str(e)}"


def fetch_content(
    url: Annotated[str, "URL to fetch content from"],
    title: Annotated[str, "Page title"],
    interpretation_id: Annotated[int, "Interpretation ID this URL belongs to"]
) -> FetchedContent:
    """
    Fetch full content from a URL and return structured result
    """
    content = fetch_webpage_text(url)

    is_error = content.startswith("Error fetching content:")

    return FetchedContent(
        url=url,
        title=title,
        content=content,
        fetch_timestamp=datetime.now().isoformat(),
        interpretation_id=interpretation_id,
        success=not is_error,
        error=content if is_error else None
    )
