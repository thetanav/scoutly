import os
import re
import httpx
import asyncio
import trafilatura
from typing import Optional
import uuid
import time
from ddgs import DDGS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-scraper/1.0)"}


def extract_text(html: str) -> str:
    """Extract clean text from HTML using trafilatura."""
    try:
        text = trafilatura.extract(html, output_format="markdown")
        return text if text else ""
    except Exception:
        return ""


async def fetch_html(url: str, session: httpx.AsyncClient) -> tuple[str, Optional[str]]:
    """Fetch raw HTML from a single URL using httpx with optimized settings."""
    try:
        response = await session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
            },
            timeout=8,
            follow_redirects=True,
        )
        response.raise_for_status()
        return url, response.text
    except Exception:
        return url, None


async def scrape_urls(urls: list[str]) -> dict[str, Optional[str]]:
    """Fetch and parse multiple URLs concurrently with optimized settings."""
    results = {}

    # Configure client with optimal settings for scraping
    limits = httpx.Limits(
        max_connections=30, max_keepalive_connections=15, keepalive_expiry=30.0
    )

    async with httpx.AsyncClient(
        timeout=8,
        follow_redirects=True,
        limits=limits,
        http2=True,  # Enable HTTP/2 for faster requests
    ) as session:
        # Fetch all URLs concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)

        async def fetch_with_limit(url):
            async with semaphore:
                return await fetch_html(url, session)

        fetch_tasks = [fetch_with_limit(url) for url in urls]
        html_results = await asyncio.gather(*fetch_tasks)

    # Parse HTML synchronously - selectolax is very fast, no need for thread pool
    for url, html in html_results:
        if html:
            text = extract_text(html)
            results[url] = text if text else None
        else:
            results[url] = None

    return results


async def use_scraper(search_results: list[dict], st: float) -> str:
    """Scrape URLs and save to files with performance optimizations."""
    folder_name = f"scraped/{uuid.uuid4().hex[:8]}"
    os.makedirs(folder_name, exist_ok=True)

    urls = [result["href"] for result in search_results]

    print(f"\n📋 Found {len(urls)} pages in {st:.2f}s:")
    for i, url in enumerate(urls, 1):
        display_url = url[:70] + "..." if len(url) > 70 else url
        print(f"  {i}. {display_url}")

    t1 = time.time()
    print("⏳ Fetching and parsing pages...")
    texts = await scrape_urls(urls)

    # Write files
    successful_scrapes = 0
    failed_scrapes = 0

    for i, (url, text) in enumerate(texts.items(), 1):
        if text:
            successful_scrapes += 1
            filepath = os.path.join(folder_name, f"{i}.txt")
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception:
                failed_scrapes += 1
        else:
            failed_scrapes += 1

    t2 = time.time()
    scrape_time = t2 - t1
    avg_time = scrape_time / len(urls) if urls else 0

    print(f"\n✅ Scraping Performance:")
    print(f"  • Successfully processed: {successful_scrapes}/{len(urls)} pages")
    print(f"  • Failed/Empty: {failed_scrapes}/{len(urls)} pages")
    print(f"  • Total time: {scrape_time:.2f}s")
    print(f"  • Average per page: {avg_time:.2f}s")
    print(f"  • Speed: {len(urls) / scrape_time:.1f} pages/second\n")

    return folder_name


async def use_search(queries: list[str]) -> tuple[list[dict], float]:
    """Search using DuckDuckGo and return results as dicts."""
    ddgs = DDGS()
    t1 = time.time()

    async def search_single(query: str) -> list:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: ddgs.text(query, max_results=5))

    # Run searches concurrently
    results_lists = await asyncio.gather(*[search_single(q) for q in queries])

    t2 = time.time()

    # Flatten and convert to dicts
    all_results = [item for sublist in results_lists for item in sublist]
    search_results = [
        {"title": r["title"], "href": r["href"], "body": r.get("body")}
        for r in all_results
    ]

    return search_results, t2 - t1
