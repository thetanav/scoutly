import asyncio
import streamlit as st
from utils.scraper import use_scraper
from utils.search import use_search
from utils.ai import extract_search_keywords, ai_finder, ai_stream_response

st.title("Scoutly Research Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Enter your research question"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        try:
            # Extract keywords
            search_keywords = asyncio.run(extract_search_keywords(prompt))
            st.write(f"🔍 Using keywords: {', '.join(search_keywords)}")

            # Search
            search_results = asyncio.run(use_search(search_keywords))
            st.write("🌐 Searching completed")

            # Scrape
            folder_name = asyncio.run(use_scraper(search_results))
            st.write("📄 Scraping completed")

            # Process documents
            topic = " ".join(search_keywords)
            vectorstore = asyncio.run(ai_finder(folder_name, topic))
            st.write("🧠 Processing completed")

            # Stream response
            st.write_stream(ai_stream_response(vectorstore, prompt))
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Add assistant response to chat history (simplified, assuming we can get the full response)
    # For now, skip adding to history to avoid complexity