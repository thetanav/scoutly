import asyncio
import time
from utils.scraper import use_scraper, use_search
from utils.ai import extract_search_keywords, ai_finder, ai_main


async def main():
    # Get user input - only the prompt
    user_prompt = input("❓ Enter your research question: ").strip()

    if not user_prompt:
        print("❌ Please enter a question.")
        return

    current_time = time.time()

    # Print AI Configuration at startup
    print("\n" + "=" * 60)
    print("🤖 SCOUTLY RESEARCH AGENT - AI CONFIGURATION")
    print("=" * 60)
    print("📊 AI Models:")
    print("  • Embedding Model: embeddinggemma")
    print("  • LLM Model: minimax-m2.5:cloud")
    print("  • Vector Store: FAISS")
    print("  • Search Engine: DuckDuckGo")
    print("=" * 60 + "\n")

    print("🔍 Extracting search keywords...")
    search_keywords = await extract_search_keywords(user_prompt)
    print(f"📝 Using keywords: {', '.join(search_keywords)}")

    print("🌐 Searching for information...")
    search_results, search_time = await use_search(search_keywords)
    print(f"⏱️  Search completed in {search_time:.2f}s")

    print("📄 Scraping content...")
    folder_name = await use_scraper(search_results, search_time)

    # Use the keywords as topic for AI finder
    topic = " ".join(search_keywords)
    print("🧠 Processing documents and building knowledge base...")
    vectorstore = await ai_finder(folder_name, topic)

    print("🤖 Generating response...")
    response, sources = await ai_main(vectorstore, user_prompt)

    print("\n" + "=" * 60)
    print("📄 RESPONSE")
    print("=" * 60)
    print(f"{response}")
    print("=" * 60)

    print("\n🔗 SOURCE DOCUMENTS:")
    for i, source in enumerate(sources, 1):
        print(f"  {i}. {source}")

    print("\n" + "=" * 60)
    print("🧠 AI METADATA USED")
    print("=" * 60)
    print("📊 Configuration:")
    print("  • Embedding Model: embeddinggemma")
    print("  • LLM Model: minimax-m2.5:cloud")
    print("  • Vector Store: FAISS")
    print("  • Vector DB Path: Managed in memory")
    print("  • Chunk Size: 1000 tokens")
    print("  • Chunk Overlap: 200 tokens")
    print("  • Retrieval K: 5 documents")
    print("=" * 60)
    print(f"\n⏱️  Total Completed in {time.time() - current_time:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
