import asyncio
import concurrent.futures
from ddgs import DDGS


async def use_search(queries: list[str]) -> list[dict]:
    """Search using DuckDuckGo and return results as dicts."""
    ddgs = DDGS()
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, lambda q=q: ddgs.text(q, max_results=3))
            for q in queries
        ]
        results_lists = await asyncio.gather(*tasks)
    # Flatten the list of lists into a single list
    all_results = [item for sublist in results_lists for item in sublist]
    # Convert to dicts
    search_results = [
        {"title": r["title"], "href": r["href"], "body": r.get("body")}
        for r in all_results
    ]
    return search_results
