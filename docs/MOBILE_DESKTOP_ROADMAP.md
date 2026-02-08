# Roadmap : Application Mobile/Desktop

**Derniere mise a jour** : 2026-02-08

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

Tables dans les deux DB : `taxa`, `vernacular_names`, `enrichment_cache`, `animal_history`, `favorites`, `user_settings`, `taxa_fts` (FTS5).

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

**Progression : Phases 1-3 completees, app.py reduit de 2190 a 1949 lignes (-241)**

Architecture modulaire creee dans `daynimal/ui/` :
- `state.py` (AppState), `views/base.py` (BaseView), `components/widgets.py` (Loading, Error, EmptyState)
- `components/animal_card.py` (AnimalCard reutilisable), `views/search_view.py` (SearchView)
- `utils/debounce.py` (Debouncer 300ms, conserve mais non utilise dans SearchView)
- 37 tests UI dans `tests/ui/` (100%)

**Fait :**
- [x] Infrastructure UI : AppState, BaseView, widgets reutilisables (Phase 1)
- [x] SearchView extraite avec AnimalCard reutilisable (Phase 2)
- [x] Corrections : race conditions, type annotations, thread safety AppState, protection page.update() (Phase 3)
- [x] Recherche classique Enter/Button au lieu du debouncing automatique (Phase 3)
- [x] Fuite de ressources Repository resolue (AppState.close_repository)

**Reste a faire :**
- [ ] Extraire `_load_and_display_animal()` — unifier 3 methodes dupliquees (~240 lignes)
- [ ] Extraire HistoryView et FavoritesView (~300 lignes)
- [ ] Extraire SettingsView (~150 lignes)
- [ ] Extraire StatsView (~120 lignes)
- [ ] Extraire TodayView + ImageCarousel + AnimalDisplay (~500 lignes)
- [ ] Creer AppController, reduire app.py a ~50 lignes entry point (~600 lignes)

**Corrections ciblees restantes :**
- [ ] **Settings synchrone** — `app.py` (lignes 2100-2103)
  - `self.repository.get_stats()` bloque le thread UI
  - Fix : utiliser `asyncio.to_thread()` comme les autres vues

### Corrections mineures

- [ ] **CLI History double parsing** — `main.py` (lignes 194-286, 334-381)
  - Argparse parse `--page` en int, reconvertit en string, puis `cmd_history()` re-parse en int
  - Fix : passer `args.page` et `args.per_page` directement a `cmd_history()`
- [ ] **Mutation globale settings** — `main.py` (lignes 353-354)
  - `--db` flag mute `settings.database_url` globalement, peut polluer les tests
  - Fix : passer database_url explicitement au repository

### Tests manquants

Couverture actuelle : **~27%**

| Composant | Couverture | Verdict |
|-----------|-----------|---------|
| APIs externes (wikidata, wikipedia, commons) | **92%** | Excellent |
| Schemas (schemas.py) | **88%** | Bon |
| CLI (main.py) | **80%** | Bon |
| Repository (repository.py) | **41%** | Insuffisant |
| GUI (app.py + ui/) | **37 tests UI** | En cours (SearchView, AnimalCard, widgets testes) |
| Attribution (attribution.py) | **0%** | Risque legal |
| DB Models (models.py) | **0%** | A risque |
| Import/Migration scripts | **0%** | Acceptable (usage unique) |

Effort estime pour atteindre 70% : 2-3 jours

Tests a ecrire en priorite :
- [ ] Tests `repository.py` : `get_by_id()`, `get_by_name()`, `search()`, `get_random()`, `get_animal_of_the_day()`
- [ ] Tests `repository.py` : favoris (`add_favorite`, `remove_favorite`, `is_favorite`, `get_favorites`)
- [ ] Tests `repository.py` : settings (`get_setting`, `set_setting`)
- [ ] Tests `repository.py` : cache (`_get_cached_*`, `_fetch_and_cache_*`, `_save_cache`)
- [ ] Tests `attribution.py` : `AttributionInfo`, `DataAttribution`, factory functions, legal notices

### Validation mobile precoce

- [ ] Builder un APK "hello world" avec Flet pour valider la compilation Android
- [ ] Identifier les problemes specifiques mobile (performance, permissions) le plus tot possible

### Reference rapide des fichiers a modifier

| Fichier | Problemes | Priorite |
|---------|-----------|----------|
| `db/session.py` | ~~Engine recree a chaque appel~~ | ~~Critique~~ Non critique |
| `db/models.py` | ~~datetime.utcnow() x3~~, ~~index manquant~~ | Corrige |
| `attribution.py` | ~~datetime.utcnow() x3~~ | Corrige |
| `repository.py` | ~~Thread safety~~, ~~print()~~, ~~_save_cache sans rollback~~ | Corrige |
| `app.py` | **Extraction vues** (Search fait, 5 restantes), ~~debouncing~~, duplication x3, sync settings, ~~resource leak~~ | **Critique** |
| `main.py` | Double parsing history, mutation settings | Mineur |
| `sources/*.py` | HTTP error handling inconsistant (pas de retry 429/503) | Mineur |

**Duree estimee Phase 2a : 2-3 semaines**

---

## Phase 2b : Features essentielles mobile (2-3 semaines)

### Robustesse HTTP (prerequis mobile)
Les API clients (`sources/*.py`) ont une gestion d'erreurs inconsistante qui pose probleme sur mobile (connexions instables) :
- Wikidata gere gracieusement les erreurs (fallback), Wikipedia et Commons crashent sur 4xx/5xx
- Pas de retry sur 429 (rate limit) ou 503 (service unavailable)
- Pas de degradation gracieuse quand les APIs sont inaccessibles
- [ ] Harmoniser la gestion d'erreurs HTTP dans les 3 clients API
- [ ] Ajouter retry avec backoff exponentiel (1s, 2s, 4s) pour 429 et 503
- [ ] Degradation gracieuse : retourner `None` au lieu de crasher quand API down

### Distribution DB mobile (prerequis)

Voir "Pipeline de donnees" plus haut pour les tailles.

**Note :** Depuis le refactoring de fevrier 2026, les TSV de distribution incluent deja les noms TAXREF (89K noms FR). Il suffit de les compresser et heberger.

**Etape 1 : Preparer les fichiers de distribution**
- [ ] Compresser les TSV existants en `.gz`
- [ ] Heberger sur GitHub Releases ou CDN

Commande pour regenerer les TSV (si necessaire) :
```bash
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
gzip data/animalia_taxa_minimal.tsv
gzip data/animalia_vernacular_minimal.tsv
```

**Etape 2 : Premier lancement dans l'app mobile**
- [ ] Creer fonction `download_and_setup_db()` :
  1. Verifier espace disponible (~150 MB necessaires)
  2. Telecharger TSV.gz (~14-16 MB)
  3. Decompresser (~56 MB temporaires)
  4. Importer dans SQLite (creer `daynimal.db` ~117 MB)
  5. Construire index FTS5
  6. Supprimer les TSV decompresses
- [ ] Creer ecran de premier lancement avec progress bar
- [ ] Gerer les erreurs : espace insuffisant, echec telechargement, reprise

Tailles de reference :
- APK Flet : ~30-40 MB
- Telechargement premier lancement : ~14-16 MB (TSV.gz avec TAXREF)
- DB SQLite apres import : ~117 MB (apres VACUUM)
- App totale sur appareil : ~150-180 MB (APK + DB + cache)
- Contrainte Google Play : APK < 150 MB (donc DB telechargee separement, obligatoire)

### Cache d'images (4 jours)
- [ ] Service `ImageCache` (telechargement, stockage local)
- [ ] Strategie de cache (LRU, taille max 500 MB configurable, purge)
- [ ] Indicateur de telechargement
- [ ] Mode donnees : haute qualite vs economique
- [ ] Tests

Chemins par plateforme :
- Desktop : `~/.daynimal/cache/images/`
- Android : `/data/data/com.daynimal/cache/images/`
- iOS : `Library/Caches/images/`

Table a creer :
```sql
CREATE TABLE image_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    local_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    downloaded_at DATETIME NOT NULL
);
CREATE INDEX ix_image_cache_url ON image_cache(url);
```

### Mode hors ligne (3 jours)
- [ ] Detection de connectivite
- [ ] UI adaptative (afficher message si pas d'internet)
- [ ] Indication claire des donnees necessitant internet vs disponibles localement
- [ ] Indicateurs visuels (icone online/offline)
- [ ] Queue de synchronisation pour actions hors ligne

Pattern d'implementation :
```python
if is_online():
    animal = repo.get_by_id(taxon_id, enrich=True)
else:
    animal = repo.get_by_id(taxon_id, enrich=False)
    show_message("Mode hors ligne - donnees limitees")
```

### Notes personnelles (3 jours)
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

**Duree estimee Phase 2b : 2-3 semaines**

---

## Phase 2c : Features secondaires (2 semaines)

### Pagination UI History/Favoris (1 jour)
Actuellement hardcode `per_page=50` sans controles de navigation (`app.py` lignes 881, 1078).
Le backend supporte la pagination mais l'UI ne l'expose pas.
- [ ] Ajouter boutons "Page precedente / suivante" ou "Charger plus"
- [ ] Afficher le nombre total d'entrees

### Favoris avances (2 jours)
Les favoris basiques (ajout/suppression/liste) sont implementes en Phase 1.
Reste a ajouter :
- [ ] Recherche et filtrage dans les favoris
- [ ] Statistiques : nombre de favoris par famille, classe, ordre

### Notifications (3 jours)
- [ ] Service de notifications
- [ ] Notification quotidienne programmee "Decouvrez l'animal du jour !"
- [ ] Heure personnalisable
- [ ] Parametre activation/desactivation
- [ ] Tests Android (FCM) et iOS (APNs)

### Partage (2 jours)
- [ ] Fonction de partage natif (texte + image)
- [ ] Formats : texte seul, image, lien web
- [ ] Formatage du texte partage (+ attributions legales automatiques)
- [ ] Tests

### Statistiques personnelles (2 jours)
- [ ] Nombre total d'animaux consultes
- [ ] Graphiques : repartition par famille, classe, ordre
- [ ] Tendances temporelles (animaux vus par semaine/mois)
- [ ] Animal le plus consulte

### Mode decouverte (2 jours)
- [ ] "Animal aleatoire" avec categories (mammiferes, oiseaux, reptiles, etc.)
- [ ] "Defi du jour" : decouvrir X animaux
- [ ] Suggestions basees sur l'historique

### Optimisations performances (2 jours)
- [ ] Pagination lazy (charger 20 animaux a la fois)
- [ ] Images : thumbnails vs full resolution
- [ ] Index SQLite sur colonnes frequemment filtrees
- [ ] Cache en memoire pour vues recentes

**Duree estimee Phase 2c : 2 semaines**

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

### Features premium additionnelles
Deplacees ici depuis la Phase 2 — a implementer apres validation du modele freemium :
- **Quiz mode avance** : deviner animal a partir d'image, questions classification/habitat/statut, modes facile/moyen/difficile, score et progression
- **Badges/Achievements** : "Explorateur de mammiferes" (100 vus), "Protecteur" (50 especes en danger), "Taxonomiste" (toutes les classes)
- **Export de donnees** : favoris en PDF, historique en CSV/JSON, rapport personnalise (statistiques + favoris)
- **Statistiques avancees** : graphiques detailles, tendances, comparaisons
- **Collections personnalisees illimitees** : creation, edition, partage

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

*Statut : Phase 1 completee - Phase 2a (stabilisation) en cours*
