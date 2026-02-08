# Plan : Refactorer les workflows de génération et construction des DBs

## Contexte

Les scripts actuels mélangent extraction, filtrage, et import dans un seul script (`import_gbif_fast.py`). De plus, les noms TAXREF ne sont pas intégrés dans les fichiers de distribution minimaux, ce qui fait perdre ~39K espèces françaises à la DB minimale.

On sépare clairement deux workflows :
1. **Génération des fichiers de distribution** : fichiers bruts → TSV prêts à l'emploi
2. **Construction de la DB** : TSV de distribution → DB SQLite

## Fichiers à créer

### 1. `daynimal/db/generate_distribution.py`

**Rôle :** Générer les fichiers de distribution TSV à partir des sources brutes (GBIF + TAXREF).

**Arguments :**
- `--mode full|minimal` (obligatoire)
- `--backbone <path>` (optionnel, chemin vers backbone.zip déjà téléchargé ; sinon téléchargement auto dans `data/`)
- `--taxref <path>` (optionnel, chemin vers TAXREFv18.txt)
- `--output-dir <dir>` (défaut: `data/`)

**Étapes pour le mode minimal :**

```
1. Localiser backbone.zip :
   - Si --backbone fourni : utiliser ce chemin
   - Sinon : télécharger dans output-dir si absent (réutiliser download_backbone())
2. Extraire taxa Animalia rank='species' depuis GBIF → taxa TSV temporaire
3. Extraire vernacular names depuis GBIF → vernacular TSV temporaire
4. Si --taxref fourni :
   a. Construire mapping canonical_name → taxon_id depuis le taxa TSV
   b. Parser TAXREF (Animalia, NOM_VERN non vide)
   c. Matcher canonical_name → taxon_id
   d. Ajouter les noms TAXREF matchés au vernacular TSV (éviter doublons)
   Si --taxref NON fourni :
   → Afficher WARNING avec conseil de téléchargement :
     "TAXREF non fourni. Les noms français seront limités aux données GBIF."
     "Pour enrichir avec ~49K noms français supplémentaires :"
     "  1. Télécharger TAXREF depuis https://inpn.mnhn.fr/telechargement/referentielEspece/taxref"
     "  2. Décompresser et relancer avec --taxref data/TAXREFv18.txt"
5. Cleanup (minimal seulement) : lire vernacular TSV → set de taxon_ids avec noms,
   puis filtrer taxa TSV pour ne garder que ces taxon_ids
6. Afficher statistiques
```

**Étapes pour le mode full :** Identique mais sans filtre rank='species' (étape 2) et sans cleanup (étape 5).

**Noms des fichiers de sortie :**
- Full : `animalia_taxa.tsv` + `animalia_vernacular.tsv`
- Minimal : `animalia_taxa_minimal.tsv` + `animalia_vernacular_minimal.tsv`

**Code réutilisé depuis les scripts à supprimer :**
- Logique d'extraction de `import_gbif_fast.py` : `extract_and_filter_taxa()`, `extract_and_filter_vernacular()`
- Logique de parsing TAXREF de `export_taxref_tsv.py` / `import_taxref_french_fast.py`

**Modules partagés existants :**
- `import_gbif_utils.py` : `download_backbone()`, `TAXON_COLUMNS`, `VERNACULAR_COLUMNS`, `parse_int()`

### 2. `daynimal/db/build_db.py`

**Rôle :** Construire une DB SQLite à partir des fichiers de distribution TSV.

**Arguments :**
- `--taxa <path>` (obligatoire)
- `--vernacular <path>` (obligatoire)
- `--db <filename>` (défaut: `daynimal.db`)

**Étapes :**

```
1. Créer DB + schéma (Base.metadata.create_all)
2. Optimiser PRAGMA SQLite (synchronous OFF, cache 256MB)
3. Import taxa depuis TSV (bulk insert par batch de 5000)
4. Import vernacular depuis TSV (bulk insert par batch de 10000)
5. Restaurer PRAGMA
6. VACUUM
7. Afficher statistiques
8. Rappeler de lancer init-fts
```

**Code réutilisé depuis `import_gbif_fast.py` :**
- `optimize_database_for_import()`, `restore_database_settings()`
- `bulk_import_taxa()`, `bulk_import_vernacular()`

### 3. Ajouter `extract_canonical_name()` dans `import_gbif_utils.py`

Cette fonction (actuellement dans `export_taxref_tsv.py` et `import_taxref_french_fast.py`) est nécessaire pour `generate_distribution.py`. La déplacer dans le module utilitaire partagé.

## Fichiers à supprimer

| Fichier | Remplacé par |
|---------|-------------|
| `daynimal/db/import_gbif_fast.py` | `generate_distribution.py` + `build_db.py` |
| `daynimal/db/import_taxref_french_fast.py` | `generate_distribution.py` (--taxref) |
| `daynimal/db/export_taxref_tsv.py` | `generate_distribution.py` |
| `daynimal/db/import_taxref_tsv.py` | `build_db.py` |

## Mise à jour `pyproject.toml`

**Entry points à supprimer :**
- `import-gbif-fast`
- `import-taxref-french-fast`
- `export-taxref-tsv`
- `import-taxref-tsv`

**Entry points à ajouter :**
- `generate-distribution` → `daynimal.db.generate_distribution:main`
- `build-db` → `daynimal.db.build_db:main`

## Mise à jour documentation

Mettre à jour `docs/MOBILE_DESKTOP_ROADMAP.md` (section Pipeline) et `CLAUDE.md` (section Setup/Commands) avec les nouveaux workflows.

## Workflows finaux

### Desktop
```bash
# 1. Générer fichiers de distribution
uv run generate-distribution --mode full --taxref data/TAXREFv18.txt
# ou --mode minimal

# 2. Construire la DB
uv run build-db --taxa data/animalia_taxa.tsv --vernacular data/animalia_vernacular.tsv --db daynimal.db
# ou avec les fichiers minimal

# 3. Index FTS5
uv run init-fts
```

### Mobile (premier lancement)
```bash
# Côté serveur (une seule fois) :
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
gzip data/animalia_taxa_minimal.tsv data/animalia_vernacular_minimal.tsv
# → héberger sur CDN / GitHub Releases

# Côté mobile :
# 1. Télécharger + décompresser les TSV
# 2. build-db (même logique que desktop)
# 3. init-fts
# 4. Supprimer les TSV
```

## Vérification

1. `uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt`
   - Vérifier que les TSV contiennent les noms TAXREF fusionnés
   - Vérifier que le cleanup exclut les espèces sans aucun nom

2. `uv run build-db --taxa data/animalia_taxa_minimal.tsv --vernacular data/animalia_vernacular_minimal.tsv --db test_minimal.db`
   - Compter taxa, vernacular, noms FR
   - Attendu : ~166K+ espèces (vs 127K avant), ~52K+ noms FR (vs 43K avant)

3. Même chose en mode full, vérifier cohérence avec l'ancienne DB

4. `uv run pytest` pour vérifier que les tests existants passent
