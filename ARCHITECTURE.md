# Architecture Overview

## 1. Project Structure

### benchmarks
- `benchmarks.search_relevance` — Benchmark search relevance for well-known animal names.

### daynimal
- `daynimal.__init__` — Daynimal - Daily Animal Discovery App
- `daynimal.app` — Daynimal Flet App - Desktop/Mobile Application
- `daynimal.attribution` — Attribution management for legal compliance.
- `daynimal.config`
- `daynimal.connectivity` — Network connectivity detection for offline mode.
- `daynimal.image_cache` — Image cache service for downloading and serving images locally.
- `daynimal.main` — Daynimal CLI - Daily Animal Discovery
- `daynimal.notifications` — Notification service for daily animal reminders.
- `daynimal.repository` — Animal Repository - aggregates data from local DB and external APIs.
- `daynimal.schemas`

### daynimal/db
- `daynimal.db.__init__`
- `daynimal.db.build_db` — Build a SQLite database from distribution TSV files.
- `daynimal.db.first_launch` — First-launch setup: download distribution from GitHub Releases, build minimal DB.
- `daynimal.db.generate_distribution` — Generate distribution TSV files from raw sources (GBIF + TAXREF).
- `daynimal.db.import_gbif_utils` — GBIF Backbone Taxonomy - Shared utilities for import scripts.
- `daynimal.db.init_fts` — Initialize FTS5 (Full-Text Search) table for fast animal search.
- `daynimal.db.models`
- `daynimal.db.session`

### daynimal/resources
- `daynimal.resources.__init__` — Embedded data resources for Daynimal.

### daynimal/sources
- `daynimal.sources.__init__`
- `daynimal.sources.base` — Base class for external data sources.
- `daynimal.sources.commons` — Wikimedia Commons API client.
- `daynimal.sources.gbif_media` — GBIF Media API client.
- `daynimal.sources.phylopic_local` — Local PhyloPic lookup service.
- `daynimal.sources.wikidata` — Wikidata API client.
- `daynimal.sources.wikipedia` — Wikipedia API client.

### daynimal/sources/legacy
- `daynimal.sources.legacy.__init__` — Legacy API clients (kept for reference, no longer used in production).
- `daynimal.sources.legacy.phylopic` — PhyloPic API client.

### daynimal/ui
- `daynimal.ui.__init__` — UI module for Daynimal Flet application.
- `daynimal.ui.app_controller` — App controller for managing views and navigation.
- `daynimal.ui.state` — Application state management for Daynimal UI.

### daynimal/ui/components
- `daynimal.ui.components.__init__` — Reusable UI components for Daynimal app.
- `daynimal.ui.components.animal_card` — Reusable animal card component for list views.
- `daynimal.ui.components.animal_display` — Animal display component for showing detailed animal information.
- `daynimal.ui.components.image_carousel` — Image carousel component for displaying animal images with navigation.
- `daynimal.ui.components.image_gallery_dialog` — Image gallery dialog for lazy-loading and browsing all animal images.
- `daynimal.ui.components.pagination` — Reusable pagination bar component.
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
- `daynimal.ui.views.setup_view` — Setup view for first-launch database installation.
- `daynimal.ui.views.stats_view` — Statistics view for displaying database statistics.
- `daynimal.ui.views.today_view` — Today view for displaying the animal of the day or random animals.

### root
- `generate_architecture`

### scripts
- `scripts.download_phylopic` — Download all PhyloPic SVG silhouettes with metadata into a zip file.
- `scripts.prepare_release` — Prepare distribution files for GitHub Release.

## 2. Entry Points
- benchmarks.search_relevance
- daynimal.app
- daynimal.main
- daynimal.db.build_db
- daynimal.db.generate_distribution
- daynimal.db.init_fts
- scripts.download_phylopic
- scripts.prepare_release

## 3. Internal Dependencies

### benchmarks.search_relevance
- depends on `daynimal.db.models`
- depends on `daynimal.repository`

### daynimal.__init__
- depends on `daynimal.attribution`
- depends on `daynimal.repository`
- depends on `daynimal.schemas`

### daynimal.app
- depends on `daynimal.config`
- depends on `daynimal.db.first_launch`
- depends on `daynimal.repository`
- depends on `daynimal.ui.app_controller`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.setup_view`

### daynimal.attribution
- depends on `daynimal.schemas`

### daynimal.db.__init__
- depends on `daynimal.db.models`
- depends on `daynimal.db.session`

### daynimal.db.build_db
- depends on `daynimal.config`
- depends on `daynimal.db.models`
- depends on `daynimal.db.session`

### daynimal.db.first_launch
- depends on `daynimal.config`
- depends on `daynimal.db.build_db`
- depends on `daynimal.db.init_fts`

### daynimal.db.generate_distribution
- depends on `daynimal.db.import_gbif_utils`

### daynimal.db.init_fts
- depends on `daynimal.config`
- depends on `daynimal.db.session`

### daynimal.db.session
- depends on `daynimal.config`

### daynimal.image_cache
- depends on `daynimal.config`
- depends on `daynimal.db.models`
- depends on `daynimal.schemas`
- depends on `daynimal.sources.base`

### daynimal.main
- depends on `daynimal.__init__`
- depends on `daynimal.attribution`
- depends on `daynimal.config`
- depends on `daynimal.db.build_db`
- depends on `daynimal.db.first_launch`
- depends on `daynimal.db.generate_distribution`
- depends on `daynimal.db.init_fts`
- depends on `daynimal.db.models`
- depends on `daynimal.repository`

### daynimal.notifications
- depends on `daynimal.repository`

### daynimal.repository
- depends on `daynimal.connectivity`
- depends on `daynimal.db.models`
- depends on `daynimal.db.session`
- depends on `daynimal.image_cache`
- depends on `daynimal.schemas`
- depends on `daynimal.sources.commons`
- depends on `daynimal.sources.gbif_media`
- depends on `daynimal.sources.phylopic_local`
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

### daynimal.sources.gbif_media
- depends on `daynimal.schemas`
- depends on `daynimal.sources.base`

### daynimal.sources.legacy.phylopic
- depends on `daynimal.config`
- depends on `daynimal.schemas`
- depends on `daynimal.sources.base`

### daynimal.sources.phylopic_local
- depends on `daynimal.schemas`

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
- depends on `daynimal.notifications`
- depends on `daynimal.ui.components.widgets`
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
- depends on `daynimal.config`
- depends on `daynimal.schemas`

### daynimal.ui.components.animal_display
- depends on `daynimal.schemas`

### daynimal.ui.components.image_carousel
- depends on `daynimal.image_cache`
- depends on `daynimal.schemas`

### daynimal.ui.components.image_gallery_dialog
- depends on `daynimal.image_cache`
- depends on `daynimal.schemas`

### daynimal.ui.state
- depends on `daynimal.image_cache`
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
- depends on `daynimal.ui.components.animal_card`
- depends on `daynimal.ui.components.pagination`
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.history_view
- depends on `daynimal.ui.components.animal_card`
- depends on `daynimal.ui.components.pagination`
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.search_view
- depends on `daynimal.ui.components.animal_card`
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.settings_view
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.setup_view
- depends on `daynimal.db.first_launch`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.stats_view
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

### daynimal.ui.views.today_view
- depends on `daynimal.schemas`
- depends on `daynimal.ui.components.animal_display`
- depends on `daynimal.ui.components.image_gallery_dialog`
- depends on `daynimal.ui.components.widgets`
- depends on `daynimal.ui.state`
- depends on `daynimal.ui.views.base`

## 4. External Dependencies
- logging (used 17 times)
- flet (used 16 times)
- asyncio (used 12 times)
- typing (used 12 times)
- pathlib (used 11 times)
- sqlalchemy (used 9 times)
- httpx (used 8 times)
- datetime (used 7 times)
- traceback (used 7 times)
- argparse (used 6 times)
- csv (used 4 times)
- dataclasses (used 4 times)
- re (used 4 times)
- time (used 4 times)
- hashlib (used 3 times)
- io (used 3 times)
- json (used 3 times)
- os (used 3 times)
- threading (used 3 times)
- zipfile (used 3 times)
- abc (used 2 times)
- collections (used 2 times)
- gzip (used 2 times)
- shutil (used 2 times)
- sys (used 2 times)
- __future__ (used 1 times)
- ast (used 1 times)
- concurrent (used 1 times)
- contextlib (used 1 times)
- enum (used 1 times)
- math (used 1 times)
- plyer (used 1 times)
- pydantic (used 1 times)
- pydantic_settings (used 1 times)
- random (used 1 times)
- sqlite3 (used 1 times)
- subprocess (used 1 times)
- types (used 1 times)
- unicodedata (used 1 times)

## 5. Signatures and Calls

### Module: benchmarks.search_relevance
> Benchmark search relevance for well-known animal names.
> 
> Usage:
>     uv run python benchmarks/search_relevance.py
>     uv run python benchmarks/search_relevance.py --limit 10
>     uv run python benchmarks/search_relevance.py --queries lion tiger
>     uv run python benchmarks/search_relevance.py --verbose
```python
def run(queries, limit, verbose)
```
- calls: `AnimalRepository`, `enumerate`, `io.TextIOWrapper`, `len`, `print`, `sum`
```python
def main()
```
- calls: `argparse.ArgumentParser`, `run`

### Module: daynimal.app
> Daynimal Flet App - Desktop/Mobile Application
> 
> A cross-platform application built with Flet (Flutter for Python) that displays
> daily animal discoveries with enriched information.
```python
class DaynimalApp  # Main application class for Daynimal Flet app.
    def __init__(self, page)
    # calls: hasattr, is_mobile, self.build
    def build(self)  # Build the user interface.
    # calls: AppState, SetupView, is_mobile, resolve_database, self._build_desktop_no_db_screen, self._build_main_app, self._load_theme, self.page.add, self.page.update, self.setup_view.build
    def _build_desktop_no_db_screen(self)  # Show an informational screen when DB is missing on desktop.
    # calls: ft.Column, ft.Container, ft.FilledButton, ft.Icon, ft.Margin.symmetric, ft.Padding.symmetric, ft.Text, self.page.add
    async def _on_quit_click(self, _)  # Handle quit button click.
    # calls: self.page.window.close
    def _build_main_app(self)  # Build the main application UI (after DB is available).
    # calls: AppController, self.app_controller.build, self.page.add, self.page.controls.clear
    def _on_setup_complete(self)  # Called when first-launch setup finishes successfully.
    # calls: resolve_database, self._build_main_app, self.page.update
    def _load_theme(self)  # Load theme setting from database and apply to page.
    # calls: AnimalRepository
    def cleanup(self)  # Clean up resources (close connections, database, etc.).
    # calls: hasattr, self.app_controller.cleanup, traceback.print_exc
    def on_disconnect(self, e)  # Handle page disconnect event (when user closes the window).
    # calls: os._exit, self.cleanup, traceback.print_exc
    def on_close(self, e)  # Handle page close event.
    # calls: self.cleanup, traceback.print_exc
```
```python
def _show_error(page, error)  # Show error visually on the page (critical for mobile debugging).
```
- calls: `ft.Column`, `ft.Text`, `str`, `traceback.format_exc`
```python
def _install_asyncio_exception_handler()  # Print all unhandled async exceptions to the terminal.
```
- calls: `asyncio.get_running_loop`, `isinstance`, `print`, `traceback.print_exception`, `type`
```python
def main()  # Main entry point for the Flet app.
```
- calls: `DaynimalApp`, `_install_asyncio_exception_handler`, `_show_error`, `ft.run`

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
def create_gbif_media_attribution(author, license, url)  # Create attribution for a GBIF Media image.
```
- calls: `AttributionInfo`, `datetime.now`
```python
def create_phylopic_attribution(author, license, url)  # Create attribution for a PhyloPic silhouette.
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
```python
def get_app_data_dir()  # Répertoire de données persistantes (DB, config, cache).
```
- calls: `Path`, `os.getenv`
```python
def get_app_temp_dir()  # Répertoire temporaire (téléchargements, décompression).
```
- calls: `Path`, `os.getenv`
```python
def is_mobile()  # True si l'app tourne dans un environnement mobile Flet.
```
- calls: `os.getenv`

### Module: daynimal.connectivity
> Network connectivity detection for offline mode.
> 
> Provides a lightweight connectivity check to avoid long API timeouts
> when the device is offline. Uses a HEAD request to wikidata.org with
> a short timeout and caches the result for 60 seconds.
```python
class ConnectivityService  # Detects network connectivity via a lightweight HEAD request.
    def __init__(self)
    # calls: threading.Lock
    @property
    def is_online(self)  # Return cached connectivity state, refreshing if TTL expired.
    # calls: self.check, time.monotonic
    def check(self)  # Force an immediate connectivity check.
    # calls: httpx.head, time.monotonic
    def set_offline(self)  # Mark as offline (e.g. after API failure).
    # calls: time.monotonic
    def set_online(self)  # Mark as online.
    # calls: time.monotonic
    @property
    def force_offline(self)  # Whether offline mode is forced by user.
    @force_offline.setter
    def force_offline(self, value)  # Set forced offline mode.
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

### Module: daynimal.db.first_launch
> First-launch setup: download distribution from GitHub Releases, build minimal DB.
> 
> This module handles:
> - Database resolution (find existing DB or fallback via .daynimal_config)
> - Downloading compressed TSV files from GitHub Releases
> - Verifying checksums
> - Building the minimal SQLite database
> - Initializing FTS5 search index
```python
def _get_db_path_from_url()  # Extract database file path from settings.database_url.
```
- calls: `Path`, `len`
```python
def _get_config_file_path()  # Get path to .daynimal_config file (same directory as default DB).
```
- calls: `_get_db_path_from_url`
```python
def is_db_valid(db_path)  # Check if a database file exists and contains taxa data.
```
- calls: `sqlite3.connect`, `str`
```python
def save_db_config(db_path)  # Save the active database path to .daynimal_config.
```
- calls: `_get_config_file_path`, `json.dumps`, `str`
```python
def resolve_database()  # Find the active database, updating settings if needed.
```
- calls: `Path`, `_get_config_file_path`, `_get_db_path_from_url`, `is_db_valid`, `json.loads`
```python
def verify_checksum(file_path, expected_sha256)  # Verify SHA256 checksum of a file.
```
- calls: `hashlib.sha256`, `iter`, `open`
```python
def download_file(url, dest, progress_callback)  # Download a file with streaming and optional progress reporting.
```
- calls: `httpx.stream`, `int`, `len`, `open`, `progress_callback`
```python
def download_and_setup_db(progress_callback)  # Download distribution files and build the minimal database.
```
- calls: `ValueError`, `_download_progress`, `_progress`, `build_database`, `download_file`, `get_app_data_dir`, `get_app_temp_dir`, `gzip.open`, `init_fts`, `isinstance`, `json.loads`, `open`, `progress_callback`, `save_db_config`, `shutil.copyfileobj`, `shutil.rmtree`, `str`, `verify_checksum`

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
class ImageCacheModel(Base)  # Cache for downloaded images from Wikimedia Commons.
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

### Module: daynimal.image_cache
> Image cache service for downloading and serving images locally.
```python
class ImageCacheService  # Downloads and caches images locally for offline use.
    def __init__(self, session, cache_dir, max_size_mb, cache_hd)
    # calls: ImageCacheModel.__table__.create, self._cache_dir.mkdir
    @property
    def client(self)
    # calls: httpx.Client
    def close(self)
    # calls: self._client.close
    @staticmethod
    def _url_to_path(url, cache_dir)  # Convert URL to local file path using SHA256 hash.
    # calls: hashlib.sha256, hashlib.sha256.hexdigest
    def cache_single_image(self, image)  # Download and cache a single image (thumbnail preferred).
    # calls: self._download_and_store, self.get_cache_size, self.purge_lru
    def cache_images_with_progress(self, images, on_progress)  # Download and cache images with progress callback.
    # calls: enumerate, len, on_progress, self._download_and_store, self.get_cache_size, self.purge_lru, time.sleep
    def are_all_cached(self, images)  # Check if all images are already cached in DB.
    # calls: ImageCacheModel.url.in_, len, self._session.query, self._session.query.filter
    def cache_images(self, images)  # Download and cache images locally.
    # calls: enumerate, self._download_and_store, self.get_cache_size, self.purge_lru, time.sleep
    def _download_and_store(self, url, is_thumbnail)  # Download a single image and store it in cache.
    # calls: ImageCacheModel, Path, datetime.now, len, retry_with_backoff, self._session.add, self._session.commit, self._session.query, self._session.query.filter, self._session.rollback, self._url_to_path, self.client.get, str
    def get_local_path(self, url)  # Get local path for a cached image, updating last_accessed_at.
    # calls: Path, datetime.now, self._session.commit, self._session.delete, self._session.query, self._session.query.filter
    def get_cache_size(self)  # Get total cache size in bytes from DB.
    # calls: func.sum, self._session.query, self._session.query.scalar
    def purge_lru(self, target_size_bytes)  # Remove least recently accessed images until cache is under target size.
    # calls: ImageCacheModel.last_accessed_at.asc, Path, self._session.commit, self._session.delete, self._session.query, self._session.query.order_by, self.get_cache_size
    def clear(self)  # Clear all cached images.
    # calls: Path, Path.unlink, len, self._cache_dir.exists, self._cache_dir.iterdir, self._session.commit, self._session.delete, self._session.query, self._session.query.all
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
def cmd_setup(mode, no_taxref)  # Download and set up the database.
```
- calls: `_setup_full`, `_setup_minimal`, `print`, `resolve_database`
```python
def _setup_minimal()  # Download pre-built minimal database from GitHub Releases.
```
- calls: `SystemExit`, `download_and_setup_db`, `print`
```python
def _setup_full(no_taxref)  # Build full database from GBIF backbone + optional TAXREF.
```
- calls: `Path`, `SystemExit`, `build_database`, `download_file`, `generate_distribution`, `init_fts`, `open`, `print`, `save_db_config`, `shutil.copyfileobj`, `zipfile.ZipFile`
```python
def cmd_history(page, per_page)  # Show history of viewed animals.
```
- calls: `AnimalRepository`, `print`
```python
def cmd_clear_cache()  # Clear the enrichment cache so animals are re-fetched from APIs.
```
- calls: `AnimalRepository`, `TaxonModel.is_enriched.is_`, `print`
```python
def create_parser()  # Create and configure the argument parser.
```
- calls: `argparse.ArgumentParser`
```python
def main()  # Main entry point.
```
- calls: `SystemExit`, `cmd_clear_cache`, `cmd_credits`, `cmd_history`, `cmd_info`, `cmd_random`, `cmd_search`, `cmd_setup`, `cmd_stats`, `cmd_today`, `create_parser`, `print`, `resolve_database`, `temporary_database`

### Module: daynimal.notifications
> Notification service for daily animal reminders.
```python
class NotificationService  # In-app notification service that sends a daily desktop notification.
    def __init__(self, repository)
    @property
    def enabled(self)  # Whether notifications are enabled.
    # calls: self.repository.get_setting
    @property
    def notification_time(self)  # Configured notification time (HH:MM format).
    # calls: self.repository.get_setting
    def start(self)  # Start the periodic check loop.
    # calls: asyncio.create_task, self._check_loop
    def stop(self)  # Stop the periodic check loop.
    # calls: self._task.cancel
    async def _check_loop(self)  # Periodically check if it's time to send a notification.
    # calls: asyncio.sleep, self._send_notification, self._should_notify
    def _should_notify(self)  # Check if a notification should be sent now.
    # calls: datetime.now, datetime.now.strftime, int, self.notification_time.split, self.repository.get_setting
    async def _send_notification(self)  # Send the daily animal notification.
    # calls: asyncio.to_thread, datetime.now, datetime.now.strftime, self.repository.set_setting
```

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
    # calls: ConnectivityService, ImageCacheService, get_session, threading.Lock
    @property
    def wikidata(self)
    # calls: WikidataAPI
    @property
    def wikipedia(self)
    # calls: WikipediaAPI
    @property
    def commons(self)
    # calls: CommonsAPI
    @property
    def gbif_media(self)
    # calls: GbifMediaAPI
    def close(self)  # Close all connections.
    # calls: self._commons.close, self._gbif_media.close, self._wikidata.close, self._wikipedia.close, self.image_cache.close, self.session.close
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
    # calls: self.close
    def get_by_id(self, taxon_id, enrich)  # Get animal by GBIF taxon ID.
    # calls: AnimalInfo, self._enrich, self._model_to_taxon, self.session.get
    def get_by_name(self, scientific_name, enrich)  # Get animal by scientific name.
    # calls: AnimalInfo, or_, self._enrich, self._model_to_taxon, self.session.query, self.session.query.filter
    def search(self, query, limit)  # Search for animals by name (scientific or vernacular) using FTS5.
    # calls: self._search_fts5, self._search_like
    def _search_fts5(self, query, limit)  # Search using FTS5 with relevance ranking.
    # calls: AnimalInfo, TaxonModel.taxon_id.in_, joinedload, len, max, remove_accents, self._model_to_taxon, self._relevance_score, self.session.execute, self.session.execute.fetchall, self.session.query, self.session.query.options, text
    @staticmethod
    def _relevance_score(model, query_lower)  # Compute a relevance score for a taxon model against a query.
    # calls: len, min
    def _search_like(self, query, limit)  # Fallback LIKE-based search when FTS5 is unavailable.
    # calls: AnimalInfo, func.lower, func.lower.contains, len, self._model_to_taxon, self.session.query, self.session.query.filter, self.session.query.join, set
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
    # calls: self._save_cache, self.connectivity.set_offline, self.wikidata.get_by_taxonomy
    def _fetch_and_cache_wikipedia(self, taxon_id, scientific_name)  # Fetch Wikipedia and cache it.
    # calls: self._save_cache, self.connectivity.set_offline, self.wikipedia.get_by_taxonomy
    def _fetch_and_cache_images(self, taxon_id, scientific_name, wikidata, taxon)  # Fetch images with cascade: Commons → GBIF Media → PhyloPic (local).
    # calls: get_phylopic_silhouette, rank_images, self._save_cache, self.commons.get_by_source_id, self.commons.get_by_taxonomy, self.commons.get_images_for_wikidata, self.connectivity.set_offline, self.gbif_media.get_media_for_taxon, self.image_cache.cache_single_image
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
class ImageSource(str, Enum)  # Source of an image.
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
class CommonsImage  # Image data from Wikimedia Commons, GBIF, or PhyloPic.
    @property
    def commons_page_url(self)  # URL to the image's source page.
    # calls: self.filename.replace
    @property
    def license_url(self)  # URL to the license.
    @property
    def source_label(self)  # Human-readable label for the image source.
    # calls: ImageSource, isinstance, self._SOURCE_LABELS.get
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
    def _request_with_retry(self, method, url)  # Make HTTP request with automatic retry on rate limit and service errors.
    # calls: ValueError, retry_with_backoff, self.client.get, self.client.post
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
```python
def retry_with_backoff(func, max_retries, backoff_base)  # Execute HTTP request with exponential backoff retry.
```
- calls: `float`, `func`, `range`, `time.sleep`

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
    # calls: iter, next, self._parse_image_info, self._request_with_retry
    def get_by_taxonomy(self, scientific_name, limit)  # Find images on Commons for a species by scientific name.
    # calls: self._search_category, self.search
    def search(self, query, limit)  # Search Commons for images matching query.
    # calls: self._parse_image_info, self._request_with_retry
    def get_images_for_wikidata(self, qid, limit)  # Get images associated with a Wikidata entity.
    # calls: self._parse_image_info, self._request_with_retry
    def _search_category(self, scientific_name, limit)  # Search for images in a species category.
    # calls: self._parse_image_info, self._request_with_retry
    def _parse_image_info(self, filename, imageinfo)  # Parse image info from API response.
    # calls: CommonsImage, re.sub, re.sub.strip, self._is_valid_image_url, self._parse_license
    def _is_valid_image_url(self, url)  # Check if URL points to a valid image file.
    # calls: any
    def _parse_license(self, license_text)  # Parse license text to License enum.
```
```python
def rank_images(images, p18_filename)  # Rank images: P18 first, then by assessment quality, photos before drawings.
```
- calls: `sorted`

### Module: daynimal.sources.gbif_media
> GBIF Media API client.
> 
> Fetches images from GBIF's species media endpoint as a fallback
> when Wikimedia Commons has no images for a species.
> 
> Only images with commercial-use-compatible licenses are returned:
> CC0, CC-BY, CC-BY-SA, Public Domain. Images with NC or ND clauses
> are rejected.
```python
class GbifMediaAPI(DataSource)  # Client for GBIF Media API.
    @property
    def source_name(self)
    @property
    def license(self)
    def get_by_source_id(self, source_id)  # Not applicable for GBIF Media — use get_media_for_taxon instead.
    def get_by_taxonomy(self, scientific_name)  # Not applicable — use get_media_for_taxon with a taxon key.
    def search(self, query, limit)  # Not applicable — use get_media_for_taxon with a taxon key.
    def get_media_for_taxon(self, taxon_key, limit)  # Fetch images for a GBIF taxon, filtering for commercial-use licenses.
    # calls: len, max, self._parse_media_item, self._request_with_retry
    def _parse_media_item(self, item)  # Parse a GBIF media item to a CommonsImage.
    # calls: CommonsImage, _parse_gbif_license, len, re.sub, re.sub.strip
```
```python
def _parse_gbif_license(license_url)  # Parse a GBIF license URL to a License enum.
```

### Module: daynimal.sources.legacy.phylopic
> PhyloPic API client.
> 
> Fetches silhouette images from PhyloPic (https://www.phylopic.org/)
> as a last-resort fallback when no photos are available.
> 
> PhyloPic provides free silhouette images of organisms, organized by
> phylogenetic taxonomy. When no image exists for the exact species,
> we traverse up the GBIF taxonomy (genus → family → order → class)
> to find the closest available silhouette.
> 
> Only images with commercial-use-compatible licenses are returned.
```python
class PhyloPicAPI(DataSource)  # Client for PhyloPic API.
    @property
    def client(self)  # Lazy-initialized HTTP client with redirect support.
    # calls: httpx.Client
    @property
    def source_name(self)
    @property
    def license(self)
    def get_by_source_id(self, source_id)  # Not applicable — use get_silhouettes_for_taxon instead.
    def get_by_taxonomy(self, scientific_name)  # Not applicable — use get_silhouettes_for_taxon with a GBIF key.
    def search(self, query, limit)  # Not applicable — use get_silhouettes_for_taxon with a GBIF key.
    def get_silhouettes_for_taxon(self, gbif_key, limit)  # Fetch silhouette images for a GBIF taxon key.
    # calls: self._get_parent_keys, self._try_resolve_and_get_image
    def _try_resolve_and_get_image(self, gbif_key)  # Try to resolve a GBIF key and get its PhyloPic image.
    # calls: self._get_node_image, self._resolve_gbif_key
    def _get_parent_keys(self, gbif_key)  # Fetch parent taxon keys from GBIF API.
    # calls: self._request_with_retry
    def _resolve_gbif_key(self, gbif_key)  # Resolve a GBIF species key to a PhyloPic node UUID.
    # calls: len, self._request_with_retry, str
    def _get_node_image(self, node_uuid)  # Fetch the primary image for a PhyloPic node.
    # calls: self._parse_image, self._request_with_retry
    def _parse_image(self, image_data)  # Parse a PhyloPic image object to a CommonsImage.
    # calls: CommonsImage, _parse_phylopic_license, float, int
```
```python
def _parse_phylopic_license(license_url)  # Parse a PhyloPic license URL to a License enum.
```

### Module: daynimal.sources.phylopic_local
> Local PhyloPic lookup service.
> 
> Replaces the PhyloPic API client with a local CSV-based lookup.
> The CSV contains ~11,950 silhouette metadata entries downloaded from PhyloPic.
> Taxonomy traversal is done locally using the Taxon hierarchy fields.
```python
def _parse_phylopic_license(license_url)  # Parse a PhyloPic license URL to a License enum.
```
```python
def _load_csv()  # Load PhyloPic metadata CSV into two dicts.
```
- calls: `Path`, `Path.resolve`, `csv.DictReader`, `len`, `open`
```python
def _get_lookups()  # Get or initialize the lookup dicts (lazy singleton).
```
- calls: `_load_csv`
```python
def _row_to_image(row)  # Convert a CSV row to a CommonsImage, or None if license is rejected.
```
- calls: `CommonsImage`, `_parse_phylopic_license`
```python
def _find_in_lookups(key, specific, general)  # Try to find a valid image for a key, preferring specific over general.
```
- calls: `_row_to_image`
```python
def get_silhouette_for_taxon(taxon)  # Look up a PhyloPic silhouette for the given taxon.
```
- calls: `_find_in_lookups`, `_get_lookups`, `getattr`

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
    # calls: self._parse_entity, self._request_with_retry
    def get_by_taxonomy(self, scientific_name)  # Find a Wikidata entity by scientific name using SPARQL.
    # calls: self._find_taxon_qid, self.get_by_source_id
    def search(self, query, limit)  # Search Wikidata for entities matching query.
    # calls: self._request_with_retry, self.get_by_source_id
    def _find_taxon_qid(self, scientific_name)  # Find QID for a taxon by its scientific name.
    # calls: self._request_with_retry, self._search_taxon_qid
    def _search_taxon_qid(self, scientific_name)  # Fallback search for taxon QID.
    # calls: self._is_taxon, self._request_with_retry
    def _is_taxon(self, qid)  # Check if an entity is a taxon (has P225 taxon name).
    # calls: bool, self._request_with_retry
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
    # calls: WikipediaArticle, int, iter, next, self._request_with_retry
    def get_by_taxonomy(self, scientific_name)  # Find a Wikipedia article by scientific name.
    # calls: self._search_in_language
    def search(self, query, limit, language)  # Search Wikipedia for articles matching query.
    # calls: self._request_with_retry, self.get_by_source_id, str
    def get_full_article(self, page_id, language)  # Fetch full article content (not just summary).
    # calls: WikipediaArticle, self._request_with_retry, str
    def _search_in_language(self, scientific_name, language)  # Search for an article by scientific name in a specific language.
    # calls: self._request_with_retry, self.get_by_source_id, str
```

### Module: daynimal.ui.app_controller
> App controller for managing views and navigation.
```python
class AppController  # Main application controller.
    def __init__(self, page)  # Initialize AppController.
    # calls: AppState, FavoritesView, HistoryView, NotificationService, SearchView, SettingsView, StatsView, TodayView, asyncio.create_task, ft.Button, ft.ButtonStyle, ft.Column, ft.Container, ft.Icon, ft.NavigationBar, ft.NavigationBarDestination, ft.Padding, ft.Row, ft.Text, self.load_animal_from_favorite, self.load_animal_from_history, self.load_animal_from_search
    def build(self)  # Build the app UI.
    # calls: ft.Column, self.notification_service.start, self.show_today_view
    def on_nav_change(self, e)  # Handle navigation bar changes.
    # calls: len, self.show_favorites_view, self.show_history_view, self.show_search_view, self.show_settings_view, self.show_stats_view, self.show_today_view
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
    # calls: ErrorWidget, LoadingWidget, asyncio.sleep, asyncio.to_thread, self._update_offline_banner, self.page.update, self.show_today_view, self.today_view._display_animal, str, traceback.print_exc
    def on_favorite_toggle(self, taxon_id, is_favorite)  # Handle favorite toggle from any view.
    # calls: ft.SnackBar, ft.Text, self.page.show_dialog, str, traceback.print_exc
    def _update_offline_banner(self)  # Update offline banner visibility based on connectivity state.
    # calls: self.page.update
    async def _retry_connection(self, e)  # Retry network connection and reload current animal if back online.
    # calls: asyncio.to_thread, self._load_and_display_animal, self._update_offline_banner
    def cleanup(self)  # Clean up resources.
    # calls: self.notification_service.stop, self.state.close_repository
```

### Module: daynimal.ui.components.animal_card
> Reusable animal card component for list views.
> 
> This module provides a clickable card widget used in History, Favorites, and Search views.
> Eliminates 3 duplications from the original app.py.
```python
class AnimalCard(ft.Card)  # Reusable animal card for displaying an animal in a list.
    def __init__(self, animal, on_click, metadata_icon, metadata_text, metadata_icon_color)  # Initialize animal card.
    # calls: _get_display_name, ft.Column, ft.Container, ft.Icon, ft.Row, ft.Text, on_click, super, super.__init__
```
```python
def _get_display_name(taxon)  # Return the best display name for a taxon.
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
- calls: `AnimalCard`

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
    def __init__(self, images, current_index, on_index_change, animal_display_name, animal_taxon_id, image_cache)  # Initialize ImageCarousel.
    def build(self)  # Build the carousel UI.
    # calls: ft.Column, ft.Container, ft.IconButton, ft.Image, ft.Padding, ft.Row, ft.Text, len, self._build_empty_state, self._build_error_content, self.image_cache.get_local_path, str
    def _build_empty_state(self)  # Build the empty state UI when no images available.
    # calls: ft.Column, ft.Container, ft.Icon, ft.Text
    def _build_error_content(self, image)  # Build the error content for failed image loads.
    # calls: ft.Column, ft.Container, ft.Icon, ft.Text
    def _on_prev(self, e)  # Navigate to previous image.
    # calls: len, self.on_index_change
    def _on_next(self, e)  # Navigate to next image.
    # calls: len, self.on_index_change
```

### Module: daynimal.ui.components.image_gallery_dialog
> Image gallery dialog for lazy-loading and browsing all animal images.
```python
class ImageGalleryDialog  # Dialog that downloads remaining images with progress, then shows a carousel.
    def __init__(self, images, image_cache, page, animal_display_name, animal_taxon_id)
    def open(self)  # Open the gallery dialog.
    # calls: self._show_carousel_dialog, self._show_download_dialog, self.image_cache.are_all_cached
    def _show_download_dialog(self)  # Show dialog with progress bar, then switch to carousel when done.
    # calls: ft.AlertDialog, ft.Button, ft.Column, ft.Container, ft.ProgressBar, ft.Text, len, self.page.pop_dialog, self.page.run_task, self.page.show_dialog
    async def _download_all(self)  # Download all images in a thread, updating progress bar.
    # calls: asyncio.to_thread, self._build_carousel_controls, self.page.update
    def _show_carousel_dialog(self)  # Show dialog directly with carousel (images already cached).
    # calls: ft.AlertDialog, ft.Button, ft.Column, ft.Container, ft.Text, self._build_carousel_controls, self.page.pop_dialog, self.page.show_dialog
    def _build_carousel_controls(self)  # Build carousel controls for the current image.
    # calls: ft.Container, ft.IconButton, ft.Image, ft.Row, ft.Text, len, self.image_cache.get_local_path, str
    def _on_prev(self, e)  # Navigate to previous image.
    # calls: len, self._refresh_carousel
    def _on_next(self, e)  # Navigate to next image.
    # calls: len, self._refresh_carousel
    def _refresh_carousel(self)  # Refresh the carousel content in the dialog.
    # calls: self._build_carousel_controls, self.page.update
```

### Module: daynimal.ui.components.pagination
> Reusable pagination bar component.
```python
class PaginationBar  # Pagination bar: [< Précédent]  Page X / Y  [Suivant >]
    def __init__(self, page, total, per_page, on_page_change)
    @property
    def total_pages(self)
    # calls: math.ceil, max
    def build(self)
    # calls: ft.Button, ft.Container, ft.Padding.symmetric, ft.Row, ft.Text, self.on_page_change
```

### Module: daynimal.ui.components.widgets
> Reusable UI widgets for Daynimal app.
> 
> This module eliminates code duplication by providing common widgets
> used across multiple views.
```python
class LoadingWidget(ft.Container)  # Loading indicator widget.
    def __init__(self, message, subtitle)  # Initialize loading widget.
    # calls: ft.Alignment, ft.Column, ft.ProgressRing, ft.Text, super, super.__init__
```
```python
class ErrorWidget(ft.Container)  # Error display widget.
    def __init__(self, title, details)  # Initialize error widget.
    # calls: ft.Alignment, ft.Column, ft.Icon, ft.Text, super, super.__init__
```
```python
class EmptyStateWidget(ft.Container)  # Empty state widget.
    def __init__(self, icon, title, description, icon_size, icon_color)  # Initialize empty state widget.
    # calls: ft.Column, ft.Icon, ft.Text, super, super.__init__
```
```python
def view_header(title)  # Standard page header used by all views.
```
- calls: `ft.Container`, `ft.Row`, `ft.Text`

### Module: daynimal.ui.state
> Application state management for Daynimal UI.
> 
> This module provides centralized state management for the Flet application,
> including repository lifecycle, current animal display, and caching.
```python
@dataclass
class AppState  # Shared application state across all views.
    @property
    def image_cache(self)  # Get image cache service from repository.
    @property
    def repository(self)  # Get or create repository (lazy initialization, thread-safe).
    # calls: AnimalRepository, self._repository.get_setting
    def close_repository(self)  # Close repository and cleanup resources.
    # calls: self._repository.close
    @property
    def is_online(self)  # Return current network connectivity state.
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
    def __init__(self, page, app_state)  # Initialize base view.
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
    def log_info(self, message)  # Log info message.
    def log_error(self, context, error)  # Log error message.
    # calls: type
```

### Module: daynimal.ui.views.favorites_view
> Favorites view for displaying favorite animals.
```python
class FavoritesView(BaseView)  # View for displaying and managing favorite animals.
    def __init__(self, page, app_state, on_animal_click)  # Initialize FavoritesView.
    # calls: ft.Column, ft.Container, super, super.__init__
    def build(self)  # Build the favorites view UI.
    # calls: asyncio.create_task, ft.Column, ft.Container, ft.Divider, self.load_favorites, view_header
    async def load_favorites(self)  # Load favorites from repository.
    # calls: PaginationBar, PaginationBar.build, asyncio.sleep, asyncio.to_thread, create_favorite_card, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, self.app_state.repository.get_favorites, self.page.update, str, traceback.print_exc
    def _on_page_change(self, new_page)  # Handle page change from pagination bar.
    # calls: asyncio.create_task, self.load_favorites
    def _on_item_click(self, taxon_id)  # Handle click on a favorite item.
    # calls: self.on_animal_click, traceback.print_exc
```

### Module: daynimal.ui.views.history_view
> History view for displaying animal viewing history.
```python
class HistoryView(BaseView)  # View for displaying and managing animal viewing history.
    def __init__(self, page, app_state, on_animal_click)  # Initialize HistoryView.
    # calls: ft.Column, ft.Container, super, super.__init__
    def build(self)  # Build the history view UI.
    # calls: asyncio.create_task, ft.Column, ft.Container, ft.Divider, self.load_history, view_header
    async def load_history(self)  # Load history from repository.
    # calls: PaginationBar, PaginationBar.build, asyncio.sleep, asyncio.to_thread, create_history_card, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, self.app_state.repository.get_history, self.page.update, str, traceback.print_exc
    def _on_page_change(self, new_page)  # Handle page change from pagination bar.
    # calls: asyncio.create_task, self.load_history
    def _on_item_click(self, taxon_id)  # Handle click on a history item.
    # calls: self.on_animal_click, traceback.print_exc
```

### Module: daynimal.ui.views.search_view
> Search view for Daynimal app.
> 
> This module provides the search interface with a classic search field
> (submit on Enter or button click).
```python
class SearchView(BaseView)  # Search view with search field and results list.
    def __init__(self, page, app_state, on_result_click)  # Initialize search view.
    # calls: ft.Column, ft.IconButton, ft.TextField, super, super.__init__
    def build(self)  # Build the search view UI.
    # calls: ft.Container, ft.Divider, ft.Padding, ft.Row, self.show_empty_search_state, view_header
    async def refresh(self)  # Refresh search view (no-op for search view).
    def _on_submit(self, e)  # Handle Enter key in search field.
    # calls: asyncio.create_task, self.perform_search, self.search_field.value.strip
    def _on_search_click(self, e)  # Handle search button click.
    # calls: asyncio.create_task, self.perform_search, self.search_field.value.strip
    def show_empty_search_state(self)  # Show empty state (before any search).
    # calls: ft.Alignment, ft.Column, ft.Container, ft.Icon, ft.Text
    async def perform_search(self, query)  # Perform search in repository.
    # calls: asyncio.sleep, asyncio.to_thread, create_search_card, ft.Alignment, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, len, self.app_state.repository.search, self.log_error, self.log_info, self.page.update, str
```

### Module: daynimal.ui.views.settings_view
> Settings view for app configuration and credits.
```python
class SettingsView(BaseView)  # View for app settings, preferences, and credits.
    def __init__(self, page, app_state)  # Initialize SettingsView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the settings view UI.
    # calls: asyncio.create_task, self._load_settings
    async def _load_settings(self)  # Load settings and build the UI.
    # calls: asyncio.to_thread, ft.Button, ft.Column, ft.Container, ft.Divider, ft.Dropdown, ft.Icon, ft.Padding, ft.Row, ft.Switch, ft.Text, ft.dropdown.Option, range, self.app_state.image_cache.get_cache_size, self.page.update, str, traceback.print_exc, view_header
    def _on_clear_cache(self, e)  # Handle clear cache button click.
    # calls: asyncio.create_task, self._load_settings, self.app_state.image_cache.clear, traceback.print_exc
    def _on_offline_toggle(self, e)  # Handle forced offline mode toggle.
    # calls: traceback.print_exc
    def _on_theme_toggle(self, e)  # Handle theme toggle switch change.
    # calls: self.app_state.repository.set_setting, self.page.update, traceback.print_exc
    def _on_notifications_toggle(self, e)  # Handle notification toggle switch change.
    # calls: getattr, traceback.print_exc
    def _on_notification_time_change(self, e)  # Handle notification time dropdown change.
    # calls: self.app_state.repository.set_setting, traceback.print_exc
```

### Module: daynimal.ui.views.setup_view
> Setup view for first-launch database installation.
```python
class SetupView(BaseView)  # View displayed on first launch when no database is found.
    def __init__(self, page, app_state, on_setup_complete)  # Initialize SetupView.
    # calls: super, super.__init__
    def build(self)  # Build the setup view UI — shows welcome screen.
    # calls: self._show_welcome
    def _show_welcome(self)  # Display welcome screen with Commencer button.
    # calls: ft.Alignment, ft.Button, ft.ButtonStyle, ft.Column, ft.Container, ft.Icon, ft.Text
    def _on_start_click(self, e)  # Handle Commencer button click — launch async setup.
    # calls: asyncio.create_task, self._start_setup
    async def _start_setup(self)  # Run the download and setup process with real progress.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Alignment, ft.Animation, ft.Button, ft.Column, ft.Container, ft.Icon, ft.ProgressBar, ft.Text, self.log_error, self.on_setup_complete, self.page.update, str
    def _update_progress(self, stage, progress)  # Update UI with weighted global progress.
    # calls: _global_progress, self.page.update
    async def refresh(self)  # No-op refresh.
```
```python
def _global_progress(stage, local_progress)  # Convert a per-stage progress to a global 0.0–1.0 progress.
```
- calls: `sum`

### Module: daynimal.ui.views.stats_view
> Statistics view for displaying database statistics.
```python
class StatsView(BaseView)  # View for displaying database statistics with responsive cards.
    def __init__(self, page, app_state)  # Initialize StatsView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the statistics view UI.
    # calls: asyncio.create_task, ft.Column, ft.Container, ft.Divider, self._display_stats, self.load_stats, self.page.update, view_header
    def _stat_card(self, icon, color, value, label, subtitle)  # Build a compact horizontal stat card.
    # calls: ft.Alignment, ft.Card, ft.Column, ft.Container, ft.Icon, ft.Padding, ft.Row, ft.Text
    def _display_stats(self, stats)  # Display statistics cards.
    # calls: self._stat_card
    async def load_stats(self)  # Load statistics from repository.
    # calls: asyncio.sleep, asyncio.to_thread, ft.Column, ft.Container, ft.Icon, ft.ProgressRing, ft.Text, self._display_stats, self.app_state.repository.get_stats, self.page.update, str, traceback.print_exc
```

### Module: daynimal.ui.views.today_view
> Today view for displaying the animal of the day or random animals.
```python
class TodayView(BaseView)  # View for displaying the animal of the day or random animals.
    def __init__(self, page, app_state, on_favorite_toggle)  # Initialize TodayView.
    # calls: ft.Column, super, super.__init__
    def build(self)  # Build the today view UI.
    # calls: ft.Alignment, ft.Button, ft.ButtonStyle, ft.Column, ft.Container, ft.Divider, ft.Icon, ft.Padding, ft.Row, ft.Text, self._display_animal, view_header
    async def _load_today_animal(self, e)  # Load today's animal.
    # calls: self._load_animal_for_today_view
    async def _load_random_animal(self, e)  # Load a random animal.
    # calls: self._load_animal_for_today_view
    async def _load_animal_for_today_view(self, mode)  # Load and display an animal in the Today view.
    # calls: ErrorWidget, LoadingWidget, asyncio.sleep, asyncio.to_thread, self._display_animal, self.on_load_complete, self.page.update, str, traceback.print_exc
    def _display_animal(self, animal)  # Display animal information in the Today view.
    # calls: AnimalDisplay, ft.Button, ft.Column, ft.Container, ft.Divider, ft.Icon, ft.IconButton, ft.Image, ft.Padding, ft.Row, ft.Text, len, self._open_gallery, self.app_state.image_cache.get_local_path, self.app_state.repository.is_favorite, self.page.update, str
    def _on_favorite_toggle(self, e)  # Handle favorite button toggle.
    # calls: self._display_animal, self.app_state.repository.is_favorite, self.on_favorite_toggle_callback
    def _open_gallery(self, images, animal)  # Open the image gallery dialog.
    # calls: ImageGalleryDialog
    @staticmethod
    def _build_share_text(animal)  # Build formatted share text for an animal.
    # calls: len
    async def _on_copy_text(self, e)  # Copy formatted animal text to clipboard.
    # calls: ft.Clipboard, ft.Clipboard.set, ft.SnackBar, ft.Text, self._build_share_text, self.page.show_dialog
    def _on_open_wikipedia(self, e)  # Open Wikipedia article in default browser.
    # calls: ft.UrlLauncher, self.page.run_task
```

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

### Module: scripts.download_phylopic
> Download all PhyloPic SVG silhouettes with metadata into a zip file.
> 
> Usage:
>     uv run python scripts/download_phylopic.py
> 
> Output:
>     data/phylopic_dump.zip containing:
>     - svgs/<uuid>.svg          (all SVG silhouettes)
>     - phylopic_metadata.csv    (metadata: uuid, taxon, license, attribution, etc.)
```python
def fetch_json(client, url, params)  # Fetch JSON from URL with retry on 429/503.
```
- calls: `float`, `range`, `time.sleep`
```python
def fetch_svg(client, url)  # Download SVG content.
```
- calls: `float`, `range`, `time.sleep`
```python
def get_build_number(client)  # Get current PhyloPic build number.
```
- calls: `fetch_json`
```python
def iter_all_images(client, build)  # Iterate over all images, page by page, yielding each image item.
```
- calls: `fetch_json`, `range`, `str`, `time.sleep`
```python
def extract_metadata(item)  # Extract metadata from an image item.
```
```python
def main()
```
- calls: `csv.DictWriter`, `enumerate`, `extract_metadata`, `fetch_svg`, `get_build_number`, `httpx.Client`, `io.StringIO`, `iter_all_images`, `len`, `sum`, `time.sleep`, `zipfile.ZipFile`

### Module: scripts.prepare_release
> Prepare distribution files for GitHub Release.
> 
> This script:
> 1. Verifies TSV files exist
> 2. Compresses them to .gz
> 3. Calculates checksums
> 4. Generates manifest.json with metadata
> 5. Creates RELEASE_NOTES.md with instructions
```python
def detect_github_user()  # Detect GitHub user/org from the upstream remote of the current branch.
```
- calls: `re.search`, `subprocess.run`
```python
def get_file_size_mb(path)  # Get file size in MB.
```
```python
def calculate_sha256(path)  # Calculate SHA256 checksum of a file.
```
- calls: `hashlib.sha256`, `iter`, `open`
```python
def compress_file(input_path, output_path)  # Compress a file using gzip.
```
- calls: `gzip.open`, `open`, `print`
```python
def verify_tsv_files(data_dir, files)  # Verify that all TSV files exist.
```
- calls: `get_file_size_mb`, `print`
```python
def compress_distribution(data_dir, output_dir, version)  # Compress distribution files and generate manifest.
```
- calls: `calculate_sha256`, `compress_file`, `datetime.now`, `datetime.now.isoformat`, `print`
```python
def generate_release_notes(output_dir, manifest, version, github_user)  # Generate release notes with instructions.
```
- calls: `open`, `print`, `sum`
```python
def generate_checksums_file(output_dir, manifest)  # Generate checksums.txt for easy verification.
```
- calls: `open`, `print`
```python
def main()  # Main entry point.
```
- calls: `Path`, `argparse.ArgumentParser`, `compress_distribution`, `detect_github_user`, `generate_checksums_file`, `generate_release_notes`, `json.dump`, `open`, `print`, `sum`, `verify_tsv_files`

## 6. High-Coupling Modules (Risk Zones)
- No obvious high-coupling modules detected

## 7. Dependency Cycles Detected
- No obvious cycles detected
