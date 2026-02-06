"""
Daynimal CLI - Daily Animal Discovery

Usage:
    daynimal                  Show today's animal
    daynimal random           Show a random animal
    daynimal search <query>   Search for animals
    daynimal info <id|name>   Get info about a specific animal by ID or name
    daynimal stats            Show database statistics
    daynimal credits          Show full legal credits and licenses
"""

import sys

from daynimal import AnimalInfo
from daynimal.attribution import get_app_legal_notice
from daynimal.repository import AnimalRepository


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
            print(f"   Conservation: {wd.iucn_status.value}")
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
        else:
            print("No animals in database. Run 'import-gbif' first.")


def cmd_random():
    """Show a random animal."""
    with AnimalRepository() as repo:
        animal = repo.get_random()
        if animal:
            print_animal(animal)
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


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        cmd_today()
    elif args[0] == "random":
        cmd_random()
    elif args[0] == "search" and len(args) > 1:
        cmd_search(" ".join(args[1:]))
    elif args[0] == "info" and len(args) > 1:
        cmd_info(" ".join(args[1:]))
    elif args[0] == "stats":
        cmd_stats()
    elif args[0] == "credits":
        cmd_credits()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
