"""
Daynimal CLI - Daily Animal Discovery

A command-line tool to discover and learn about animals every day.
"""

import argparse
from contextlib import contextmanager

from daynimal import AnimalInfo
from daynimal.attribution import get_app_legal_notice
from daynimal.config import settings
from daynimal.db.first_launch import download_and_setup_db, resolve_database
from daynimal.repository import AnimalRepository


@contextmanager
def temporary_database(database_url: str | None = None):
    """
    Context manager to temporarily set database_url without polluting global state.

    This allows CLI --db flag to work without permanently mutating the global settings,
    which could pollute tests or other code using the same process.

    Args:
        database_url: Temporary database URL to use, or None to use current settings

    Yields:
        None

    Example:
        with temporary_database("sqlite:///custom.db"):
            repo = AnimalRepository()
            # Uses custom.db
        # settings.database_url is restored
    """
    if database_url is None:
        # No change needed
        yield
        return

    # Save original value
    original_url = settings.database_url

    try:
        # Temporarily set new value
        settings.database_url = database_url
        yield
    finally:
        # Always restore original value
        settings.database_url = original_url


def print_animal(animal: AnimalInfo):
    """
    Pretty print animal information with REQUIRED attributions.

    IMPORTANT: The attribution section at the end is LEGALLY REQUIRED
    for commercial use. Do not remove or hide it.
    """
    print("\n" + "=" * 60)
    print(f"  {animal.display_name.upper()}")
    print(f"  {animal.taxon.scientific_name}")
    print(f"  ID: {animal.taxon.taxon_id}")
    print("=" * 60)

    # Classification
    print("\n[Classification]")
    if animal.taxon.kingdom:
        print(f"   Kingdom: {animal.taxon.kingdom}")
    if animal.taxon.phylum:
        print(f"   Phylum:  {animal.taxon.phylum}")
    if animal.taxon.class_:
        print(f"   Class:   {animal.taxon.class_}")
    if animal.taxon.order:
        print(f"   Order:   {animal.taxon.order}")
    if animal.taxon.family:
        print(f"   Family:  {animal.taxon.family}")
    if animal.taxon.genus:
        print(f"   Genus:   {animal.taxon.genus}")

    # Vernacular names
    if animal.taxon.vernacular_names:
        print("\n[Common Names]")
        for lang, names in list(animal.taxon.vernacular_names.items())[:5]:
            print(f"   [{lang}] {', '.join(names[:3])}")

    # Wikidata info
    if animal.wikidata:
        wd = animal.wikidata
        print(f"\n[Data from Wikidata: {wd.qid}]")
        if wd.iucn_status:
            # Handle both enum and string (from cache)
            status = (
                wd.iucn_status.value
                if hasattr(wd.iucn_status, "value")
                else wd.iucn_status
            )
            print(f"   Conservation: {status}")
        if wd.mass:
            print(f"   Mass: {wd.mass}")
        if wd.length:
            print(f"   Length: {wd.length}")
        if wd.lifespan:
            print(f"   Lifespan: {wd.lifespan}")

    # Description from Wikipedia
    if animal.wikipedia and animal.description:
        print(f"\n[Description from Wikipedia ({animal.wikipedia.language})]")
        desc = animal.description
        if len(desc) > 500:
            desc = desc[:500] + "..."
        # Wrap text for readability
        words = desc.split()
        line = "   "
        for word in words:
            if len(line) + len(word) > 75:
                print(line)
                line = "   " + word
            else:
                line += " " + word if line.strip() else word
        if line.strip():
            print(line)

    # Images with individual attribution
    if animal.images:
        print(f"\n[Images ({len(animal.images)} found)]")
        for img in animal.images[:3]:
            print(f"   - {img.thumbnail_url or img.url}")
            # REQUIRED: Show attribution for each image
            print(f"     Credit: {img.get_attribution_text()}")

    # ============================================================
    # LEGAL REQUIREMENT: Attribution section
    # This section MUST be displayed for commercial compliance
    # ============================================================
    print("\n")
    print(animal.get_attribution_text())
    print("")


def cmd_today():
    """Show today's animal."""
    with AnimalRepository() as repo:
        animal = repo.get_animal_of_the_day()
        if animal:
            print_animal(animal)
            repo.add_to_history(animal.taxon.taxon_id, command="today")
        else:
            print("No animals in database. Run 'import-gbif' first.")


def cmd_random():
    """Show a random animal."""
    with AnimalRepository() as repo:
        animal = repo.get_random()
        if animal:
            print_animal(animal)
            repo.add_to_history(animal.taxon.taxon_id, command="random")
        else:
            print("No animals in database. Run 'import-gbif' first.")


def cmd_search(query: str):
    """Search for animals."""
    with AnimalRepository() as repo:
        results = repo.search(query, limit=10)

        if not results:
            print(f"No results for '{query}'")
            return

        print(f"\nFound {len(results)} results for '{query}':\n")
        for animal in results:
            names = []
            for lang in ["fr", "en"]:
                if animal.taxon.vernacular_names.get(lang):
                    names.append(animal.taxon.vernacular_names[lang][0])
                    break

            name_str = f" ({names[0]})" if names else ""
            print(
                f"  [{animal.taxon.taxon_id}] {animal.taxon.scientific_name}{name_str}"
            )

        # Attribution for search results (taxonomy only)
        print("\n" + "-" * 50)
        print("Data: GBIF Backbone Taxonomy (CC-BY 4.0)")
        print("https://doi.org/10.15468/39omei")


def cmd_info(name: str):
    """Get detailed info about an animal."""
    with AnimalRepository() as repo:
        # Try by ID first if numeric
        if name.isdigit():
            animal = repo.get_by_id(int(name))
        else:
            animal = repo.get_by_name(name)

        if animal:
            print_animal(animal)
            repo.add_to_history(animal.taxon.taxon_id, command="info")
        else:
            print(f"Animal not found: {name}")
            print("Try searching first with: daynimal search <query>")


def cmd_stats():
    """Show database statistics."""
    with AnimalRepository() as repo:
        stats = repo.get_stats()

        print("\n[Database Statistics]")
        print("-" * 30)
        print(f"Total taxa:       {stats['total_taxa']:,}")
        print(f"Species:          {stats['species_count']:,}")
        print(f"Vernacular names: {stats['vernacular_names']:,}")
        print(f"Enriched:         {stats['enrichment_progress']}")
        print("-" * 30)


def cmd_credits():
    """
    Show full legal credits and licenses.

    This information should also be accessible in the app's
    "About" or "Credits" section for legal compliance.
    """
    print(get_app_legal_notice("full"))


def cmd_setup(mode: str = "full", no_taxref: bool = False):
    """Download and set up the database.

    Args:
        mode: 'full' (build from GBIF backbone) or 'minimal' (download pre-built).
        no_taxref: Skip TAXREF French names download (full mode only).
    """
    if resolve_database() is not None:
        print("Database already exists. Nothing to do.")
        return

    if mode == "minimal":
        _setup_minimal()
    else:
        _setup_full(no_taxref=no_taxref)


def _setup_minimal():
    """Download pre-built minimal database from GitHub Releases."""
    print("Setting up Daynimal database (minimal, downloading ~13 MB)...\n")

    def progress(stage: str, progress: float | None):
        labels = {
            "download_manifest": "Downloading manifest",
            "download_taxa": "Downloading taxa",
            "download_vernacular": "Downloading vernacular names",
            "decompress": "Decompressing",
            "build_db": "Building database",
            "build_fts": "Building search index",
            "cleanup": "Cleaning up",
        }
        label = labels.get(stage, stage)
        if progress is not None:
            print(f"\r  {label}... {progress:.0%}", end="", flush=True)
        else:
            print(f"\r  {label}...", flush=True)

    try:
        download_and_setup_db(progress_callback=progress)
        print("\n\nSetup complete! You can now use 'daynimal' commands.")
    except Exception as e:
        print(f"\n\nSetup failed: {e}")
        raise SystemExit(1)


def _setup_full(no_taxref: bool = False):
    """Build full database from GBIF backbone + optional TAXREF."""
    import zipfile
    from pathlib import Path

    from daynimal.db.build_db import build_database
    from daynimal.db.first_launch import download_file, save_db_config
    from daynimal.db.generate_distribution import generate_distribution
    from daynimal.db.init_fts import init_fts

    print("Setting up Daynimal database (full, ~1 GB)...\n")

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    db_filename = "daynimal.db"
    db_path = Path(db_filename)

    try:
        # Step 1: Download and extract TAXREF (unless --no-taxref)
        taxref_path = None
        taxref_file = data_dir / "TAXREFv18.txt"

        if not no_taxref:
            if taxref_file.exists():
                print(f"TAXREF already present: {taxref_file}")
                taxref_path = taxref_file
            else:
                taxref_url = (
                    "https://assets.patrinat.fr/files/referentiel/TAXREF_v18_2025.zip"
                )
                taxref_zip = data_dir / "TAXREF_v18_2025.zip"

                print("Downloading TAXREF (~100 MB)...")

                def _taxref_progress(downloaded: int, total: int | None):
                    if total:
                        pct = downloaded / total
                        print(
                            f"\r  Downloading TAXREF... {pct:.0%}", end="", flush=True
                        )

                download_file(
                    taxref_url, taxref_zip, progress_callback=_taxref_progress
                )
                print()

                # Extract TAXREFv18.txt from ZIP
                print("  Extracting TAXREFv18.txt...")
                with zipfile.ZipFile(taxref_zip, "r") as zf:
                    # Find the file in the archive
                    taxref_member = None
                    for name in zf.namelist():
                        if name.endswith("TAXREFv18.txt"):
                            taxref_member = name
                            break

                    if taxref_member is None:
                        print(
                            "  WARNING: TAXREFv18.txt not found in archive, skipping TAXREF."
                        )
                    else:
                        # Extract to data/ directory with flat name
                        with (
                            zf.open(taxref_member) as src,
                            open(taxref_file, "wb") as dst,
                        ):
                            import shutil

                            shutil.copyfileobj(src, dst)
                        print(f"  Extracted: {taxref_file}")
                        taxref_path = taxref_file
        else:
            print("TAXREF: skipped (--no-taxref)")

        # Step 2: Generate distribution TSV files (downloads backbone.zip if needed)
        print("\nGenerating distribution files (this may take a while)...\n")
        generate_distribution(
            mode="full",
            backbone_path=None,
            taxref_path=taxref_path,
            output_dir=data_dir,
        )

        # Step 3: Build database from TSV files
        taxa_tsv = data_dir / "animalia_taxa.tsv"
        vernacular_tsv = data_dir / "animalia_vernacular.tsv"
        print("\nBuilding database...\n")
        build_database(taxa_tsv, vernacular_tsv, db_filename)

        # Step 4: Initialize FTS5
        print("\nInitializing search index...\n")
        init_fts(db_path=db_filename)

        # Step 5: Save config
        save_db_config(db_path)

        print("\n\nSetup complete! You can now use 'daynimal' commands.")

    except Exception as e:
        # Cleanup partial DB on failure
        if db_path.exists():
            db_path.unlink(missing_ok=True)
        print(f"\n\nSetup failed: {e}")
        raise SystemExit(1)


def cmd_history(page: int = 1, per_page: int = 10):
    """
    Show history of viewed animals.

    Args:
        page: Page number (>= 1)
        per_page: Number of entries per page (>= 1)

    Usage:
        daynimal history                   Show last 10 entries
        daynimal history --page <n>        Show page n (10 entries per page)
        daynimal history --page <n> --per-page <m>  Show page n with m entries per page
    """
    # Validate arguments (argparse already does type checking)
    if page < 1:
        print("Error: page must be >= 1")
        return

    if per_page < 1:
        print("Error: per-page must be >= 1")
        return

    with AnimalRepository() as repo:
        animals, total = repo.get_history(page=page, per_page=per_page)

        if total == 0:
            print("\nNo history yet. View some animals first!")
            print("Try: daynimal random")
            return

        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page  # Ceiling division

        print("\n" + "=" * 60)
        print(f"  HISTORY - {total:,} animal(s) viewed")
        print("=" * 60)
        print(f"  Page {page}/{total_pages} ({per_page} per page)")
        print("=" * 60 + "\n")

        if not animals:
            print(f"  No entries on page {page}")
            print(f"  (Total pages: {total_pages})")
            return

        for animal in animals:
            # Format viewed time
            viewed_str = (
                animal.viewed_at.strftime("%Y-%m-%d %H:%M:%S")
                if animal.viewed_at
                else "Unknown"
            )
            cmd_str = f"[{animal.command}]" if animal.command else ""

            # Get display name
            display_name = animal.display_name

            print(f"  [{animal.taxon.taxon_id}] {display_name}")
            print(f"      {animal.taxon.scientific_name}")
            print(f"      Viewed: {viewed_str} {cmd_str}")
            print()

        # Show navigation hint
        if total_pages > 1:
            print("-" * 60)
            if page < total_pages:
                print(
                    f"  Next page: daynimal history --page {page + 1} --per-page {per_page}"
                )
            if page > 1:
                print(
                    f"  Previous page: daynimal history --page {page - 1} --per-page {per_page}"
                )


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="daynimal",
        description="Daily Animal Discovery - Learn about one animal per day",
        epilog="For more information, visit: https://github.com/yourusername/daynimal",
    )

    # Global options
    parser.add_argument(
        "--db", type=str, metavar="PATH", help="Use alternative database file"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # today command (default if no command specified)
    subparsers.add_parser("today", help="Show today's animal (default)")

    # random command
    subparsers.add_parser("random", help="Show a random animal")

    # search command
    parser_search = subparsers.add_parser("search", help="Search for animals by name")
    parser_search.add_argument(
        "query", nargs="+", help="Search query (scientific or common name)"
    )

    # info command
    parser_info = subparsers.add_parser(
        "info", help="Get detailed information about a specific animal"
    )
    parser_info.add_argument(
        "identifier", nargs="+", help="Animal ID or scientific name"
    )

    # stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # credits command
    subparsers.add_parser("credits", help="Show full legal credits and licenses")

    # setup command
    parser_setup = subparsers.add_parser(
        "setup", help="Download and set up the database"
    )
    parser_setup.add_argument(
        "--mode",
        choices=["full", "minimal"],
        default="full",
        help="'full' (default): build from GBIF backbone (~1 GB). 'minimal': download pre-built (~117 MB)",
    )
    parser_setup.add_argument(
        "--no-taxref",
        action="store_true",
        help="Skip TAXREF French names download (full mode only)",
    )

    # history command
    parser_history = subparsers.add_parser(
        "history", help="Show history of viewed animals"
    )
    parser_history.add_argument(
        "--page", type=int, default=1, help="Page number (default: 1)"
    )
    parser_history.add_argument(
        "--per-page",
        type=int,
        default=10,
        help="Number of items per page (default: 10)",
    )

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Prepare database URL if custom path provided
    database_url = f"sqlite:///{args.db}" if args.db else None

    # Use context manager to temporarily set database without polluting global state
    with temporary_database(database_url):
        # Route to appropriate command
        # Default to 'today' if no command specified
        command = args.command or "today"

        # Setup command doesn't need an existing DB
        if command == "setup":
            cmd_setup(mode=args.mode, no_taxref=args.no_taxref)
            return

        # All other commands require a database
        if resolve_database() is None:
            print("Database not found. Run 'daynimal setup' first.")
            raise SystemExit(1)

        if command == "today":
            cmd_today()
        elif command == "random":
            cmd_random()
        elif command == "search":
            query = " ".join(args.query)
            cmd_search(query)
        elif command == "info":
            identifier = " ".join(args.identifier)
            cmd_info(identifier)
        elif command == "stats":
            cmd_stats()
        elif command == "credits":
            cmd_credits()
        elif command == "history":
            # Pass argparse values directly (no double parsing)
            cmd_history(page=args.page, per_page=args.per_page)


if __name__ == "__main__":
    main()
