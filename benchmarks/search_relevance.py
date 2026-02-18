"""Benchmark search relevance for well-known animal names.

Usage:
    uv run python benchmarks/search_relevance.py
    uv run python benchmarks/search_relevance.py --limit 10
    uv run python benchmarks/search_relevance.py --queries lion tiger
    uv run python benchmarks/search_relevance.py --verbose
"""

import argparse
import sys
import io

from daynimal.repository import AnimalRepository

# Default queries covering French and English common animal names
DEFAULT_QUERIES = [
    "aigle",
    "eagle",
    "tiger",
    "lion",
    "wolf",
    "chat",
    "requin",
    "baleine",
    "ours",
    "dauphin",
    "serpent",
    "tortue",
]


def run(queries: list[str], limit: int, verbose: bool) -> None:
    # Force UTF-8 on Windows
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    repo = AnimalRepository()
    try:
        for query in queries:
            results = repo.search(query, limit=limit)
            names = [r.display_name for r in results]
            print(f"{query:12s} -> {names}")

            if verbose:
                from daynimal.db.models import TaxonModel

                for i, r in enumerate(results):
                    model = repo.session.get(TaxonModel, r.taxon.taxon_id)
                    vn_count = len(model.vernacular_names)
                    exact = sum(
                        1
                        for vn in model.vernacular_names
                        if (vn.name or "").lower() == query.lower()
                    )
                    prefix = sum(
                        1
                        for vn in model.vernacular_names
                        if (vn.name or "").lower().startswith(query.lower() + " ")
                        or (vn.name or "").lower().startswith(query.lower() + "-")
                    )
                    score = repo._relevance_score(model, query.lower())
                    print(
                        f"  {i + 1:2d}. {r.display_name}"
                        f"  (ID={r.taxon.taxon_id}, vn={vn_count},"
                        f" exact={exact}, prefix={prefix}, score={score})"
                    )
                print()
    finally:
        repo.close()


def main():
    parser = argparse.ArgumentParser(description="Benchmark search relevance")
    parser.add_argument(
        "--queries",
        nargs="+",
        default=DEFAULT_QUERIES,
        help="Queries to test (default: predefined list)",
    )
    parser.add_argument(
        "--limit", type=int, default=5, help="Max results per query (default: 5)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed scoring for each result",
    )
    args = parser.parse_args()
    run(args.queries, args.limit, args.verbose)


if __name__ == "__main__":
    main()
