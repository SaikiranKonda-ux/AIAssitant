from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SearchInterpretation(BaseModel):
    query: str = Field(description="Reformulated search query")
    rationale: str = Field(description="Why this interpretation is relevant")
    interpretation_id: int = Field(description="Unique identifier for this interpretation")


class QueryFormulations(BaseModel):
    original_query: str = Field(description="User's original query")
    interpretations: List[SearchInterpretation] = Field(description="3-5 different search interpretations")


class URLResult(BaseModel):
    url: str = Field(description="URL of the search result")
    title: str = Field(description="Title of the page")
    snippet: str = Field(description="Brief description/snippet")
    interpretation_id: int = Field(description="Which interpretation this URL belongs to")


class SearchResults(BaseModel):
    interpretation_id: int = Field(description="Which interpretation was searched")
    query: str = Field(description="The search query used")
    urls: List[URLResult] = Field(description="List of URLs found (up to 10)")


class ClassifiedURL(BaseModel):
    url: str = Field(description="Selected URL")
    title: str = Field(description="Page title")
    relevance_score: float = Field(description="Relevance score 0.0-1.0")
    reason: str = Field(description="Why this URL was selected")
    interpretation_id: int = Field(description="Source interpretation")


class ClassifiedURLs(BaseModel):
    interpretation_id: int = Field(description="Which interpretation was classified")
    selected: List[ClassifiedURL] = Field(description="0-2 best URLs selected")


class FetchedContent(BaseModel):
    url: str = Field(description="URL of fetched content")
    title: str = Field(description="Page title")
    content: str = Field(description="Full text content extracted")
    fetch_timestamp: str = Field(description="When content was fetched")
    interpretation_id: int = Field(description="Source interpretation")
    success: bool = Field(description="Whether fetch was successful")
    error: Optional[str] = Field(default=None, description="Error message if fetch failed")


class CleanedContent(BaseModel):
    url: str = Field(description="Source URL")
    title: str = Field(description="Page title")
    relevant_text: str = Field(description="Cleaned, relevant text only")
    key_points: List[str] = Field(description="Key facts extracted")
    interpretation_id: int = Field(description="Source interpretation")
    confidence: float = Field(description="Confidence in relevance 0.0-1.0")


class ResearchResult(BaseModel):
    url: str = Field(description="Source URL")
    title: str = Field(description="Page title")
    summary: str = Field(description="Concise summary of content")
    key_facts: List[str] = Field(description="Key facts from this source")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    interpretation_source: str = Field(description="Which interpretation led to this result")


class FinalReport(BaseModel):
    original_query: str = Field(description="User's original query")
    total_sources: int = Field(description="Number of sources analyzed")
    results: List[ResearchResult] = Field(description="Research findings")
    timestamp: str = Field(description="When report was generated")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for inclusion")
