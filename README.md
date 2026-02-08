# 🦁 Daynimal

**Daynimal** is a daily animal discovery application that displays one random animal per day with enriched information from multiple sources.

## Features

- **Daily Animal**: Get a deterministic animal of the day (changes daily based on date seed)
- **Random Discovery**: Explore random animals from the database
- **Rich Information**: Combines GBIF taxonomy with real-time data from Wikidata, Wikipedia, and Wikimedia Commons
- **French Names**: Optional import of ~49,000 French vernacular names from TAXREF (official French reference)
- **Smart Search**: Full-text search (FTS5) across scientific and vernacular names in multiple languages
- **Offline-First**: Local SQLite database with ~1.5M animal taxa (or minimal 127K species)
- **Legal Compliance**: Proper attribution for all data sources (GBIF CC-BY 4.0, TAXREF Etalab 2.0, Wikipedia/Commons CC-BY-SA)
- **History & Favorites**: Track viewed animals and mark favorites with full pagination support
- **GUI Application**: Cross-platform desktop/mobile app built with Flet (Flutter for Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/notoraptor/daynimal.git
cd daynimal
```

2. Install dependencies using [uv](https://github.com/astral-sh/uv):
```bash
uv sync
```

3. Generate distribution files and build database:
```bash
# Step 1: Generate TSV files from GBIF (~500MB download)
# Optional: add --taxref for ~49K French names (see docs/TAXREF.md)
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
# Without TAXREF (French names limited to GBIF):
# uv run generate-distribution --mode minimal

# Step 2: Build SQLite database from TSV files
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv
```

4. Initialize FTS5 search index (recommended):
```bash
uv run init-fts
```

See [`docs/TAXREF.md`](docs/TAXREF.md) for complete TAXREF documentation.

## Running the Application

### CLI Mode

```bash
# Show today's animal
uv run daynimal

# Show random animal
uv run daynimal random

# Search for animals
uv run daynimal search lion

# Get info about specific animal
uv run daynimal info "Canis lupus"

# Show history
uv run daynimal history

# Show database statistics
uv run daynimal stats

# Show full legal credits
uv run daynimal credits
```

### GUI Mode (Flet)

```bash
# Run the desktop/mobile app
python daynimal/app.py

# OR run with debug logging (recommended for development)
python debug/run_app_debug.py --quiet
```

The GUI application provides an intuitive interface with 6 tabs:
- **Today** - View the animal of the day or a random animal
- **History** - Browse previously viewed animals
- **Favorites** - Manage your favorite animals
- **Search** - Search by scientific or common names
- **Stats** - Database statistics
- **Settings** - Theme, credits, preferences

## Development

### Debugging the Flet App

The project includes a complete debugging system for the Flet GUI application:

```bash
# Launch app with debug logging
python debug/run_app_debug.py --quiet

# View filtered logs (removes Flet internal noise)
python debug/debug_filter.py

# View only errors
python debug/debug_filter.py --errors-only

# Follow logs in real-time
python debug/debug_filter.py --tail
```

📚 **Full documentation**: See [`debug/README.md`](debug/README.md) for complete debugging guide.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=daynimal

# Run specific test file
uv run pytest tests/test_wikidata.py
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .
```

## Architecture

The application follows a three-layer architecture:

1. **Database Layer** (`db/`) - Local SQLite with GBIF Backbone Taxonomy
2. **API Layer** (`sources/`) - External APIs (Wikidata, Wikipedia, Wikimedia Commons)
3. **Repository Layer** (`repository.py`) - Orchestration with caching

### Key Components

- **`daynimal/db/`** - Database models and session management
- **`daynimal/sources/`** - External API integrations
- **`daynimal/repository.py`** - Main data access layer with enrichment logic
- **`daynimal/schemas.py`** - Data models and schemas
- **`daynimal/main.py`** - CLI entry point
- **`daynimal/app.py`** - Flet GUI application
- **`daynimal/debug.py`** - Debugging and logging utilities

## Data Sources

This project uses data from multiple sources:

- **GBIF Backbone Taxonomy** (CC-BY 4.0) - Base taxonomic data (~1.5M animal taxa)
- **TAXREF** (Etalab Open License 2.0) - French vernacular names (~49,000 names, optional)
  - Official French taxonomic reference by Muséum national d'Histoire naturelle
  - See [`docs/TAXREF.md`](docs/TAXREF.md) for import instructions
- **Wikidata** (CC0) - Species properties (IUCN status, mass, lifespan)
- **Wikipedia** (CC-BY-SA) - Article extracts and descriptions
- **Wikimedia Commons** (CC-BY-SA) - Images with licensing metadata

All data sources require proper attribution. See credits with `uv run daynimal credits`.

## Project Structure

```
daynimal/
├── daynimal/           # Main package
│   ├── db/            # Database layer
│   ├── sources/       # External API integrations
│   ├── app.py         # Flet GUI application
│   ├── debug.py       # Debugging utilities
│   ├── main.py        # CLI entry point
│   ├── repository.py  # Data access layer
│   └── schemas.py     # Data models
├── data/              # Raw data files (GBIF, TAXREF) - gitignored
├── tmp/               # Temporary/decompressed files - gitignored
├── debug/             # Debugging tools
│   ├── run_app_debug.py    # Debug launcher
│   ├── debug_filter.py     # Log filtering
│   ├── view_logs.py        # Log viewer
│   └── README.md           # Debug documentation
├── docs/              # Documentation
│   ├── TAXREF.md      # TAXREF import guide
│   └── ...            # Other guides
├── tests/             # Test suite
├── logs/              # Application logs (created at runtime)
├── CLAUDE.md          # Claude Code project instructions
└── pyproject.toml     # Project configuration
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## Acknowledgments

- GBIF Backbone Taxonomy for providing comprehensive taxonomic data
- Wikimedia Foundation for Wikidata, Wikipedia, and Commons data
- Flet framework for the GUI capabilities
