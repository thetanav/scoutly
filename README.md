# Scoutly

A fast and efficient web scraping tool that searches for queries using DuckDuckGo and extracts text content from the resulting web pages.

## Features

- **Asynchronous Search**: Concurrently search multiple queries using DuckDuckGo.
- **Web Scraping**: Extract clean text content from search result URLs.
- **Fast Processing**: Utilizes async HTTP requests and HTML parsing for speed.
- **Simple Output**: Saves scraped content to organized text files.

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

## Usage

### Running the Script

Execute the main script to perform a search and scrape:

```bash
uv run python main.py
```

This will search for predefined queries about the "Asia Cup trophy controversy" and save the scraped text to the `scraped/` directory.

### Custom Queries

Modify the `query` list in `main.py` to search for your own topics:

```python
query = [
    "your search query here",
    "another query",
]
```

### Output

Scraped content is saved in the `scraped/` directory as `.txt` files, named after the page titles (sanitized for filesystem compatibility).

## Project Structure

```
scoutly/
├── src/
│   └── scoutly/
│       ├── __init__.py
│       └── utils/
│           ├── scraper.py    # Web scraping functionality
│           └── search.py     # DuckDuckGo search integration
├── tests/                   # Test files (future)
├── main.py                  # Main entry point
├── pyproject.toml           # Project configuration
├── uv.lock                  # Dependency lock file
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

## Dependencies

- `ddgs`: DuckDuckGo search API
- `httpx`: Asynchronous HTTP client
- `selectolax`: Fast HTML parsing
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
