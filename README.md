# 🧠 Scoutly - Research Agent

A smart research assistant that:
- 🔍 Searches DuckDuckGo for **5 keywords**
- 🌐 Scrapes **top 7 results** per keyword
- 📚 Builds a **RAG pipeline** for intelligent Q&A
- ⚡ Delivers **context-rich answers** with sources

## 🎯 Features

| Feature | Description |
|---------|-------------|
| **Multi-Keyword Search** | Searches 5 keywords simultaneously |
| **Smart Scraping** | Extracts top 7 results from DuckDuckGo |
| **RAG Pipeline** | Vector database + LLM for accurate answers |
| **Source Attribution** | Every answer cites original sources |
| **Async Processing** | Fast parallel scraping and processing |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Search** | DuckDuckGo |
| **Scraping** | Selectolax |
| **Vector DB** | Chroma |
| **Embeddings** | Embedding Gemma |
| **LLM** | Gemma3 |
| **Framework** | LangChain / Docling |

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/research-agent
cd research-agent
pip install -r requirements.txt

# Run with your keywords
streamlit run app.py
```
