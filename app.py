import asyncio
import base64

import streamlit as st

from utils.ai import (
    ai_finder,
    ai_stream_response,
    extract_search_keywords,
    evaluate_sufficiency,
)
from utils.scraper import use_scraper, use_search, search_pdfs


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
            # Extract keywords with AI strategy
            with st.spinner("🧠 Analyzing question and planning research..."):
                search_strategy = asyncio.run(extract_search_keywords(prompt))
                keywords = search_strategy["keywords"]
                max_pages = search_strategy.get("max_pages", 5)
                retry_keywords = search_strategy.get("retry_keywords", [])
                search_type = search_strategy.get("search_type", "general")

            st.info(
                f"📊 Research plan: {len(keywords)} search topics, will scrape up to {max_pages} pages"
            )

            # Initial search
            with st.spinner("Searching for information..."):
                search_results, search_time = asyncio.run(
                    use_search(keywords, search_type=search_type, max_results_per_query=8)
                )

            # Initial scrape
            with st.spinner("Scraping web pages..."):
                folder_name, next_index = asyncio.run(
                    use_scraper(search_results, search_time)
                )

            # Build initial RAG
            with st.spinner("Building knowledge base..."):
                topic = " ".join(keywords)
                vectorstore = asyncio.run(ai_finder(folder_name, topic))

            # Evaluate sufficiency
            with st.spinner("Evaluating research depth..."):
                retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                initial_docs = retriever.invoke(prompt)
                context = "\n\n".join([doc.page_content for doc in initial_docs])

                evaluation = asyncio.run(evaluate_sufficiency(prompt, context))

            # Adaptive loop: get more info if needed
            max_iterations = 3
            iteration = 0

            while not evaluation["sufficient"] and iteration < max_iterations:
                iteration += 1
                st.info(
                    f"🔄 Need more info ({iteration}/{max_iterations}): {evaluation['reason']}"
                )

                # Get additional keywords
                additional_keywords = evaluation.get("retry_keywords", [])
                if not additional_keywords and retry_keywords:
                    additional_keywords = retry_keywords

                if not additional_keywords:
                    break

                # Search more
                with st.spinner(
                    f"Searching for more information (round {iteration + 1})..."
                ):
                    more_results, _ = asyncio.run(use_search(additional_keywords[:2], search_type=search_type, max_results_per_query=5))

                # Scrape more
                with st.spinner(
                    f"Scraping additional pages (round {iteration + 1})..."
                ):
                    folder_name, next_index = asyncio.run(
                        use_scraper(more_results, 0, folder_name, next_index)
                    )

                # Search and download PDF if needed
                if iteration == 1:
                    with st.spinner("Searching for relevant PDFs..."):
                        pdf_count = asyncio.run(
                            search_pdfs(
                                additional_keywords[:1], folder_name, max_pdfs=1
                            )
                        )
                        if pdf_count > 0:
                            st.info(f"📄 Downloaded {pdf_count} relevant PDF")

                # Rebuild RAG with new content
                with st.spinner("Updating knowledge base..."):
                    vectorstore = asyncio.run(ai_finder(folder_name, topic))

                # Re-evaluate
                with st.spinner("Re-evaluating..."):
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                    initial_docs = retriever.invoke(prompt)
                    context = "\n\n".join([doc.page_content for doc in initial_docs])
                    evaluation = asyncio.run(evaluate_sufficiency(prompt, context))

            if not evaluation["sufficient"]:
                st.warning(
                    "⚠️ Could not gather complete information, but here's what we found:"
                )

            # Generate response
            response_text = ""
            response_placeholder = st.empty()

            with st.spinner("Generating response..."):
                for chunk in ai_stream_response(vectorstore, prompt):
                    response_text += chunk
                    response_placeholder.write(response_text)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            response_text = f"Error: {str(e)}"

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_text})
