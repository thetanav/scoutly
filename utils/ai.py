import os

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# Centralized model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embeddinggemma")
LLM_MODEL = os.getenv("LLM_MODEL", "minimax-m2.5:cloud")

# Initialize embeddings and LLM
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
llm = OllamaLLM(model=LLM_MODEL)


async def extract_search_keywords(user_prompt: str) -> dict:
    """Extract intelligent search keywords from user prompt.

    Analyzes question type and generates optimized search strategy.

    Returns:
        dict with keys:
            - keywords: list of search terms
            - max_pages: int (how many pages to scrape)
            - retry_keywords: list of alternative keywords
            - search_type: str (general, academic, news, comparison)
            - focus_areas: list of specific aspects to search for
    """

    # Detect question type for better keyword generation
    question_lower = user_prompt.lower()
    is_comparison = any(
        word in question_lower
        for word in ["vs", "versus", "compare", "difference", "better"]
    )
    is_howto = any(
        word in question_lower
        for word in ["how to", "how do", "guide", "tutorial", "steps"]
    )
    is_explanation = any(
        word in question_lower for word in ["what is", "explain", "why does", "meaning"]
    )
    is_list = any(
        word in question_lower for word in ["list", "top", "best", "examples", "ways"]
    )
    is_academic = any(
        word in question_lower
        for word in ["research", "study", "paper", "scientific", "evidence"]
    )

    # Build context-aware prompt
    prompt = f"""You are a search strategy expert. Analyze this question and generate optimal search keywords.

Question: "{user_prompt}"

Question Analysis:
- {"COMPARISON" if is_comparison else ""}
- {"HOW-TO" if is_howto else ""}
- {"EXPLANATION" if is_explanation else ""}
- {"LIST/EXAMPLES" if is_list else ""}
- {"ACADEMIC/RESEARCH" if is_academic else ""}

Respond in this exact format:
KEYWORDS: <3-5 best search terms, comma-separated, most relevant first>
MAX_PAGES: <number 5-15, more for complex questions>
RETRY_KEYWORDS: <3 alternative angles if first results fail>
SEARCH_TYPE: <general|academic|news|comparison|how-to>
FOCUS_AREAS: <2-3 specific aspects to prioritize, comma-separated>

Guidelines:
- For comparisons: search both options + "vs" + "comparison"
- For how-to: include "tutorial" + "guide" + specific steps
- For explanations: include "definition" + "explained" + "examples"
- For lists: include "top" + "best" + "examples"
- For academic: include "research" + "study" + "data"
- Always include the main topic as-is (no stemming)
- Prioritize exact phrases in quotes for specific terms"""

    try:
        response = llm.invoke(prompt)
        response_text = response.strip()

        keywords = []
        max_pages = 5
        retry_keywords = []
        search_type = "general"
        focus_areas = []

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
                except ValueError:
                    max_pages = 5
            elif line.startswith("RETRY_KEYWORDS:"):
                retry_keywords = [
                    k.strip()
                    for k in line.split("RETRY_KEYWORDS:")[1].strip().split(",")
                    if k.strip()
                ]
            elif line.startswith("SEARCH_TYPE:"):
                search_type = line.split("SEARCH_TYPE:")[1].strip().lower()
            elif line.startswith("FOCUS_AREAS:"):
                focus_areas = [
                    k.strip()
                    for k in line.split("FOCUS_AREAS:")[1].strip().split(",")
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
            "keywords": keywords[:5],
            "max_pages": max_pages,
            "retry_keywords": retry_keywords[:3],
            "search_type": search_type,
            "focus_areas": focus_areas,
        }

    except Exception:
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
            "search_type": "general",
            "focus_areas": [],
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

    except Exception:
        return {
            "sufficient": True,  # Assume sufficient on error to avoid infinite loop
            "reason": "Error evaluating context",
            "retry_keywords": [],
            "refined_query": "",
        }


async def ai_finder(folder_name: str, topic: str = "") -> FAISS:
    """Process scraped text and PDFs, create embeddings, and build FAISS vector store."""

    all_documents = []

    # Load source URL mapping from SOURCES.md
    source_map = {}
    sources_path = os.path.join(folder_name, "SOURCES.md")
    if os.path.exists(sources_path):
        with open(sources_path, "r", encoding="utf-8") as f:
            current_file = None
            current_url = None
            for line in f:
                line = line.strip()
                if line.startswith("- URL: "):
                    current_url = line.split("- URL: ")[1].strip()
                elif line.startswith("- File: "):
                    current_file = line.split("- File: ")[1].strip()
                    # File always comes after URL, so save the pair
                    if current_url:
                        source_map[current_file] = current_url
                    current_file = None
                    current_url = None

    # Process each file in the folder
    for filename in os.listdir(folder_name):
        filepath = os.path.join(folder_name, filename)
        source_url = source_map.get(filename, filename)

        if filename.endswith(".md") and filename != "SOURCES.md":
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    doc = Document(
                        page_content=content,
                        metadata={"source": source_url, "file": filename},
                    )
                    all_documents.append(doc)
            except Exception:
                print(f" ! Error processing {filename}")
                continue

        elif filename.endswith(".pdf"):
            try:
                reader = PdfReader(filepath)
                pdf_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pdf_text += page_text + "\n"
                if pdf_text.strip():
                    doc = Document(
                        page_content=pdf_text,
                        metadata={"source": source_url, "file": filename},
                    )
                    all_documents.append(doc)
            except Exception:
                print(f" ! Error processing PDF {filename}")
                continue

    if not all_documents:
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
    except Exception:
        return "RAG failed", []


def ai_stream_response(vectorstore: FAISS, user_prompt: str):
    """Generate streaming response with source attribution."""

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    relevant_docs = retriever.invoke(user_prompt)

    # Combine the content
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Collect unique source URLs
    sources = list(
        dict.fromkeys(doc.metadata.get("source", "unknown") for doc in relevant_docs)
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
        for chunk in llm.stream(full_prompt):
            yield chunk

        # Append sources at the end
        yield "\n\n---\n**Sources:**\n"
        for i, src in enumerate(sources, 1):
            if src.startswith("http"):
                yield f"{i}. [{src}]({src})\n"
            else:
                yield f"{i}. {src}\n"

    except Exception:
        yield "RAG failed"
