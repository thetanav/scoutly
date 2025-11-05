import asyncio
import time
from scoutly.utils.scraper import use_scraper
from scoutly.utils.search import use_search


async def main():
    current_time = time.time()
    query = [
        "trophy controversy in asia cup",
        "india refuse to accept asia cup trophy",
        "what happened in asia cup",
    ]
    results = await use_search(query)
    await use_scraper(results)
    print(f"[INFO] Finished searching in {time.time() - current_time} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
