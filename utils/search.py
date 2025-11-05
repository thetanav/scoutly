import asyncio
import concurrent.futures
from ddgs import DDGS

ddgs = DDGS()


async def use_search(queries: list[str]) -> list[dict[str, str]]:
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, lambda q=q: ddgs.text(q, max_results=5))
            for q in queries
        ]
        results_lists = await asyncio.gather(*tasks)
    # Flatten the list of lists into a single list
    all_results = [item for sublist in results_lists for item in sublist]
    return all_results
