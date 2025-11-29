# Scoutly - AI-Powered Research Assistant with RAG

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/open%20source-yes-brightgreen.svg)](https://github.com/thetanav/scoutly)

An open-source research tool that analyzes user questions, automatically extracts search keywords, finds relevant information online, and provides comprehensive AI-generated answers using Retrieval-Augmented Generation (RAG) with Docling document processing and Ollama Gemma models.

## Features

- **Automatic Keyword Extraction**: AI analyzes user questions to extract optimal search terms using Gemma 3
- **Asynchronous Search**: Concurrently search extracted keywords using DuckDuckGo
- **Web Scraping & File Storage**: Extract clean text content from search results and save to organized files
- **Document Processing**: Uses Docling to process and chunk scraped text documents
- **RAG System**:
  - Creates embeddings using Gemma embedding model via Ollama
  - Stores document chunks in FAISS vector database
  - Retrieves relevant information for user queries
- **AI Response Generation**: Uses Gemma 3 model via Ollama to provide detailed answers based on retrieved context
- **Terminal Interface**: Simple command-line interface for research queries
- **Fast Processing**: Utilizes async HTTP requests and HTML parsing for speed

## Flow

1. **Keyword Extraction**: Gemma 3 analyzes the user's question to extract relevant search keywords
2. **Scraper**: Searches for the keywords and scrapes content to a unique folder with text files
3. **Document Processing & Embedding**: Docling processes text files, chunks them, and creates embeddings using Gemma embedding model
4. **Vector Storage**: Stores embedded chunks in FAISS vector database
5. **Retrieval**: For user queries, retrieves most relevant document chunks
6. **Generation**: Gemma 3 generates comprehensive answers based on retrieved context

## Installation

### Prerequisites

- Python 3.13 or higher
- Ollama installed and running
- Gemma models: `embeddinggemma:latest` and `gemma3:1b` (run `ollama pull embeddinggemma:latest` and `ollama pull gemma3:1b`)

### Setup

1. Clone or download the project:

   ```bash
   git clone <repository-url>
   cd scoutly
   ```

2. Install dependencies:

   ```bash
   pip install -e .
   ```

3. Install Ollama and pull required models:

   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull required models
   ollama pull embeddinggemma:latest
   ollama pull gemma3:1b
   ```

4. Start Ollama service:

   ```bash
   ollama serve
   ```

## Usage

### Running the CLI Script

Execute the main script to perform a search, scrape, and analyze:

```bash
python main.py
```

Enter your research question. The AI will automatically extract search keywords, find relevant information, and provide a comprehensive answer using RAG.

### Example

```
Enter your research question: What is machine learning?
```

The app will:

1. Extract keywords: "machine learning", "artificial intelligence", "algorithms", "data science"
2. Search and scrape relevant web content
3. Process documents with Docling and create embeddings
4. Build FAISS vector store
5. Retrieve relevant information and generate response using Gemma 3

### Output

```
Extracting search keywords...
Using keywords: machine learning, artificial intelligence, algorithms, data science
Searching for information...
Scraping content...
Extracting important information...
Generating response...

Response:
Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that enable computers to perform specific tasks without explicit instructions. It involves training systems on data to recognize patterns and make decisions.

Key aspects include:
- Supervised learning (labeled data)
- Unsupervised learning (unlabeled data)
- Deep learning (neural networks)
- Applications in image recognition, natural language processing, recommendation systems
```

## Demo

Try the interactive web interface powered by Streamlit:

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your browser to the provided URL (usually http://localhost:8501).

3. Enter your research question in the chat input.

The app will automatically extract keywords, search the web, scrape content, process documents, and generate a response using RAG.

### Screenshots

*(Add screenshots here after running the app)*

## Architecture

- **Keyword Extraction**: Gemma 3 model analyzes user queries
- **Search & Scraping**: DuckDuckGo search with async web scraping
- **Document Processing**: Docling handles various document formats and text chunking
- **Embeddings**: Gemma embedding model creates vector representations
- **Vector Storage**: FAISS provides efficient similarity search
- **Retrieval**: Semantic search finds relevant document chunks
- **Generation**: Gemma 3 produces context-aware responses

## Dependencies

- `docling`: Document processing and chunking
- `langchain`: RAG orchestration framework
- `langchain-ollama`: Ollama integration for LangChain
- `faiss-cpu`: Vector similarity search
- `ollama`: Local LLM inference
- `aiohttp`, `httpx`: Async HTTP requests
- `selectolax`: HTML parsing
- `ddgs`: DuckDuckGo search API

## Project Structure

```
scoutly/
├── utils/
│   ├── scraper.py     # Web scraping and file saving functionality
│   ├── search.py      # DuckDuckGo search integration
│   └── ai.py          # RAG system with Docling and Ollama Gemma models
├── scraped/           # Generated folders with scraped content
├── main.py            # CLI entry point
├── pyproject.toml     # Project configuration
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Development

### Running Tests

```bash
# Add tests to tests/ directory and run with:
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Disclaimer

This tool is for research and educational purposes. Respect website terms of service and robots.txt when scraping.
