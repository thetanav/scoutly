import streamlit as st
import asyncio
from utils.search import use_search
from utils.scraper import use_scraper
from utils.ai import analyze_query
from utils.models import ResearchQuery


def run_async(coro):
    """Helper to run async functions in Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


st.title("OSS Deep Researcher")

query_input = st.text_area("Enter your research queries (one per line):")

model_choice = st.selectbox("Choose AI Model for Analysis:", ["Ollama (Local)", "Gemini Flash", "OpenRouter (Free)"])

if st.button("Research"):
    if query_input:
        queries = [q.strip() for q in query_input.split('\n') if q.strip()]
        if queries:
            with st.spinner("Searching..."):
                search_results = run_async(use_search(queries))
            st.write(f"Found {len(search_results)} search results.")

            with st.spinner("Scraping content..."):
                scraped_contents = run_async(use_scraper(search_results))
            st.write(f"Scraped {len(scraped_contents)} pages.")

            with st.spinner(f"Analyzing with {model_choice}..."):
                # For simplicity, analyze the first query
                result = run_async(analyze_query(queries[0], scraped_contents, model_choice))
                result.search_results = search_results

            st.subheader("Summary")
            st.write(result.summary)

            if hasattr(result, 'analysis') and result.analysis:
                st.subheader("Analysis")
                st.write(result.analysis)

            st.subheader("Scraped Contents")
            for content in result.scraped_contents:
                with st.expander(content.title):
                    st.write(content.content)
        else:
            st.error("Please enter at least one query.")
    else:
        st.error("Please enter queries.")