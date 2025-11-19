# Deep Research - AI-Powered Research Assistant

An open-source research tool that analyzes user questions, automatically extracts search keywords, finds relevant information online, and provides comprehensive AI-generated answers.

## Features

- **Automatic Keyword Extraction**: AI analyzes user questions to extract optimal search terms
- **Asynchronous Search**: Concurrently search extracted keywords using DuckDuckGo
- **Web Scraping & File Storage**: Extract clean text content from search results and save to organized files (500 chars each)
- **AI Information Extraction**: Uses Gemini Flash 2.0 lite to extract important information (200 words) from scraped files
- **AI Response Generation**: Uses Google Flash 2.5 to provide detailed answers based on extracted information
- **Terminal Interface**: Simple command-line interface for research queries
- **Fast Processing**: Utilizes async HTTP requests and HTML parsing for speed

## Flow

1. **Keyword Extraction**: AI analyzes the user's question to extract relevant search keywords
2. **Scraper**: Searches for the keywords and scrapes content to a unique folder with text files (500 chars each)
3. **AI Finder**: Extracts important information related to the keywords from all files in the folder (200 words)
4. **AI Main**: Responds to the user's original question using the extracted important information

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

## Usage

Run the application:

```bash
uv run python main.py
```

Enter your research question. The AI will automatically extract search keywords, find relevant information, and provide a comprehensive answer.

### Example

```
Enter your research question: What happened with the Asia Cup trophy controversy?
```

The app will:

1. Extract search keywords from your question (e.g., "Asia Cup trophy controversy")
2. Search for information using DuckDuckGo
3. Scrape content from search results and save to files
4. Extract important information using AI
5. Generate a detailed response to your question

## Project Structure

```
scoutly/
├── utils/
│   ├── scraper.py     # Web scraping and file saving functionality
│   ├── search.py      # DuckDuckGo search integration
│   └── ai.py          # AI information extraction and response generation
├── scraped/           # Generated folders with scraped content
├── main.py            # CLI entry point
├── pyproject.toml     # Project configuration
├── uv.lock            # Dependency lock file
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Dependencies

- `ddgs`: DuckDuckGo search API
- `httpx`: Asynchronous HTTP client
- `selectolax`: Fast HTML parsing
- `google-generativeai`: Google Gemini AI models
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
