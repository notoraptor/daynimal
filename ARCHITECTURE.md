# Architecture Overview

## 1. Project Structure

### daynimal
- `daynimal.__init__` — Daynimal - Daily Animal Discovery App
- `daynimal.app` — Daynimal Flet App - Desktop/Mobile Application
- `daynimal.attribution` — Attribution management for legal compliance.
- `daynimal.config`
- `daynimal.debug` — Debug utilities for Daynimal Flet app.
- `daynimal.main` — Daynimal CLI - Daily Animal Discovery
- `daynimal.repository` — Animal Repository - aggregates data from local DB and external APIs.
- `daynimal.schemas`

### daynimal/db
- `daynimal.db.__init__`
- `daynimal.db.build_db` — Build a SQLite database from distribution TSV files.
- `daynimal.db.generate_distribution` — Generate distribution TSV files from raw sources (GBIF + TAXREF).
- `daynimal.db.import_gbif_utils` — GBIF Backbone Taxonomy - Shared utilities for import scripts.
- `daynimal.db.init_fts` — Initialize FTS5 (Full-Text Search) table for fast animal search.
- `daynimal.db.models`
- `daynimal.db.session`

### daynimal/sources
- `daynimal.sources.__init__`
- `daynimal.sources.base` — Base class for external data sources.
- `daynimal.sources.commons` — Wikimedia Commons API client.
- `daynimal.sources.wikidata` — Wikidata API client.
- `daynimal.sources.wikipedia` — Wikipedia API client.

### daynimal/ui
- `daynimal.ui.__init__` — UI module for Daynimal Flet application.
- `daynimal.ui.app_controller` — App controller for managing views and navigation.
- `daynimal.ui.state` — Application state management for Daynimal UI.

### daynimal/ui/components
- `daynimal.ui.components.__init__` — Reusable UI components for Daynimal app.
- `daynimal.ui.components.animal_card` — Reusable animal card component for list views.
- `daynimal.ui.components.animal_display` — Animal display component for showing detailed animal information.
- `daynimal.ui.components.image_carousel` — Image carousel component for displaying animal images with navigation.
- `daynimal.ui.components.widgets` — Reusable UI widgets for Daynimal app.

### daynimal/ui/utils
- `daynimal.ui.utils.__init__` — UI utilities for Daynimal app.
- `daynimal.ui.utils.debounce` — Debouncing utility for UI inputs.

### daynimal/ui/views
- `daynimal.ui.views.__init__` — Views for Daynimal app.
- `daynimal.ui.views.base` — Base view class for Daynimal UI.
- `daynimal.ui.views.favorites_view` — Favorites view for displaying favorite animals.
- `daynimal.ui.views.history_view` — History view for displaying animal viewing history.
- `daynimal.ui.views.search_view` — Search view for Daynimal app.
- `daynimal.ui.views.settings_view` — Settings view for app configuration and credits.
- `daynimal.ui.views.stats_view` — Statistics view for displaying database statistics.
- `daynimal.ui.views.today_view` — Today view for displaying the animal of the day or random animals.

### debug
- `debug.debug_filter` — Filter and display relevant logs from Daynimal application.
- `debug.run_app_debug` — Debug launcher for Daynimal Flet application.
- `debug.view_logs` — Utility script to view Daynimal logs.

### root
- `generate_architecture`

## 2. Entry Points
- daynimal.app
- daynimal.main
- daynimal.db.build_db
- daynimal.db.generate_distribution
- daynimal.db.init_fts
- debug.debug_filter
- debug.run_app_debug
- debug.view_logs

## 3. Internal Dependencies

### daynimal.__init__
- depends on `daynimal.attribution`
- depends on `daynimal.repository`
- depends on `daynimal.schemas`

### daynimal.app
- depends on `daynimal.debug`
- depends on `daynimal.repository`
- depends on `daynimal.ui.app_controller`

### daynimal.attribution
- depends on `daynimal.schemas`

### daynimal.db.__init__
- depends on `daynimal.db.models`
- depends on `daynimal.db.session`

### daynimal.db.build_db
- depends on `daynimal.config`
- depends on `daynimal.db.models`
- depends on `daynimal.db.session`

### daynimal.db.generate_distribution
- depends on `daynimal.db.import_gbif_utils`

### daynimal.db.init_fts
- depends on `daynimal.config`
- depends on `daynimal.db.session`

### daynimal.db.session
- depends on `daynimal.config`

### daynimal.main
- depends on `daynimal.__init__`
- depends on `daynimal.attribution`
- depends on `daynimal.config`
- depends on `daynimal.repository`

### daynimal.repository
- depends on `daynimal.db.models`
- depends on `daynimal.db.session`
- depends on `daynimal.schemas`
- depends on `daynimal.sources.commons`
- depends on `daynimal.sources.wikidata`
- depends on `daynimal.sources.wikipedia`

### daynimal.sources.__init__
- depends on `daynimal.sources.base`
- depends on `daynimal.sources.commons`
- depends on `daynimal.sources.wikidata`
- depends on `daynimal.sources.wikipedia`

### daynimal.sources.base
- depends on `daynimal.config`

### daynimal.sources.commons
- depends on `daynimal.schemas`
- depends on `daynimal.sources.base`

### daynimal.sources.wikidata
- depends on `daynimal.schemas`
- depends on `daynimal.sources.base`

### daynimal.sources.wikipedia
- depends on `daynimal.config`
- depends on `daynimal.schemas`
- depends on `daynimal.sources.base`

### daynimal.ui.__init__
- depends on `daynimal.ui.state`

### daynimal.ui.app_controller
- depends on `daynimal.debug`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.favorites_view`
- depends on `daynimal.ui.views.history_view`
- depends on `daynimal.ui.views.search_view`
- depends on `daynimal.ui.views.settings_view`
- depends on `daynimal.ui.views.stats_view`
- depends on `daynimal.ui.views.today_view`

### daynimal.ui.components.__init__
- depends on `daynimal.ui.components.animal_card`
- depends on `daynimal.ui.components.widgets`

### daynimal.ui.components.animal_card
- depends on `daynimal.schemas`

### daynimal.ui.components.animal_display
- depends on `daynimal.schemas`

### daynimal.ui.components.image_carousel
- depends on `daynimal.schemas`

### daynimal.ui.state
- depends on `daynimal.repository`
- depends on `daynimal.schemas`

### daynimal.ui.utils.__init__
- depends on `daynimal.ui.utils.debounce`

### daynimal.ui.views.__init__
- depends on `daynimal.ui.views.base`
- depends on `daynimal.ui.views.search_view`

### daynimal.ui.views.base
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`

### daynimal.ui.views.favorites_view
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.history_view
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.search_view
- depends on `daynimal.ui.components.animal_card`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.settings_view
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.stats_view
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.today_view
- depends on `daynimal.schemas`
- depends on `daynimal.ui.components.animal_display`
- depends on `daynimal.ui.components.image_carousel`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### debug.run_app_debug
- depends on `daynimal.app`
- depends on `daynimal.debug`

## 4. External Dependencies
- flet (used 14 times)
- pathlib (used 9 times)
- typing (used 9 times)
- asyncio (used 8 times)
- sqlalchemy (used 8 times)
- argparse (used 7 times)
- datetime (used 6 times)
- traceback (used 6 times)
- dataclasses (used 4 times)
- sys (used 4 times)
- abc (used 2 times)
- csv (used 2 times)
- httpx (used 2 times)
- logging (used 2 times)
- re (used 2 times)
- subprocess (used 2 times)
- threading (used 2 times)
- ast (used 1 times)
- collections (used 1 times)
- concurrent (used 1 times)
- contextlib (used 1 times)
- enum (used 1 times)
- io (used 1 times)
- json (used 1 times)
- os (used 1 times)
- pydantic_settings (used 1 times)
- random (used 1 times)
- time (used 1 times)
- unicodedata (used 1 times)
- zipfile (used 1 times)

## 5. Signatures and Calls

### Module: daynimal.app
> Daynimal Flet App - Desktop/Mobile Application
> 
> A cross-platform application built with Flet (Flutter for Python) that displays
> daily animal discoveries with enriched information.
```python
class DaynimalApp  # Main application class for Daynimal Flet app.
    def __init__(self, page)
    # calls: hasattr, isinstance, self.build, self.debugger.logger.info
    def build(self)  # Build the user interface.
    # calls: AppController, self._load_theme, self.app_controller.build, self.page.add, self.page.update
    def _load_theme(self)  # Load theme setting from database and apply to page.
    # calls: AnimalRepository
    def cleanup(self)  # Clean up resources (close connections, database, etc.).
    # calls: hasattr, self.app_controller.cleanup, self.debugger.logger.error, self.debugger.logger.info
    def on_disconnect(self, e)  # Handle page disconnect event (when user closes the window).
    # calls: self.cleanup, self.debugger.logger.error, self.debugger.logger.info
    def on_close(self, e)  # Handle page close event.
    # calls: self.cleanup, self.debugger.logger.error, self.debugger.logger.info
```
```python
def main()  # Main entry point for the Flet app.
```
- calls: `DaynimalApp`, `ft.app`

### Module: daynimal.attribution
> Attribution management for legal compliance.
> 
> This module ensures proper attribution for all data sources
> as required by their respective licenses:
> 
> - GBIF Backbone: CC-BY 4.0 (attribution required)
> - TAXREF: Etalab Open License 2.0 (attribution required, compatible with CC-BY)
> - Wikidata: CC0 (no attribution required, but recommended)
> - Wikipedia: CC-BY-SA 4.0 (attribution required, share-alike)
> - Wikimedia Commons: varies (CC-BY, CC-BY-SA, CC0, Public Domain)
> 
> IMPORTANT: Commercial use requires displaying these attributions
> to end users in the application.
```python
@dataclass
class AttributionInfo  # Attribution information for a single data source.
    def to_text(self, format)  # Generate attribution text.
    # calls: self._full_text, self._short_text
    def _full_text(self)  # Generate full attribution text.
    def _short_text(self)  # Generate short attribution text.
    def to_html(self)  # Generate HTML attribution with links.
```
```python
@dataclass
class DataAttribution  # Complete attribution for an animal's data.
    def get_all(self)  # Get all attributions as a list.
    def to_text(self, format)  # Generate complete attribution text.
    # calls: self.get_all
    def to_html(self)  # Generate HTML attribution block.
    # calls: self.get_all
    def get_required_attributions(self)  # Get only attributions that are legally required (non-CC0).
    # calls: self.get_all
```
```python
def create_wikidata_attribution(qid)  # Create attribution for a specific Wikidata entity.
```
- calls: `AttributionInfo`, `datetime.now`
```python
def create_wikipedia_attribution(title, language, url, modified)  # Create attribution for a Wikipedia article.
```
- calls: `AttributionInfo`, `datetime.now`
```python
def create_commons_attribution(filename, author, license, url)  # Create attribution for a Wikimedia Commons image.
```
- calls: `AttributionInfo`, `datetime.now`
```python
def get_app_legal_notice(format)  # Get the application's legal notice for display in About page.
```

### Module: daynimal.config
```python
class Settings(BaseSettings)
```

### Module: daynimal.db.build_db
> Build a SQLite database from distribution TSV files.
> 
> This script takes pre-generated TSV files (from generate_distribution.py) and
> imports them into a new SQLite database with optimized settings.
> 
> Usage:
>     # Build from minimal distribution
>     uv run build-db --taxa data/animalia_taxa_minimal.tsv \
>                      --vernacular data/animalia_vernacular_minimal.tsv
> 
>     # Build with custom database name
>     uv run build-db --taxa data/animalia_taxa.tsv \
>                      --vernacular data/animalia_vernacular.tsv \
>                      --db daynimal_full.db
```python
def optimize_database_for_import(engine)  # Configure SQLite for maximum import speed.
```
- calls: `print`, `text`
```python
def restore_database_settings(engine)  # Restore normal database settings after import.
```
- calls: `print`, `text`
```python
def bulk_import_taxa(engine, tsv_path)  # Import taxa from TSV file using optimized bulk insert.
```
- calls: `bool`, `csv.reader`, `int`, `len`, `open`, `print`, `text`
```python
def bulk_import_vernacular(engine, tsv_path)  # Import vernacular names from TSV file using optimized bulk insert.
```
- calls: `csv.reader`, `int`, `len`, `open`, `print`, `text`
```python
def build_database(taxa_tsv, vernacular_tsv, db_filename)  # Build a SQLite database from distribution TSV files.
```
- calls: `Base.metadata.create_all`, `FileNotFoundError`, `Path`, `RuntimeError`, `bulk_import_taxa`, `bulk_import_vernacular`, `get_engine`, `optimize_database_for_import`, `print`, `restore_database_settings`, `text`
```python
def main()  # Main entry point for build-db.
```
- calls: `Path`, `argparse.ArgumentParser`, `build_database`

### Module: daynimal.db.generate_distribution
> Generate distribution TSV files from raw sources (GBIF + TAXREF).
> 
> This script produces ready-to-import TSV files that can be used by build_db.py
> to construct a SQLite database. It supports two modes:
> 
>   - full: All Animalia kingdom taxa (all ranks)
>   - minimal: Species with vernacular names only
> 
> When --taxref is provided, French names from TAXREF are merged into the
> vernacular TSV, enriching the distribution with ~49K additional French names.
> 
> Usage:
>     # Minimal distribution with TAXREF French names
>     uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
> 
>     # Full distribution without TAXREF
>     uv run generate-distribution --mode full
> 
>     # With pre-downloaded backbone
>     uv run generate-distribution --mode minimal --backbone data/backbone.zip
```python
def extract_and_filter_taxa(zip_path, output_path, mode)  # Extract taxa from GBIF ZIP and create a filtered TSV file.
```
- calls: `FileNotFoundError`, `csv.reader`, `csv.writer`, `int`, `io.TextIOWrapper`, `len`, `next`, `open`, `print`, `set`, `zipfile.ZipFile`
```python
def extract_and_filter_vernacular(zip_path, output_path, valid_taxon_ids)  # Extract vernacular names from GBIF ZIP and create a filtered TSV file.
```
- calls: `csv.reader`, `csv.writer`, `io.TextIOWrapper`, `len`, `next`, `open`, `parse_int`, `print`, `zipfile.ZipFile`
```python
def build_canonical_to_taxon_ids(taxa_tsv)  # Build a mapping from lowercase canonical_name to taxon_id from the taxa TSV.
```
- calls: `csv.reader`, `int`, `len`, `open`, `print`
```python
def parse_taxref_french_names(taxref_path)  # Parse TAXREF file and extract unique French vernacular names for Animalia.
```
- calls: `csv.DictReader`, `extract_canonical_name`, `len`, `open`, `print`, `set`
```python
def merge_taxref_into_vernacular(vernacular_tsv, taxref_entries, canonical_to_id)  # Append TAXREF French names to the vernacular TSV, avoiding duplicates.
```
- calls: `csv.reader`, `csv.writer`, `len`, `open`, `print`, `set`, `str`
```python
def cleanup_taxa_without_vernacular(taxa_tsv, vernacular_tsv, output_taxa_tsv)  # Filter taxa TSV to keep only taxa that have at least one vernacular name.
```
- calls: `csv.reader`, `csv.writer`, `int`, `len`, `open`, `parse_int`, `print`, `set`
```python
def generate_distribution(mode, backbone_path, taxref_path, output_dir)  # Main logic for generating distribution TSV files.
```
- calls: `FileNotFoundError`, `build_canonical_to_taxon_ids`, `cleanup_taxa_without_vernacular`, `csv.reader`, `download_backbone`, `extract_and_filter_taxa`, `extract_and_filter_vernacular`, `len`, `merge_taxref_into_vernacular`, `open`, `parse_taxref_french_names`, `print`
```python
def main()  # Main entry point for generate-distribution.
```
- calls: `Path`, `argparse.ArgumentParser`, `generate_distribution`

### Module: daynimal.db.import_gbif_utils
> GBIF Backbone Taxonomy - Shared utilities for import scripts.
> 
> This module contains common functions and constants used by both
> the standard and fast GBIF importers.
```python
def download_backbone(dest_path)  # Download the GBIF Backbone ZIP file with resume support.
```
- calls: `httpx.head`, `httpx.stream`, `int`, `len`, `open`, `print`
```python
def extract_canonical_name(scientific_name)  # Extract canonical name (genus + species only) from a scientific name.
```
- calls: `len`, `re.sub`
```python
def parse_int(value)  # Parse integer, returning None for empty strings.
```
- calls: `int`

### Module: daynimal.db.init_fts
> Initialize FTS5 (Full-Text Search) table for fast animal search.
> 
> FTS5 is a SQLite virtual table that provides efficient full-text search
> capabilities. This module creates and populates the taxa_fts table.
```python
def create_fts_table(session)  # Create the FTS5 virtual table for taxa search.
```
- calls: `print`, `text`
```python
def populate_fts_table(session)  # Populate the FTS5 table with data from taxa and vernacular_names tables.
```
- calls: `print`, `text`
```python
def init_fts(db_path)  # Initialize FTS5 search: create and populate the table.
```
- calls: `create_fts_table`, `get_session`, `populate_fts_table`, `print`
```python
def rebuild_fts()  # Rebuild the FTS5 table (useful after importing new taxa).
```
- calls: `get_session`, `print`, `text`
```python
def main()  # Main entry point for CLI command.
```
- calls: `argparse.ArgumentParser`, `init_fts`

### Module: daynimal.db.models
```python
class Base(DeclarativeBase)
```
```python
class TaxonModel(Base)  # Core taxonomy table imported from GBIF Backbone.
```
```python
class VernacularNameModel(Base)  # Vernacular (common) names for taxa in different languages.
```
```python
class EnrichmentCacheModel(Base)  # Cache for enrichment data from external APIs.
```
```python
class AnimalHistoryModel(Base)  # History of viewed animals.
```
```python
class UserSettingsModel(Base)  # User preferences and settings.
```
```python
class FavoriteModel(Base)  # User's favorite animals.
```
```python
def _utcnow()
```
- calls: `datetime.now`

### Module: daynimal.db.session
```python
def get_engine()  # Create and return SQLAlchemy engine.
```
- calls: `create_engine`
```python
def get_session()  # Create and return a new database session.
```
- calls: `get_engine`, `session_factory`, `sessionmaker`

### Module: daynimal.debug
> Debug utilities for Daynimal Flet app.
> 
> Provides logging configuration and utilities to capture application logs,
> stdout/stderr, and exceptions for easier debugging of the Flet application.
```python
class FletDebugger  # Centralized debugging system for Flet applications.
    def __init__(self, log_dir, log_to_console)  # Initialize the Flet debugger.
    # calls: Path, datetime.now, datetime.now.strftime, self._setup_logging, self.log_dir.mkdir
    def _setup_logging(self, log_to_console)  # Configure Python logging with file and optional console handlers.
    # calls: logging.FileHandler, logging.Formatter, logging.StreamHandler, logging.basicConfig, logging.getLogger, self.logger.addHandler, self.logger.handlers.clear, self.logger.setLevel
    def log_app_start(self)  # Log application startup.
    # calls: self.logger.info
    def log_app_stop(self)  # Log application shutdown.
    # calls: self.logger.info
    def log_view_change(self, view_name)  # Log navigation to a new view.
    # calls: self.logger.info
    def log_animal_load(self, mode, animal_name)  # Log animal loading.
    # calls: self.logger.info
    def log_search(self, query, results_count)  # Log search operation.
    # calls: self.logger.info
    def log_error(self, context, error)  # Log an error with context.
    # calls: self.logger.error, self.logger.exception, type
    def log_exception(self, exc_type, exc_value, exc_traceback)  # Log uncaught exception (for sys.excepthook).
    # calls: self.logger.critical
    def get_logger(self)  # Get the logger instance for custom logging.
    def print_log_location(self)  # Print the log file location to console.
    # calls: print, self.log_file.absolute
```
```python
def get_debugger(log_dir, log_to_console)  # Get or create the global debugger instance.
```
- calls: `FletDebugger`, `sys.__excepthook__`
```python
def log_info(message)  # Quick logging function - info level.
```
```python
def log_error(message)  # Quick logging function - error level.
```
```python
def log_debug(message)  # Quick logging function - debug level.
```

### Module: daynimal.main
> Daynimal CLI - Daily Animal Discovery
> 
> A command-line tool to discover and learn about animals every day.
```python
@contextmanager
def temporary_database(database_url)  # Context manager to temporarily set database_url without polluting global state.
```
```python
def print_animal(animal)  # Pretty print animal information with REQUIRED attributions.
```
- calls: `hasattr`, `len`, `list`, `print`
```python
def cmd_today()  # Show today's animal.
```
- calls: `AnimalRepository`, `print`, `print_animal`
```python
def cmd_random()  # Show a random animal.
```
- calls: `AnimalRepository`, `print`, `print_animal`
```python
def cmd_search(query)  # Search for animals.
```
- calls: `AnimalRepository`, `len`, `print`
```python
def cmd_info(name)  # Get detailed info about an animal.
```
- calls: `AnimalRepository`, `int`, `print`, `print_animal`
```python
def cmd_stats()  # Show database statistics.
```
- calls: `AnimalRepository`, `print`
```python
def cmd_credits()  # Show full legal credits and licenses.
```
- calls: `get_app_legal_notice`, `print`
```python
def cmd_history(page, per_page)  # Show history of viewed animals.
```
- calls: `AnimalRepository`, `print`
```python
def create_parser()  # Create and configure the argument parser.
```
- calls: `argparse.ArgumentParser`
```python
def main()  # Main entry point.
```
- calls: `cmd_credits`, `cmd_history`, `cmd_info`, `cmd_random`, `cmd_search`, `cmd_stats`, `cmd_today`, `create_parser`, `temporary_database`

### Module: daynimal.repository
> Animal Repository - aggregates data from local DB and external APIs.
> 
> This is the main interface for retrieving enriched animal information.
> It handles:
> - Querying the local GBIF-based taxonomy database
> - Fetching additional data from Wikidata, Wikipedia, Commons
> - Caching enrichment data locally
```python
class AnimalRepository  # Repository for accessing animal information.
    def __init__(self, session)
    # calls: get_session, threading.Lock
    @property
    def wikidata(self)
    # calls: WikidataAPI
    @property
    def wikipedia(self)
    # calls: WikipediaAPI
    @property
    def commons(self)
    # calls: CommonsAPI
    def close(self)  # Close all connections.
    # calls: self._commons.close, self._wikidata.close, self._wikipedia.close, self.session.close
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
    # calls: self.close
    def get_by_id(self, taxon_id, enrich)  # Get animal by GBIF taxon ID.
    # calls: AnimalInfo, self._enrich, self._model_to_taxon, self.session.get
    def get_by_name(self, scientific_name, enrich)  # Get animal by scientific name.
    # calls: AnimalInfo, or_, self._enrich, self._model_to_taxon, self.session.query, self.session.query.filter
    def search(self, query, limit)  # Search for animals by name (scientific or vernacular) using FTS5.
    # calls: AnimalInfo, TaxonModel.taxon_id.in_, func.lower, func.lower.contains, len, remove_accents, self._model_to_taxon, self.session.execute, self.session.execute.fetchall, self.session.query, self.session.query.filter, self.session.query.join, set, text
    def get_random(self, rank, prefer_unenriched, enrich)  # Get a random animal using fast ID-based selection.
    # calls: AnimalInfo, self._enrich, self._get_random_by_id_range, self._model_to_taxon
    def _get_random_by_id_range(self, rank, is_enriched)  # Fast random selection by ID range.
    # calls: TaxonModel.is_enriched.is_, func.max, func.min, random.randint, range, self.session.query, self.session.query.filter, self.session.query.first
    def get_animal_of_the_day(self, date)  # Get a consistent "animal of the day" based on the date.
    # calls: AnimalInfo, TaxonModel.is_synonym.is_, datetime.now, func.max, func.min, random.Random, self._enrich, self._model_to_taxon, self.session.query, self.session.query.filter, self.session.query.first
    def _enrich(self, animal, taxon_model)  # Enrich animal with data from external APIs (parallelized).
    # calls: ThreadPoolExecutor, datetime.now, self._fetch_and_cache_images, self._get_cached_images, self._get_cached_wikidata, self._get_cached_wikipedia, self.session.commit
    def _get_cached_wikidata(self, taxon_id)  # Load cached Wikidata from database.
    # calls: WikidataEntity, json.loads, self.session.query, self.session.query.filter
    def _get_cached_wikipedia(self, taxon_id)  # Load cached Wikipedia from database.
    # calls: WikipediaArticle, json.loads, self.session.query, self.session.query.filter
    def _get_cached_images(self, taxon_id)  # Load cached images from database.
    # calls: CommonsImage, json.loads, self.session.query, self.session.query.filter
    def _fetch_and_cache_wikidata(self, taxon_id, scientific_name)  # Fetch Wikidata and cache it.
    # calls: self._save_cache, self.wikidata.get_by_taxonomy
    def _fetch_and_cache_wikipedia(self, taxon_id, scientific_name)  # Fetch Wikipedia and cache it.
    # calls: self._save_cache, self.wikipedia.get_by_taxonomy
    def _fetch_and_cache_images(self, taxon_id, scientific_name, wikidata)  # Fetch Commons images and cache them.
    # calls: self._save_cache, self.commons.get_by_taxonomy, self.commons.get_images_for_wikidata
    def _save_cache(self, taxon_id, source, data)  # Save data to enrichment cache.
    # calls: EnrichmentCacheModel, datetime.now, isinstance, json.dumps, self._to_dict, self.session.add, self.session.commit, self.session.query, self.session.query.filter, self.session.rollback
    def _to_dict(self, obj)  # Convert dataclass to dict, handling enums.
    # calls: asdict, asdict.items, hasattr, is_dataclass
    def _model_to_taxon(self, model)  # Convert TaxonModel to Taxon schema.
    # calls: Taxon, TaxonomicRank
    def get_stats(self)  # Get database statistics.
    # calls: TaxonModel.is_enriched.is_, self.session.query, self.session.query.count, self.session.query.filter
    def add_to_history(self, taxon_id, command)  # Add an animal view to the history.
    # calls: AnimalHistoryModel, datetime.now, self.session.add, self.session.commit
    def get_history(self, page, per_page)  # Get history of viewed animals with pagination.
    # calls: AnimalHistoryModel.viewed_at.desc, AnimalInfo, joinedload, self._model_to_taxon, self.session.query, self.session.query.count, self.session.query.options
    def get_history_count(self)  # Get total number of history entries.
    # calls: self.session.query, self.session.query.count
    def clear_history(self)  # Clear all history entries.
    # calls: self.session.commit, self.session.query, self.session.query.count, self.session.query.delete
    def get_setting(self, key, default)  # Get a user setting by key.
    # calls: self.session.query, self.session.query.filter
    def set_setting(self, key, value)  # Set a user setting.
    # calls: UserSettingsModel, self.session.add, self.session.commit, self.session.query, self.session.query.filter, str
    def add_favorite(self, taxon_id)  # Add an animal to favorites.
    # calls: FavoriteModel, self.session.add, self.session.commit, self.session.query, self.session.query.filter
    def remove_favorite(self, taxon_id)  # Remove an animal from favorites.
    # calls: self.session.commit, self.session.delete, self.session.query, self.session.query.filter
    def is_favorite(self, taxon_id)  # Check if an animal is in favorites.
    # calls: self.session.query, self.session.query.filter
    def get_favorites(self, page, per_page)  # Get paginated list of favorite animals.
    # calls: AnimalInfo, FavoriteModel.added_at.desc, self._model_to_taxon, self.session.query, self.session.query.count, self.session.query.order_by
    def get_favorites_count(self)  # Get total number of favorites.
    # calls: self.session.query, self.session.query.count
```
```python
def remove_accents(text)  # Remove accents from text for better search matching.
```
- calls: `unicodedata.category`, `unicodedata.normalize`

### Module: daynimal.schemas
```python
class TaxonomicRank(str, Enum)
```
```python
class ConservationStatus(str, Enum)  # IUCN Red List categories.
```
```python
class License(str, Enum)  # Licenses compatible with commercial use.
```
```python
@dataclass
class Taxon  # Core taxonomic data from GBIF Backbone.
```
```python
@dataclass
class WikidataEntity  # Data retrieved from Wikidata.
```
```python
@dataclass
class WikipediaArticle  # Data retrieved from Wikipedia.
    @property
    def article_url(self)  # URL to the Wikipedia article.
    # calls: self.title.replace
    @property
    def license_url(self)  # URL to CC-BY-SA 4.0 license.
    def get_attribution_text(self)  # Generate required attribution text.
    def get_attribution_html(self)  # Generate HTML attribution with proper links.
```
```python
@dataclass
class CommonsImage  # Image data from Wikimedia Commons.
    @property
    def commons_page_url(self)  # URL to the image's page on Wikimedia Commons.
    # calls: self.filename.replace
    @property
    def license_url(self)  # URL to the license.
    def get_attribution_text(self)  # Generate required attribution text for this image.
    # calls: hasattr
    def get_attribution_html(self)  # Generate HTML attribution with proper links.
    # calls: hasattr
```
```python
@dataclass
class AnimalInfo  # Aggregated animal information from all sources.
    @property
    def display_name(self)  # Best name to display to users.
    # calls: self.taxon.vernacular_names.get
    @property
    def description(self)  # Best description available.
    @property
    def main_image(self)  # Primary image for display.
    def get_attribution_text(self)  # Generate complete attribution text for all data sources used.
    # calls: self.wikipedia.get_attribution_text
    def get_attribution_html(self)  # Generate complete HTML attribution for all data sources.
    # calls: self.wikipedia.get_attribution_html
    def get_required_attributions_summary(self)  # Get a summary of required attributions as a dictionary.
```

### Module: daynimal.sources.base
> Base class for external data sources.
```python
class DataSource(ABC, Generic)  # Abstract base class for external data sources.
    def __init__(self)
    @property
    def client(self)  # Lazy-initialized HTTP client.
    # calls: httpx.Client
    def close(self)  # Close the HTTP client.
    # calls: self._client.close
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
    # calls: self.close
    @property
    @abstractmethod
    def source_name(self)  # Name of the data source (e.g., 'wikidata', 'wikipedia').
    @property
    @abstractmethod
    def license(self)  # License of the data from this source.
    @abstractmethod
    def get_by_source_id(self, source_id)  # Fetch data using the source's native identifier.
    @abstractmethod
    def get_by_taxonomy(self, scientific_name)  # Fetch data using a scientific (taxonomic) name.
    @abstractmethod
    def search(self, query, limit)  # Search for entities matching a query.
```

### Module: daynimal.sources.commons
> Wikimedia Commons API client.
> 
> Wikimedia Commons only accepts free content that allows commercial use.
> Each image has its own license (CC-BY, CC-BY-SA, CC0, Public Domain).
> https://commons.wikimedia.org/wiki/Commons:Licensing
```python
class CommonsAPI(DataSource)  # Client for Wikimedia Commons API.
    @property
    def source_name(self)
    @property
    def license(self)
    def get_by_source_id(self, source_id)  # Fetch image info by filename.
    # calls: iter, next, self._parse_image_info, self.client.get
    def get_by_taxonomy(self, scientific_name, limit)  # Find images on Commons for a species by scientific name.
    # calls: self._search_category, self.search
    def search(self, query, limit)  # Search Commons for images matching query.
    # calls: self._parse_image_info, self.client.get
    def get_images_for_wikidata(self, qid, limit)  # Get images associated with a Wikidata entity.
    # calls: self._parse_image_info, self.client.get
    def _search_category(self, scientific_name, limit)  # Search for images in a species category.
    # calls: self._parse_image_info, self.client.get
    def _parse_image_info(self, filename, imageinfo)  # Parse image info from API response.
    # calls: CommonsImage, re.sub, re.sub.strip, self._is_valid_image_url, self._parse_license
    def _is_valid_image_url(self, url)  # Check if URL points to a valid image file.
    # calls: any
    def _parse_license(self, license_text)  # Parse license text to License enum.
```

### Module: daynimal.sources.wikidata
> Wikidata API client.
> 
> Wikidata content is licensed under CC0 (public domain).
> https://www.wikidata.org/wiki/Wikidata:Licensing
```python
class WikidataAPI(DataSource)  # Client for Wikidata API.
    @property
    def source_name(self)
    @property
    def license(self)
    def get_by_source_id(self, source_id)  # Fetch a Wikidata entity by its QID.
    # calls: self._parse_entity, self.client.get
    def get_by_taxonomy(self, scientific_name)  # Find a Wikidata entity by scientific name using SPARQL.
    # calls: self._find_taxon_qid, self.get_by_source_id
    def search(self, query, limit)  # Search Wikidata for entities matching query.
    # calls: self.client.get, self.get_by_source_id
    def _find_taxon_qid(self, scientific_name)  # Find QID for a taxon by its scientific name.
    # calls: self._search_taxon_qid, self.client.get
    def _search_taxon_qid(self, scientific_name)  # Fallback search for taxon QID.
    # calls: self._is_taxon, self.client.get
    def _is_taxon(self, qid)  # Check if an entity is a taxon (has P225 taxon name).
    # calls: bool, self.client.get
    def _parse_entity(self, qid, data)  # Parse raw Wikidata entity into WikidataEntity schema.
    # calls: WikidataEntity, int, self._get_claim_value, self._get_commons_url, self._get_quantity_string
    def _get_claim_value(self, claim_list, value_type)  # Extract value from a claim list.
    # calls: isinstance
    def _get_quantity_string(self, claim_list)  # Extract quantity with unit from a claim.
    def _get_commons_url(self, filename)  # Convert Commons filename to URL.
```

### Module: daynimal.sources.wikipedia
> Wikipedia API client.
> 
> Wikipedia content is licensed under CC-BY-SA 4.0.
> https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content
> 
> Commercial use is allowed with proper attribution and share-alike.
```python
class WikipediaAPI(DataSource)  # Client for Wikipedia API.
    def __init__(self, languages)  # Initialize Wikipedia API client.
    # calls: super, super.__init__
    @property
    def source_name(self)
    @property
    def license(self)
    def get_by_source_id(self, source_id, language)  # Fetch a Wikipedia article by page ID or title.
    # calls: WikipediaArticle, int, iter, next, self.client.get
    def get_by_taxonomy(self, scientific_name)  # Find a Wikipedia article by scientific name.
    # calls: self._search_in_language
    def search(self, query, limit, language)  # Search Wikipedia for articles matching query.
    # calls: self.client.get, self.get_by_source_id, str
    def get_full_article(self, page_id, language)  # Fetch full article content (not just summary).
    # calls: WikipediaArticle, self.client.get, str
    def _search_in_language(self, scientific_name, language)  # Search for an article by scientific name in a specific language.
    # calls: self.client.get, self.get_by_source_id, str
```

### Module: daynimal.ui.app_controller
> App controller for managing views and navigation.
```python
class AppController  # Main application controller.
    def __init__(self, page, debugger)  # Initialize AppController.
    # calls: AppState, FavoritesView, HistoryView, SearchView, SettingsView, StatsView, TodayView, asyncio.create_task, ft.Column, ft.NavigationBar, ft.NavigationBarDestination, get_debugger, self.load_animal_from_favorite, self.load_animal_from_history, self.load_animal_from_search
    def build(self)  # Build the app UI.
    # calls: ft.Column, self.show_today_view
    def on_nav_change(self, e)  # Handle navigation bar changes.
    # calls: len, self.debugger.log_view_change, self.show_favorites_view, self.show_history_view, self.show_search_view, self.show_settings_view, self.show_stats_view, self.show_today_view
    def show_today_view(self)  # Show the Today view.
    # calls: self.page.update, self.today_view.build
    def show_history_view(self)  # Show the History view.
    # calls: self.history_view.build, self.page.update
    def show_favorites_view(self)  # Show the Favorites view.
    # calls: self.favorites_view.build, self.page.update
    def show_search_view(self)  # Show the Search view.
    # calls: self.page.update, self.search_view.build
    def show_stats_view(self)  # Show the Stats view.
    # calls: self.page.update, self.stats_view.build
    def show_settings_view(self)  # Show the Settings view.
    # calls: self.page.update, self.settings_view.build
    async def load_animal_from_history(self, taxon_id)  # Load an animal from history and display in Today view.
    # calls: self._load_and_display_animal
    async def load_animal_from_favorite(self, taxon_id)  # Load an animal from favorites and display in Today view.
    # calls: self._load_and_display_animal
    async def load_animal_from_search(self, taxon_id)  # Load an animal from search and display in Today view.
    # calls: self._load_and_display_animal
    async def _load_and_display_animal(self, taxon_id, source, enrich, add_to_history)  # Unified method to load and display an animal in Today view.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, print, self.debugger.log_animal_load, self.debugger.log_error, self.debugger.logger.error, self.page.update, self.show_today_view, self.today_view._display_animal, str, traceback.format_exc
    def on_favorite_toggle(self, taxon_id, is_favorite)  # Handle favorite toggle from any view.
    # calls: ft.SnackBar, ft.Text, print, self.debugger.log_error, self.debugger.logger.error, self.page.update, str, traceback.format_exc
    def cleanup(self)  # Clean up resources.
    # calls: self.state.close_repository
```

### Module: daynimal.ui.components.animal_card
> Reusable animal card component for list views.
> 
> This module provides a clickable card widget used in History, Favorites, and Search views.
> Eliminates 3 duplications from the original app.py.
```python
class AnimalCard(ft.Card)  # Reusable animal card for displaying an animal in a list.
    def __init__(self, animal, on_click, metadata_icon, metadata_text, metadata_icon_color)  # Initialize animal card.
    # calls: ft.Column, ft.Container, ft.Icon, ft.Row, ft.Text, on_click, super, super.__init__
```
```python
def create_history_card(animal, on_click, viewed_at_str)  # Create an animal card for History view.
```
- calls: `AnimalCard`
```python
def create_favorite_card(animal, on_click)  # Create an animal card for Favorites view.
```
- calls: `AnimalCard`
```python
def create_search_card(animal, on_click)  # Create an animal card for Search view.
```
- calls: `AnimalCard`, `iter`, `len`, `next`

### Module: daynimal.ui.components.animal_display
> Animal display component for showing detailed animal information.
```python
class AnimalDisplay  # Component for displaying detailed animal information.
    def __init__(self, animal)  # Initialize AnimalDisplay.
    def build(self)  # Build the animal display UI.
    # calls: ft.Divider, ft.Text, self._build_classification, self._build_vernacular_names, self._build_wikidata_info, self._build_wikipedia_description, self.animal.display_name.upper
    def _build_classification(self)  # Build classification section.
    # calls: any, ft.Divider, ft.Text
    def _build_vernacular_names(self)  # Build vernacular names section.
    # calls: ft.Divider, ft.Text, len, list, self.animal.taxon.vernacular_names
    def _build_wikidata_info(self)  # Build Wikidata information section.
    # calls: ft.Divider, ft.Text, hasattr
    def _build_wikipedia_description(self)  # Build Wikipedia description section.
    # calls: ft.Divider, ft.Text
```

### Module: daynimal.ui.components.image_carousel
> Image carousel component for displaying animal images with navigation.
```python
class ImageCarousel  # Image carousel with navigation controls.
    def __init__(self, images, current_index, on_index_change, animal_display_name, animal_taxon_id)  # Initialize ImageCarousel.
    def build(self)  # Build the carousel UI.
    # calls: ft.Column, ft.Container, ft.IconButton, ft.Image, ft.Row, ft.Text, len, self._build_empty_state, self._build_error_content
    def _build_empty_state(self)  # Build the empty state UI when no images available.
    # calls: ft.Column, ft.Container, ft.Icon, ft.Text
    def _build_error_content(self, image)  # Build the error content for failed image loads.
    # calls: ft.Column, ft.Container, ft.Icon, ft.Text
    def _on_prev(self, e)  # Navigate to previous image.
    # calls: len, self.on_index_change
    def _on_next(self, e)  # Navigate to next image.
    # calls: len, self.on_index_change
```

### Module: daynimal.ui.components.widgets
> Reusable UI widgets for Daynimal app.
> 
> This module eliminates code duplication by providing common widgets
> used across multiple views.
```python
class LoadingWidget(ft.Container)  # Loading indicator widget.
    def __init__(self, message)  # Initialize loading widget.
    # calls: ft.Column, ft.ProgressRing, ft.Text, super, super.__init__
```
```python
class ErrorWidget(ft.Container)  # Error display widget.
    def __init__(self, title, details)  # Initialize error widget.
    # calls: ft.Column, ft.Icon, ft.Text, super, super.__init__
```
```python
class EmptyStateWidget(ft.Container)  # Empty state widget.
    def __init__(self, icon, title, description, icon_size, icon_color)  # Initialize empty state widget.
    # calls: ft.Column, ft.Icon, ft.Text, super, super.__init__
```

### Module: daynimal.ui.state
> Application state management for Daynimal UI.
> 
> This module provides centralized state management for the Flet application,
> including repository lifecycle, current animal display, and caching.
```python
@dataclass
class AppState  # Shared application state across all views.
    @property
    def repository(self)  # Get or create repository (lazy initialization, thread-safe).
    # calls: AnimalRepository
    def close_repository(self)  # Close repository and cleanup resources.
    # calls: self._repository.close
    def reset_animal_display(self)  # Reset animal display state (used when loading new animal).
```

### Module: daynimal.ui.utils.debounce
> Debouncing utility for UI inputs.
> 
> This module provides a Debouncer class to prevent excessive function calls
> when user input changes rapidly (e.g., search field).
```python
class Debouncer  # Debouncer to delay function execution until input stabilizes.
    def __init__(self, delay)  # Initialize debouncer.
    async def debounce(self, func)  # Execute function after delay, cancelling previous pending calls.
    # calls: asyncio.create_task, self._debounced_call, self._task.cancel, self._task.done
    async def _debounced_call(self, func)  # Internal method to wait and execute function.
    # calls: asyncio.sleep, func
```

### Module: daynimal.ui.views.base
> Base view class for Daynimal UI.
> 
> All views inherit from BaseView to ensure consistent interface and behavior.
```python
class BaseView(ABC)  # Abstract base class for all views in the Daynimal app.
    def __init__(self, page, app_state, debugger)  # Initialize base view.
    # calls: ft.Column
    @abstractmethod
    def build(self)  # Build the view's UI.
    async def refresh(self)  # Refresh view data.
    def show_loading(self, message)  # Show loading indicator.
    # calls: LoadingWidget, self.page.update
    def show_error(self, title, details)  # Show error state.
    # calls: ErrorWidget, self.page.update
    def show_empty_state(self, icon, title, description, icon_size, icon_color)  # Show empty state.
    # calls: EmptyStateWidget, self.page.update
    def log_info(self, message)  # Log info message (with fallback to print).
    # calls: print, self.debugger.logger.info
    def log_error(self, context, error)  # Log error message (with fallback to print).
    # calls: print, self.debugger.log_error
```

### Module: daynimal.ui.views.favorites_view
> Favorites view for displaying favorite animals.
```python
class FavoritesView(BaseView)  # View for displaying and managing favorite animals.
    def __init__(self, page, app_state, on_animal_click, debugger)  # Initialize FavoritesView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the favorites view UI.
    # calls: asyncio.create_task, ft.Column, ft.Container, ft.Divider, ft.Row, ft.Text, self.load_favorites
    async def load_favorites(self)  # Load favorites from repository.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Card, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Row, ft.Text, print, self.app_state.repository.get_favorites, self.debugger.log_error, self.debugger.logger.error, self.page.update, str, traceback.format_exc
    def _on_favorite_item_click(self, e)  # Handle click on a favorite item.
    # calls: print, self.debugger.log_error, self.debugger.logger.error, self.debugger.logger.info, self.on_animal_click, traceback.format_exc
```

### Module: daynimal.ui.views.history_view
> History view for displaying animal viewing history.
```python
class HistoryView(BaseView)  # View for displaying and managing animal viewing history.
    def __init__(self, page, app_state, on_animal_click, debugger)  # Initialize HistoryView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the history view UI.
    # calls: asyncio.create_task, ft.Column, ft.Container, ft.Divider, ft.Row, ft.Text, self.load_history
    async def load_history(self)  # Load history from repository.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Card, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Row, ft.Text, print, self.app_state.repository.get_history, self.debugger.log_error, self.debugger.logger.error, self.page.update, str, traceback.format_exc
    def _on_history_item_click(self, e)  # Handle click on history item - load animal and switch to Today view.
    # calls: print, self.debugger.log_error, self.debugger.logger.error, self.debugger.logger.info, self.on_animal_click, traceback.format_exc
```

### Module: daynimal.ui.views.search_view
> Search view for Daynimal app.
> 
> This module provides the search interface with a classic search field
> (submit on Enter or button click).
```python
class SearchView(BaseView)  # Search view with search field and results list.
    def __init__(self, page, app_state, on_result_click, debugger)  # Initialize search view.
    # calls: ft.Column, ft.IconButton, ft.TextField, super, super.__init__
    def build(self)  # Build the search view UI.
    # calls: ft.Container, ft.Divider, ft.Icon, ft.Padding, ft.Row, ft.Text, self.show_empty_search_state
    async def refresh(self)  # Refresh search view (no-op for search view).
    def _on_submit(self, e)  # Handle Enter key in search field.
    # calls: asyncio.create_task, self.perform_search, self.search_field.value.strip
    def _on_search_click(self, e)  # Handle search button click.
    # calls: asyncio.create_task, self.perform_search, self.search_field.value.strip
    def show_empty_search_state(self)  # Show empty state (before any search).
    # calls: ft.Column, ft.Container, ft.Icon, ft.Text
    async def perform_search(self, query)  # Perform search in repository.
    # calls: asyncio.sleep, asyncio.to_thread, create_search_card, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, len, self.app_state.repository.search, self.log_error, self.log_info, self.page.update, str
```

### Module: daynimal.ui.views.settings_view
> Settings view for app configuration and credits.
```python
class SettingsView(BaseView)  # View for app settings, preferences, and credits.
    def __init__(self, page, app_state, debugger)  # Initialize SettingsView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the settings view UI.
    # calls: asyncio.create_task, self._load_settings
    async def _load_settings(self)  # Load settings and build the UI.
    # calls: asyncio.to_thread, ft.Column, ft.Container, ft.Divider, ft.Icon, ft.Padding, ft.Row, ft.Switch, ft.Text, print, self.debugger.log_error, self.debugger.logger.error, self.page.update, str, traceback.format_exc
    def _on_theme_toggle(self, e)  # Handle theme toggle switch change.
    # calls: print, self.app_state.repository.set_setting, self.debugger.log_error, self.debugger.logger.error, self.debugger.logger.info, self.page.update, traceback.format_exc
```

### Module: daynimal.ui.views.stats_view
> Statistics view for displaying database statistics.
```python
class StatsView(BaseView)  # View for displaying database statistics with responsive cards.
    def __init__(self, page, app_state, debugger)  # Initialize StatsView.
    # calls: ft.Row, super, super.__init__
    def build(self)  # Build the statistics view UI.
    # calls: asyncio.create_task, ft.Column, ft.Container, ft.Divider, ft.Row, ft.Text, self._display_stats, self.load_stats, self.page.update
    def _display_stats(self, stats)  # Display statistics cards.
    # calls: ft.Card, ft.Column, ft.Container, ft.Icon, ft.Text
    async def load_stats(self)  # Load statistics from repository.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, print, self._display_stats, self.app_state.repository.get_stats, self.debugger.log_error, self.debugger.logger.error, self.page.update, str, traceback.format_exc
```

### Module: daynimal.ui.views.today_view
> Today view for displaying the animal of the day or random animals.
```python
class TodayView(BaseView)  # View for displaying the animal of the day or random animals.
    def __init__(self, page, app_state, on_favorite_toggle, debugger)  # Initialize TodayView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the today view UI.
    # calls: ft.Button, ft.ButtonStyle, ft.Column, ft.Container, ft.Divider, ft.Icon, ft.Padding, ft.Row, ft.Text, self._display_animal
    async def _load_today_animal(self, e)  # Load today's animal.
    # calls: self._load_animal_for_today_view
    async def _load_random_animal(self, e)  # Load a random animal.
    # calls: self._load_animal_for_today_view
    async def _load_animal_for_today_view(self, mode)  # Load and display an animal in the Today view.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, print, self._display_animal, self.debugger.log_animal_load, self.debugger.log_error, self.debugger.logger.error, self.page.update, str, traceback.format_exc
    def _display_animal(self, animal)  # Display animal information in the Today view.
    # calls: AnimalDisplay, ImageCarousel, ft.Container, ft.Divider, ft.IconButton, ft.Padding, ft.Row, ft.Text, len, self.app_state.repository.is_favorite, self.page.update
    def _on_favorite_toggle(self, e)  # Handle favorite button toggle.
    # calls: self._display_animal, self.app_state.repository.is_favorite, self.on_favorite_toggle_callback
    def _on_image_index_change(self, new_index)  # Handle image index change in carousel.
    # calls: self._display_animal
```

### Module: debug.debug_filter
> Filter and display relevant logs from Daynimal application.
> 
> This script filters out verbose Flet internal logs and shows only
> application-level events (INFO, WARNING, ERROR, CRITICAL).
> 
> Usage (from project root):
>     python debug/debug_filter.py                    # Show filtered latest log
>     python debug/debug_filter.py --tail             # Follow filtered log
>     python debug/debug_filter.py --errors-only      # Show only errors
>     python debug/debug_filter.py --search "keyword" # Search for specific keyword
```python
def get_latest_log()  # Get the most recent log file.
```
- calls: `Path`, `sorted`
```python
def filter_line(line, errors_only, search)  # Determine if a line should be displayed.
```
- calls: `any`
```python
def colorize_log_line(line)  # Add color to log lines based on level (ANSI escape codes).
```
```python
def show_filtered_log(log_file, errors_only, search, colorize)  # Display filtered log file.
```
- calls: `colorize_log_line`, `filter_line`, `open`, `print`, `sys.stdout.isatty`
```python
def tail_filtered_log(log_file, errors_only, search)  # Follow log file and display filtered lines in real-time.
```
- calls: `colorize_log_line`, `filter_line`, `open`, `print`, `sys.stdout.isatty`, `time.sleep`
```python
def show_statistics(log_file)  # Show statistics about the log file.
```
- calls: `open`, `print`
```python
def main()  # Main entry point.
```
- calls: `argparse.ArgumentParser`, `get_latest_log`, `print`, `show_filtered_log`, `show_statistics`, `sys.exit`, `tail_filtered_log`

### Module: debug.run_app_debug
> Debug launcher for Daynimal Flet application.
> 
> This script launches the Flet app with full debug logging enabled.
> Logs are written to logs/ directory with timestamps.
> 
> Usage (from project root):
>     python debug/run_app_debug.py              # Run with console logs
>     python debug/run_app_debug.py --quiet      # Run without console logs (file only)
>     python debug/run_app_debug.py --tail       # Run and tail the log file in parallel
```python
def main()  # Launch the Flet app with debugging enabled.
```
- calls: `DaynimalApp`, `argparse.ArgumentParser`, `ft.run`, `get_debugger`, `print`, `subprocess.Popen`

### Module: debug.view_logs
> Utility script to view Daynimal logs.
> 
> Usage (from project root):
>     python debug/view_logs.py              # Show latest log file
>     python debug/view_logs.py --tail       # Follow latest log file (real-time)
>     python debug/view_logs.py --list       # List all log files
>     python debug/view_logs.py --all        # Show all logs concatenated
```python
def get_log_files()  # Get all log files sorted by modification time (newest first).
```
- calls: `Path`, `sorted`
```python
def show_latest_log(tail)  # Show or tail the latest log file.
```
- calls: `get_log_files`, `open`, `print`, `str`, `subprocess.run`
```python
def list_log_files()  # List all log files with their sizes and timestamps.
```
- calls: `Path`, `Path.stat`, `datetime.fromtimestamp`, `datetime.fromtimestamp.strftime`, `get_log_files`, `len`, `print`
```python
def show_all_logs()  # Show all log files concatenated.
```
- calls: `get_log_files`, `len`, `open`, `print`, `reversed`
```python
def main()  # Main entry point.
```
- calls: `argparse.ArgumentParser`, `list_log_files`, `show_all_logs`, `show_latest_log`

### Module: generate_architecture
```python
def is_excluded(path)
```
- calls: `any`
```python
def find_python_files()
```
- calls: `Path`, `is_excluded`, `os.walk`
```python
def _parse_tree(file_path)  # Parse a Python file into an AST, or return None on error.
```
- calls: `ast.parse`
```python
def _parse_imports_from_tree(tree)  # Extract import paths from an already-parsed AST.
```
- calls: `ast.walk`, `isinstance`, `set`
```python
def _extract_known_names(tree)  # Extract imported names and top-level definitions.
```
- calls: `ast.iter_child_nodes`, `ast.walk`, `isinstance`, `set`
```python
def resolve_import(imp, internal_modules)  # Resolve an import path to an internal module name, or None.
```
```python
def _get_dotted_name(node)  # Reconstruct full dotted name from an AST expression (e.g. self.page.update).
```
- calls: `_get_dotted_name`, `isinstance`
```python
def _extract_calls(node, known_names)  # Extract architecturally meaningful call names from an AST node.
```
- calls: `_get_dotted_name`, `ast.walk`, `isinstance`, `len`, `set`
```python
def _get_decorators(node)  # Extract decorator names from a function/method/class node.
```
- calls: `_get_dotted_name`
```python
def _get_bases(node)  # Extract base class names from a ClassDef node.
```
- calls: `_get_dotted_name`
```python
def extract_signatures_and_calls(tree, known_names)  # Extract classes, functions, calls, and entry point info from a parsed AST.
```
- calls: `_extract_calls`, `_get_bases`, `_get_decorators`, `ast.get_docstring`, `ast.iter_child_nodes`, `isinstance`, `sorted`
```python
def detect_layer(path)  # Group modules by their actual parent directory.
```
- calls: `len`
```python
def generate()
```
- calls: `Counter`, `_extract_known_names`, `_parse_imports_from_tree`, `_parse_tree`, `ast.get_docstring`, `defaultdict`, `detect_layer`, `extract_signatures_and_calls`, `find_python_files`, `len`, `list`, `open`, `print`, `resolve_import`, `set`, `sorted`, `tuple`, `zip`

## 6. High-Coupling Modules (Risk Zones)
- No obvious high-coupling modules detected

## 7. Dependency Cycles Detected
- No obvious cycles detected
