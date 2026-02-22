# Roadmap : Application Mobile/Desktop

**Derniere mise a jour** : 2026-02-22 11:17

---

## Etat actuel

Application Flet desktop fonctionnelle avec 6 onglets (Decouverte, Historique, Favoris, Recherche, Statistiques, Parametres). Architecture modulaire, infrastructure mobile prete (cache images, mode hors ligne, distribution TSV). Chemins mobile-aware (`get_app_data_dir()`, `get_app_temp_dir()`), detection mobile via `is_mobile()`. Build mobile valide sur emulateur Android (premier lancement + telechargement DB OK). Setup CLI etendu (`daynimal setup --mode full|minimal --no-taxref`). Desktop sans DB : ecran informatif avec commandes CLI (setup auto reserve au mobile). Navbar fixe en bas (scroll deplace vers le contenu). Chargement paresseux des images (1 seule image au chargement, galerie a la demande). Silhouettes PhyloPic locales en fallback. Recherche FTS5 amelioree (pertinence, classement). Logging simplifie via `logging` standard Python (suppression du systeme debug custom). Notifications periodiques via `desktop-notifier` (date de depart, periode configurable, callback au clic). Chargement auto d'un animal au demarrage (configurable).

**Prochaine etape** : tests appareil reel et ajustements UI mobile (Phase 3).

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

### Differences de filtrage entre modes

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

**Note** : VACUUM est applique automatiquement aux deux modes en fin d'import. `generate-distribution` fusionne les noms TAXREF directement dans les fichiers de distribution via le flag `--taxref`.

### Distribution desktop

**Methode rapide** (automatise tout) :
```bash
# Setup complet (telecharge GBIF + TAXREF, genere distribution, build DB + FTS5)
uv run daynimal setup --mode full

# Ou sans TAXREF (noms francais limites a GBIF)
uv run daynimal setup --mode full --no-taxref

# Ou DB minimale pre-construite (~13 MB download)
uv run daynimal setup --mode minimal
```

**Methode manuelle** (etape par etape) :
```bash
# 1. Generer les fichiers de distribution (auto-download de backbone.zip si absent)
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt

# 2. Construire la DB SQLite
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv

# 3. Construire l'index de recherche FTS5
uv run init-fts

```

### Distribution mobile

L'app mobile telecharge des TSV pre-compresses au premier lancement :

| Fichier | Taille brute | Taille gzip |
|---------|-------------|-------------|
| `animalia_taxa_minimal.tsv.gz` | 23 MB | 4.15 MB |
| `animalia_vernacular_minimal.tsv.gz` | 33 MB | 9.21 MB |
| **Total** | **56 MB** | **13.37 MB** |

Pipeline premier lancement : telecharge TSV.gz (13 MB) → decompresse → importe SQLite (117 MB) → FTS5 → cleanup.

Contrainte Google Play : APK < 150 MB, donc DB telechargee separement.

### Resume des tailles

| Scenario | Taille |
|----------|--------|
| Desktop DB (full) | 1.08 GB |
| Desktop DB (minimal) | 117 MB |
| Mobile : telechargement initial | 13.37 MB |
| Mobile : DB sur appareil | 117 MB |
| Mobile : espace total (APK + DB + cache) | ~150-180 MB |

Tables : `taxa`, `vernacular_names`, `enrichment_cache`, `animal_history`, `favorites`, `user_settings`, `image_cache`, `taxa_fts` (FTS5).

---

## Phases completees

### Phase 1 : Application desktop (completee 2026-02-07)

App Flet avec 6 onglets : Decouverte (animal aleatoire, image unique + galerie a la demande), Historique (paginee), Favoris, Recherche (FTS5), Statistiques, Parametres (theme clair/sombre, credits). DB minimale 163K especes, chargement async.

### Phase 2a : Stabilisation et refactoring (completee fev 2026)

- **Bugs critiques corriges** : `datetime.utcnow()` → `datetime.now(UTC)`, `print()` → logger, index `is_synonym`, thread safety `_enrich()`
- **Refactoring** : `app.py` reduit de 2190 a 128 lignes (-94%). Architecture modulaire dans `daynimal/ui/` : AppState, BaseView, 6 vues, 5 composants, AppController
- **Tests** : 50 → 949 tests (94% couverture). Modules critiques a 93-100% : attribution, repository, schemas, sources, CLI. Modules UI a 88-100%.
- **Corrections mineures** : CLI history double parsing, mutation globale settings
- **Nettoyage debug** : suppression du systeme `FletDebugger` custom au profit du `logging` standard Python. Suppression du dossier `debug/` et de `daynimal/debug.py`.

### Phase 2b : Features essentielles mobile (completee fev 2026)

- **Robustesse HTTP** : `retry_with_backoff()` dans `sources/base.py`, backoff exponentiel 429/503, degradation gracieuse. 17 tests.
- **Distribution mobile** : script `prepare_release.py`, TSV.gz heberges sur GitHub Releases, checksums SHA256.
- **Premier lancement** : module `first_launch.py` (resolution DB, telechargement streaming, verification SHA256, build DB + FTS5). `SetupView` dans GUI, commande `setup` en CLI. 13 tests.
- **Cache d'images** : `ImageCacheService` avec LRU (500 MB configurable), mode HD/thumbnails, integration UI et Settings. 22 tests.
- **Mode hors ligne** : `ConnectivityService` (HEAD wikidata.org, cache 60s), bandeau UI, skip enrichissement, toggle "Forcer hors ligne" dans Parametres. 11 tests.

### Phase 2c : Features secondaires (completee fev 2026)

- **Pagination** : composant `PaginationBar` reutilisable, integre dans HistoryView et FavoritesView (per_page=20). 6 tests.
- **Notifications desktop** : `NotificationService` via `desktop-notifier`, notifications periodiques configurables (date de depart, periode, callback au clic). Tests unitaires.
- **Partage desktop** : copier texte formate, ouvrir Wikipedia, copier chemin image locale. Attribution legale automatique. 5 tests.

### Phase 2d : Polissage UI et performances (completee fev 2026)

- **Chargement paresseux des images** : seule la premiere image est telechargee a l'enrichissement. Bouton "Plus d'images" ouvre un `ImageGalleryDialog` avec progress bar puis carousel. `cache_single_image()`, `cache_images_with_progress()`, `are_all_cached()` dans `ImageCacheService`. 8 tests ajoutes.
- **Silhouettes PhyloPic locales** : CSV local pour fallback quand aucune image Commons/Wikidata. Evite les appels API PhyloPic.
- **Classement des images** : `rank_images()` dans `sources/commons.py` priorise P18 Wikidata, puis par qualite/pertinence.
- **Recherche amelioree** : meilleure pertinence FTS5, classement des resultats.
- **Fix fermeture app** : arret propre du repository et des connexions HTTP.
- **UI factorisee** : composant `view_header()` partage, `AnimalDisplay` pour les cartes d'animaux (historique, favoris, recherche).

---

## Phase 3 : Validation et build mobile

Objectif : valider que Flet compile sur mobile et deployer l'app.

### Workflow de test Android

```bash
# Define tool paths (required — $ANDROID_HOME is NOT set on this machine)
ADB="$HOME/Android/Sdk/platform-tools/adb"
EMULATOR="$HOME/Android/Sdk/emulator/emulator"

# Build APK (3 architectures: arm64-v8a, armeabi-v7a, x86_64)
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run flet build apk --no-rich-output

# Lancer l'emulateur (AVD "daynimal_test", Pixel 6, API 35)
"$EMULATOR" -avd daynimal_test -no-audio &

# Installer et lancer l'app
"$ADB" wait-for-device
"$ADB" install -r build/apk/app-x86_64-release.apk
"$ADB" shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1

# Verifier l'UI (screenshot) et les logs
"$ADB" exec-out screencap -p > tmp/screenshot.png
"$ADB" logcat -d | grep -i "flutter\|python\|error" | grep -v "audit\|InetDiag"

# Redemarrer l'app
"$ADB" shell am force-stop com.daynimal.daynimal
```

**Note** : BlueStacks est incompatible avec Flet (ecran blanc). Utiliser l'emulateur Android Studio (AVD `daynimal_test`).
Voir `CLAUDE.md` pour les chemins ADB exacts et les instructions detaillees.

### Etape 1 : Adaptations pre-build

- [x] Remplacer `webbrowser.open()` par `page.launch_url()` (today_view.py)
- [x] Creer `get_app_data_dir()` / `get_app_temp_dir()` mobile-aware dans config.py (utilise `FLET_APP_STORAGE_DATA` / `FLET_APP_STORAGE_TEMP`)
- [x] Corriger chemins hardcodes dans first_launch.py (tmp/, db filename) et debug.py (logs/)
- [x] Ajouter detection de plateforme pour features desktop-only (desktop-notifier)
- [x] Ajouter `is_mobile()` dans config.py (detection via `FLET_APP_STORAGE_DATA`)
- [x] Desktop sans DB : ecran informatif avec commandes CLI au lieu du setup auto (reserve au mobile)
- [x] Etendre `daynimal setup` avec `--mode full|minimal` et `--no-taxref` (telechargement TAXREF inclus)
- [x] Configuration Android dans pyproject.toml (`[tool.flet]`, permissions, split_per_abi)
- [x] Fix imports absolus pour Android (`sys.modules` hack dans app.py)
- [x] Migrer widgets deprecated (`ElevatedButton`/`TextButton` → `Button`, `ft.alignment.center` → `ft.Alignment`)

### Etape 2 : Build et test Android

- [x] Compilation APK avec Flet CLI (`flet build apk`) — 3 architectures (arm64, armv7, x86_64)
- [x] Tests emulateur Android (AVD via Android Studio emulator) — ecran premier lancement OK
- [x] Tester telechargement DB depuis ecran premier lancement — OK (fix parsing manifest dict)
- [x] Tester navigation complete apres installation DB — ecran principal avec 6 onglets OK
- [x] UX onboarding premier lancement : accueil + "Commencer" → progression ("Preparation des donnees sur les animaux...") avec barre reelle (poids : download ~70%, build ~30%) → "Tout est pret !" (2s) → transition auto vers decouverte
- [x] Fix scroll : navbar fixe en bas, scroll deplace vers le content_container
- [ ] Ajustements UI/UX mobile (tailles, touch targets, navigation) — tests sur emulateur + desktop

**Note** : BlueStacks est incompatible avec Flet (ecran blanc). Utiliser l'emulateur Android Studio (AVD `daynimal_test`). Voir CLAUDE.md pour les commandes ADB.

### Etape 3 : Adaptations mobile

- [ ] Partage mobile (share sheet natif Android/iOS) — remplace les boutons desktop
- [ ] Notifications mobiles (FCM Android, APNs iOS) — remplace desktop-notifier

### Etape 4 : Build iOS (si Mac disponible)

- [ ] Configuration build iOS
- [ ] Compilation IPA
- [ ] Tests simulateur

### Etape 5 : Documentation et stores

- [x] Guide d'installation et de build (`docs/ANDROID_DEV_GUIDE.md`)
- [ ] Screenshots pour stores

### Etape 6 : Tests appareils reels

- [ ] Tests appareil reel Android
- [ ] Tests appareil reel iOS (si disponible)
- [ ] Corrections finales avant publication

---

## Phase 4 : Internationalisation et accessibilite

### Internationalisation

- [ ] Configuration Flet i18n (fr + en)
- [ ] Fichiers de traduction (JSON ou .po)
- [ ] Detection langue systeme
- [ ] Selecteur de langue dans parametres
- [ ] Tests dans les deux langues

### Accessibilite

- [ ] Taille de texte ajustable (3 niveaux)
- [ ] Contraste eleve
- [ ] Labels semantiques
- [ ] Tests screen readers : TalkBack (Android), VoiceOver (iOS), NVDA (Windows)

---

## Phase 5 : Monetisation (post-lancement)

A implementer apres validation du produit avec des utilisateurs reels.

### Publicite et achats

- [ ] Integration SDK publicites (AdMob ou equivalent)
- [ ] Placement bannieres (non intrusif)
- [ ] Systeme achat in-app (premium unlock)
- [ ] Logique version gratuite vs premium
- [ ] Tests achats (sandbox)

### Premium (~3-5 EUR)

Offre premium : sans publicites, DB complete, pre-telechargement images.

- [ ] Telechargement DB complete (premium uniquement)
  - [ ] Service de telechargement en background
  - [ ] Progress bar et gestion d'erreurs
  - [ ] Hebergement DB complete (GitHub Releases ou CDN)
- [ ] Heberger TSV full compresses pour mode hors ligne complet
- [ ] Implementer telechargement background de la DB full
- [ ] Systeme de gestion du stockage (verifier espace disponible)

---

## Phase 6 : Features avancees (post-MVP)

A planifier selon feedback utilisateurs.

### Statistiques personnelles

- [ ] Nombre total d'animaux consultes
- [ ] Graphiques : repartition par famille, classe, ordre
- [ ] Tendances temporelles (animaux vus par semaine/mois)
- [ ] Animal le plus consulte

### Mode decouverte

- [ ] "Animal aleatoire" avec categories (mammiferes, oiseaux, reptiles, etc.)
- [ ] "Defi du jour" : decouvrir X animaux
- [ ] Suggestions basees sur l'historique

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

### Features premium additionnelles

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

## Elements obsoletes (supprimes)

Items retires de la roadmap car deja implementes ou generiques :

- ~~Optimisations performances~~ (ex-Phase 2c) : pagination lazy, thumbnails vs HD, index SQLite, cache memoire — **tout deja implemente**
- ~~Tests unitaires des nouvelles fonctionnalites~~ (ex-Phase 2d) : pratique courante, pas une tache specifique
- ~~Tests d'integration~~ (ex-Phase 2d) : idem
- ~~Optimisation performances chargement images~~ (ex-Phase 2d) : implemente via ImageCacheService + chargement paresseux (Phase 2d)
- ~~Correction de bugs~~ (ex-Phase 2d) : pratique courante

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
1. Telecharger TSV compresses (~14 MB, TAXREF inclus) au premier lancement
2. Creer DB SQLite locale (~117 MB avec FTS5)
3. Enrichissement a la demande (Wikidata, Wikipedia, Commons)
4. Cache local des animaux consultes

**Premium** : option de telecharger la DB complete (~1.7 GB) pour mode 100% hors ligne.

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

*Statut : Phases 1 a 2d completees — Phase 3 en cours (build mobile valide sur emulateur, tests appareil reel a suivre)*
