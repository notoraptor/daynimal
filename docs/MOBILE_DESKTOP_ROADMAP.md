# Roadmap : Application Mobile/Desktop

**Derniere mise a jour** : 2026-02-07

---

## Etat actuel

### Phase 1 Desktop : completee (2026-02-07)

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

## Phase 2 : Fonctionnalites mobiles

### Distribution DB mobile (prerequis)
- [ ] Heberger TSV compresses (GitHub Releases ou CDN)
  - `animalia_taxa_minimal.tsv.gz` : 84 MB
  - `animalia_vernacular_minimal.tsv.gz` : 9.3 MB
  - Total compresse : ~93 MB, decompresse : ~470 MB
- [ ] Creer fonction `download_and_setup_db()` dans l'app mobile
- [ ] Creer ecran de premier lancement avec progress bar
- [ ] Verifier espace disponible avant telechargement (~200 MB necessaires)

Note : pour regenerer les TSV : `uv run import-gbif-fast --mode minimal --save-tsv`

Tailles de reference :
- APK Flet : ~30-40 MB
- DB SQLite apres import : 153 MB (vernacular 47%, FTS5 27%, taxa 26%)
- App totale sur appareil : ~200 MB (app + DB + cache)
- Contrainte Google Play : APK < 150 MB (donc DB doit etre telechargee separement)

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

### Internationalisation (2 jours)
- [ ] Configuration Flet i18n (fr + en)
- [ ] Fichiers de traduction (JSON ou .po)
- [ ] Detection langue systeme
- [ ] Selecteur de langue dans parametres
- [ ] Tests dans les deux langues

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
- Quiz mode avance
- Badges et achievements
- Export de donnees (PDF, CSV)
- Statistiques avancees
- Collections personnalisees illimitees

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

### Tests et accessibilite (4 jours)
- [ ] Tests unitaires des nouvelles fonctionnalites
- [ ] Tests d'integration
- [ ] Optimisation performances (chargement images, etc.)
- [ ] Correction de bugs
- [ ] Accessibilite : taille de texte ajustable (3 niveaux), contraste eleve, labels semantiques
- [ ] Tests screen readers : TalkBack (Android), VoiceOver (iOS), NVDA (Windows)

**Duree estimee Phase 2 : 4-5 semaines**

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

A planifier selon feedback utilisateurs :

- **Parcours taxonomique** : arbre hierarchique interactif (Royaume > Phylum > Classe > ...), compteurs par branche
- **Filtres avances** : par statut IUCN, habitat (marin/terrestre/aerien), region geographique, taille/masse, combinaison de filtres
- **Collections thematiques** : pre-definies (animaux en danger, marins, nocturnes...) + personnalisables + partageables
- **Quiz mode** : deviner animal a partir d'image, questions classification/habitat/statut, modes facile/moyen/difficile, score et progression
- **Badges/Achievements** : "Explorateur de mammiferes" (100 vus), "Protecteur" (50 especes en danger), "Taxonomiste" (toutes les classes)
- **Comparaison d'animaux** : comparer 2-3 animaux cote a cote (taille, masse, habitat, statut)
- **Export de donnees** : favoris en PDF, historique en CSV/JSON, rapport personnalise (statistiques + favoris)
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

*Statut : Phase 1 completee - Pret pour Phase 2 Mobile*
