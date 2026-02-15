import os
import httpx
import asyncio
import trafilatura
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import uuid
import time
from ddgs import DDGS

# Shared thread pool for CPU-bound work (trafilatura parsing, file I/O)
_executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-scraper/1.0)"}


def write_sources(folder_name: str, sources: list[dict]) -> None:
    """Write SOURCES.md with all source URLs and titles."""
    filepath = os.path.join(folder_name, "SOURCES.md")

    # Load existing sources if file exists
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Parse existing entries to avoid duplicates
        for line in content.split("\n"):
            if line.startswith("- URL: "):
                existing.append(line.split("- URL: ")[1].strip())

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Sources\n\n")
        f.write(f"_Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}_\n\n")

        seen_urls = set(existing)
        idx = 1

        # Write existing first
        for url in existing:
            f.write(f"## Source {idx}\n")
            f.write(f"- URL: {url}\n\n")
            idx += 1

        # Write new sources
        for source in sources:
            url = source.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = source.get("title", "Unknown")
            file_ref = source.get("file", "")
            source_type = source.get("type", "webpage")

            f.write(f"## Source {idx}\n")
            f.write(f"- Title: {title}\n")
            f.write(f"- URL: {url}\n")
            f.write(f"- Type: {source_type}\n")
            if file_ref:
                f.write(f"- File: {file_ref}\n")
            f.write("\n")
            idx += 1


async def download_pdf(url: str, folder_name: str, index: int) -> bool:
    """Download a PDF file to the folder."""
    try:
        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        ) as session:
            response = await session.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                return False

            filepath = os.path.join(folder_name, f"{index}.pdf")
            with open(filepath, "wb") as f:
                f.write(response.content)
            return True
    except Exception:
        return False


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
    loop = asyncio.get_event_loop()

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

    # Parse HTML in parallel using thread pool (trafilatura is CPU-bound)
    async def extract_async(url: str, html: Optional[str]) -> tuple[str, Optional[str]]:
        if not html:
            return url, None
        text = await loop.run_in_executor(_executor, extract_text, html)
        return url, text if text else None

    extract_tasks = [extract_async(url, html) for url, html in html_results]
    parsed_results = await asyncio.gather(*extract_tasks)

    for url, text in parsed_results:
        results[url] = text

    return results


async def use_scraper(
    search_results: list[dict],
    st: float,
    folder_name: str | None = None,
    start_index: int | None = None,
) -> tuple[str, int]:
    """Scrape URLs and save to files with performance optimizations.

    Args:
        search_results: List of search result dicts with 'href' key
        st: Search time for display
        folder_name: Optional existing folder to append to (for incremental scraping)
        start_index: Starting index for file naming (continues from previous if folder_name provided)

    Returns:
        tuple of (folder_name, next_available_index)
    """
    loop = asyncio.get_event_loop()

    if folder_name is None:
        folder_name = f"scraped/{uuid.uuid4().hex[:8]}"
        start_index = 1
    else:
        existing = [
            f
            for f in os.listdir(folder_name)
            if f.endswith(".md") and f.startswith("RES_")
        ]
        start_index = len(existing) + 1

    os.makedirs(folder_name, exist_ok=True)

    urls = [result["href"] for result in search_results]
    titles = {result["href"]: result.get("title", "") for result in search_results}

    print(f"\n📋 Found {len(urls)} pages in {st:.2f}s:")
    for i, url in enumerate(urls, 1):
        display_url = url[:70] + "..." if len(url) > 70 else url
        print(f"  {i}. {display_url}")

    t1 = time.time()
    print("⏳ Fetching and parsing pages...")
    texts = await scrape_urls(urls)

    # Write files in parallel using thread pool and track sources
    successful_scrapes = 0
    failed_scrapes = 0
    sources = []

    def write_file(filepath: str, content: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    write_futures = []
    file_metadata = []  # Track (url, index) for each write task

    for i, (url, text) in enumerate(texts.items(), start_index):
        if text:
            filepath = os.path.join(folder_name, f"RES_{i}.md")
            write_futures.append(
                loop.run_in_executor(_executor, write_file, filepath, text)
            )
            file_metadata.append((url, i))
        else:
            failed_scrapes += 1

    # Await all file writes concurrently
    if write_futures:
        write_results = await asyncio.gather(*write_futures)
        for (url, idx), success in zip(file_metadata, write_results):
            if success:
                successful_scrapes += 1
                sources.append(
                    {
                        "url": url,
                        "title": titles.get(url, ""),
                        "file": f"RES_{idx}.md",
                        "type": "webpage",
                    }
                )
            else:
                failed_scrapes += 1

    # Write SOURCES.md
    write_sources(folder_name, sources)

    t2 = time.time()
    scrape_time = t2 - t1
    avg_time = scrape_time / len(urls) if urls else 0

    print("\n✅ Scraping Performance:")
    print(f"  • Successfully processed: {successful_scrapes}/{len(urls)} pages")
    print(f"  • Failed/Empty: {failed_scrapes}/{len(urls)} pages")
    print(f"  • Total time: {scrape_time:.2f}s")
    print(f"  • Average per page: {avg_time:.2f}s")
    print(f"  • Speed: {len(urls) / scrape_time:.1f} pages/second\n")

    next_index = start_index + successful_scrapes
    return folder_name, next_index


async def use_search(
    queries: list[str],
    search_type: str = "general",
    max_results_per_query: int = 5,
) -> tuple[list[dict], float]:
    """Search using DuckDuckGo with intelligent query optimization.

    Args:
        queries: List of search queries
        search_type: Type of search (general, academic, news, comparison, how-to)
        max_results_per_query: Number of results per query

    Returns:
        tuple of (list of result dicts, search time in seconds)
    """
    ddgs = DDGS()
    t1 = time.time()

    # Add search type modifiers to improve results
    query_modifiers = {
        "general": "",
        "academic": " scholarly article",
        "news": " latest news 2025",
        "comparison": " vs comparison review",
        "how-to": " guide tutorial",
    }

    # Expand queries with modifiers and variations
    expanded_queries = []
    for query in queries:
        modifier = query_modifiers.get(search_type, "")
        # Original query
        expanded_queries.append(query)
        # With modifier
        if modifier:
            expanded_queries.append(query + modifier)

    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in expanded_queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique_queries.append(q)

    async def search_single(query: str) -> list:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: ddgs.text(query, max_results=max_results_per_query)
        )

    # Run searches concurrently
    results_lists = await asyncio.gather(*[search_single(q) for q in unique_queries])

    t2 = time.time()

    # Deduplicate results by URL
    seen_urls = set()
    unique_results = []

    for sublist in results_lists:
        for r in sublist:
            url = r.get("href", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(
                    {
                        "title": r.get("title", ""),
                        "href": url,
                        "body": r.get("body", ""),
                    }
                )

    return unique_results, t2 - t1


async def search_pdfs(queries: list[str], folder_name: str, max_pdfs: int = 1) -> int:
    """Search for PDFs and download them concurrently.

    Args:
        queries: List of search queries with "filetype:pdf" appended
        folder_name: Folder to save PDFs
        max_pdfs: Maximum number of PDFs to download

    Returns:
        Number of PDFs downloaded
    """
    pdf_queries = [f"{q} filetype:pdf" for q in queries]
    loop = asyncio.get_event_loop()

    # Search all queries in parallel using thread pool
    ddgs = DDGS()

    async def search_single_pdf(query: str) -> list:
        try:
            return await loop.run_in_executor(
                _executor, lambda: ddgs.text(query, max_results=3)
            )
        except Exception:
            return []

    all_results = await asyncio.gather(*[search_single_pdf(q) for q in pdf_queries])

    # Collect unique PDF URLs
    pdf_urls = []
    seen = set()
    for results in all_results:
        for r in results:
            href = r.get("href", "")
            if (
                href
                and href not in seen
                and (href.lower().endswith(".pdf") or "pdf" in href.lower())
            ):
                seen.add(href)
                pdf_urls.append(href)
                if len(pdf_urls) >= max_pdfs:
                    break
        if len(pdf_urls) >= max_pdfs:
            break

    pdf_urls = pdf_urls[:max_pdfs]

    if not pdf_urls:
        return 0

    print(f"\n📄 Found {len(pdf_urls)} PDF(s), downloading...")

    # Download all PDFs concurrently
    download_tasks = [
        download_pdf(url, folder_name, i) for i, url in enumerate(pdf_urls, 1)
    ]
    download_results = await asyncio.gather(*download_tasks)

    downloaded = 0
    pdf_sources = []
    for i, (url, success) in enumerate(zip(pdf_urls, download_results), 1):
        if success:
            downloaded += 1
            pdf_sources.append(
                {
                    "url": url,
                    "title": url.split("/")[-1],
                    "file": f"{i}.pdf",
                    "type": "pdf",
                }
            )
            print(f"  ✓ Downloaded: {url[:60]}...")

    # Write PDF sources to SOURCES.md
    if pdf_sources:
        write_sources(folder_name, pdf_sources)

    print(f"✅ Downloaded {downloaded} PDF(s)\n")
    return downloaded
