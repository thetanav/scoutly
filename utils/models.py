from pydantic import BaseModel
from typing import List, Optional


class SearchResult(BaseModel):
    title: str
    href: str
    body: Optional[str] = None


class ScrapedContent(BaseModel):
    url: str
    title: str
    content: str


class ResearchQuery(BaseModel):
    queries: List[str]


class DeepResearchResult(BaseModel):
    query: str
    search_results: List[SearchResult]
    scraped_contents: List[ScrapedContent]
    summary: Optional[str] = None
    analysis: Optional[str] = None