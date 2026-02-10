# Distribution Release Process

This document explains how to prepare and publish distribution files for Daynimal mobile/desktop deployment.

## Overview

The distribution process creates compressed TSV files that mobile/desktop apps download on first launch to build their local SQLite database.

**Key benefits:**
- **Small download**: ~13.4 MB (vs 117 MB database)
- **Verifiable**: SHA256 checksums included
- **Fast decompression**: gzip compression (75.6% reduction)

## Prerequisites

1. **Generate distribution TSV files**:
   ```bash
   uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
   ```

   This creates:
   - `data/animalia_taxa_minimal.tsv` (~23 MB)
   - `data/animalia_vernacular_minimal.tsv` (~33 MB)

2. **Verify files exist**:
   ```bash
   ls -lh data/animalia_taxa_minimal.tsv data/animalia_vernacular_minimal.tsv
   ```

## Prepare Release

Run the release preparation script:

```bash
uv run python scripts/prepare_release.py --version 1.0.0
```

This generates in `dist/`:
- `animalia_taxa_minimal.tsv.gz` (4.15 MB)
- `animalia_vernacular_minimal.tsv.gz` (9.21 MB)
- `manifest.json` (metadata + checksums)
- `checksums.txt` (for sha256sum verification)
- `RELEASE_NOTES.md` (GitHub release description)

## Publish to GitHub Releases

### Step 1: Create Release on GitHub

1. Go to: https://github.com/YOUR_USER/daynimal/releases/new
2. Choose a tag: `v1.0.0` (create new tag on publish)
3. Release title: `Database Distribution v1.0.0`
4. Copy content from `dist/RELEASE_NOTES.md` to description

### Step 2: Upload Assets

Upload these 4 files from `dist/` folder:
- `animalia_taxa_minimal.tsv.gz`
- `animalia_vernacular_minimal.tsv.gz`
- `manifest.json`
- `checksums.txt`

### Step 3: Publish

Click "Publish release"

### Step 4: Get URLs

After publishing, note the asset URLs:
```
https://github.com/YOUR_USER/daynimal/releases/download/v1.0.0/animalia_taxa_minimal.tsv.gz
https://github.com/YOUR_USER/daynimal/releases/download/v1.0.0/animalia_vernacular_minimal.tsv.gz
https://github.com/YOUR_USER/daynimal/releases/download/v1.0.0/manifest.json
```

These URLs will be used by the mobile app for downloading.

## Update App Configuration

Update the download URLs in your app configuration:

```python
# Example in config.py or similar
DISTRIBUTION_BASE_URL = "https://github.com/YOUR_USER/daynimal/releases/download/v1.0.0"
DISTRIBUTION_VERSION = "1.0.0"
```

## Verification

Users can verify downloads with:

```bash
# Download checksums file
wget https://github.com/YOUR_USER/daynimal/releases/download/v1.0.0/checksums.txt

# Verify files
sha256sum -c checksums.txt
```

Expected output:
```
animalia_taxa_minimal.tsv.gz: OK
animalia_vernacular_minimal.tsv.gz: OK
```

## File Structure

### manifest.json

```json
{
  "version": "1.0.0",
  "generated_at": "2026-02-09T23:08:05.128151+00:00",
  "files": {
    "animalia_taxa_minimal.tsv.gz": {
      "original_size_bytes": 23949239,
      "compressed_size_bytes": 4356591,
      "sha256": "...",
      "compression_ratio": "81.8%"
    },
    "animalia_vernacular_minimal.tsv.gz": {
      "original_size_bytes": 33562335,
      "compressed_size_bytes": 9659355,
      "sha256": "...",
      "compression_ratio": "71.2%"
    }
  }
}
```

The app can parse this manifest to:
- Verify file integrity before decompression
- Show accurate download progress
- Check version compatibility

## Automation (Future)

Consider automating this with GitHub Actions:

```yaml
# .github/workflows/release-distribution.yml
name: Release Distribution

on:
  release:
    types: [created]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - name: Prepare release
        run: |
          uv run python scripts/prepare_release.py --version ${{ github.ref_name }}

      - name: Upload assets
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/animalia_taxa_minimal.tsv.gz
            dist/animalia_vernacular_minimal.tsv.gz
            dist/manifest.json
            dist/checksums.txt
```

## Troubleshooting

### TSV files missing

If `prepare_release.py` reports missing files:

```bash
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
```

### Checksums don't match

Re-run preparation script to regenerate checksums:

```bash
rm -rf dist/
uv run python scripts/prepare_release.py --version 1.0.0
```

### Large file sizes

If compressed files are too large:
- Verify you're using `--mode minimal` (not `full`)
- Check TSV files aren't corrupted
- Compression should achieve ~75% reduction

## See Also

- [TAXREF Integration](TAXREF.md) - French names from TAXREF
- [Mobile Roadmap](MOBILE_DESKTOP_ROADMAP.md) - Phase 2b distribution plans
- [CLAUDE.md](../CLAUDE.md) - Development commands
