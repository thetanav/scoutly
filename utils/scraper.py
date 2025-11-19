import os
import time
import httpx
import asyncio
from typing import Optional
from selectolax.parser import HTMLParser
import uuid


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
                results[url] = extract_text(html)[:1000]  # Limit to 500 chars

    return results


async def use_scraper(search_results: list[dict]) -> str:
    """Scrape URLs and save to files in a unique folder."""
    folder_name = f"scraped/{uuid.uuid4().hex[:8]}"
    os.makedirs(folder_name, exist_ok=True)
    
    urls = [result['href'] for result in search_results]
    texts = await scrape_urls(urls)
    
    for i, (url, text) in enumerate(texts.items()):
        if text:
            filename = f"{i+1}.txt"
            filepath = os.path.join(folder_name, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
    
    return folder_name
