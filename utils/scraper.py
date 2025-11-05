import os
import time
import httpx
import asyncio
from typing import Optional
from selectolax.parser import HTMLParser
from .models import SearchResult, ScrapedContent


async def fetch_html(url: str, session: httpx.AsyncClient) -> Optional[str]:
    """Fetch raw HTML from a single URL using httpx."""
    try:
        response = await session.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def extract_text(html: str) -> str:
    """Extract clean text from HTML using selectolax."""
    tree = HTMLParser(html)
    paragraphs = [node.text() for node in tree.css("p") if node.text()]
    return " ".join(paragraphs)


async def scrape_urls(urls: list[str]) -> dict[str, Optional[str]]:
    """Fetch and parse multiple URLs concurrently using httpx."""
    results = {}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as session:
        tasks = [fetch_html(url, session) for url in urls]
        html_pages = await asyncio.gather(*tasks)

        for url, html in zip(urls, html_pages):
            if html:
                results[url] = extract_text(html)[:200]

    return results


async def use_scraper(searchResults: list[SearchResult]) -> list[ScrapedContent]:
    scraped_contents = []
    urls = [result.href for result in searchResults]
    texts = await scrape_urls(urls)
    for url, text in texts.items():
        if text:
            # Find the corresponding search result
            matching_result = next((r for r in searchResults if r.href == url), None)
            if matching_result:
                scraped_content = ScrapedContent(
                    url=url,
                    title=matching_result.title,
                    content=text
                )
                scraped_contents.append(scraped_content)
    return scraped_contents
