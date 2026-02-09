import asyncio
import concurrent.futures
from ddgs import DDGS
import time


async def use_search(queries: list[str]) -> list[dict]:
    """Search using DuckDuckGo and return results as dicts."""
    ddgs = DDGS()
    loop = asyncio.get_event_loop()
    t1 = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, lambda q=q: ddgs.text(q, max_results=3))
            for q in queries
        ]
        results_lists = await asyncio.gather(*tasks)
    t2 = time.time()
    # Flatten the list of lists into a single list
    all_results = [item for sublist in results_lists for item in sublist]
    # Convert to dicts
    search_results = [
        {"title": r["title"], "href": r["href"], "body": r.get("body")}
        for r in all_results
    ]
    return search_results, t2 - t1
