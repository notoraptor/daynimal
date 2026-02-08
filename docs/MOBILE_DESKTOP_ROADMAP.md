# Roadmap : Application Mobile/Desktop

**Derniere mise a jour** : 2026-02-07

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
- Base de donnees minimale : 127k especes, 153 MB apres VACUUM
- Fichiers TSV compresses : 93 MB (pour distribution mobile)
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
| **Pipeline** | 1. Extraire Animalia (tous rangs)<br>2. Importer tout | 1. Extraire Animalia (rank='species' seulement)<br>2. Importer<br>3. **Supprimer especes sans noms** |
| **Taxa resultants** | 4.4M (hierarchie complete) | 127K (especes avec noms uniquement) |
| **Noms vernaculaires** | 1.16M (tous rangs) | 1.07M (especes seulement) |
| **Taille finale** | 1.8 GB | 153 MB |

**Exemple concret** :
- Mode full : inclut `Felidae` (famille → "Cats", "Felins"), `Panthera` (genre → "Big cats"), `Panthera leo` (espece → "Lion")
- Mode minimal : inclut **seulement** `Panthera leo` (espece avec noms vernaculaires)

**Note** : VACUUM est applique automatiquement aux deux modes en fin d'import.

### Fichiers presents sur le disque (fevrier 2026)

**Données brutes** (`data/`, gitignore) :

| Fichier | Taille | Lignes |
|---------|--------|--------|
| `backbone.zip` | 927 MB | - |
| `TAXREF_v18_2025.zip` | 58 MB | - |
| `animalia_taxa.tsv` | 598 MB | 4 432 185 |
| `animalia_vernacular.tsv` | 32 MB | 1 112 887 |
| `animalia_taxa_minimal.tsv` | 439 MB | 3 053 779 |
| `animalia_vernacular_minimal.tsv` | 31 MB | 1 072 723 |

**Bases de données** (racine, gitignore) :

| Fichier | Taille | Taxa | Vernaculaires | Noms FR |
|---------|--------|------|---------------|---------|
| `daynimal.db` (full) | 1.8 GB | 4 432 185 | 1 162 173 | 93 777 |
| `daynimal_minimal.db` | 153 MB | 127 762 | 1 072 723 | 43 606 |

Tables dans les deux DB : `taxa`, `vernacular_names`, `enrichment_cache`, `animal_history`, `taxa_fts` (FTS5).
Tables supplementaires dans la full DB : `favorites`, `user_settings`.

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
- Telechargement : 985 MB (backbone.zip 927 MB + TAXREF 58 MB)
- Fichiers intermediaires TSV : ~630 MB (full) ou ~470 MB (minimal), supprimables apres import
- DB finale : **1.8 GB** (full) ou **153 MB** (minimal)

### Distribution mobile

L'app mobile ne peut pas telecharger `backbone.zip` (927 MB) ni executer le pipeline complet.
Il faut heberger des fichiers pre-filtres (TSV compresses) que l'app telecharge au premier lancement.

Fichiers a heberger (GitHub Releases ou CDN) :

| Fichier | Taille (non compresse) | Taille (gzip, estimee) |
|---------|----------------------|----------------------|
| `animalia_taxa_minimal.tsv.gz` | 439 MB | ~80-85 MB |
| `animalia_vernacular_minimal.tsv.gz` | 31 MB | ~8-10 MB |
| **Total** | **470 MB** | **~93 MB** |

Pipeline au premier lancement de l'app mobile :
```
Telecharge TSV.gz (~93-110 MB)
  -> Decompresse (~470 MB temporaires)
    -> Importe dans SQLite (~153 MB)
      -> Construit index FTS5
        -> Supprime les TSV decompresses
          -> Pret (~200 MB total sur appareil : APK + DB + cache)
```

Contrainte Google Play : APK < 150 MB, donc la DB doit etre telechargee separement (obligatoire).

### Resume des tailles

| Scenario | Fichiers | Taille |
|----------|----------|--------|
| Desktop : telechargement brut | backbone.zip + TAXREF | **985 MB** |
| Desktop : DB finale (full) | daynimal.db + FTS5 | **1.8 GB** |
| Desktop : DB finale (minimal) | daynimal_minimal.db + FTS5 | **153 MB** |
| Mobile : telechargement (sans TAXREF) | 2 TSV.gz | **~93 MB** |
| Mobile : telechargement (avec TAXREF) | 2 TSV.gz + export TAXREF | **~100-110 MB** |
| Mobile : DB sur appareil | SQLite + FTS5 | **~153 MB** |
| Mobile : espace total | APK + DB + cache images | **~200 MB** |

---

## Phase 2a : Stabilisation (1 semaine)

Corriger la dette technique avant d'ajouter des features mobiles.
Un bug de thread safety en desktop est genant ; sur mobile avec contraintes memoire, c'est un crash.

Revue de code : fevrier 2026 (verdict code 6.5/10)

### Bugs critiques

- [x] `datetime.utcnow()` → `datetime.now(UTC)` (6 occurrences dans `models.py` et `attribution.py`)
- [x] `print()` → `logger.warning()` dans `repository.py` (lignes 599, 612, 635)
- [ ] **Engine SQLAlchemy recree a chaque session** — `db/session.py` (lignes 7-16)
  - `get_session()` cree un nouveau engine a chaque appel au lieu d'un singleton
  - Impact : fuite de ressources (connection pools), degradation de performance
  - Fix : variable globale `_engine` avec lazy init, ou `@lru_cache` sur `get_engine()`
- [ ] **Index manquant sur `is_synonym`** — `db/models.py` (ligne 46)
  - Colonne frequemment filtree (3M+ lignes) sans index = full table scan
  - Fix : ajouter `index=True` sur la colonne (`is_synonym: Mapped[bool] = mapped_column(Boolean, default=False, index=True)`)
- [ ] **Thread safety dans `_enrich()`** — `repository.py` (lignes 483-659)
  - Workers du `ThreadPoolExecutor` partagent la meme session SQLAlchemy (non thread-safe)
  - `_save_cache()` fait commit sans try/except ni rollback
  - Impact : race conditions, corruption potentielle de donnees
  - Fix option A (recommande) : creer nouvelle session par thread dans `_fetch_and_cache_*()`
  - Fix option B : utiliser `threading.Lock()` autour de `_save_cache()`

### Refactoring app.py (2200 lignes, monolithe)

- [ ] **Debouncing recherche** — `app.py` (lignes 1388-1467)
  - `on_search_change` declenche une requete DB a chaque frappe clavier
  - "guepard" = 7 requetes, race conditions, flickering des resultats
  - Fix : attendre 300ms apres derniere frappe avant de chercher
- [ ] **Extraire `_load_and_display_animal()`** — `app.py` (~200 lignes dupliquees)
  - 3 methodes quasi-identiques (95% identiques) :
    - `load_animal_from_history` (lignes 225-296, 72 lignes)
    - `load_animal_from_favorite` (lignes 1214-1300, 87 lignes)
    - `load_animal_from_search` (lignes 1643-1732, 90 lignes)
  - Deja divergence : `load_animal_from_search` ajoute a l'historique, les autres non
  - Fix : extraire methode unique `_load_and_display_animal(taxon_id, source)`
- [ ] **Settings synchrone** — `app.py` (lignes 2100-2103)
  - `self.repository.get_stats()` bloque le thread UI
  - Fix : utiliser `asyncio.to_thread()` comme les autres vues
- [ ] **Fuite de ressources Repository** — `app.py` (lignes 38-42, 468-469)
  - Repository cree on-demand, fermeture depend des handlers cleanup (on_disconnect, on_close)
  - Si force quit ou crash, connexions HTTP et DB restent ouvertes
  - Fix : initialiser repository dans `__init__`, fermer dans `__del__` ou context manager

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
| GUI (app.py) | **0%** | Critique |
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
| `db/session.py` | Engine recree a chaque appel | Critique |
| `db/models.py` | ~~datetime.utcnow() x3~~, index manquant | Critique |
| `attribution.py` | ~~datetime.utcnow() x3~~ | Corrige |
| `repository.py` | Thread safety, ~~print()~~, _save_cache sans rollback | Critique |
| `app.py` | Debouncing, duplication x3, pagination, sync settings, resource leak | Important |
| `main.py` | Double parsing history, mutation settings | Mineur |
| `sources/*.py` | HTTP error handling inconsistant (pas de retry 429/503) | Mineur |

**Duree estimee Phase 2a : 1 semaine**

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

Voir "Pipeline de donnees" plus haut pour les tailles et le probleme TAXREF.

**Etape 1 : Preparer les fichiers de distribution**
- [ ] Decider : inclure les noms TAXREF dans la distribution mobile ou non
  - Si oui : creer un script d'export des vernacular depuis la DB enrichie (apres import TAXREF)
  - Les TSV actuels ne contiennent que les noms GBIF (43K FR au lieu de 93K)
- [ ] Regenerer les TSV si necessaire
- [ ] Compresser en `.gz` (`gzip animalia_taxa_minimal.tsv`, etc.)
- [ ] Heberger sur GitHub Releases ou CDN
  - `animalia_taxa_minimal.tsv.gz` (~93 MB total compresse, avec ou sans TAXREF)

Commande pour regenerer les TSV :
```bash
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
```

**Etape 2 : Premier lancement dans l'app mobile**
- [ ] Creer fonction `download_and_setup_db()` :
  1. Verifier espace disponible (~200 MB necessaires)
  2. Telecharger TSV.gz (~93-110 MB)
  3. Decompresser (~470 MB temporaires)
  4. Importer dans SQLite (creer `daynimal.db` ~153 MB)
  5. Construire index FTS5
  6. Supprimer les TSV decompresses
- [ ] Creer ecran de premier lancement avec progress bar
- [ ] Gerer les erreurs : espace insuffisant, echec telechargement, reprise

Tailles de reference :
- APK Flet : ~30-40 MB
- Telechargement premier lancement : ~93-110 MB
- DB SQLite apres import : ~153 MB (vernacular 47%, FTS5 27%, taxa 26%)
- App totale sur appareil : ~200 MB (APK + DB + cache)
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

**Duree estimee totale Phase 2 : 7-8 semaines**

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

### Refactoring architecture app.py
Actuellement un monolithe de 2200 lignes (classe unique gerant 6 vues, tout le state, toutes les interactions API).
Tester les vues individuellement est impossible.
- [ ] Extraire chaque vue dans sa propre classe/fichier
- [ ] Creer un systeme de composants reutilisables (affichage animal, loading, erreurs)
- [ ] Ajouter des tests GUI (necessite framework de test Flet)

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
1. Telecharger TSV compresses (~93 MB) au premier lancement
2. Creer DB SQLite locale (~153 MB avec FTS5)
3. Enrichissement a la demande (Wikidata, Wikipedia, Commons)
4. Cache local des animaux consultes

**Premium** : option de telecharger la DB complete (~1.7 GB) pour mode 100% hors ligne.

Pattern premier lancement :
```python
if not database_exists():
    show_setup_screen()
    download_tsv_files()       # ~93 MB
    decompress_and_import()    # Creer DB locale
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
