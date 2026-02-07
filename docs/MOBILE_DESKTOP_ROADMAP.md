# Roadmap : Transformation en Application Mobile/Desktop

Ce document détaille l'analyse et le plan pour transformer Daynimal d'une CLI en une application mobile et desktop, tout en conservant l'interface en ligne de commande.

**Date de création** : 2026-02-06
**Dernière mise à jour** : 2026-02-07
**Statut** : ✅ Phase 1 Desktop complétée

---

## 📅 Mise à jour du 2026-02-07 : Phase 1 Desktop complétée! 🎉

### ✅ Toutes les fonctionnalités Phase 1 implémentées

**Application Flet complète avec 5 onglets:**

1. **📅 Onglet "Aujourd'hui"**
   - ✅ Vue "Animal du jour" avec chargement automatique
   - ✅ Bouton "Animal aléatoire"
   - ✅ Carousel d'images interactif (navigation gauche/droite)
   - ✅ Indicateur de position (Image X/Y)
   - ✅ Persistence de l'état (l'animal reste affiché quand on change d'onglet)
   - ✅ Affichage complet : taxonomie, noms vernaculaires, données Wikidata, description Wikipedia
   - ✅ Gestion d'erreurs d'images avec URL affichée

2. **📚 Onglet "Historique"**
   - ✅ Liste paginée des animaux consultés (50 derniers)
   - ✅ **Navigation cliquable** : cliquer sur une entrée → affiche l'animal dans l'onglet "Aujourd'hui"
   - ✅ Affichage : nom, nom scientifique, date/heure de consultation
   - ✅ Icône de navigation (→) pour indiquer la clicabilité
   - ✅ Effet ripple au clic

3. **🔍 Onglet "Recherche"**
   - ✅ Recherche en temps réel (FTS5)
   - ✅ Résultats avec nom scientifique et vernaculaire
   - ✅ Clic sur résultat → affiche l'animal

4. **📊 Onglet "Statistiques"**
   - ✅ 4 cards de statistiques
   - ✅ **Layout horizontal avec wrap** (retour à la ligne automatique)
   - ✅ **Hauteur uniforme** (220px pour toutes les cards)
   - ✅ **Alignement en haut** (pas centré verticalement)
   - ✅ **Persistence de l'état** : affichage instantané au retour, rafraîchissement en arrière-plan
   - ✅ **Mise à jour automatique** : détecte les changements dans la DB
   - ✅ Statistiques affichées : Taxa totaux, Espèces, Animaux enrichis, Noms vernaculaires

5. **⚙️ Onglet "Paramètres"**
   - ✅ Section informations de l'application
   - ✅ **Toggle thème clair/sombre** avec persistence en DB
   - ✅ Section crédits (GBIF, Wikidata, Wikipedia, Commons)
   - ✅ Statistiques de la base de données

**Améliorations techniques:**
- ✅ **Persistence d'état** : Les onglets conservent leur état (animal affiché, stats, etc.)
- ✅ **Table user_settings** : Stockage des préférences utilisateur
- ✅ **Migration** : Script `migrate_add_user_settings.py` pour ajouter la table
- ✅ **Filtre d'images** : Exclusion automatique des fichiers audio/vidéo (.mp3, .mp4, etc.)
- ✅ **Gestion d'erreurs** : Affichage de l'URL problématique quand une image ne charge pas
- ✅ **Logging amélioré** : Erreurs affichées dans la console et les logs
- ✅ **Navigation fluide** : Barre de navigation fixe en bas, toujours visible
- ✅ **Chargement async optimisé** : Toutes les opérations utilisent `asyncio.to_thread`

**Qualité du code:**
- ✅ Gestion d'erreurs complète avec stack traces
- ✅ Messages d'erreur clairs dans l'UI
- ✅ Logs dans la console pour debug
- ✅ Code structuré et maintenable

### 🎯 Prochaine étape : Phase 2 Mobile

La Phase 1 Desktop est **100% complète**. Toutes les fonctionnalités de base sont implémentées et fonctionnelles.

---

## 1. État actuel du projet

### ✅ Fonctionnalités déjà implémentées

- **Base de données locale** : SQLite avec ~4.4M taxa
- **Recherche rapide** : FTS5 pour recherche full-text instantanée
- **Historique** : Tracking complet des animaux consultés avec pagination
- **Enrichissement de données** : Wikidata, Wikipedia, Wikimedia Commons
- **Attributions légales** : Conformité CC-BY/CC-BY-SA automatique
- **CLI complète** : Interface en ligne de commande fonctionnelle

### Architecture actuelle

```
daynimal/
├── daynimal/
│   ├── db/              # Couche données (SQLite + modèles)
│   ├── sources/         # APIs externes (Wikidata, Wikipedia, Commons)
│   ├── repository.py    # Orchestration données + enrichissement
│   ├── schemas.py       # Modèles de données
│   ├── main.py          # Point d'entrée CLI
│   └── config.py        # Configuration
└── tests/               # Tests unitaires complets
```

---

## 2. Fonctionnalités manquantes pour une application

### 📱 Essentielles (MVP mobile/desktop)

#### Gestion utilisateur
- **Favoris/Bookmarks**
  - Marquer des animaux comme favoris
  - Liste des favoris avec recherche/filtrage
  - Statistiques : nombre de favoris par famille, etc.

- **Notes personnelles**
  - Ajouter des notes textuelles sur des animaux
  - Modifier/supprimer des notes
  - Recherche dans les notes

- **Paramètres utilisateur**
  - Langue préférée (fr/en/etc.)
  - Thème (clair/sombre)
  - Taille de texte (accessibilité)
  - Notifications activées/désactivées

#### Expérience mobile
- **Cache d'images local**
  - Téléchargement et stockage des images
  - Gestion du cache (limite de taille, purge)
  - Mode données : haute qualité vs économique

- **Mode hors ligne**
  - Détection de la connectivité
  - Affichage gracieux quand pas d'internet
  - Indication claire des données nécessitant internet
  - Queue de synchronisation pour actions hors ligne

- **Notifications**
  - Notification quotidienne : "Découvrez l'animal du jour !"
  - Personnalisation de l'heure
  - Activation/désactivation par l'utilisateur

- **Partage**
  - Partager un animal (texte + image)
  - Formats : texte seul, image, lien web
  - Inclure automatiquement les attributions légales

#### Navigation améliorée
- **Parcours taxonomique**
  - Arbre de navigation : Royaume → Phylum → Classe → etc.
  - Vue hiérarchique interactive
  - Compteurs par branche (ex: "Mammalia (5,500 espèces)")

- **Filtres avancés**
  - Par statut de conservation IUCN (EN, VU, LC, etc.)
  - Par habitat (marin, terrestre, aérien, etc.)
  - Par région géographique
  - Par taille/masse
  - Combinaison de filtres

- **Collections thématiques**
  - Pré-définies : Animaux en danger, Marins, Nocturnes, etc.
  - Personnalisables par l'utilisateur
  - Partageables

#### Engagement utilisateur
- **Statistiques personnelles**
  - Nombre total d'animaux consultés
  - Graphiques : répartition par famille, classe, ordre
  - Tendances temporelles (animaux vus par semaine/mois)
  - Animal le plus consulté

- **Mode découverte**
  - "Animal aléatoire" avec catégories (mammifères, oiseaux, etc.)
  - "Défi du jour" : découvrir X animaux
  - Suggestions basées sur l'historique

### 🎯 Nice-to-have (post-MVP)

- **Badges/Achievements**
  - "Explorateur de mammifères" (100 mammifères vus)
  - "Protecteur" (50 espèces en danger consultées)
  - "Taxonomiste" (consulté toutes les classes)

- **Quiz mode**
  - Deviner l'animal à partir d'une image
  - Questions sur classification, habitat, statut
  - Modes : facile/moyen/difficile
  - Score et progression

- **Comparaison d'animaux**
  - Comparer 2-3 animaux côte à côte
  - Tableau comparatif : taille, masse, habitat, statut

- **Carte géographique**
  - Distribution géographique des espèces (si données disponibles)
  - Explorer par région

- **Export de données**
  - Exporter favoris en PDF
  - Exporter historique en CSV/JSON
  - Rapport personnalisé (statistiques + favoris)

- **Mode apprentissage**
  - Flashcards pour mémoriser
  - Listes d'étude personnalisées
  - Suivi de progression

---

## 3. Recommandations technologiques

### ⭐ Framework recommandé : Flet

**Description** : Framework Python basé sur Flutter permettant de créer des applications cross-platform avec un code unique.

#### Pourquoi Flet ?

✅ **Avantages** :
- **Python pur** : Pas besoin d'apprendre un nouveau langage
- **Cross-platform réel** : Un code → iOS/Android/Windows/Mac/Linux/Web
- **UI moderne** : Material Design intégré
- **Rapide à prototyper** : API simple et intuitive
- **SQLite natif** : Parfait pour notre base de données locale
- **Communauté active** : Documentation claire, exemples nombreux
- **Taille du projet** : Parfait pour apps de contenu riches

⚠️ **Inconvénients** :
- Moins mature que Flutter natif
- Performance légèrement inférieure au natif pur
- Taille de l'app assez grosse (~40-50 MB)

#### Installation et démarrage

```bash
pip install flet
```

#### Exemple basique

```python
import flet as ft
from daynimal.repository import AnimalRepository

def main(page: ft.Page):
    page.title = "Daynimal - Daily Animal Discovery"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Récupération de l'animal du jour
    with AnimalRepository() as repo:
        animal = repo.get_animal_of_the_day()

    # Interface
    page.add(
        ft.AppBar(title=ft.Text("Daynimal"), center_title=True),
        ft.Container(
            content=ft.Column([
                ft.Text(
                    animal.display_name,
                    size=30,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    animal.taxon.scientific_name,
                    size=18,
                    italic=True,
                    color=ft.colors.GREY_700
                ),
                ft.Image(
                    src=animal.images[0].url if animal.images else None,
                    width=400,
                    height=300,
                    fit=ft.ImageFit.COVER
                ),
            ]),
            padding=20
        )
    )

# Desktop
ft.app(target=main)

# Mobile
# ft.app(target=main, view=ft.AppView.FLET_APP_NATIVE)
```

### Alternatives considérées

#### Kivy
- **Avantages** : Très mature, excellent support mobile
- **Inconvénients** : UI moins moderne, courbe d'apprentissage plus raide
- **Verdict** : Bon choix alternatif si Flet ne convient pas

#### BeeWare (Toga)
- **Avantages** : UI vraiment native (widgets natifs)
- **Inconvénients** : Moins mature, support mobile en développement
- **Verdict** : À surveiller pour l'avenir

#### Web app (FastAPI + React) + PWA
- **Avantages** : Très flexible, UI moderne
- **Inconvénients** : Nécessite JavaScript/TypeScript
- **Verdict** : Si équipe avec compétences frontend JS

---

## 4. Architecture proposée

### Structure du projet

```
daynimal/
├── daynimal/                    # Backend (core) - inchangé
│   ├── __init__.py
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   ├── import_gbif.py
│   │   └── init_fts.py
│   ├── sources/
│   │   ├── base.py
│   │   ├── wikidata.py
│   │   ├── wikipedia.py
│   │   └── commons.py
│   ├── repository.py            # Logique métier
│   ├── schemas.py               # Modèles de données
│   ├── config.py
│   ├── attribution.py
│   └── cli/                     # CLI séparé (nouveau dossier)
│       └── main.py              # Ancien main.py déplacé ici
│
├── daynimal_ui/                 # Frontend Flet (nouveau)
│   ├── __init__.py
│   ├── app.py                   # Point d'entrée GUI
│   │
│   ├── views/                   # Écrans de l'application
│   │   ├── __init__.py
│   │   ├── today_view.py        # Animal du jour
│   │   ├── random_view.py       # Animal aléatoire
│   │   ├── search_view.py       # Recherche
│   │   ├── history_view.py      # Historique
│   │   ├── favorites_view.py    # Favoris (nouveau)
│   │   ├── detail_view.py       # Détail d'un animal
│   │   └── settings_view.py     # Paramètres (nouveau)
│   │
│   ├── components/              # Composants réutilisables
│   │   ├── __init__.py
│   │   ├── animal_card.py       # Carte animal (liste)
│   │   ├── image_gallery.py     # Galerie d'images
│   │   ├── taxonomy_tree.py     # Arbre taxonomique
│   │   └── app_bar.py           # Barre de navigation
│   │
│   ├── services/                # Services UI
│   │   ├── __init__.py
│   │   ├── image_cache.py       # Cache d'images local
│   │   ├── notifications.py     # Notifications
│   │   └── share.py             # Partage
│   │
│   └── assets/                  # Ressources
│       ├── icons/
│       └── images/
│
├── tests/
│   ├── test_repository.py       # Tests backend existants
│   ├── test_history.py
│   └── test_ui/                 # Tests UI (nouveau)
│       └── test_views.py
│
├── docs/
│   ├── CLAUDE.md
│   └── MOBILE_DESKTOP_ROADMAP.md  # Ce fichier
│
├── pyproject.toml
└── README.md
```

### Points d'entrée

```toml
# pyproject.toml
[project.scripts]
daynimal = "daynimal.cli.main:main"              # CLI (existant)
daynimal-ui = "daynimal_ui.app:main"             # GUI
init-fts = "daynimal.db.init_fts:init_fts"      # Utilitaires
migrate-history = "daynimal.db.migrate_add_history:migrate"
```

### Séparation des responsabilités

| Couche | Responsabilité | Technologie |
|--------|----------------|-------------|
| **Core** (`daynimal/`) | Logique métier, accès données, enrichissement | Python pur, SQLAlchemy |
| **CLI** (`daynimal/cli/`) | Interface ligne de commande | argparse, Python |
| **UI** (`daynimal_ui/`) | Interface graphique | Flet (Flutter) |
| **Tests** | Validation | pytest |

**Avantages** :
- ✅ CLI reste intact et indépendant
- ✅ Backend réutilisable (possible API REST future)
- ✅ Tests indépendants par couche
- ✅ Facilite le développement parallèle

---

## 5. Plan de développement

### Phase 1 : Prototype Flet Desktop ✅ COMPLÉTÉE (2026-02-07)

**Objectif** : Valider l'approche avec une version desktop basique. → ✅ **RÉUSSI**

**Tâches** :
1. **Setup projet** ✅
   - [x] Application Flet créée (`daynimal/app.py`)
   - [x] Point d'entrée configuré (`uv run python -m daynimal.app`)
   - [x] Dépendances ajoutées (`flet>=0.25.0`)

2. **Préparation base de données** ✅
   - [x] ~~Script DB minimale~~ → **FAIT** (`import-gbif-fast --mode minimal`)
   - [x] Génération DB minimale testée (127k espèces, 153 MB)
   - [x] Migration user_settings créée et exécutée
   - [x] Filtre d'images implémenté (exclusion audio/vidéo)

3. **Vues essentielles** ✅ (toutes implémentées dans `app.py`)
   - [x] Vue "Animal du jour" avec persistence d'état
   - [x] Vue recherche (intégration FTS5)
   - [x] Vue historique avec navigation cliquable
   - [x] Vue statistiques avec layout horizontal
   - [x] Vue paramètres/à propos

4. **Composants et fonctionnalités** ✅
   - [x] Carousel d'images avec navigation
   - [x] Affichage complet des données (taxonomie, Wikidata, Wikipedia, images)
   - [x] Gestion d'erreurs avec messages clairs
   - [x] Chargement asynchrone (pas de freeze)
   - [x] Toggle thème clair/sombre

5. **Navigation** ✅
   - [x] Bottom navigation bar (5 onglets)
   - [x] Navigation fixe (visible pendant scroll)
   - [x] Gestion de l'état (persistence entre onglets)
   - [x] Navigation depuis historique vers "Aujourd'hui"

6. **Polish** ✅
   - [x] Thème Material Design cohérent
   - [x] Layout responsive (cards statistiques wrap automatiquement)
   - [x] Animations de chargement (ProgressRing)
   - [x] Tests manuels effectués

**Livrable** : ✅ Application desktop **complète et fonctionnelle** avec toutes les fonctionnalités de base.

### Phase 2 : Fonctionnalités mobiles (3 semaines)

**Objectif** : Ajouter les fonctionnalités spécifiques mobile et enrichir l'expérience.

**Tâches** :

1. **Favoris** (3 jours)
   - [ ] Table `favorites` dans DB
   - [ ] Méthodes repository : `add_favorite()`, `remove_favorite()`, `get_favorites()`
   - [ ] Vue favoris avec liste
   - [ ] Bouton "ajouter aux favoris" dans détail
   - [ ] Tests unitaires

2. **Cache d'images** (4 jours)
   - [ ] Service `ImageCache` (téléchargement, stockage local)
   - [ ] Stratégie de cache (LRU, taille max)
   - [ ] Indicateur de téléchargement
   - [ ] Mode données (haute qualité vs économique)
   - [ ] Tests

3. **Mode hors ligne** (3 jours)
   - [ ] Détection connectivité
   - [ ] UI adaptative (afficher message si pas d'internet)
   - [ ] Queue de synchronisation
   - [ ] Indicateurs visuels

4. **Paramètres** (2 jours)
   - [ ] Vue paramètres (`settings_view.py`)
   - [ ] Thème clair/sombre (toggle)
   - [ ] Choix de langue (fr/en)
   - [ ] Stockage préférences (SQLite ou fichier)

5. **Notifications** (3 jours)
   - [ ] Service de notifications
   - [ ] Notification quotidienne programmée
   - [ ] Paramètre activation/désactivation
   - [ ] Tests (Android/iOS)

6. **Partage** (2 jours)
   - [ ] Fonction de partage natif (texte + image)
   - [ ] Formatage du texte partagé (+ attributions)
   - [ ] Tests

7. **Monétisation** (4 jours)
   - [ ] Intégration SDK publicités (AdMob ou équivalent)
   - [ ] Placement bannières (non intrusif)
   - [ ] Système achat in-app (premium unlock)
   - [ ] Logique version gratuite vs premium
   - [ ] Téléchargement DB complète (premium uniquement)
     - [ ] Service de téléchargement en background
     - [ ] Progress bar et gestion d'erreurs
     - [ ] Hébergement DB complète (GitHub releases ou CDN)
   - [ ] Tests achats (sandbox)

8. **Internationalisation (i18n)** (2 jours)
   - [ ] Configuration Flet i18n (fr + en)
   - [ ] Fichiers de traduction (JSON ou .po)
   - [ ] Détection langue système
   - [ ] Sélecteur de langue dans paramètres
   - [ ] Tests dans les deux langues

9. **Tests et optimisations** (4 jours)
   - [ ] Tests unitaires des nouvelles fonctionnalités
   - [ ] Tests d'intégration
   - [ ] Tests accessibilité (TalkBack, VoiceOver)
   - [ ] Optimisation performances (chargement images, etc.)
   - [ ] Correction de bugs

**Livrable** : Application avec fonctionnalités mobiles complètes.

### Phase 3 : Build et déploiement mobile (1 semaine)

**Objectif** : Compiler et tester sur appareils réels.

**Tâches** :

1. **Android** (3 jours)
   - [ ] Configuration build Android
   - [ ] Compilation APK
   - [ ] Tests sur émulateur
   - [ ] Tests sur appareil réel
   - [ ] Ajustements UI/UX

2. **iOS** (3 jours, si Mac disponible)
   - [ ] Configuration build iOS
   - [ ] Compilation
   - [ ] Tests sur simulateur
   - [ ] Tests sur appareil réel (nécessite compte développeur Apple)
   - [ ] Ajustements UI/UX

3. **Documentation** (1 jour)
   - [ ] Guide d'installation
   - [ ] Guide de build
   - [ ] Screenshots

**Livrable** : APK Android (et IPA iOS si possible) fonctionnels.

### Phase 4 : Features avancées (post-MVP)

À planifier selon feedback utilisateurs :

- Parcours taxonomique interactif
- Filtres avancés
- Collections thématiques
- Statistiques avancées
- Quiz mode
- Badges

---

## 6. Considérations techniques

### Base de données

**Nouvelles tables à ajouter** :

```sql
-- Favoris
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxon_id INTEGER NOT NULL,
    added_at DATETIME NOT NULL,
    FOREIGN KEY (taxon_id) REFERENCES taxa(taxon_id) ON DELETE CASCADE
);
CREATE INDEX ix_favorites_taxon_id ON favorites(taxon_id);
CREATE INDEX ix_favorites_added_at ON favorites(added_at DESC);

-- Notes personnelles
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxon_id INTEGER NOT NULL,
    note TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (taxon_id) REFERENCES taxa(taxon_id) ON DELETE CASCADE
);
CREATE INDEX ix_notes_taxon_id ON notes(taxon_id);

-- Paramètres utilisateur
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Cache d'images (métadonnées)
CREATE TABLE image_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    local_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    downloaded_at DATETIME NOT NULL
);
CREATE INDEX ix_image_cache_url ON image_cache(url);
```

### Gestion du cache d'images

**Stratégie** :
1. Télécharger images à la demande
2. Stocker dans répertoire app local
3. Limite : 500 MB (configurable)
4. LRU : supprimer les plus anciennes si limite atteinte

**Chemins** :
- Desktop : `~/.daynimal/cache/images/`
- Mobile Android : `/data/data/com.daynimal/cache/images/`
- Mobile iOS : `Library/Caches/images/`

### Performance

**Optimisations à prévoir** :
- Pagination lazy (charger 20 animaux à la fois)
- Images : thumbnails vs full resolution
- Index SQLite sur colonnes fréquemment filtrées
- Cache en mémoire pour vues récentes

---

## 7. Décisions stratégiques

### ✅ Décisions validées

#### 1. Synchronisation cloud
**Décision** : ❌ **Pas de cloud pour le moment**
- Tout reste local
- Simplifie le développement MVP
- Pas de coûts serveur
- À reconsidérer post-MVP selon feedback utilisateurs

#### 2. Modèle de monétisation
**Décision** : ✅ **Deux versions (freemium)**

**Version gratuite (avec publicités)** :
- Toutes les fonctionnalités de base
- DB taxonomique légère embarquée (~50 MB)
- Enrichissement à la demande (nécessite internet)
- Cache local des animaux consultés
- Publicités non intrusives (bannières)

**Version premium (payante, ~3-5€)** :
- ✅ Sans publicités
- ✅ **Mode hors ligne complet** : option de télécharger toute la base (~600 MB)
- ✅ Features bonus :
  - Quiz mode avancé
  - Badges et achievements
  - Export de données (PDF, CSV)
  - Statistiques avancées
  - Collections personnalisées illimitées

**Objectif** : Générer des revenus tout en gardant l'app accessible.

#### 3. Langues
**Décision** : ✅ **Français + Anglais pour commencer**

**Phase 1 (MVP)** :
- Traduction complète de l'UI (fr + en)
- Descriptions en langue originale (pas de traduction)
- Détection automatique de la langue système
- Sélection manuelle dans paramètres

**Phase 2 (post-MVP)** :
- [ ] TODO : Évaluer traduction automatique des descriptions (API de traduction)
- [ ] TODO : Ajouter d'autres langues (es, de, pt, etc.)
- [ ] TODO : Contributions communautaires pour traductions

#### 4. Accessibilité
**Décision** : ✅ **Support accessibilité de base**

**À implémenter** :
- ✅ Taille de texte ajustable (3 niveaux : normal, grand, très grand)
- ✅ Contraste élevé (thème sombre inclus)
- ✅ Labels sémantiques pour screen readers (support natif Flet/Flutter)
- ⚠️ **Note** : Tests screen readers à faire manuellement (TalkBack Android, VoiceOver iOS)

**Tests recommandés** :
- Android : Activer TalkBack dans paramètres → Accessibilité
- iOS : Activer VoiceOver dans Réglages → Accessibilité
- Desktop : NVDA (Windows), VoiceOver (Mac)

#### 5. Stratégie de base de données
**Décision** : ✅ **Option C - DB légère + chargement progressif (hybride)**

**Problématique** :
- DB complète = ~1.7 GB (4.4M taxa tous rangs confondus + FTS5)
- Limite Google Play pour APK = 150 MB
- Téléchargement complet au premier lancement = mauvaise UX

**Solution implémentée** : ✅ **Mode minimal via `import-gbif-fast`**

### Approche technique retenue

**Génération de deux types de DB à la source** :

```bash
# DB COMPLÈTE (développement/desktop)
uv run import-gbif-fast --mode full
# → 4.4M taxa (tous rangs taxonomiques)
# → ~1.7 GB

# DB MINIMALE (mobile)
uv run import-gbif-fast --mode minimal
# → 127,762 espèces avec noms vernaculaires uniquement
# → ~200 MB avec index FTS5
# → Filtrage : rank='species' ET a des vernacular names

# Avec sauvegarde TSV pour distribution
uv run import-gbif-fast --mode minimal --save-tsv
# → Crée animalia_taxa_minimal.tsv + animalia_vernacular_minimal.tsv
# → Compresser en .tsv.gz (~93 MB) pour distribution
```

**Pourquoi cette approche est meilleure** :
- ✅ **Direct** : TSV brut → DB minimale (un seul passage, pas besoin de DB full d'abord)
- ✅ **Efficace** : Filtrage pendant le parsing (pas de post-traitement)
- ✅ **Flexible** : Même structure de DB, juste moins de données
- ✅ **Distribution optimale** : TSV compressé = beaucoup plus petit que SQLite
- ✅ **Stratégie GBIF native** : Ils distribuent des TSV, pas des DBs

### Déploiement mobile

**Version gratuite** :
1. **Distribution des TSV compressés** (~93 MB)
   - Héberger `animalia_taxa_minimal.tsv.gz` (84 MB) et `animalia_vernacular_minimal.tsv.gz` (9.3 MB)
   - GitHub Releases, CDN, ou site perso

2. **Premier lancement de l'app**
   - Télécharger les TSV compressés (~93 MB)
   - Décompresser (~470 MB)
   - Créer la DB SQLite locale (~200 MB avec index FTS5)
   - Durée estimée : 1-2 minutes en WiFi

3. **Enrichissement à la demande** (nécessite internet)
   - Au clic sur un animal : fetch Wikidata, Wikipedia, Commons
   - Cache local après première consultation
   - Indicateur visuel "données en ligne" vs "données en cache"

4. **Cache persistant**
   - Animaux consultés stockés localement
   - Images en cache (limite 500 MB, LRU)
   - Fonctionne hors ligne pour animaux déjà vus

**Version premium** :
5. **Option "Mode hors ligne complet"** (dans paramètres)
   - Téléchargement de la DB complète (~1.7 GB) via TSV compressés
   - Toutes les données taxonomiques (4.4M taxa)
   - FTS5 complet
   - Option de pré-télécharger images (choix utilisateur)
   - Fonctionne 100% hors ligne après téléchargement

### Avantages de la solution

- ✅ **APK ultra-léger** (~30-40 MB avec framework Flet)
- ✅ **Démarrage rapide** : App démarre immédiatement, téléchargement en background
- ✅ **Contenu grand public** : Espèces connues avec noms communs
- ✅ **Scalable** : Facile d'ajouter d'autres modes (ultra-minimal, medium, etc.)
- ✅ **Pas de gaspillage** : Pas besoin de créer DB full pour avoir DB minimal
- ✅ **Distribution efficace** : TSV compressé = optimal pour téléchargement
- ✅ **Incitation premium claire** : Version gratuite limitée mais fonctionnelle, premium = hors ligne complet

### Implémentation code

```python
# Détection du premier lancement
if not database_exists():
    show_setup_screen()
    download_tsv_files()  # ~30-50 MB
    decompress_and_import()  # Créer DB locale
    create_fts_index()

# Enrichissement conditionnel
if is_online():
    animal = repo.get_by_id(taxon_id, enrich=True)  # Fetch APIs
else:
    animal = repo.get_by_id(taxon_id, enrich=False)  # Données locales uniquement
    show_message("Mode hors ligne - données limitées")

# Mode hors ligne complet (premium)
if is_premium and settings.offline_mode_enabled:
    if not is_full_db_downloaded():
        show_download_prompt()  # Télécharge DB complète (TSV full)
```

### 🎉 Résultats de l'implémentation

**Base de données minimale générée avec succès** (2026-02-06) :

**Statistiques** :
- ✅ **127,762 espèces** avec noms vernaculaires (stratégie Option D)
  - Réduction de 96% : 3,053,779 espèces extraites → 127,762 conservées
  - Critères : `rank='species'` ET possède au moins un nom vernaculaire
- ✅ **1,072,723 noms vernaculaires** dans 28 langues
- ✅ **Index FTS5 créé** pour recherche instantanée
- ✅ **Fichiers TSV générés** pour distribution mobile

**Tailles des fichiers** :
```
Non compressés :
- animalia_taxa_minimal.tsv      : 439 MB
- animalia_vernacular_minimal.tsv: 31 MB
- Total                          : ~470 MB

Compressés (gzip -9) :
- animalia_taxa_minimal.tsv.gz      : 84 MB
- animalia_vernacular_minimal.tsv.gz: 9.3 MB
- Total                             : ~93 MB ✅

Base de données SQLite :
- daynimal_minimal.db (avant VACUUM) : 912 MB (avec ~740 MB d'espace vide)
- daynimal_minimal.db (après VACUUM)  : 153 MB ✅
  - vernacular_names + index : 81 MB (47%)
  - FTS5 tables (recherche)  : 47 MB (27%)
  - taxa + index             : 44 MB (26%)
```

**⚠️ Important** : Toujours exécuter `VACUUM` après création de la DB :
```python
import sqlite3
conn = sqlite3.connect('daynimal_minimal.db')
conn.execute('VACUUM')
conn.close()
```

**Tests de validation** :
- ✅ Recherche FTS5 fonctionnelle et rapide (testée sur "lion", "chat", "butterfly")
- ✅ Enrichissement Wikidata/Wikipedia/Commons opérationnel
- ✅ Commandes `search`, `info`, `random` validées avec `--db daynimal_minimal.db`
- ✅ VACUUM validé : 912 MB → 153 MB (réduction de 83%)
- ⚠️ Encodage Windows (problème d'affichage terminal, n'affecte pas la fonctionnalité)

**Taille finale pour mobile** :
- 📦 TSV compressés (distribution) : **93 MB**
- 💾 DB SQLite après import (sur appareil) : **153 MB**
- 📱 App totale estimée : ~200 MB (app 30 MB + DB 153 MB + cache 20 MB)

**Décision** : ✅ **153 MB accepté** - Taille acceptable pour 2026, recherche rapide avec FTS5

**Conclusion** :
- ✅ **Distribution optimale** : 93 MB compressé (téléchargement WiFi ~30-60 sec)
- ✅ **Contenu pertinent** : 127k espèces avec noms communs = grand public
- ✅ **Performance** : Recherche instantanée avec FTS5
- ✅ **Prêt pour prototype Flet**

### Tâches techniques

**Phase 1** :
- ✅ ~~Créer script pour DB minimale~~ → **FAIT** (`import-gbif-fast --mode minimal`)
- ✅ ~~Générer DB minimale et fichiers TSV~~ → **FAIT** (127k espèces, 93 MB compressé)
- ✅ ~~Créer index FTS5 pour recherche~~ → **FAIT** (script `init-fts --db` modifié)
- ✅ ~~Valider recherche et enrichissement~~ → **FAIT** (tests manuels OK)
- [ ] Héberger TSV compressés (GitHub Releases ou CDN)
- [ ] Créer fonction `download_and_setup_db()` dans l'app mobile
- [ ] Créer écran de premier lancement avec progress bar

**Phase 2 (premium)** :
- [ ] Héberger TSV full compressés pour mode hors ligne complet
- [ ] Implémenter téléchargement background de la DB full
- [ ] Système de gestion du stockage (vérifier espace disponible)

---

## 8. Ressources

### Documentation Flet
- Site officiel : https://flet.dev
- GitHub : https://github.com/flet-dev/flet
- Exemples : https://github.com/flet-dev/examples

### Tutoriels recommandés
- Flet crash course : https://flet.dev/docs/tutorials/python-todo
- Building mobile apps : https://flet.dev/docs/guides/python/mobile

### Outils
- Flet CLI : Compilation mobile/desktop
- Flutter DevTools : Debug UI
- Android Studio : Émulateur Android
- Xcode : Émulateur iOS (Mac uniquement)

---

## 9. Conclusion

### ✅ Décisions stratégiques validées

**Toutes les questions en suspens ont été résolues** :
1. ✅ Pas de synchronisation cloud (pour le moment)
2. ✅ Modèle freemium : gratuit avec pub + premium payant (~3-5€)
3. ✅ Langues : fr + en (UI seulement, descriptions en TODO)
4. ✅ Accessibilité : support de base avec tests manuels
5. ✅ **Stratégie DB hybride** : légère embarquée + enrichissement à la demande

### 🎯 Proposition de valeur claire

**Version gratuite** :
- App fonctionnelle avec toutes les features de base
- Nécessite internet pour enrichissement
- Publicités non intrusives

**Version premium** (3-5€) :
- Sans publicités
- Mode hors ligne complet (600 MB téléchargeables)
- Features bonus (quiz, badges, export, stats avancées)

→ **Incitation forte à upgrader** : valeur claire (hors ligne)

### 🎉 Prototype Flet fonctionnel (2026-02-06)

**Application desktop créée et testée avec succès !**

**Fichier créé** : `daynimal/app.py` (310 lignes)

**Fonctionnalités implémentées** :
- ✅ Interface graphique Flet (Flutter pour Python)
- ✅ Vue "Animal du jour" avec chargement automatique au démarrage
- ✅ Bouton "Animal aléatoire" pour découvrir d'autres espèces
- ✅ Affichage complet des informations :
  - Nom d'affichage et nom scientifique
  - Classification taxonomique (règne, embranchement, classe, ordre, famille)
  - Noms vernaculaires multilingues (5 premières langues)
  - Données enrichies Wikidata (statut IUCN, masse, longueur, durée de vie)
  - Description Wikipedia (tronquée à 500 caractères)
  - Première image disponible avec crédit artiste
  - Attribution légale (GBIF)
- ✅ Indicateur de chargement pendant fetch
- ✅ Gestion d'erreurs avec messages clairs
- ✅ Intégration complète avec `AnimalRepository`
- ✅ Historique automatique (enregistrement des consultations)
- ✅ Scroll automatique pour contenu long

**Commande de lancement** :
```bash
uv run daynimal-app
```

**Dépendance ajoutée** :
- `flet>=0.25.0` dans `pyproject.toml`
- Auto-installation de `flet-desktop` au premier lancement

**Corrections techniques appliquées** :
- Capitalisation API Flet : `ft.colors` → `ft.Colors`
- Icônes : `ft.icons.TODAY` → `ft.Icons.CALENDAR_TODAY`
- Attribut Wikipedia : `extract` → `summary`

**Architecture** :
- Classe `DaynimalApp` qui gère l'état et la logique
- Méthode `build()` pour construire l'UI
- Méthodes `show_today()` et `show_random()` pour charger les animaux
- Méthode `display_animal()` pour afficher les informations
- Context manager `with AnimalRepository()` pour accès DB

### 📋 Prochaines étapes immédiates

1. ✅ ~~Valider l'approche~~ → **FAIT**
2. ✅ ~~Créer script DB minimale~~ → **FAIT** (`import-gbif-fast --mode minimal`)
3. ✅ ~~Tester génération DB minimale~~ → **FAIT** (127k espèces, 93 MB compressé, FTS5 OK)
4. ✅ ~~Créer prototype minimal Flet~~ → **FAIT** (1 vue "Animal du jour" fonctionnelle)
5. ✅ ~~Tester sur desktop~~ → **FAIT** (Windows validé)
6. ⏭️ **Continuer avec Phase 1 complète** (ajouter plus de vues et features)

### 🔜 Phase 1 complète - Fonctionnalités à ajouter

**Vues supplémentaires** :
- [ ] Vue Historique (liste paginée des animaux consultés)
- [ ] Vue Recherche (intégration FTS5, résultats en temps réel)
- [ ] Vue Statistiques (graphiques de la DB)
- [ ] Vue À propos / Crédits complets

**Améliorations UI/UX** :
- [ ] Navigation par onglets ou drawer menu
- [ ] Thème sombre/clair
- [ ] Animations de transition
- [ ] Images en carousel (toutes les images, pas juste la première)
- [ ] Chargement asynchrone des images (éviter freeze)
- [ ] Placeholder pendant chargement des images

**Features additionnelles** :
- [ ] Favoris / "J'aime"
- [ ] Partage (export info en texte/image)
- [ ] Paramètres (langue préférée, taille police, etc.)
- [ ] Option `--db` pour tester avec DB minimale

**Optimisations** :
- [ ] Cache des images téléchargées
- [ ] Préchargement des données au démarrage
- [ ] Gestion des erreurs réseau (mode dégradé sans enrichissement)

### 💪 Avantages de l'approche

**Technique** :
- ✅ Réutilisation maximale du code backend existant
- ✅ CLI toujours disponible pour power users et tests
- ✅ Un seul code pour toutes les plateformes (iOS/Android/Desktop/Web)
- ✅ Développement rapide avec Python pur
- ✅ UI moderne et professionnelle (Material Design)

**Business** :
- ✅ Modèle de revenus clair (premium)
- ✅ APK léger = meilleur taux de téléchargement
- ✅ Version gratuite attractive = large base d'utilisateurs
- ✅ Premium avec valeur claire = bon taux de conversion attendu

### ⏱️ Délais estimés (révisés)

- **Phase 1** - Prototype desktop : 2 semaines (DB minimale déjà faite !)
- **Phase 2** - Features mobiles + monétisation : 4 semaines (+1 pour pub/premium/i18n)
- **Phase 3** - Build et déploiement : 1 semaine
- **Total MVP complet : ~7 semaines** (~1.5-2 mois)

### 🚀 Roadmap post-MVP

**Court terme** (après lancement) :
- Analyser métriques utilisateurs (taux de conversion, rétention)
- Itérer sur UI/UX selon feedback
- Corriger bugs critiques

**Moyen terme** (3-6 mois) :
- Collections thématiques
- Quiz mode avancé
- Traduction descriptions (API auto-traduction)
- Langues additionnelles (es, de, pt)

**Long terme** (6-12 mois) :
- Synchronisation cloud (si demandé)
- Parcours taxonomique interactif
- Mode apprentissage / flashcards
- Partenariats conservation (dons, sensibilisation)

---

## 🎊 Conclusion et prochaines étapes

### ✅ Phase 1 Desktop : 100% complétée (2026-02-07)

**Toutes les fonctionnalités de l'application desktop sont implémentées:**
- 5 onglets fonctionnels (Aujourd'hui, Historique, Recherche, Statistiques, Paramètres)
- Carousel d'images interactif
- Toggle thème clair/sombre avec persistence
- Navigation depuis historique
- Statistiques avec layout responsive
- Gestion d'erreurs robuste
- Filtre d'images (exclusion audio/vidéo)

**Application prête pour:**
- ✅ Tests utilisateurs sur desktop
- ✅ Démarrage Phase 2 (fonctionnalités mobiles)
- ✅ Build mobile Android/iOS

### 🚀 Prochaine étape : Phase 2 Mobile

**Priorités Phase 2:**
1. **Favoris** : Permettre de sauvegarder des animaux favoris
2. **Cache d'images** : Téléchargement et stockage local
3. **Mode hors ligne** : Détection connectivité + UI adaptative
4. **Notifications** : Notification quotidienne "Animal du jour"
5. **Partage** : Partager un animal (texte + image)
6. **Monétisation** : Publicités + version premium
7. **Internationalisation** : Support fr + en

**Délai estimé Phase 2:** 3-4 semaines

---

*Document maintenu par Claude Code*
*Dernière mise à jour : 2026-02-07*
*Statut : ✅ Phase 1 Desktop complétée à 100% - Prêt pour Phase 2 Mobile*
