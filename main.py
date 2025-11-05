import asyncio
import time
from utils.scraper import use_scraper
from utils.search import use_search
from utils.ai import analyze_query


async def main():
    current_time = time.time()
    query = [
        "trophy controversy in asia cup",
        "india refuse to accept asia cup trophy",
        "what happened in asia cup",
    ]
    search_results = await use_search(query)
    scraped_contents = await use_scraper(search_results)
    result = await analyze_query(query[0], scraped_contents)
    result.search_results = search_results
    print(f"Summary: {result.summary}")
    print(f"[INFO] Finished searching in {time.time() - current_time} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
