#!/usr/bin/env python3
"""
Prepare distribution files for GitHub Release.

This script:
1. Verifies TSV files exist
2. Compresses them to .gz
3. Calculates checksums
4. Generates manifest.json with metadata
5. Creates RELEASE_NOTES.md with instructions
"""

import gzip
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def detect_github_user() -> str | None:
    """Detect GitHub user/org from the upstream remote of the current branch."""
    try:
        # Get the remote tracking branch (e.g. "origin/master")
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            remote_name = result.stdout.strip().split("/")[0]
        else:
            remote_name = "origin"

        # Get the remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name], capture_output=True, text=True
        )
        if result.returncode != 0:
            return None

        url = result.stdout.strip()

        # Parse GitHub user from HTTPS or SSH URL
        # HTTPS: https://github.com/USER/REPO.git
        # SSH: git@github.com:USER/REPO.git
        match = re.search(r"github\.com[:/]([^/]+)/", url)
        if match:
            return match.group(1)
    except FileNotFoundError:
        pass
    return None


def get_file_size_mb(path: Path) -> float:
    """Get file size in MB."""
    return path.stat().st_size / (1024 * 1024)


def calculate_sha256(path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compress_file(input_path: Path, output_path: Path) -> None:
    """Compress a file using gzip."""
    print(f"  Compressing {input_path.name}...")
    with open(input_path, "rb") as f_in:
        with gzip.open(output_path, "wb", compresslevel=9) as f_out:
            f_out.writelines(f_in)


def verify_tsv_files(data_dir: Path, files: list[str]) -> bool:
    """Verify that all TSV files exist."""
    print("Verifying TSV files...")
    all_exist = True
    for filename in files:
        path = data_dir / filename
        if not path.exists():
            print(f"  [MISSING] {filename}")
            all_exist = False
        else:
            print(f"  [OK] {filename} ({get_file_size_mb(path):.2f} MB)")
    return all_exist


def compress_distribution(data_dir: Path, output_dir: Path, version: str) -> dict:
    """Compress distribution files and generate manifest."""
    output_dir.mkdir(exist_ok=True)

    files_to_compress = ["animalia_taxa_minimal.tsv", "animalia_vernacular_minimal.tsv"]

    manifest = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }

    print("\nCompressing files...")
    for filename in files_to_compress:
        input_path = data_dir / filename
        output_path = output_dir / f"{filename}.gz"

        original_size = input_path.stat().st_size
        compress_file(input_path, output_path)
        compressed_size = output_path.stat().st_size
        sha256 = calculate_sha256(output_path)
        ratio = (1 - compressed_size / original_size) * 100

        print(f"    {output_path.name}: {compressed_size / (1024 * 1024):.2f} MB")

        manifest["files"][f"{filename}.gz"] = {
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "sha256": sha256,
            "compression_ratio": f"{ratio:.1f}%",
        }

    return manifest


def generate_release_notes(
    output_dir: Path, manifest: dict, version: str, github_user: str
) -> None:
    """Generate release notes with instructions."""
    total_original = sum(f["original_size_bytes"] for f in manifest["files"].values())
    total_compressed = sum(
        f["compressed_size_bytes"] for f in manifest["files"].values()
    )
    total_ratio = (1 - total_compressed / total_original) * 100

    notes = f"""# Daynimal Database Distribution v{version}

## 📦 Distribution Files

This release contains the compressed database files for Daynimal mobile/desktop app.

### Files Included

"""

    for filename, info in manifest["files"].items():
        notes += f"- **{filename}**: {info['compressed_size_bytes'] / (1024 * 1024):.2f} MB\n"
        notes += f"  - SHA256: `{info['sha256']}`\n"
        notes += f"  - Compression: {info['compression_ratio']} reduction\n\n"

    notes += f"""### Total Size

- **Compressed**: {total_compressed / (1024 * 1024):.2f} MB
- **Uncompressed**: {total_original / (1024 * 1024):.2f} MB
- **Total compression**: {total_ratio:.1f}% reduction

## 📊 Database Statistics

- **Species count**: ~127,000 animal species (Animalia kingdom)
- **Vernacular names**: ~89,000 French names from TAXREF + multilingual from GBIF
- **Database size after import**: ~117 MB (SQLite with indexes)

## 🚀 Usage

### For Mobile App (First Launch)

The app will automatically:
1. Check available storage (~150 MB required)
2. Download these files (~13.4 MB)
3. Decompress and import into SQLite
4. Build FTS5 search indexes
5. Clean up temporary files

### For Manual Setup

```bash
# Download files
wget https://github.com/{github_user}/daynimal/releases/download/v{version}/animalia_taxa_minimal.tsv.gz
wget https://github.com/{github_user}/daynimal/releases/download/v{version}/animalia_vernacular_minimal.tsv.gz

# Verify checksums (optional but recommended)
sha256sum -c checksums.txt

# Decompress
gunzip animalia_taxa_minimal.tsv.gz
gunzip animalia_vernacular_minimal.tsv.gz

# Import into database
uv run build-db --taxa animalia_taxa_minimal.tsv --vernacular animalia_vernacular_minimal.tsv

# Initialize search indexes
uv run init-fts
```

## 📝 Data Sources

- **GBIF Backbone Taxonomy**: CC-BY 4.0 (https://www.gbif.org/)
- **TAXREF v18**: Etalab Open License 2.0 (https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref)

## ⚠️ Requirements

- Python 3.10+
- ~150 MB free storage
- Internet connection for first download

---

Generated on {manifest["generated_at"]}
"""

    notes_path = output_dir / "RELEASE_NOTES.md"
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(notes)

    print(f"\n[OK] Release notes: {notes_path}")


def generate_checksums_file(output_dir: Path, manifest: dict) -> None:
    """Generate checksums.txt for easy verification."""
    checksums_path = output_dir / "checksums.txt"
    with open(checksums_path, "w", encoding="utf-8") as f:
        for filename, info in manifest["files"].items():
            f.write(f"{info['sha256']}  {filename}\n")
    print(f"[OK] Checksums file: {checksums_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Prepare distribution files for release"
    )
    parser.add_argument(
        "--version", type=str, default="1.0.0", help="Release version (default: 1.0.0)"
    )
    parser.add_argument(
        "--github-user",
        type=str,
        default=None,
        help="GitHub user/org for download URLs (auto-detected from git remote if omitted)",
    )
    args = parser.parse_args()

    # Resolve GitHub user
    github_user = args.github_user or detect_github_user()
    if not github_user:
        print("[WARNING] Could not detect GitHub user. Use --github-user to set it.")
        github_user = "YOUR_USER"
    else:
        print(f"GitHub user: {github_user}")

    print("=" * 70)
    print(f"Daynimal Distribution Release Preparation v{args.version}")
    print("=" * 70)

    data_dir = Path("data")
    output_dir = Path("dist")

    files_to_compress = ["animalia_taxa_minimal.tsv", "animalia_vernacular_minimal.tsv"]

    # Step 1: Verify files exist
    if not verify_tsv_files(data_dir, files_to_compress):
        print("\n[ERROR] Some TSV files are missing!")
        print("Generate them with: uv run generate-distribution --mode minimal")
        return 1

    # Step 2: Compress files
    manifest = compress_distribution(data_dir, output_dir, args.version)

    # Step 3: Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[OK] Manifest: {manifest_path}")

    # Step 4: Generate checksums file
    generate_checksums_file(output_dir, manifest)

    # Step 5: Generate release notes
    generate_release_notes(output_dir, manifest, args.version, github_user)

    # Summary
    total_compressed = sum(
        f["compressed_size_bytes"] for f in manifest["files"].values()
    )
    print("\n" + "=" * 70)
    print("[SUCCESS] Release preparation complete!")
    print(f"   Total download size: {total_compressed / (1024 * 1024):.2f} MB")
    print(f"   Output directory: {output_dir.absolute()}")
    print("=" * 70)

    print("\nNext steps:")
    print("   1. Create a new GitHub Release")
    print(f"   2. Tag it as v{args.version}")
    print("   3. Upload files from dist/ folder:")
    print("      - animalia_taxa_minimal.tsv.gz")
    print("      - animalia_vernacular_minimal.tsv.gz")
    print("      - manifest.json")
    print("      - checksums.txt")
    print("   4. Copy content from RELEASE_NOTES.md to release description")

    return 0


if __name__ == "__main__":
    exit(main())
