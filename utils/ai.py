import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize embeddings and LLM
embeddings = OllamaEmbeddings(model="embeddinggemma")
llm = OllamaLLM(model="minimax-m2.5:cloud")


async def extract_search_keywords(user_prompt: str) -> dict:
    """Extract search keywords from user prompt using A super great model.

    Returns:
        dict with keys:
            - keywords: list of search terms
            - max_pages: int (how many pages to scrape initially)
            - retry_keywords: list of additional keywords if first attempt fails
    """

    prompt = f"""Analyze this research question and provide search strategy.

Question: "{user_prompt}"

Respond in this exact format:
KEYWORDS: <primary search terms, comma-separated, max 3>
MAX_PAGES: <number 3-10, how many pages to scrape initially>
RETRY_KEYWORDS: <alternative/different angles to search if first results insufficient, comma-separated, max 3>

Example for "What are the health benefits of meditation?":
KEYWORDS: meditation benefits, health benefits meditation, mindfulness benefits
MAX_PAGES: 5
RETRY_KEYWORDS: meditation scientific studies, meditation mental health research, mindfulness meditation effects"""

    try:
        response = llm.invoke(prompt)
        response_text = response.strip()

        keywords = []
        max_pages = 5
        retry_keywords = []

        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("KEYWORDS:"):
                keywords = [
                    k.strip()
                    for k in line.split("KEYWORDS:")[1].strip().split(",")
                    if k.strip()
                ]
            elif line.startswith("MAX_PAGES:"):
                try:
                    max_pages = int(line.split("MAX_PAGES:")[1].strip())
                except:
                    max_pages = 5
            elif line.startswith("RETRY_KEYWORDS:"):
                retry_keywords = [
                    k.strip()
                    for k in line.split("RETRY_KEYWORDS:")[1].strip().split(",")
                    if k.strip()
                ]

        # Fallback if parsing failed
        if not keywords:
            words = user_prompt.lower().replace("?", "").split()
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
            }
            filtered = [w for w in words if w not in question_words and len(w) > 2]
            keywords = [" ".join(filtered[:4])] if filtered else [user_prompt]
            max_pages = 5

        return {
            "keywords": keywords[:3],
            "max_pages": max_pages,
            "retry_keywords": retry_keywords[:3],
        }

    except Exception as e:
        # Simple fallback
        words = user_prompt.lower().replace("?", "").split()
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
        }
        filtered = [w for w in words if w not in question_words and len(w) > 2]
        return {
            "keywords": [" ".join(filtered[:4])] if filtered else [user_prompt],
            "max_pages": 5,
            "retry_keywords": [],
        }


async def evaluate_sufficiency(user_prompt: str, context: str) -> dict:
    """Evaluate if the scraped context is sufficient to answer the question.

    Returns:
        dict with keys:
            - sufficient: bool
            - reason: str (explanation)
            - retry_keywords: list of additional search terms if insufficient
            - retry_query: str (refined search query)
    """
    prompt = f"""You are a research assistant evaluating if you have enough information to answer a question.

QUESTION: {user_prompt}

CONTEXT AVAILABLE:
{context[:2000]}

Evaluate if this context is sufficient to give a comprehensive answer. Consider:
- Do you have enough details to explain the topic?
- Are there gaps in key information?
- Is the information accurate and up-to-date?

Respond in this exact format:
SUFFICIENT: yes or no
REASON: brief explanation (1-2 sentences)
RETRY_KEYWORDS: if not sufficient, list 2-3 specific aspects that need more research (comma-separated)
REFINED_QUERY: if not sufficient, a better search query to find missing information"""

    try:
        response = llm.invoke(prompt)
        response_text = response.strip()

        sufficient = False
        reason = "Unable to evaluate"
        retry_keywords = []
        refined_query = ""

        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("SUFFICIENT:"):
                sufficient = "yes" in line.lower().split("SUFFICIENT:")[1].strip()[:3]
            elif line.startswith("REASON:"):
                reason = line.split("REASON:")[1].strip()
            elif line.startswith("RETRY_KEYWORDS:"):
                retry_keywords = [
                    k.strip()
                    for k in line.split("RETRY_KEYWORDS:")[1].strip().split(",")
                    if k.strip()
                ]
            elif line.startswith("REFINED_QUERY:"):
                refined_query = line.split("REFINED_QUERY:")[1].strip()

        return {
            "sufficient": sufficient,
            "reason": reason,
            "retry_keywords": retry_keywords[:3],
            "refined_query": refined_query,
        }

    except Exception as e:
        return {
            "sufficient": True,  # Assume sufficient on error to avoid infinite loop
            "reason": f"Error evaluating: {str(e)}",
            "retry_keywords": [],
            "refined_query": "",
        }


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


async def ai_main(vectorstore: FAISS, user_prompt: str) -> tuple[str, list[str]]:
    """Retrieve relevant information and generate response using Gemma 3."""

    # Retrieve relevant documents
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    relevant_docs = await retriever.ainvoke(user_prompt)

    # Combine the content
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Extract sources
    sources = list(
        set([doc.metadata.get("source", "unknown") for doc in relevant_docs])
    )

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
        return response, sources
    except Exception as e:
        return f"RAG failed: {str(e)}", []


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
