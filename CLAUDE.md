# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

**CRITICAL**: Always consider this file as canonical memory of the codebase.  
Claude Code should reference this architecture before suggesting any code changes, refactoring, or fixes.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for complete structure, function/class signatures, and internal dependencies.

**Instruction for Claude Code**:
- Assume the contents of `ARCHITECTURE.md` as fully accurate and up-to-date.
- Use it to understand module layers, function/method signatures, classes, dependencies, and high-risk zones.
- Before making any suggestions, cross-reference `ARCHITECTURE.md` to avoid hallucinations.
- At the start, **always** re-generate `ARCHITECTURE.md` with following command: `uv run generate_architecture.py`
- At the start, **always** read [`docs/MOBILE_DESKTOP_ROADMAP.md`](docs/MOBILE_DESKTOP_ROADMAP.md) to understand current priorities and planned features.
- For Android build, emulator setup, and ADB testing, refer to [`docs/ANDROID_DEV_GUIDE.md`](docs/ANDROID_DEV_GUIDE.md).
- **CRITICAL**: Before ANY modification of code UI (Flet), **always** read [`docs/FLET_API_GUIDE.md`](docs/FLET_API_GUIDE.md) for the current API (Flet 0.80+). Ne JAMAIS deviner l'API Flet — toujours consulter ce guide en premier.

**CRITICAL: Environment Management**:
- This project uses **uv** for dependency management with a local `.venv`
- **ALWAYS** use `uv run <command>` to execute Python scripts/commands
- **NEVER** use `python <script>` directly - it may use wrong environment
- Examples: `uv run pytest`, `uv run scripts/compress_distribution.py`, `uv run daynimal`

## Project Overview

Daynimal is a daily animal discovery application (CLI + Flet GUI) that displays one random animal per day with enriched information from multiple sources. The app combines local taxonomy data from GBIF with real-time data from Wikidata, Wikipedia, and Wikimedia Commons.

**CRITICAL: Legal Compliance**
- This project uses data from multiple sources (GBIF CC-BY 4.0, TAXREF Etalab 2.0, Wikidata CC0, Wikipedia/Commons CC-BY-SA).
- All data sources REQUIRE proper attribution for commercial use.
- The `attribution.py` module and attribution methods in schemas MUST be preserved.
- Never remove or hide attribution text in output - it is legally required.

**CRITICAL: File Organization**
- **Raw data files** (GBIF downloads, TAXREF files, etc.) → `data/` directory
- **Temporary/decompressed files** → `tmp/` directory
- Both directories are in `.gitignore` and should NEVER be committed
- Always use these directories for data processing workflows

## Development Commands

### Setup
```bash
# Install dependencies (using uv)
uv sync

# First-time setup: Generate distribution files + build database
# Step 1: Generate TSV files from GBIF (+ optional TAXREF for French names)
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
# Without TAXREF (French names limited to GBIF):
# uv run generate-distribution --mode minimal
# For full database with all ranks:
# uv run generate-distribution --mode full --taxref data/TAXREFv18.txt

# Step 2: Build the SQLite database from TSV files
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv
# For full database:
# uv run build-db --taxa data/animalia_taxa.tsv \
#                 --vernacular data/animalia_vernacular.tsv

# Step 3: Initialize FTS5 for fast search
uv run init-fts
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_wikidata.py

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_commons.py::test_get_images_for_wikidata
```

### Code Quality
```bash
# Format code (Ruff)
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .
```

### Running the Application

**CLI Mode:**
```bash
# Show today's animal
uv run daynimal

# Show random animal
uv run daynimal random

# Search for animals
uv run daynimal search lion

# Get info about specific animal (by ID or name)
uv run daynimal info "Canis lupus"
uv run daynimal info 5219243

# Show history of viewed animals
uv run daynimal history                    # Last 10 entries
uv run daynimal history --page 2           # Page 2 (10 per page)
uv run daynimal history --page 1 --per-page 5  # Custom pagination

# Show database statistics
uv run daynimal stats

# Show full legal credits
uv run daynimal credits
```

**GUI Mode (Flet):**
```bash
# Run the desktop/mobile app (via entry point or directly)
uv run daynimal-app
# or: python daynimal/app.py
```

**Android Build & Test (via ADB):**
```bash
# Build APK (requires Android SDK — auto-installed by Flet CLI)
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run flet build apk --no-rich-output

# APKs are in build/apk/ (arm64-v8a, armeabi-v7a, x86_64)

# Launch Android emulator (AVD "daynimal_test" already created)
$ANDROID_HOME/emulator/emulator -avd daynimal_test -no-audio &

# Wait for emulator, then install and launch
adb wait-for-device
adb install -r build/apk/app-x86_64-release.apk   # x86_64 for emulator
adb shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1

# Take screenshot to verify UI
adb exec-out screencap -p > screenshot.png

# Check logs for errors
adb logcat -d | grep -i "flutter\|python\|error" | grep -v "audit\|InetDiag"

# Force stop and relaunch
adb shell am force-stop com.daynimal.daynimal
```

**Note**: BlueStacks is incompatible with Flet apps (white screen). Use Android Studio emulator (AVD) instead. On Windows, use Unix-style paths for adb/emulator in Git Bash (e.g. `"/c/Users/.../Android/sdk/platform-tools/adb"`).

**Clicking buttons in the emulator via ADB**: Flet uses Flutter rendering — `adb shell input tap X Y` requires exact pixel coordinates. Do NOT guess coordinates from screenshots. Instead:
1. Dump the UI hierarchy: `adb shell uiautomator dump //sdcard/ui.xml && adb shell cat //sdcard/ui.xml`
2. Find the button's `bounds="[left,top][right,bottom]"` in the XML
3. Compute center: `x = (left + right) / 2`, `y = (top + bottom) / 2`
4. Tap: `adb shell input tap <x> <y>`

On Windows/Git Bash, use `//sdcard/` (double slash) to prevent path conversion by MSYS.

**Emulator screenshots**: Save screenshots to `tmp/` (git-ignored), not the project root. Example: `adb exec-out screencap -p > tmp/screenshot.png`

## Architecture

### Three-Layer Data Architecture

1. **Local Database Layer** (`db/`)
   - SQLite database with GBIF Backbone Taxonomy (Animalia only)
   - Models: `TaxonModel`, `VernacularNameModel`, `EnrichmentCacheModel`, `AnimalHistoryModel`, `FavoriteModel`, `UserSettingsModel`
   - ~1.5M animal taxa with taxonomic hierarchy and common names
   - **Two-step pipeline**: `generate_distribution.py` (raw → TSV) + `build_db.py` (TSV → SQLite)
   - **French Names from TAXREF**: Merged during distribution generation (--taxref flag)
     - TAXREF is the official French taxonomic reference (Museum national d'Histoire naturelle)
     - License: Etalab Open License 2.0 (compatible with CC-BY 4.0)
     - See `docs/TAXREF.md` for complete documentation
   - **FTS5 Full-Text Search**: Virtual table `taxa_fts` for instant searches
     - Indexes scientific names, canonical names, and all vernacular names (including French)
     - Provides relevance ranking and prefix matching
     - Initialize with `uv run init-fts` after importing GBIF data (and TAXREF if used)
     - Falls back to slower LIKE queries if not initialized
   - **Animal History**: Tracks all viewed animals with timestamps
     - Records which command was used (today, random, info, search)
     - Supports full history (multiple views of same animal)
     - Pagination support for large histories
   - **Favorites**: Users can mark animals as favorites
     - Managed through `FavoriteModel` with unique constraint on taxon_id
     - Full CRUD operations in `AnimalRepository`

2. **External API Layer** (`sources/`)
   - Abstract base class: `DataSource` (base.py)
   - Three implementations following same interface:
     - `WikidataAPI`: Species properties (IUCN status, mass, lifespan)
     - `WikipediaAPI`: Article extracts and descriptions
     - `CommonsAPI`: Images with licensing metadata
   - All APIs use lazy-initialized httpx clients with proper User-Agent
   - All implement: `get_by_source_id()`, `get_by_taxonomy()`, `search()`
   - All HTTP calls use `_request_with_retry()` with exponential backoff (retry on 429/503)
   - Graceful degradation: return `None` or `[]` instead of crashing on errors

3. **Repository Layer** (`repository.py`)
   - `AnimalRepository`: Main interface for data access
   - Orchestrates local DB queries with external API enrichment
   - Implements caching: fetched data stored in `EnrichmentCacheModel`
   - Key methods:
     - `get_by_id()`, `get_by_name()`: Fetch and enrich single animal
     - `search()`: Search by scientific or vernacular names (uses FTS5 if available)
     - `get_random()`: Random animal (preferring unenriched for discovery)
     - `get_animal_of_the_day()`: Deterministic selection based on date seed
     - `add_to_history()`: Record animal view with command metadata
     - `get_history()`: Retrieve paginated history
     - `clear_history()`: Delete all history entries
     - `add_favorite()`, `remove_favorite()`, `is_favorite()`, `get_favorites()`: Favorites CRUD
     - `get_setting()`, `set_setting()`: User preferences (key-value store)
   - Enrichment is idempotent: API data cached locally, marked with `is_enriched` flag
   - History is automatically recorded when animals are displayed via CLI

### Schema Hierarchy

All data models in `schemas.py` use `@dataclass`:
- `Taxon`: Core taxonomic data from GBIF
- `WikidataEntity`, `WikipediaArticle`, `CommonsImage`: External API data
- `AnimalInfo`: Aggregate model combining all sources with attribution methods

Each schema with external data has `get_attribution_text()` method for legal compliance.

### Configuration

`config.py` uses pydantic-settings:
- Database URL (default: `sqlite:///daynimal.db`)
- Data directory for GBIF downloads
- Wikipedia language preference
- API rate limiting and timeouts
- All overridable via environment variables with `DAYNIMAL_` prefix

## Testing Patterns

Tests use `MockHttpClient` from `conftest.py` to avoid network calls:
- Fixtures return pre-configured mock clients for each API
- Response fixtures in `tests/fixtures/` contain real API response structures
- When adding API calls, add corresponding mock responses in fixtures

Example:
```python
def test_my_feature(mock_wikidata_client):
    api = WikidataAPI()
    api._client = mock_wikidata_client  # Inject mock
    result = api.get_by_taxonomy("Canis lupus")
    assert result is not None
```

UI tests are in `tests/ui/` and use `pytest-asyncio` for async testing. They test `AppState`, reusable widgets, `Debouncer`, `SearchView`, and `AnimalCard`.

## Important Notes

- **Taxonomic Rank**: The enum is `TaxonomicRank`, model field is `rank`
- **Class Field**: Python reserved keyword handled as `class_` in models, `class` in DB
- **Enrichment**: Always happens through `AnimalRepository._enrich()`, never directly from APIs
- **DB Pipeline**: Two-step process: `generate-distribution` creates TSV files, `build-db` imports them into SQLite
- **Date-based Selection**: `get_animal_of_the_day()` uses date as seed for deterministic but varied selection
- **Context Managers**: Repository, APIs, and DB sessions all support `with` statement
- **FTS5 Search**: `search()` uses FTS5 if available, gracefully falls back to LIKE queries otherwise
  - After importing data, run `uv run init-fts` to enable fast search
  - FTS5 provides instant results even with 1.5M taxa

## File Structure

```
daynimal/
├── db/              # Database layer
│   ├── models.py    # SQLAlchemy models (TaxonModel, VernacularNameModel, etc.)
│   ├── session.py   # DB session management
│   ├── generate_distribution.py  # Generate distribution TSV files (GBIF + TAXREF)
│   ├── build_db.py              # Build SQLite DB from distribution TSV files
│   ├── import_gbif_utils.py     # Shared utilities (download, column defs)
│   └── init_fts.py              # FTS5 index initialization
├── sources/         # External API integrations
│   ├── base.py      # Abstract DataSource base + retry_with_backoff()
│   ├── wikidata.py  # Wikidata SPARQL queries
│   ├── wikipedia.py # Wikipedia article fetcher
│   └── commons.py   # Wikimedia Commons images
├── ui/              # Modular UI architecture (Flet GUI)
│   ├── state.py     # AppState (shared state + repository lifecycle)
│   ├── components/
│   │   ├── widgets.py      # LoadingWidget, ErrorWidget, EmptyStateWidget
│   │   └── animal_card.py  # AnimalCard + helpers (history, favorite, search)
│   ├── views/
│   │   ├── base.py         # BaseView (abstract class for all views)
│   │   └── search_view.py  # SearchView (classic search with Enter/button)
│   └── utils/
│       └── debounce.py     # Debouncer (300ms async, not used in SearchView)
├── attribution.py   # Legal attribution helpers
├── config.py        # Application settings
├── repository.py    # Data orchestration layer (with parallel API calls)
├── schemas.py       # Pydantic/dataclass models
├── main.py          # CLI entry point
├── app.py           # Flet GUI application (delegates to ui/ modules)
└── debug.py         # Debugging and logging utilities

debug/               # Debugging tools and documentation
├── run_app_debug.py # Debug launcher for Flet app
├── debug_filter.py  # Smart log filtering (removes Flet noise)
├── view_logs.py     # Log viewing utilities
└── README.md        # Debug system documentation

scripts/             # Build and release scripts
└── prepare_release.py          # Compress TSV + generate manifest for GitHub Release

docs/                # Documentation
├── DISTRIBUTION_RELEASE.md     # Distribution release process
├── FLET_API_GUIDE.md           # Flet API reference
├── TAXREF.md                   # TAXREF integration guide
└── MOBILE_DESKTOP_ROADMAP.md   # Development roadmap

tests/
├── conftest.py      # Pytest fixtures and mocks
├── fixtures/        # Mock API responses
├── test_*.py        # Unit tests per module
└── ui/              # UI component and view tests
    ├── test_state.py        # AppState tests
    ├── test_widgets.py      # Reusable widgets tests
    ├── test_debouncer.py    # Debouncer tests
    ├── test_search_view.py  # SearchView tests
    └── test_animal_card.py  # AnimalCard tests

logs/                # Application logs (created at runtime)
└── daynimal_*.log   # Timestamped log files
```

## When Modifying Code

- **Adding API calls**: Update corresponding DataSource subclass, add tests with mocks
- **Changing schemas**: Update both the dataclass and any attribution methods
- **Modifying enrichment**: Changes go in `AnimalRepository._enrich()` and cache methods
  - **Note**: `_enrich()` uses `ThreadPoolExecutor` to parallelize Wikidata and Wikipedia calls
  - Images are always fetched after (may depend on Wikidata results)
- **Database changes**: Create new models or migrations, update import script if needed
- **CLI commands**: Add to `main.py` following existing command pattern
- **GUI changes**: New views and components go in `daynimal/ui/` (extend `BaseView` for views, add components in `components/`). Legacy code remains in `app.py` until fully migrated. Use async/await patterns for UI responsiveness
- **Debugging GUI issues**: Use the debug system in `debug/` folder
  - Launch with `python debug/run_app_debug.py --quiet`
  - View logs with `python debug/debug_filter.py`
  - All UI events are automatically logged (navigation, loading, searches, errors)
