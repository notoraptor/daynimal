# Roadmap : Application Mobile/Desktop

**Derniere mise a jour** : 2026-02-10

---

## Etat actuel

### Phase 1 Desktop : complétée (2026-02-07)

Application Flet fonctionnelle avec 6 onglets :
- Aujourd'hui (animal du jour + aleatoire, carousel d'images)
- Historique (liste paginee, navigation cliquable)
- Favoris (ajout/suppression, persistence)
- Recherche (FTS5, resultats en temps reel)
- Statistiques (cards responsive, persistence d'etat)
- Parametres (theme clair/sombre, credits)

Infrastructure :
- Base de donnees minimale : 163K especes, 117 MB apres VACUUM
- Fichiers TSV compresses : ~14-16 MB (pour distribution mobile, TAXREF inclus)
- Chargement async, gestion d'erreurs, logging integre

---

## Pipeline de donnees (reference)

### Sources brutes (a telecharger une seule fois)

| Fichier | Source | Taille | Licence | Telechargement |
|---------|--------|--------|---------|----------------|
| `backbone.zip` | GBIF Backbone Taxonomy | **927 MB** | CC-BY 4.0 | Auto (par `generate-distribution`) |
| `TAXREF_v18_2025.zip` | patrinat.fr (MNHN) | **58 MB** | Etalab 2.0 | Manuel |

### Pipeline de fabrication

Le pipeline est separe en deux etapes :
1. **generate-distribution** : sources brutes (GBIF + TAXREF) → fichiers TSV de distribution
2. **build-db** : fichiers TSV → base de donnees SQLite

```
backbone.zip (927 MB) + TAXREFv18.txt (optionnel)
    |
    +-- generate-distribution --mode full --taxref data/TAXREFv18.txt
    |       |-- data/animalia_taxa.tsv .............. ~598 MB (4.4M lignes)
    |       +-- data/animalia_vernacular.tsv ........ ~32 MB  (1.1M lignes, noms TAXREF inclus)
    |
    +-- generate-distribution --mode minimal --taxref data/TAXREFv18.txt
            |-- data/animalia_taxa_minimal.tsv ...... ~20 MB (166K+ lignes)
            +-- data/animalia_vernacular_minimal.tsv  ~32 MB  (1M+ lignes, noms TAXREF inclus)

Ensuite pour chaque mode :
    build-db --taxa <taxa.tsv> --vernacular <vernacular.tsv> --db daynimal.db
    init-fts
```

### Différences de filtrage entre modes

Les deux modes appliquent un filtrage different sur le GBIF Backbone Taxonomy :

| Critere | Mode **full** | Mode **minimal** |
|---------|---------------|------------------|
| **Rangs taxonomiques** | Tous (species, genus, family, order, class, phylum, subspecies, variety, etc.) | **Uniquement species** |
| **Filtrage vernaculaire** | Non | **Oui** : supprime especes sans nom vernaculaire |
| **Integration TAXREF** | Oui (45,707 noms FR ajoutes) | Oui (45,175 noms FR ajoutes) |
| **Pipeline** | 1. Extraire Animalia (tous rangs)<br>2. Fusionner TAXREF<br>3. Importer tout | 1. Extraire Animalia (rank='species' seulement)<br>2. Fusionner TAXREF<br>3. **Cleanup : supprimer especes sans noms** |
| **Taxa resultants** | 4.43M (hierarchie complete) | 163K (especes avec noms uniquement) |
| **Noms vernaculaires** | 1.16M (tous rangs) | 1.12M (especes seulement) |
| **Noms francais** | 90K (GBIF + TAXREF) | 89K (GBIF + TAXREF) |
| **Taille DB finale** | 1.08 GB (apres VACUUM) | 117 MB (apres VACUUM) |

**Exemple concret** :
- Mode full : inclut `Felidae` (famille → "Cats", "Felins"), `Panthera` (genre → "Big cats"), `Panthera leo` (espece → "Lion")
- Mode minimal : inclut **seulement** `Panthera leo` (espece avec noms vernaculaires)

**Note** : VACUUM est applique automatiquement aux deux modes en fin d'import.

### Fichiers presents sur le disque (fevrier 2026 - apres refactoring)

**Données brutes** (`data/`, gitignore) :

| Fichier | Taille | Lignes | Notes |
|---------|--------|--------|-------|
| `backbone.zip` | 927 MB | - | Source GBIF |
| `TAXREFv18.txt` | 303 MB | - | Source TAXREF decompressee |
| `animalia_taxa.tsv` | 597 MB | 4,432,185 | Mode full |
| `animalia_vernacular.tsv` | 33 MB | 1,158,594 | Mode full (GBIF + TAXREF) |
| `animalia_taxa_minimal.tsv` | 23 MB | 163,434 | Mode minimal (apres cleanup) |
| `animalia_vernacular_minimal.tsv` | 33 MB | 1,117,898 | Mode minimal (GBIF + TAXREF) |

**Bases de données** (racine, gitignore) :

| Fichier | Taille | Taxa | Vernaculaires | Noms FR | Notes |
|---------|--------|------|---------------|---------|-------|
| `daynimal.db` (full) | 1.08 GB | 4,432,185 | 1,158,594 | 90,198 | GBIF + TAXREF, VACUUM |
| `daynimal_minimal.db` | 117 MB | 163,434 | 1,117,898 | 88,781 | Especes avec noms, VACUUM |

**Ameliorations apres refactoring :**
- DB minimal : **-26% taille** (117 MB vs 159 MB), **+68% noms FR** (88K vs 53K)
- DB full : **-40% taille** (1.08 GB vs 1.8 GB), noms TAXREF integres des la generation
- Taxa minimal : cleanup correct (163K especes avec noms vs 3M avant)

Tables dans les deux DB : `taxa`, `vernacular_names`, `enrichment_cache`, `animal_history`, `favorites`, `user_settings`, `image_cache`, `taxa_fts` (FTS5).

### Problème resolu : noms TAXREF integres dans les TSV

Depuis le refactoring du pipeline (fevrier 2026), `generate-distribution` fusionne les noms
TAXREF directement dans les fichiers de distribution via le flag `--taxref`. Les noms francais
sont donc disponibles dans les TSV sans etape supplementaire.

### Distribution desktop

Pas de fichiers pre-construits a distribuer. L'utilisateur execute le pipeline lui-meme :

```bash
# 1. Generer les fichiers de distribution (auto-download de backbone.zip si absent)
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
# ou mode full :
# uv run generate-distribution --mode full --taxref data/TAXREFv18.txt
# Sans TAXREF (noms FR limites a GBIF) :
# uv run generate-distribution --mode minimal

# 2. Construire la DB SQLite
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv
# ou mode full :
# uv run build-db --taxa data/animalia_taxa.tsv \
#                 --vernacular data/animalia_vernacular.tsv

# 3. Construire l'index de recherche FTS5
uv run init-fts

# 4. Migrations (si upgrade d'une DB existante)
uv run migrate-history
uv run migrate-favorites
```

Espace disque necessaire :
- Telechargement : 985 MB (backbone.zip 927 MB + TAXREF 303 MB decompressee)
- Fichiers intermediaires TSV : ~630 MB (full) ou ~56 MB (minimal), supprimables apres import
- DB finale : **1.08 GB** (full) ou **117 MB** (minimal)

### Distribution mobile

L'app mobile ne peut pas telecharger `backbone.zip` (927 MB) ni executer le pipeline complet.
Il faut heberger des fichiers pre-filtres (TSV compresses) que l'app telecharge au premier lancement.

Fichiers a heberger (GitHub Releases ou CDN) :

| Fichier | Taille (non compresse) | Taille (gzip, estimee) |
|---------|----------------------|----------------------|
| `animalia_taxa_minimal.tsv.gz` | 23 MB | ~5-6 MB |
| `animalia_vernacular_minimal.tsv.gz` | 33 MB | ~8-10 MB |
| **Total** | **56 MB** | **~14-16 MB** |

**Note** : Les TSV incluent deja les noms TAXREF (45K noms FR integres).

Pipeline au premier lancement de l'app mobile :
```
Telecharge TSV.gz (~14-16 MB) ← 6x plus petit qu'avant !
  -> Decompresse (~56 MB temporaires)
    -> Importe dans SQLite (~117 MB)
      -> Construit index FTS5
        -> Supprime les TSV decompresses
          -> Pret (~150-180 MB total sur appareil : APK + DB + cache)
```

Contrainte Google Play : APK < 150 MB, donc la DB doit etre telechargee separement (obligatoire).

### Resume des tailles

| Scenario | Fichiers | Taille (avant) | Taille (apres) | Gain |
|----------|----------|----------------|----------------|------|
| Desktop : telechargement brut | backbone.zip + TAXREF | 985 MB | 985 MB | - |
| Desktop : DB finale (full) | daynimal.db + FTS5 | 1.8 GB | **1.08 GB** | **-40%** |
| Desktop : DB finale (minimal) | daynimal_minimal.db + FTS5 | 159 MB | **117 MB** | **-26%** |
| Mobile : telechargement TSV | 2 TSV.gz (avec TAXREF) | ~93 MB | **~14-16 MB** | **-83%** 🎉 |
| Mobile : DB sur appareil | SQLite + FTS5 | ~153 MB | **~117 MB** | **-23%** |
| Mobile : espace total | APK + DB + cache images | ~200 MB | **~150-180 MB** | **-15%** |

**Ameliorations cles pour mobile :**
- Telechargement initial 6x plus rapide (14 MB vs 93 MB)
- Moins d'espace disque requis (117 MB vs 153 MB)
- Noms francais TAXREF deja integres (89K noms vs 44K avant)

---

## Phase 2a : Stabilisation et refactoring (2-3 semaines)

Corriger la dette technique et restructurer `app.py` avant d'ajouter des features mobiles.
Un bug de thread safety en desktop est genant ; sur mobile avec contraintes memoire, c'est un crash.
Un monolithe de 2200 lignes est ingerable ; chaque feature ajoutee aggrave la dette.

Revue de code : fevrier 2026 (verdict code 6.5/10)

### Bugs critiques

- [x] `datetime.utcnow()` → `datetime.now(UTC)` (6 occurrences dans `models.py` et `attribution.py`)
- [x] `print()` → `logger.warning()` dans `repository.py` (lignes 599, 612, 635)
- [x] ~~**Engine SQLAlchemy recree a chaque session**~~ — `db/session.py` : non critique apres analyse. `get_session()` n'est appele qu'une fois par processus CLI et une fois par vie d'app GUI (lazy init du Repository).
- [x] **Index manquant sur `is_synonym`** — `db/models.py` : ajout `index=True` sur la colonne
- [x] **Thread safety dans `_enrich()`** — `repository.py` : `threading.Lock` sur `_save_cache()` + rollback on error

### Refactoring app.py (2200 lignes, monolithe)

Le refactoring d'`app.py` est un prerequis pour toutes les features suivantes. Chaque feature
ajoutee dans un monolithe de 2200 lignes aggrave la dette technique et rend les tests impossibles.

**Progression : Phase 2a COMPLETEE - Architecture modulaire terminee !**

**app.py reduit de 2190 a 128 lignes (-94% / -2062 lignes)**

Architecture modulaire complete dans `daynimal/ui/` :
- **State** : `state.py` (AppState avec repository lifecycle)
- **Base** : `views/base.py` (BaseView pour toutes les vues)
- **Components** :
  - `components/widgets.py` (LoadingWidget, ErrorWidget, EmptyStateWidget)
  - `components/animal_card.py` (AnimalCard reutilisable)
  - `components/pagination.py` (PaginationBar reutilisable)
  - `components/image_carousel.py` (ImageCarousel avec navigation)
  - `components/animal_display.py` (AnimalDisplay pour details)
- **Views** (toutes etendent BaseView) :
  - `views/search_view.py` (SearchView)
  - `views/history_view.py` (HistoryView)
  - `views/favorites_view.py` (FavoritesView)
  - `views/settings_view.py` (SettingsView avec async operations)
  - `views/stats_view.py` (StatsView avec cache)
  - `views/today_view.py` (TodayView utilisant ImageCarousel et AnimalDisplay)
- **Controller** : `ui/app_controller.py` (AppController orchestrant toutes les vues)
- **Utils** : `utils/debounce.py` (Debouncer 300ms, conserve)
- **Tests** : 61 tests UI dans `tests/ui/` (100%)

**Fait :**
- [x] Infrastructure UI : AppState, BaseView, widgets reutilisables (Phase 1)
- [x] SearchView extraite avec AnimalCard reutilisable (Phase 2)
- [x] Corrections : race conditions, type annotations, thread safety AppState, protection page.update() (Phase 3)
- [x] Recherche classique Enter/Button au lieu du debouncing automatique (Phase 3)
- [x] Fuite de ressources Repository resolue (AppState.close_repository)
- [x] Extraire `_load_and_display_animal()` — unifier 3 methodes dupliquees (Phase 4 : -119 lignes)
- [x] Extraire HistoryView (~195 lignes)
- [x] Extraire FavoritesView (~195 lignes)
- [x] Extraire SettingsView (~260 lignes avec async operations)
- [x] Extraire StatsView (~250 lignes avec cache)
- [x] Extraire ImageCarousel (~195 lignes)
- [x] Extraire AnimalDisplay (~205 lignes)
- [x] Extraire TodayView (~320 lignes utilisant ImageCarousel et AnimalDisplay)
- [x] Creer AppController (~330 lignes orchestrant 6 vues)
- [x] Reduire app.py a 128 lignes entry point (-94%)

**Reste a faire :**

**Corrections ciblees restantes :**
- [x] **Settings synchrone** — Resolu dans SettingsView (utilise `asyncio.to_thread()`)

### Corrections mineures

- [x] **CLI History double parsing** — Resolu
  - `cmd_history()` accepte maintenant `page: int, per_page: int` directement
  - `main()` passe les valeurs parsees par argparse sans reconversion
  - Tests mis a jour (34 tests CLI passent)
- [x] **Mutation globale settings** — Resolu avec context manager
  - Nouveau `temporary_database()` context manager sauvegarde/restaure settings
  - Plus de pollution globale entre tests ou executions CLI
  - Tests mis a jour pour verifier la restauration des settings

### Tests — ✅ Achievements exceptionnels

**Couverture actuelle : 55%** — **499 tests passent** (vs ~50 tests initiaux)

**🎉 Succès Phase 2a - Tests critiques (Fév 2026)**
- **attribution.py** : 0% → **100%** (75 tests, compliance légale garantie)
- **repository.py** : 41% → **99%** (139 tests additionnels, 1 ligne defensive restante)

| Composant | Couverture | Verdict |
|-----------|-----------|---------|
| **Attribution (attribution.py)** | **100%** ✅ | **Excellent** — Compliance légale garantie |
| **Repository (repository.py)** | **99%** ✅ | **Excellent** — 1 ligne defensive non couverte |
| Config (config.py) | **100%** ✅ | Excellent |
| DB Models (models.py) | **100%** ✅ | Excellent (testés via repository) |
| Schemas (schemas.py) | **96%** ✅ | Excellent |
| Sources : commons.py | **93%** ✅ | Excellent (+10 tests, search, Wikidata, licenses) |
| Sources : base.py | **100%** ✅ | **Excellent** (+5 tests, context manager, lifecycle) |
| Sources : wikipedia.py | **100%** ✅ | **Excellent** (18 tests, tous les chemins couverts) |
| Sources : wikidata.py | **100%** ✅ | **Excellent** (40 tests, réécriture complète) |
| CLI (main.py) | **99%** ✅ | **Excellent** (48 tests, 1 ligne `__main__` restante) |
| GUI : search_view.py | **98%** ✅ | Excellent |
| GUI : views/base.py | **98%** ✅ | **Excellent** (+16 tests, helpers + logging) |
| GUI : 8 modules UI | **0%** | Non testé (app_controller, today_view, history_view, favorites_view, settings_view, stats_view, animal_display, image_carousel) |
| app.py (entry point) | **0%** | Acceptable (128 lignes, entry point) |
| Import/Migration scripts | **0%** | Acceptable (usage unique) |
| debug.py | **0%** | Acceptable (utilitaires debug) |

**Tests créés (Phase 2a) :**
- [x] Tests `attribution.py` : `AttributionInfo`, `DataAttribution`, factory functions, legal notices — **75 tests**
- [x] Tests `repository.py` : `get_by_id()`, `get_by_name()`, `search()`, `get_random()`, `get_animal_of_the_day()` — **30 tests**
- [x] Tests `repository.py` : cache (`_get_cached_*`, `_fetch_and_cache_*`, `_save_cache`) — **49 tests**
- [x] Tests `repository.py` : favoris (`add_favorite`, `remove_favorite`, `is_favorite`, `get_favorites`) — **25 tests**
- [x] Tests `repository.py` : settings (`get_setting`, `set_setting`) — **10 tests**
- [x] Tests `repository.py` : edge cases (FTS5, wrap-around, corrupted entries) — **10 tests**
- [x] Tests `test_history.py` : extensions (deleted taxon, concurrency) — **8 tests**
- [x] Tests `test_repository_parallel.py` : extensions (init, lifecycle) — **7 tests**
- [x] Tests UI : SearchView, AnimalCard, AppState, widgets, Debouncer, BaseView, PaginationBar — **61 tests**

**Fichiers créés :**
- `tests/test_attribution.py` (~1070 lignes)
- `tests/test_repository_advanced.py` (~413 lignes)
- `tests/test_repository_enrichment.py` (~850 lignes)
- `tests/test_repository_favorites.py` (~408 lignes)
- `tests/test_repository_settings.py` (~155 lignes)
- `tests/test_repository_edge_cases.py` (~299 lignes)
- `tests/test_sources_base.py` (5 tests, DataSource base class)
- `tests/test_commons_extended.py` (10 tests, search/Wikidata/licenses)
- `tests/test_cli_extended.py` (14 tests, print_animal enrichi, history edge cases)
- `tests/ui/test_base_view.py` (16 tests, show_loading/error/empty, logging)
- `tests/test_image_cache.py` (14 tests, ImageCacheService complet)

**Fichiers réécrits :**
- `tests/test_wikidata.py` (réécriture complète : 8 → 40 tests)

**Bugs découverts et corrigés durant les tests :**
- FTS5 : Utilisation de `rank` (keyword réservé) → `taxonomic_rank`
- FTS5 : Syntaxe SQL invalide dans GROUP_CONCAT
- Threading : SQLite in-memory non thread-safe → fixture `sync_executor`
- Cache : Colonnes `data_json` → `data`, `source="images"` → `source="commons"`

**Travail restant sur les tests :**
- [x] `sources/wikipedia.py` : **100% complété** (+8 tests, search, fallbacks, full_article)
- [x] `sources/base.py` : **100% complété** (+5 tests, context manager, close, lazy init)
- [x] `sources/commons.py` : **93% complété** (+10 tests, search, Wikidata, parsing licences)
- [x] `sources/wikidata.py` : **100% complété** (réécriture complète, 40 tests couvrant search, SPARQL fallback, _search_taxon_qid, _is_taxon, helpers)
- [x] `main.py` CLI : **99% complété** (+14 tests, print_animal enrichi, history edge cases, empty DB)
- [x] `views/base.py` : **98% complété** (+16 tests, show_loading/error/empty, logging, refresh)
- [ ] Modules UI à 0% (544 lignes) : priorité sur `app_controller.py` et `today_view.py` — **complexe, async**

### Validation mobile precoce

- [ ] Builder un APK "hello world" avec Flet pour valider la compilation Android
- [ ] Identifier les problemes specifiques mobile (performance, permissions) le plus tot possible

### Reference rapide des fichiers a modifier

| Fichier | Problemes | Priorite |
|---------|-----------|----------|
| `db/session.py` | ~~Engine recree a chaque appel~~ | ~~Critique~~ Non critique |
| `db/models.py` | ~~datetime.utcnow() x3~~, ~~index manquant~~ | Corrige |
| `attribution.py` | ~~datetime.utcnow() x3~~, ~~Tests 0%~~ | ~~Corrigé~~ **✅ Complété** |
| `repository.py` | ~~Thread safety~~, ~~print()~~, ~~_save_cache sans rollback~~, ~~Tests 41%~~ | ~~Corrigé~~ **✅ Complété** |
| `app.py` | ~~Extraction vues~~, ~~debouncing~~, ~~duplication x3~~, ~~sync settings~~, ~~resource leak~~ | **✅ Complété** |
| `main.py` | ~~Double parsing history~~, ~~mutation settings~~ | **✅ Complété** |
| `sources/*.py` | ~~HTTP error handling inconsistant (pas de retry 429/503)~~ | **✅ Complété** |

**Durée Phase 2a :**
- **✅ Tests critiques : Complétés** (455 tests, 55% couverture globale, tous les sources 93-100%, main.py 99%, base.py 98%)
- **✅ Extraction vues app.py : Complétée** (app.py réduit de 2190 à 128 lignes)
- **✅ Phase 2a terminée**

---

## Phase 2b : Features essentielles mobile (2-3 semaines)

### Robustesse HTTP (prerequis mobile) ✅
~~Les API clients (`sources/*.py`) ont une gestion d'erreurs inconsistante qui pose probleme sur mobile (connexions instables) :~~
- ~~Wikidata gere gracieusement les erreurs (fallback), Wikipedia et Commons crashent sur 4xx/5xx~~
- ~~Pas de retry sur 429 (rate limit) ou 503 (service unavailable)~~
- ~~Pas de degradation gracieuse quand les APIs sont inaccessibles~~
- [x] Harmoniser la gestion d'erreurs HTTP dans les 3 clients API
- [x] Ajouter retry avec backoff exponentiel (1s, 2s, 4s) pour 429 et 503
- [x] Degradation gracieuse : retourner `None` au lieu de crasher quand API down

**Implementation :** `retry_with_backoff()` dans `sources/base.py` + `_request_with_retry()` dans `DataSource`. 13 appels HTTP harmonises dans les 3 APIs. 17 tests dans `tests/test_http_resilience.py`.

### Distribution DB mobile (prerequis)

Voir "Pipeline de donnees" plus haut pour les tailles.

**Note :** Depuis le refactoring de fevrier 2026, les TSV de distribution incluent deja les noms TAXREF (89K noms FR). Il suffit de les compresser et heberger.

**Etape 1 : Preparer les fichiers de distribution** ✅
- [x] Compresser les TSV existants en `.gz`
- [x] Generer checksums SHA256 et manifest.json
- [x] Heberger sur GitHub Releases

**Implementation :** Script `scripts/prepare_release.py` (voir `docs/DISTRIBUTION_RELEASE.md` pour le processus complet).

Tailles mesurees :
- `animalia_taxa_minimal.tsv.gz` : 4.15 MB (81.8% reduction)
- `animalia_vernacular_minimal.tsv.gz` : 9.21 MB (71.2% reduction)
- **Total telechargement : 13.37 MB** (75.6% reduction vs 54.85 MB non compresse)

**Etape 2 : Premier lancement dans l'app** ✅
- [x] Creer fonction `download_and_setup_db()` avec pipeline complet
- [x] Resolution DB : `resolve_database()` (defaut → `.daynimal_config` → None)
- [x] Ecran de premier lancement (`SetupView`) avec progress bar et gestion d'erreurs
- [x] Integration GUI (`app.py`) : detection DB manquante, affichage SetupView, callback post-setup
- [x] Integration CLI (`main.py`) : commande `setup` + auto-detection DB manquante
- [x] 13 tests unitaires (`tests/test_first_launch.py`)

**Implementation :** Module `daynimal/db/first_launch.py` (resolution DB, telechargement streaming, verification SHA256, decompression gzip, build DB + FTS5, cleanup). Vue `daynimal/ui/views/setup_view.py` (SetupView etendant BaseView). Naming : `daynimal.db` (full/desktop), `daynimal_minimal.db` (premier lancement/mobile).

Tailles de reference :
- APK Flet : ~30-40 MB
- Telechargement premier lancement : ~13.4 MB (TSV.gz avec TAXREF)
- DB SQLite apres import : ~117 MB (apres VACUUM)
- App totale sur appareil : ~150-180 MB (APK + DB + cache)
- Contrainte Google Play : APK < 150 MB (donc DB telechargee separement, obligatoire)

### Cache d'images ✅
- [x] Service `ImageCacheService` (`daynimal/image_cache.py`) : telechargement, stockage local, purge LRU
- [x] Strategie de cache LRU (taille max 500 MB configurable, purge automatique)
- [x] Mode donnees : HD (originales) vs economique (thumbnails uniquement), configurable via `DAYNIMAL_IMAGE_CACHE_HD`
- [x] Integration enrichissement : images telechargees automatiquement lors de `_fetch_and_cache_images()`
- [x] Integration UI : `ImageCarousel` utilise le chemin local si disponible, fallback URL
- [x] Gestion cache dans Settings : affichage taille + bouton "Vider le cache"
- [x] 14 tests unitaires (`tests/test_image_cache.py`)

**Implementation :**
- Modele `ImageCacheModel` dans `db/models.py` (url, local_path, size_bytes, last_accessed_at, is_thumbnail)
- Stockage : `{cache_dir}/{hash[:2]}/{sha256(url)}.ext` (sous-dossiers par prefixe hash)
- Settings : `image_cache_dir`, `image_cache_max_size_mb`, `image_cache_hd` (overridable via env `DAYNIMAL_*`)
- Table creee automatiquement au demarrage (compatible DB existantes)

Chemins par plateforme :
- Desktop : `~/.daynimal/cache/images/`
- Android : `/data/data/com.daynimal/cache/images/`
- iOS : `Library/Caches/images/`

### Mode hors ligne ✅
- [x] Detection de connectivite (`ConnectivityService` dans `daynimal/connectivity.py`)
- [x] UI adaptative : bandeau hors ligne avec bouton "Réessayer" dans `AppController`
- [x] Skip enrichissement API quand hors ligne (retour immediat avec donnees cachees)
- [x] Indicateurs visuels (icone wifi_off + bandeau gris)
- [x] Toggle "Forcer le mode hors ligne" dans Parametres (persiste en DB)
- [x] Detection passive : HEAD request sur wikidata.org, cache TTL 60s, timeout 5s
- [x] Mise a jour automatique du statut apres echec API (`set_offline()`)
- [x] 11 tests unitaires (`tests/test_connectivity.py`)

**Implementation :**
- `ConnectivityService` : HEAD sur wikidata.org, cache 60s, mode force
- `repository.py` : `_enrich()` skip les APIs si hors ligne, `set_offline()` sur erreur reseau
- `ui/state.py` : propriete `is_online` + restauration setting `force_offline` au demarrage
- `ui/app_controller.py` : bandeau hors ligne + bouton Reessayer + mise a jour apres chaque chargement
- `ui/views/settings_view.py` : switch "Forcer le mode hors ligne"

**✅ Phase 2b terminee**

---

## Phase 2c : Features secondaires (2 semaines)

### Pagination UI History/Favoris ✅
- [x] Composant `PaginationBar` reutilisable (`daynimal/ui/components/pagination.py`)
- [x] Integration dans `HistoryView` et `FavoritesView` (`per_page=20`, navigation page precedente/suivante)
- [x] 6 tests unitaires (`tests/ui/test_pagination.py`)

### Notifications desktop ✅
- [x] Service de notifications (`daynimal/notifications.py`) : `NotificationService` avec boucle async periodique
- [x] Notification quotidienne programmee "Decouvrez l'animal du jour !" via plyer (cross-platform)
- [x] Heure personnalisable (dropdown 00:00-23:00 dans Parametres)
- [x] Parametre activation/desactivation (switch dans Parametres)
- [x] Integration `AppController` : start/stop automatique du service
- [x] 13 tests unitaires (`tests/test_notifications.py`)
- [ ] Tests Android (FCM) et iOS (APNs) — Phase 3

### Partage desktop ✅
- [x] Bouton "Copier le texte" : texte formate (nom, description, URL Wikipedia, attribution legale)
- [x] Bouton "Ouvrir Wikipedia" : ouvre l'article dans le navigateur (grise si pas d'article)
- [x] Bouton "Copier l'image" : copie le chemin local de l'image en cache (grise si pas d'image)
- [x] Attribution legale automatique (GBIF CC-BY 4.0, Wikipedia CC-BY-SA 4.0) toujours incluse
- [x] 5 tests unitaires (`tests/test_sharing.py`)
- [ ] Partage mobile (share sheet natif Android/iOS) — Phase 3

**Duree estimee Phase 2c : 1 semaine**

---

## Phase 2d : Monetisation et internationalisation (2 semaines)

A implementer apres validation du produit avec des utilisateurs.

### Monetisation (4 jours)
- [ ] Integration SDK publicites (AdMob ou equivalent)
- [ ] Placement bannieres (non intrusif)
- [ ] Systeme achat in-app (premium unlock)
- [ ] Logique version gratuite vs premium
- [ ] Telechargement DB complete (premium uniquement)
  - [ ] Service de telechargement en background
  - [ ] Progress bar et gestion d'erreurs
  - [ ] Hebergement DB complete (GitHub Releases ou CDN)
- [ ] Tests achats (sandbox)

**Gratuit** : toutes les features de base, DB legere (127k especes), publicites non intrusives
**Premium (~3-5 EUR)** :
- Sans publicites
- Mode hors ligne complet : telechargement DB complete via TSV compresses (~1.7 GB, 4.4M taxa), rebuild FTS5
- Option de pre-telecharger les images (choix utilisateur)

Pattern premium :
```python
if is_premium and settings.offline_mode_enabled:
    if not is_full_db_downloaded():
        show_download_prompt()  # Telecharge DB complete (TSV full)
```

Taches premium specifiques :
- [ ] Heberger TSV full compresses pour mode hors ligne complet
- [ ] Implementer telechargement background de la DB full
- [ ] Systeme de gestion du stockage (verifier espace disponible)

### Internationalisation (2 jours)
- [ ] Configuration Flet i18n (fr + en)
- [ ] Fichiers de traduction (JSON ou .po)
- [ ] Detection langue systeme
- [ ] Selecteur de langue dans parametres
- [ ] Tests dans les deux langues

### Tests et accessibilite (4 jours)
- [ ] Tests unitaires des nouvelles fonctionnalites
- [ ] Tests d'integration
- [ ] Optimisation performances (chargement images, etc.)
- [ ] Correction de bugs
- [ ] Accessibilite : taille de texte ajustable (3 niveaux), contraste eleve, labels semantiques
- [ ] Tests screen readers : TalkBack (Android), VoiceOver (iOS), NVDA (Windows)

**Duree estimee Phase 2d : 2 semaines**

---

**Duree estimee totale Phase 2 : 8-10 semaines**

---

## Phase 3 : Build et deploiement mobile (1 semaine)

### Android (3 jours)
- [ ] Configuration build Android (Flet CLI)
- [ ] Compilation APK
- [ ] Tests emulateur + appareil reel
- [ ] Ajustements UI/UX mobile

### iOS (3 jours, si Mac disponible)
- [ ] Configuration build iOS
- [ ] Compilation IPA
- [ ] Tests simulateur + appareil reel
- [ ] Necessite compte developpeur Apple

### Documentation (1 jour)
- [ ] Guide d'installation et de build
- [ ] Screenshots pour stores

---

## Phase 4 : Features avancees (post-MVP)

A planifier selon feedback utilisateurs.

### Statistiques personnelles
Deplacees depuis Phase 2c — non prioritaires pour le MVP :
- [ ] Nombre total d'animaux consultes
- [ ] Graphiques : repartition par famille, classe, ordre
- [ ] Tendances temporelles (animaux vus par semaine/mois)
- [ ] Animal le plus consulte

### Mode decouverte
Deplace depuis Phase 2c — non prioritaire pour le MVP :
- [ ] "Animal aleatoire" avec categories (mammiferes, oiseaux, reptiles, etc.)
- [ ] "Defi du jour" : decouvrir X animaux
- [ ] Suggestions basees sur l'historique

### Features premium additionnelles
Deplacees ici depuis la Phase 2 — a implementer apres validation du modele freemium :
- **Quiz mode avance** : deviner animal a partir d'image, questions classification/habitat/statut, modes facile/moyen/difficile, score et progression
- **Badges/Achievements** : "Explorateur de mammiferes" (100 vus), "Protecteur" (50 especes en danger), "Taxonomiste" (toutes les classes)
- **Export de donnees** : favoris en PDF, historique en CSV/JSON, rapport personnalise (statistiques + favoris)
- **Statistiques avancees** : graphiques detailles, tendances, comparaisons
- **Collections personnalisees illimitees** : creation, edition, partage

### Favoris avances
- [ ] Recherche et filtrage dans les favoris
- [ ] Statistiques : nombre de favoris par famille, classe, ordre

### Notes personnelles
- [ ] Ajouter des notes textuelles sur des animaux
- [ ] Modifier/supprimer des notes
- [ ] Recherche dans les notes
- [ ] Vue liste des notes
- [ ] Tests unitaires

Table a creer :
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxon_id INTEGER NOT NULL,
    note TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (taxon_id) REFERENCES taxa(taxon_id) ON DELETE CASCADE
);
CREATE INDEX ix_notes_taxon_id ON notes(taxon_id);
```

### Nouvelles features
- **Parcours taxonomique** : arbre hierarchique interactif (Royaume > Phylum > Classe > ...), compteurs par branche
- **Filtres avances** : par statut IUCN, habitat (marin/terrestre/aerien), region geographique, taille/masse, combinaison de filtres
- **Collections thematiques** : pre-definies (animaux en danger, marins, nocturnes...) + personnalisables + partageables
- **Comparaison d'animaux** : comparer 2-3 animaux cote a cote (taille, masse, habitat, statut)
- **Carte geographique** : distribution des especes (si donnees disponibles), exploration par region
- **Mode apprentissage** : flashcards pour memoriser, listes d'etude personnalisees, suivi de progression

---

## Decisions strategiques

| Decision | Choix |
|----------|-------|
| Cloud/sync | Non (tout local pour le MVP) |
| Monetisation | Freemium (gratuit avec pub + premium payant) |
| Langues | Francais + anglais |
| Accessibilite | Support de base (taille texte, contraste, screen readers) |
| DB mobile | DB legere embarquee + enrichissement a la demande |

### Strategie de base de donnees

**Distribution mobile** :
1. Telecharger TSV compresses (~14-16 MB, TAXREF inclus) au premier lancement
2. Creer DB SQLite locale (~117 MB avec FTS5)
3. Enrichissement a la demande (Wikidata, Wikipedia, Commons)
4. Cache local des animaux consultes

**Premium** : option de telecharger la DB complete (~1.7 GB) pour mode 100% hors ligne.

Pattern premier lancement :
```python
if not database_exists():
    show_setup_screen()
    download_tsv_files()       # ~14-16 MB
    decompress_and_import()    # Creer DB locale (~117 MB)
    create_fts_index()
```

### Alternatives a Flet considerees

Si Flet pose probleme a l'avenir :
- **Kivy** : Tres mature, excellent support mobile, UI moins moderne
- **BeeWare (Toga)** : UI vraiment native, moins mature
- **Web app (FastAPI + React)** : Tres flexible, necessite JavaScript

---

## Roadmap post-MVP

**Court terme** (apres lancement) :
- Analyser metriques utilisateurs (taux de conversion, retention)
- Iterer sur UI/UX selon feedback
- Corriger bugs critiques

**Moyen terme** (3-6 mois) :
- Collections thematiques
- Quiz mode avance
- Traduction descriptions (API auto-traduction)
- Langues additionnelles (es, de, pt)

**Long terme** (6-12 mois) :
- Synchronisation cloud (si demande)
- Parcours taxonomique interactif
- Mode apprentissage / flashcards
- Partenariats conservation (dons, sensibilisation)

---

## Ressources Flet

- Site officiel : https://flet.dev
- GitHub : https://github.com/flet-dev/flet
- Exemples : https://github.com/flet-dev/examples
- Build mobile : https://flet.dev/docs/guides/python/mobile
- Outils : Flet CLI (compilation), Flutter DevTools (debug UI), Android Studio (emulateur), Xcode (iOS, Mac uniquement)

---

*Statut : Phase 1 completee - Phase 2a (stabilisation) completee - Phase 2b (features mobile) completee - Phase 2c (features secondaires) en cours*
