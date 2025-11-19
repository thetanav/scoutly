import asyncio
import time
from utils.scraper import use_scraper
from utils.search import use_search
from utils.ai import extract_search_keywords, ai_finder, ai_main


async def main():
    # Get user input - only the prompt
    user_prompt = input("Enter your research question: ").strip()
    
    if not user_prompt:
        print("Please enter a question.")
        return
    
    current_time = time.time()
    
    print("Extracting search keywords...")
    search_keywords = await extract_search_keywords(user_prompt)
    print(f"Using keywords: {', '.join(search_keywords)}")
    
    print("Searching for information...")
    search_results = await use_search(search_keywords)
    
    print("Scraping content...")
    folder_name = await use_scraper(search_results)
    
    print("Extracting important information...")
    # Use the keywords as topic for AI finder
    topic = ' '.join(search_keywords)
    important_info = await ai_finder(folder_name, topic)
    
    print("Generating response...")
    response = await ai_main(important_info, user_prompt)
    
    print(f"\nResponse:\n{response}")
    print(f"\n[INFO] Completed in {time.time() - current_time:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
