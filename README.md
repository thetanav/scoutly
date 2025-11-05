# Scoutly - OSS Deep Researcher

An open-source deep research tool that searches for queries using DuckDuckGo, scrapes and parses text content from web pages, and provides AI-powered analysis and summarization.

## Features

- **Asynchronous Search**: Concurrently search multiple queries using DuckDuckGo.
- **Web Scraping & Parsing**: Extract clean text content from search result URLs using Pydantic models.
- **AI Analysis**: Separate AI module for deep analysis and summarization of scraped content.
- **Streamlit UI**: User-friendly web interface for interactive research.
- **Fast Processing**: Utilizes async HTTP requests and HTML parsing for speed.
- **Data Validation**: Uses Pydantic for robust data modeling.

## Installation

### Prerequisites

- Python 3.13 or higher
- uv package manager

### Setup

1. Clone or download the project:
    ```bash
    git clone <repository-url>
    cd scoutly
    ```

2. Install dependencies using uv:
    ```bash
    uv sync
    ```

3. (Optional) Install the package in development mode:
    ```bash
    uv pip install -e .
    ```

4. Set up API keys (optional, for Gemini and OpenRouter):
    ```bash
    export GEMINI_API_KEY="your-gemini-api-key"
    export OPENROUTER_API_KEY="your-openrouter-api-key"
    ```
    For Ollama, ensure Ollama is running locally with llama3.2 model.

## Usage

### Running the CLI Script

Execute the main script to perform a search, scrape, and analyze:

```bash
uv run python main.py
```

This will search for predefined queries about the "Asia Cup trophy controversy", scrape content, and display a summary.

### Running the Streamlit UI

Launch the interactive web interface:

```bash
uv run streamlit run app.py
```

Enter your research queries in the text area and click "Research" to get search results, scraped content, and AI-generated summaries.

### Custom Queries (CLI)

Modify the `query` list in `main.py` to search for your own topics:

```python
query = [
    "your search query here",
    "another query",
]
```

### Output

- **CLI**: Prints summary to console.
- **UI**: Displays summary and expandable scraped content in the browser.

## Project Structure

```
scoutly/
├── utils/
│   ├── models.py      # Pydantic data models
│   ├── scraper.py     # Web scraping and parsing functionality
│   ├── search.py      # DuckDuckGo search integration
│   └── ai.py          # AI analysis and summarization
├── tests/             # Test files (future)
├── main.py            # CLI entry point
├── app.py             # Streamlit UI entry point
├── pyproject.toml     # Project configuration
├── uv.lock            # Dependency lock file
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Dependencies

- `ddgs`: DuckDuckGo search API
- `httpx`: Asynchronous HTTP client
- `selectolax`: Fast HTML parsing
- `pydantic`: Data validation and modeling
- `streamlit`: Web UI framework
- `aiohttp`: Additional async HTTP support
- `duckduckgo-search`: Alternative search client
- `snscrape`: Social media scraping (not currently used)

## Development

### Running Tests

```bash
# Add tests to tests/ directory and run with:
uv run pytest
```

### Code Quality

```bash
# Lint code (if configured)
uv run ruff check .

# Format code
uv run ruff format .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add license information here]

## TODO

- [x] Support multiple queries
- [ ] Cache scraped pages to avoid re-fetching
- [ ] Use request body for ultra-fast scraping
- [ ] Add configuration file support
- [ ] Implement retry logic for failed requests
- [ ] Add logging and progress indicators
