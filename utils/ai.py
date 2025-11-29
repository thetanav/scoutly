import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize embeddings and LLM
embeddings = OllamaEmbeddings(model="embeddinggemma")
llm = OllamaLLM(model="gemma3:1b")


async def extract_search_keywords(user_prompt: str) -> List[str]:
    """Extract search keywords from user prompt using Gemma 3."""

    prompt = f"""What are the main topics or subjects in this question that I should search for?

Question: "{user_prompt}"

Return just the key search terms, separated by commas. For example:
Question: "What are the health benefits of meditation?"
Answer: meditation benefits, health benefits meditation, mindfulness benefits

Question: "How does climate change affect polar bears?"
Answer: climate change polar bears, polar bear habitat, global warming arctic"""

    try:
        response = llm.invoke(prompt)
        keywords_text = response.strip()
        # Clean up and split
        keywords = []
        for line in keywords_text.split("\n"):
            if "," in line or "Answer:" in line:
                # Extract the answer part
                if "Answer:" in line:
                    line = line.split("Answer:")[1].strip()
                parts = [p.strip() for p in line.split(",") if p.strip()]
                keywords.extend(parts)
                break

        # If no keywords found, try the whole text
        if not keywords:
            keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]

        # Filter and clean
        final_keywords = []
        for k in keywords:
            k = k.strip('"').strip("'")
            if len(k) > 5 and not k.lower().startswith(("what", "how", "why")):
                final_keywords.append(k)

        return (
            final_keywords[:5]
            if final_keywords
            else [" ".join(user_prompt.split()[2:6])]
        )  # Skip question word and get next words
    except Exception:
        # Simple fallback: remove question words and take key phrases
        words = user_prompt.lower().replace("?", "").split()
        # Remove question words
        question_words = {
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "which",
            "did",
            "was",
            "were",
            "has",
            "have",
            "does",
            "do",
            "is",
            "are",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "with",
            "about",
            "happened",
        }
        filtered_words = [w for w in words if w not in question_words and len(w) > 2]
        if len(filtered_words) >= 5:
            return [" ".join(filtered_words[:3]), " ".join(filtered_words)]
        else:
            return [" ".join(filtered_words)]


async def ai_finder(folder_name: str, topic: str) -> FAISS:
    """Process scraped text with Docling, create embeddings, and build FAISS vector store."""

    all_documents = []

    # Process each text file in the folder
    for filename in os.listdir(folder_name):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder_name, filename)
            try:
                # Read the text file
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Create a Document object
                doc = Document(page_content=content, metadata={"source": filename})
                all_documents.append(doc)

            except Exception as e:
                print(f" ! Error processing {filename}: {e}")
                continue

    if not all_documents:
        # Fallback: create a dummy document
        all_documents = [
            Document(page_content="No content found", metadata={"source": "fallback"})
        ]

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    chunks = text_splitter.split_documents(all_documents)

    # Create FAISS vector store
    vectorstore = FAISS.from_documents(chunks, embeddings)

    return vectorstore


async def ai_main(vectorstore: FAISS, user_prompt: str) -> str:
    """Retrieve relevant information and generate response using Gemma 3."""

    # Retrieve relevant documents
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    relevant_docs = await retriever.ainvoke(user_prompt)

    # Combine the content
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Create prompt with context
    full_prompt = f"""You are an answer engine that provides accurate, well-reasoned, and practical responses.
        Use the provided context to ground your answer, but do not mention the context directly.
        If the answer is uncertain, acknowledge briefly and provide the most likely correct information.
        Organize your response for readability using sections or bullet points when helpful.
        Prioritize: factual correctness, efficiency, and actionable advice.
        Avoid asking follow-up questions.
        Avoid phrases that weaken confidence (e.g., "this might help" -> "do this for better results").
        Keep the tone direct, clear, and concise.

        Based on the following information:

        {context}

        Answer the user's question: {user_prompt}
        """

    try:
        response = llm.invoke(full_prompt)
        return response
    except Exception as e:
        return f"RAG failed: {str(e)}"


def ai_stream_response(vectorstore: FAISS, user_prompt: str):
    """Generate streaming response using Gemma 3."""

    # Retrieve relevant documents (sync for simplicity, assuming vectorstore is ready)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    # Since retriever.ainvoke is async, but for streamlit, we'll make it sync
    # Actually, FAISS retriever has invoke method too
    relevant_docs = retriever.invoke(user_prompt)

    # Combine the content
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Create prompt with context
    full_prompt = f"""You are an answer engine that provides accurate, well-reasoned, and practical responses.
        Use the provided context to ground your answer, but do not mention the context directly.
        If the answer is uncertain, acknowledge briefly and provide the most likely correct information.
        Organize your response for readability using sections or bullet points when helpful.
        Prioritize: factual correctness, efficiency, and actionable advice.
        Avoid asking follow-up questions.
        Avoid phrases that weaken confidence (e.g., "this might help" -> "do this for better results").
        Keep the tone direct, clear, and concise.

        Based on the following information:

        {context}

        Answer the user's question: {user_prompt}
        """

    try:
        for chunk in llm.stream(full_prompt):
            yield chunk
    except Exception as e:
        yield f"RAG failed: {str(e)}"
