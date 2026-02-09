# Architecture Overview

## 1. Project Structure

### Unclassified
- daynimal.__init__
- daynimal.app
- daynimal.attribution
- daynimal.config
- daynimal.debug
- daynimal.main
- daynimal.repository
- daynimal.schemas
- daynimal.sources.__init__
- daynimal.sources.base
- daynimal.sources.wikidata
- daynimal.sources.wikipedia
- daynimal.ui.__init__
- daynimal.ui.app_controller
- daynimal.ui.components.__init__
- daynimal.ui.components.animal_card
- daynimal.ui.components.animal_display
- daynimal.ui.components.image_carousel
- daynimal.ui.components.widgets
- daynimal.ui.state
- daynimal.ui.views.__init__
- daynimal.ui.views.base
- daynimal.ui.views.favorites_view
- daynimal.ui.views.history_view
- daynimal.ui.views.search_view
- daynimal.ui.views.settings_view
- daynimal.ui.views.stats_view
- daynimal.ui.views.today_view
- debug.debug_filter
- debug.run_app_debug
- debug.view_logs
- generate_architecture

### Infrastructure
- daynimal.db.__init__
- daynimal.db.build_db
- daynimal.db.generate_distribution
- daynimal.db.import_gbif_utils
- daynimal.db.init_fts
- daynimal.db.migrate_add_favorites
- daynimal.db.migrate_add_history
- daynimal.db.migrate_add_user_settings
- daynimal.db.session

### Domain
- daynimal.db.models

### Utils
- daynimal.sources.commons
- daynimal.ui.utils.__init__
- daynimal.ui.utils.debounce

## 2. Entry Points
- daynimal.app
- daynimal.main
- daynimal.db.build_db
- daynimal.db.generate_distribution
- daynimal.db.init_fts
- daynimal.db.migrate_add_favorites
- daynimal.db.migrate_add_user_settings
- debug.debug_filter
- debug.run_app_debug
- debug.view_logs

## 3. Internal Dependencies

## 4. External Dependencies
- daynimal (used 33 times)
- flet (used 14 times)
- pathlib (used 11 times)
- argparse (used 9 times)
- typing (used 9 times)
- asyncio (used 8 times)
- datetime (used 6 times)
- sys (used 6 times)
- sqlalchemy (used 6 times)
- traceback (used 6 times)
- dataclasses (used 4 times)
- logging (used 2 times)
- threading (used 2 times)
- csv (used 2 times)
- re (used 2 times)
- httpx (used 2 times)
- sqlite3 (used 2 times)
- abc (used 2 times)
- subprocess (used 2 times)
- ast (used 1 times)
- collections (used 1 times)
- os (used 1 times)
- pydantic_settings (used 1 times)
- contextlib (used 1 times)
- random (used 1 times)
- json (used 1 times)
- unicodedata (used 1 times)
- concurrent (used 1 times)
- enum (used 1 times)
- io (used 1 times)
- zipfile (used 1 times)
- time (used 1 times)

## 5. Signatures and Calls

### Module: generate_architecture
```python
def is_excluded(path)
```
```python
def find_python_files()
```
```python
def parse_imports(file_path)
```
```python
def add_parents(tree)
```
```python
def extract_signatures_and_calls(file_path)  # Retourne dict avec classes/methods/fonctions + dépendances internes
```
```python
def detect_layer(path)
```
```python
def has_main(file_path)
```
```python
def generate()
```

### Module: daynimal.app
```python
class DaynimalApp  # Main application class for Daynimal Flet app.
    def __init__(self, page)
    def build(self)  # Build the user interface.
    def _load_theme(self)  # Load theme setting from database and apply to page.
    def cleanup(self)  # Clean up resources (close connections, database, etc.).
    def on_disconnect(self, e)  # Handle page disconnect event (when user closes the window).
    def on_close(self, e)  # Handle page close event.
    # calls: build, get, hasattr, info, isinstance
    # calls: AppController, _load_theme, add, build, update
    # calls: AnimalRepository, get_setting
    # calls: cleanup, error, hasattr, info
    # calls: cleanup, error, info
    # calls: cleanup, error, info
```
```python
def main()  # Main entry point for the Flet app.
```
```python
def app_main(page)
```

### Module: daynimal.attribution
```python
class AttributionInfo  # Attribution information for a single data source.
    def to_text(self, format)  # Generate attribution text.
    def _full_text(self)  # Generate full attribution text.
    def _short_text(self)  # Generate short attribution text.
    def to_html(self)  # Generate HTML attribution with links.
    # calls: _full_text, _short_text
    # calls: append, join
    # calls: append, join
```
```python
class DataAttribution  # Complete attribution for an animal's data.
    def get_all(self)  # Get all attributions as a list.
    def to_text(self, format)  # Generate complete attribution text.
    def to_html(self)  # Generate HTML attribution block.
    def get_required_attributions(self)  # Get only attributions that are legally required (non-CC0).
    # calls: append, extend
    # calls: append, get_all, join, to_text
    # calls: get_all, join, to_html
    # calls: get_all
```
```python
def create_wikidata_attribution(qid)  # Create attribution for a specific Wikidata entity.
```
```python
def create_wikipedia_attribution(title, language, url, modified)  # Create attribution for a Wikipedia article.
```
```python
def create_commons_attribution(filename, author, license, url)  # Create attribution for a Wikimedia Commons image.
```
```python
def get_app_legal_notice(format)  # Get the application's legal notice for display in About page.
```

### Module: daynimal.config
```python
class Settings
```
```python
class Config
```

### Module: daynimal.debug
```python
class FletDebugger  # Centralized debugging system for Flet applications.
    def __init__(self, log_dir, log_to_console)  # Initialize the Flet debugger.
    def _setup_logging(self, log_to_console)  # Configure Python logging with file and optional console handlers.
    def log_app_start(self)  # Log application startup.
    def log_app_stop(self)  # Log application shutdown.
    def log_view_change(self, view_name)  # Log navigation to a new view.
    def log_animal_load(self, mode, animal_name)  # Log animal loading.
    def log_search(self, query, results_count)  # Log search operation.
    def log_error(self, context, error)  # Log an error with context.
    def log_exception(self, exc_type, exc_value, exc_traceback)  # Log uncaught exception (for sys.excepthook).
    def get_logger(self)  # Get the logger instance for custom logging.
    def print_log_location(self)  # Print the log file location to console.
    # calls: Path, _setup_logging, mkdir, now, strftime
    # calls: FileHandler, Formatter, StreamHandler, addHandler, basicConfig, clear, getLogger, setFormatter, setLevel
    # calls: info
    # calls: info
    # calls: info
    # calls: info
    # calls: info
    # calls: error, exception, type
    # calls: critical
    # calls: absolute, print
```
```python
def get_debugger(log_dir, log_to_console)  # Get or create the global debugger instance.
```
```python
def log_info(message)  # Quick logging function - info level.
```
```python
def log_error(message)  # Quick logging function - error level.
```
```python
def log_debug(message)  # Quick logging function - debug level.
```
```python
def exception_handler(exc_type, exc_value, exc_traceback)
```

### Module: daynimal.main
```python
def temporary_database(database_url)  # Context manager to temporarily set database_url without polluting global state.
```
```python
def print_animal(animal)  # Pretty print animal information with REQUIRED attributions.
```
```python
def cmd_today()  # Show today's animal.
```
```python
def cmd_random()  # Show a random animal.
```
```python
def cmd_search(query)  # Search for animals.
```
```python
def cmd_info(name)  # Get detailed info about an animal.
```
```python
def cmd_stats()  # Show database statistics.
```
```python
def cmd_credits()  # Show full legal credits and licenses.
```
```python
def cmd_history(page, per_page)  # Show history of viewed animals.
```
```python
def create_parser()  # Create and configure the argument parser.
```
```python
def main()  # Main entry point.
```

### Module: daynimal.repository
```python
class AnimalRepository  # Repository for accessing animal information.
    def __init__(self, session)
    def wikidata(self)
    def wikipedia(self)
    def commons(self)
    def close(self)  # Close all connections.
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
    def get_by_id(self, taxon_id, enrich)  # Get animal by GBIF taxon ID.
    def get_by_name(self, scientific_name, enrich)  # Get animal by scientific name.
    def search(self, query, limit)  # Search for animals by name (scientific or vernacular) using FTS5.
    def get_random(self, rank, prefer_unenriched, enrich)  # Get a random animal using fast ID-based selection.
    def _get_random_by_id_range(self, rank, is_enriched)  # Fast random selection by ID range.
    def get_animal_of_the_day(self, date)  # Get a consistent "animal of the day" based on the date.
    def _enrich(self, animal, taxon_model)  # Enrich animal with data from external APIs (parallelized).
    def _get_cached_wikidata(self, taxon_id)  # Load cached Wikidata from database.
    def _get_cached_wikipedia(self, taxon_id)  # Load cached Wikipedia from database.
    def _get_cached_images(self, taxon_id)  # Load cached images from database.
    def _fetch_and_cache_wikidata(self, taxon_id, scientific_name)  # Fetch Wikidata and cache it.
    def _fetch_and_cache_wikipedia(self, taxon_id, scientific_name)  # Fetch Wikipedia and cache it.
    def _fetch_and_cache_images(self, taxon_id, scientific_name, wikidata)  # Fetch Commons images and cache them.
    def _save_cache(self, taxon_id, source, data)  # Save data to enrichment cache.
    def _to_dict(self, obj)  # Convert dataclass to dict, handling enums.
    def _model_to_taxon(self, model)  # Convert TaxonModel to Taxon schema.
    def get_stats(self)  # Get database statistics.
    def add_to_history(self, taxon_id, command)  # Add an animal view to the history.
    def get_history(self, page, per_page)  # Get history of viewed animals with pagination.
    def get_history_count(self)  # Get total number of history entries.
    def clear_history(self)  # Clear all history entries.
    def get_setting(self, key, default)  # Get a user setting by key.
    def set_setting(self, key, value)  # Set a user setting.
    def add_favorite(self, taxon_id)  # Add an animal to favorites.
    def remove_favorite(self, taxon_id)  # Remove an animal from favorites.
    def is_favorite(self, taxon_id)  # Check if an animal is in favorites.
    def get_favorites(self, page, per_page)  # Get paginated list of favorite animals.
    def get_favorites_count(self)  # Get total number of favorites.
    # calls: Lock, get_session
    # calls: WikidataAPI
    # calls: WikipediaAPI
    # calls: CommonsAPI
    # calls: close
    # calls: close
    # calls: AnimalInfo, _enrich, _model_to_taxon, get
    # calls: AnimalInfo, _enrich, _model_to_taxon, filter, first, or_, query
    # calls: AnimalInfo, _model_to_taxon, add, all, append, contains, execute, fetchall, filter, in_, join, len, limit, lower, query, remove_accents, set, text, update
    # calls: AnimalInfo, _enrich, _get_random_by_id_range, _model_to_taxon
    # calls: filter, first, is_, max, min, query, randint, range
    # calls: AnimalInfo, Random, _enrich, _model_to_taxon, filter, first, is_, max, min, now, order_by, query, randint
    # calls: ThreadPoolExecutor, _fetch_and_cache_images, _get_cached_images, _get_cached_wikidata, _get_cached_wikipedia, commit, error, items, now, result, submit
    # calls: WikidataEntity, filter, first, loads, query
    # calls: WikipediaArticle, filter, first, loads, query
    # calls: CommonsImage, filter, first, loads, query
    # calls: _save_cache, get_by_taxonomy, warning
    # calls: _save_cache, get_by_taxonomy, warning
    # calls: _save_cache, get_by_taxonomy, get_images_for_wikidata, warning
    # calls: EnrichmentCacheModel, _to_dict, add, commit, dumps, filter, first, isinstance, now, query, rollback
    # calls: asdict, hasattr, is_dataclass, items
    # calls: Taxon, TaxonomicRank, append
    # calls: count, filter, is_, query
    # calls: AnimalHistoryModel, add, commit, now
    # calls: AnimalInfo, _model_to_taxon, all, append, count, desc, joinedload, limit, offset, options, order_by, query, warning
    # calls: count, query
    # calls: commit, count, delete, query
    # calls: filter, first, query
    # calls: UserSettingsModel, add, commit, filter, first, query, str
    # calls: FavoriteModel, add, commit, filter, first, query
    # calls: commit, delete, filter, first, query
    # calls: filter, first, query
    # calls: AnimalInfo, _model_to_taxon, all, append, count, desc, limit, offset, order_by, query
    # calls: count, query
```
```python
def remove_accents(text)  # Remove accents from text for better search matching.
```

### Module: daynimal.schemas
```python
class TaxonomicRank
```
```python
class ConservationStatus  # IUCN Red List categories.
```
```python
class License  # Licenses compatible with commercial use.
```
```python
class Taxon  # Core taxonomic data from GBIF Backbone.
```
```python
class WikidataEntity  # Data retrieved from Wikidata.
```
```python
class WikipediaArticle  # Data retrieved from Wikipedia.
    def article_url(self)  # URL to the Wikipedia article.
    def license_url(self)  # URL to CC-BY-SA 4.0 license.
    def get_attribution_text(self)  # Generate required attribution text.
    def get_attribution_html(self)  # Generate HTML attribution with proper links.
    # calls: replace
```
```python
class CommonsImage  # Image data from Wikimedia Commons.
    def commons_page_url(self)  # URL to the image's page on Wikimedia Commons.
    def license_url(self)  # URL to the license.
    def get_attribution_text(self)  # Generate required attribution text for this image.
    def get_attribution_html(self)  # Generate HTML attribution with proper links.
    # calls: replace
    # calls: get
    # calls: hasattr
    # calls: hasattr
```
```python
class AnimalInfo  # Aggregated animal information from all sources.
    def display_name(self)  # Best name to display to users.
    def description(self)  # Best description available.
    def main_image(self)  # Primary image for display.
    def get_attribution_text(self)  # Generate complete attribution text for all data sources used.
    def get_attribution_html(self)  # Generate complete HTML attribution for all data sources.
    def get_required_attributions_summary(self)  # Get a summary of required attributions as a dictionary.
    # calls: get
    # calls: append, get_attribution_text, join
    # calls: append, get_attribution_html, join
```

### Module: daynimal.__init__

### Module: daynimal.db.build_db
```python
def optimize_database_for_import(engine)  # Configure SQLite for maximum import speed.
```
```python
def restore_database_settings(engine)  # Restore normal database settings after import.
```
```python
def bulk_import_taxa(engine, tsv_path)  # Import taxa from TSV file using optimized bulk insert.
```
```python
def bulk_import_vernacular(engine, tsv_path)  # Import vernacular names from TSV file using optimized bulk insert.
```
```python
def build_database(taxa_tsv, vernacular_tsv, db_filename)  # Build a SQLite database from distribution TSV files.
```
```python
def main()  # Main entry point for build-db.
```

### Module: daynimal.db.generate_distribution
```python
def extract_and_filter_taxa(zip_path, output_path, mode)  # Extract taxa from GBIF ZIP and create a filtered TSV file.
```
```python
def extract_and_filter_vernacular(zip_path, output_path, valid_taxon_ids)  # Extract vernacular names from GBIF ZIP and create a filtered TSV file.
```
```python
def build_canonical_to_taxon_ids(taxa_tsv)  # Build a mapping from lowercase canonical_name to taxon_id from the taxa TSV.
```
```python
def parse_taxref_french_names(taxref_path)  # Parse TAXREF file and extract unique French vernacular names for Animalia.
```
```python
def merge_taxref_into_vernacular(vernacular_tsv, taxref_entries, canonical_to_id)  # Append TAXREF French names to the vernacular TSV, avoiding duplicates.
```
```python
def cleanup_taxa_without_vernacular(taxa_tsv, vernacular_tsv, output_taxa_tsv)  # Filter taxa TSV to keep only taxa that have at least one vernacular name.
```
```python
def generate_distribution(mode, backbone_path, taxref_path, output_dir)  # Main logic for generating distribution TSV files.
```
```python
def main()  # Main entry point for generate-distribution.
```

### Module: daynimal.db.import_gbif_utils
```python
def download_backbone(dest_path)  # Download the GBIF Backbone ZIP file with resume support.
```
```python
def extract_canonical_name(scientific_name)  # Extract canonical name (genus + species only) from a scientific name.
```
```python
def parse_int(value)  # Parse integer, returning None for empty strings.
```

### Module: daynimal.db.init_fts
```python
def create_fts_table(session)  # Create the FTS5 virtual table for taxa search.
```
```python
def populate_fts_table(session)  # Populate the FTS5 table with data from taxa and vernacular_names tables.
```
```python
def init_fts(db_path)  # Initialize FTS5 search: create and populate the table.
```
```python
def rebuild_fts()  # Rebuild the FTS5 table (useful after importing new taxa).
```
```python
def main()  # Main entry point for CLI command.
```

### Module: daynimal.db.migrate_add_favorites
```python
def migrate_add_favorites(db_path)  # Add favorites table to database.
```
```python
def main()  # Main entry point for migration script.
```

### Module: daynimal.db.migrate_add_history
```python
def migrate()  # Create the animal_history table if it doesn't exist.
```

### Module: daynimal.db.migrate_add_user_settings
```python
def migrate_add_user_settings(db_path)  # Add user_settings table to database.
```
```python
def main()  # Main entry point for migration script.
```

### Module: daynimal.db.models
```python
class Base
```
```python
class TaxonModel  # Core taxonomy table imported from GBIF Backbone.
```
```python
class VernacularNameModel  # Vernacular (common) names for taxa in different languages.
```
```python
class EnrichmentCacheModel  # Cache for enrichment data from external APIs.
```
```python
class AnimalHistoryModel  # History of viewed animals.
```
```python
class UserSettingsModel  # User preferences and settings.
```
```python
class FavoriteModel  # User's favorite animals.
```
```python
def _utcnow()
```

### Module: daynimal.db.session
```python
def get_engine()  # Create and return SQLAlchemy engine.
```
```python
def get_session()  # Create and return a new database session.
```

### Module: daynimal.db.__init__

### Module: daynimal.sources.base
```python
class DataSource  # Abstract base class for external data sources.
    def __init__(self)
    def client(self)  # Lazy-initialized HTTP client.
    def close(self)  # Close the HTTP client.
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
    def source_name(self)  # Name of the data source (e.g., 'wikidata', 'wikipedia').
    def license(self)  # License of the data from this source.
    def get_by_source_id(self, source_id)  # Fetch data using the source's native identifier.
    def get_by_taxonomy(self, scientific_name)  # Fetch data using a scientific (taxonomic) name.
    def search(self, query, limit)  # Search for entities matching a query.
    # calls: Client
    # calls: close
    # calls: close
```

### Module: daynimal.sources.commons
```python
class CommonsAPI  # Client for Wikimedia Commons API.
    def source_name(self)
    def license(self)
    def get_by_source_id(self, source_id)  # Fetch image info by filename.
    def get_by_taxonomy(self, scientific_name, limit)  # Find images on Commons for a species by scientific name.
    def search(self, query, limit)  # Search Commons for images matching query.
    def get_images_for_wikidata(self, qid, limit)  # Get images associated with a Wikidata entity.
    def _search_category(self, scientific_name, limit)  # Search for images in a species category.
    def _parse_image_info(self, filename, imageinfo)  # Parse image info from API response.
    def _is_valid_image_url(self, url)  # Check if URL points to a valid image file.
    def _parse_license(self, license_text)  # Parse license text to License enum.
    # calls: _parse_image_info, get, items, iter, json, next, raise_for_status, replace, startswith
    # calls: _search_category, search
    # calls: _parse_image_info, append, get, json, raise_for_status, replace, values
    # calls: _parse_image_info, append, get, json, raise_for_status, replace, values
    # calls: _parse_image_info, append, get, json, raise_for_status, replace, values
    # calls: CommonsImage, _is_valid_image_url, _parse_license, get, lower, strip, sub
    # calls: any, endswith, lower
    # calls: items, lower, strip
```

### Module: daynimal.sources.wikidata
```python
class WikidataAPI  # Client for Wikidata API.
    def source_name(self)
    def license(self)
    def get_by_source_id(self, source_id)  # Fetch a Wikidata entity by its QID.
    def get_by_taxonomy(self, scientific_name)  # Find a Wikidata entity by scientific name using SPARQL.
    def search(self, query, limit)  # Search Wikidata for entities matching query.
    def _find_taxon_qid(self, scientific_name)  # Find QID for a taxon by its scientific name.
    def _search_taxon_qid(self, scientific_name)  # Fallback search for taxon QID.
    def _is_taxon(self, qid)  # Check if an entity is a taxon (has P225 taxon name).
    def _parse_entity(self, qid, data)  # Parse raw Wikidata entity into WikidataEntity schema.
    def _get_claim_value(self, claim_list, value_type)  # Extract value from a claim list.
    def _get_quantity_string(self, claim_list)  # Extract quantity with unit from a claim.
    def _get_commons_url(self, filename)  # Convert Commons filename to URL.
    # calls: _parse_entity, get, json, raise_for_status, startswith, upper
    # calls: _find_taxon_qid, get_by_source_id
    # calls: append, get, get_by_source_id, json, raise_for_status
    # calls: _search_taxon_qid, get, json, split
    # calls: _is_taxon, get, json, raise_for_status
    # calls: bool, get, json
    # calls: WikidataEntity, _get_claim_value, _get_commons_url, _get_quantity_string, get, int, items
    # calls: get, isinstance
    # calls: get, lstrip, split, strip
    # calls: replace
```

### Module: daynimal.sources.wikipedia
```python
class WikipediaAPI  # Client for Wikipedia API.
    def __init__(self, languages)  # Initialize Wikipedia API client.
    def source_name(self)
    def license(self)
    def get_by_source_id(self, source_id, language)  # Fetch a Wikipedia article by page ID or title.
    def get_by_taxonomy(self, scientific_name)  # Find a Wikipedia article by scientific name.
    def search(self, query, limit, language)  # Search Wikipedia for articles matching query.
    def get_full_article(self, page_id, language)  # Fetch full article content (not just summary).
    def _search_in_language(self, scientific_name, language)  # Search for an article by scientific name in a specific language.
    # calls: __init__, super
    # calls: WikipediaArticle, format, get, int, isdigit, items, iter, json, next, raise_for_status
    # calls: _search_in_language
    # calls: append, format, get, get_by_source_id, json, raise_for_status, str
    # calls: WikipediaArticle, format, get, json, raise_for_status, str
    # calls: format, get, get_by_source_id, json, lower, raise_for_status, str
```

### Module: daynimal.sources.__init__

### Module: daynimal.ui.app_controller
```python
class AppController  # Main application controller.
    def __init__(self, page, debugger)  # Initialize AppController.
    def build(self)  # Build the app UI.
    def on_nav_change(self, e)  # Handle navigation bar changes.
    def show_today_view(self)  # Show the Today view.
    def show_history_view(self)  # Show the History view.
    def show_favorites_view(self)  # Show the Favorites view.
    def show_search_view(self)  # Show the Search view.
    def show_stats_view(self)  # Show the Stats view.
    def show_settings_view(self)  # Show the Settings view.
    def on_favorite_toggle(self, taxon_id, is_favorite)  # Handle favorite toggle from any view.
    def cleanup(self)  # Clean up resources.
    # calls: AppState, Column, FavoritesView, HistoryView, NavigationBar, NavigationBarDestination, SearchView, SettingsView, StatsView, TodayView, create_task, get_debugger, load_animal_from_favorite, load_animal_from_history, load_animal_from_search
    # calls: Column, show_today_view
    # calls: len, log_view_change, show_favorites_view, show_history_view, show_search_view, show_settings_view, show_stats_view, show_today_view
    # calls: build, update
    # calls: build, update
    # calls: build, update
    # calls: build, update
    # calls: build, update
    # calls: build, update
    # calls: SnackBar, Text, add_favorite, error, format_exc, log_error, print, remove_favorite, str, update
    # calls: close_repository
```
```python
def fetch_animal()
```

### Module: daynimal.ui.state
```python
class AppState  # Shared application state across all views.
    def repository(self)  # Get or create repository (lazy initialization, thread-safe).
    def close_repository(self)  # Close repository and cleanup resources.
    def reset_animal_display(self)  # Reset animal display state (used when loading new animal).
    # calls: AnimalRepository
    # calls: close
```

### Module: daynimal.ui.__init__

### Module: daynimal.ui.components.animal_card
```python
class AnimalCard  # Reusable animal card for displaying an animal in a list.
    def __init__(self, animal, on_click, metadata_icon, metadata_text, metadata_icon_color)  # Initialize animal card.
    # calls: Column, Container, Icon, Row, Text, __init__, append, extend, on_click, super
```
```python
def create_history_card(animal, on_click, viewed_at_str)  # Create an animal card for History view.
```
```python
def create_favorite_card(animal, on_click)  # Create an animal card for Favorites view.
```
```python
def create_search_card(animal, on_click)  # Create an animal card for Search view.
```

### Module: daynimal.ui.components.animal_display
```python
class AnimalDisplay  # Component for displaying detailed animal information.
    def __init__(self, animal)  # Initialize AnimalDisplay.
    def build(self)  # Build the animal display UI.
    def _build_classification(self)  # Build classification section.
    def _build_vernacular_names(self)  # Build vernacular names section.
    def _build_wikidata_info(self)  # Build Wikidata information section.
    def _build_wikipedia_description(self)  # Build Wikipedia description section.
    # calls: Divider, Text, _build_classification, _build_vernacular_names, _build_wikidata_info, _build_wikipedia_description, append, extend, upper
    # calls: Divider, Text, any, append
    # calls: Divider, Text, append, items, join, len, list
    # calls: Divider, Text, append, hasattr
    # calls: Divider, Text, append
```

### Module: daynimal.ui.components.image_carousel
```python
class ImageCarousel  # Image carousel with navigation controls.
    def __init__(self, images, current_index, on_index_change, animal_display_name, animal_taxon_id)  # Initialize ImageCarousel.
    def build(self)  # Build the carousel UI.
    def _build_empty_state(self)  # Build the empty state UI when no images available.
    def _build_error_content(self, image)  # Build the error content for failed image loads.
    def _on_prev(self, e)  # Navigate to previous image.
    def _on_next(self, e)  # Navigate to next image.
    # calls: Column, Container, IconButton, Image, Row, Text, _build_empty_state, _build_error_content, len
    # calls: Column, Container, Icon, Text
    # calls: Column, Container, Icon, Text
    # calls: len, on_index_change
    # calls: len, on_index_change
```

### Module: daynimal.ui.components.widgets
```python
class LoadingWidget  # Loading indicator widget.
    def __init__(self, message)  # Initialize loading widget.
    # calls: Column, ProgressRing, Text, __init__, super
```
```python
class ErrorWidget  # Error display widget.
    def __init__(self, title, details)  # Initialize error widget.
    # calls: Column, Icon, Text, __init__, append, super
```
```python
class EmptyStateWidget  # Empty state widget.
    def __init__(self, icon, title, description, icon_size, icon_color)  # Initialize empty state widget.
    # calls: Column, Icon, Text, __init__, super
```

### Module: daynimal.ui.components.__init__

### Module: daynimal.ui.utils.debounce
```python
class Debouncer  # Debouncer to delay function execution until input stabilizes.
    def __init__(self, delay)  # Initialize debouncer.
```

### Module: daynimal.ui.utils.__init__

### Module: daynimal.ui.views.base
```python
class BaseView  # Abstract base class for all views in the Daynimal app.
    def __init__(self, page, app_state, debugger)  # Initialize base view.
    def build(self)  # Build the view's UI.
    def show_loading(self, message)  # Show loading indicator.
    def show_error(self, title, details)  # Show error state.
    def show_empty_state(self, icon, title, description, icon_size, icon_color)  # Show empty state.
    def log_info(self, message)  # Log info message (with fallback to print).
    def log_error(self, context, error)  # Log error message (with fallback to print).
    # calls: Column
    # calls: LoadingWidget, update
    # calls: ErrorWidget, update
    # calls: EmptyStateWidget, update
    # calls: info, print
    # calls: log_error, print
```

### Module: daynimal.ui.views.favorites_view
```python
class FavoritesView  # View for displaying and managing favorite animals.
    def __init__(self, page, app_state, on_animal_click, debugger)  # Initialize FavoritesView.
    def build(self)  # Build the favorites view UI.
    def _on_favorite_item_click(self, e)  # Handle click on a favorite item.
    # calls: Column, __init__, super
    # calls: Column, Container, Divider, Row, Text, create_task, load_favorites
    # calls: error, format_exc, info, log_error, on_animal_click, print
```
```python
def fetch_favorites()
```

### Module: daynimal.ui.views.history_view
```python
class HistoryView  # View for displaying and managing animal viewing history.
    def __init__(self, page, app_state, on_animal_click, debugger)  # Initialize HistoryView.
    def build(self)  # Build the history view UI.
    def _on_history_item_click(self, e)  # Handle click on history item - load animal and switch to Today view.
    # calls: Column, __init__, super
    # calls: Column, Container, Divider, Row, Text, create_task, load_history
    # calls: error, format_exc, info, log_error, on_animal_click, print
```
```python
def fetch_history()
```

### Module: daynimal.ui.views.search_view
```python
class SearchView  # Search view with search field and results list.
    def __init__(self, page, app_state, on_result_click, debugger)  # Initialize search view.
    def build(self)  # Build the search view UI.
    def _on_submit(self, e)  # Handle Enter key in search field.
    def _on_search_click(self, e)  # Handle search button click.
    def show_empty_search_state(self)  # Show empty state (before any search).
    # calls: Column, IconButton, TextField, __init__, super
    # calls: Container, Divider, Icon, Padding, Row, Text, show_empty_search_state
    # calls: create_task, perform_search, strip
    # calls: create_task, perform_search, strip
    # calls: Column, Container, Icon, Text
```

### Module: daynimal.ui.views.settings_view
```python
class SettingsView  # View for app settings, preferences, and credits.
    def __init__(self, page, app_state, debugger)  # Initialize SettingsView.
    def build(self)  # Build the settings view UI.
    def _on_theme_toggle(self, e)  # Handle theme toggle switch change.
    # calls: Column, __init__, super
    # calls: _load_settings, create_task
    # calls: error, format_exc, info, log_error, print, set_setting, update
```
```python
def fetch_data()
```

### Module: daynimal.ui.views.stats_view
```python
class StatsView  # View for displaying database statistics with responsive cards.
    def __init__(self, page, app_state, debugger)  # Initialize StatsView.
    def build(self)  # Build the statistics view UI.
    def _display_stats(self, stats)  # Display statistics cards.
    # calls: Row, __init__, super
    # calls: Column, Container, Divider, Row, Text, _display_stats, create_task, load_stats, update
    # calls: Card, Column, Container, Icon, Text, append
```
```python
def fetch_stats()
```

### Module: daynimal.ui.views.today_view
```python
class TodayView  # View for displaying the animal of the day or random animals.
    def __init__(self, page, app_state, on_favorite_toggle, debugger)  # Initialize TodayView.
    def build(self)  # Build the today view UI.
    def _display_animal(self, animal)  # Display animal information in the Today view.
    def _on_favorite_toggle(self, e)  # Handle favorite button toggle.
    def _on_image_index_change(self, new_index)  # Handle image index change in carousel.
    # calls: Column, __init__, super
    # calls: Button, ButtonStyle, Column, Container, Divider, Icon, Padding, Row, Text, _display_animal
    # calls: AnimalDisplay, Container, Divider, IconButton, ImageCarousel, Padding, Row, Text, append, build, extend, insert, is_favorite, len, update
    # calls: _display_animal, is_favorite, on_favorite_toggle_callback
    # calls: _display_animal
```
```python
def fetch_animal()
```

### Module: daynimal.ui.views.__init__

### Module: debug.debug_filter
```python
def get_latest_log()  # Get the most recent log file.
```
```python
def filter_line(line, errors_only, search)  # Determine if a line should be displayed.
```
```python
def colorize_log_line(line)  # Add color to log lines based on level (ANSI escape codes).
```
```python
def show_filtered_log(log_file, errors_only, search, colorize)  # Display filtered log file.
```
```python
def tail_filtered_log(log_file, errors_only, search)  # Follow log file and display filtered lines in real-time.
```
```python
def show_statistics(log_file)  # Show statistics about the log file.
```
```python
def main()  # Main entry point.
```

### Module: debug.run_app_debug
```python
def main()  # Launch the Flet app with debugging enabled.
```
```python
def app_main(page)
```

### Module: debug.view_logs
```python
def get_log_files()  # Get all log files sorted by modification time (newest first).
```
```python
def show_latest_log(tail)  # Show or tail the latest log file.
```
```python
def list_log_files()  # List all log files with their sizes and timestamps.
```
```python
def show_all_logs()  # Show all log files concatenated.
```
```python
def main()  # Main entry point.
```

## 6. High-Coupling Modules (Risk Zones)
- No obvious high-coupling modules detected

## 7. Dependency Cycles Detected
- No obvious cycles detected

## 8. Observations
- Architecture inferred statically from source code
- Layers are heuristic-based and may require validation
- Signatures include classes, methods, functions, and short docstrings
- Internal calls between functions/methods are listed
- This document is intended as canonical project memory for Claude Code
