import asyncio
import base64

import streamlit as st

from utils.ai import ai_finder, ai_stream_response, extract_search_keywords
from utils.scraper import use_scraper
from utils.search import use_search


def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


img_b64 = get_base64("public/tech.png")

st.markdown(
    f'<span style="font-size:2em; font-weight:bold;">Scoutly Research Assistant & RAG</span> <img src="data:image/png;base64,{img_b64}" width="100" style="vertical-align:middle; margin-right:20px;"> ',
    unsafe_allow_html=True,
)

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
            search_keywords, time = asyncio.run(extract_search_keywords(prompt))
            st.write(
                f"🔍 Using {len(search_keywords)} keywords: {', '.join(search_keywords)}"
            )

            # Search
            search_results = asyncio.run(use_search(search_keywords, time))
            st.write("🌐 Searching completed")

            # Scrape
            folder_name = asyncio.run(use_scraper(search_results))
            st.write("📄 Scraping completed")

            # Process documents
            topic = " ".join(search_keywords)
            vectorstore = asyncio.run(ai_finder(folder_name, topic))
            st.write("🧠 Processing completed")

            # Stream response and collect full text
            response_text = ""
            response_placeholder = st.empty()
            for chunk in ai_stream_response(vectorstore, prompt):
                response_text += chunk
                response_placeholder.write(response_text)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            response_text = f"Error: {str(e)}"

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_text})
