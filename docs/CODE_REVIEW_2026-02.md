# Revue de code Daynimal - Fevrier 2026

**Date** : 2026-02-07
**Scope** : Analyse complete du code source et de la roadmap
**Verdict code** : 6.5/10
**Verdict roadmap** : 7/10

---

## Partie 1 : Code actuel

### Ce qui est bien fait

- **Architecture trois couches** (DB / Sources API / Repository) solide et bien pensee
- **APIs externes** bien structurees avec classe abstraite `DataSource`, mock pattern excellent, context managers corrects
- **Optimisation performance** : technique MIN/MAX sans filtre + random.randint pour animal du jour (93% plus rapide)
- **Parallelisation** : `ThreadPoolExecutor` dans `_enrich()` pour Wikidata + Wikipedia en parallele
- **Infrastructure de test** : `MockHttpClient` dans conftest.py, fixtures realistes
- **Attribution legale** bien integree dans les schemas avec `get_attribution_text()`

### Bugs critiques (a corriger en priorite)

#### ~~1. `datetime.utcnow()` deprece — 6 occurrences~~ CORRIGE 2026-02-07
- ~~**Fichiers** : `db/models.py`, `attribution.py`~~
- **Correction** : Remplace par `datetime.now(UTC)` dans tous les fichiers

#### 2. Engine SQLAlchemy recree a chaque session
- **Fichier** : `db/session.py` (lignes 7-16)
- **Impact** : Fuite de ressources (connection pools), degradation de performance, anti-pattern documente
- **Fix** : Implementer singleton pattern pour l'engine

#### 3. Thread safety dans `_enrich()`
- **Fichier** : `repository.py` (lignes 483-659)
- **Impact** : Workers du ThreadPoolExecutor partagent la meme session SQLAlchemy (non thread-safe), race conditions possibles
- **Fix** : Creer nouvelles sessions par thread, ou utiliser des locks

#### ~~4. `print()` au lieu de `logger`~~ CORRIGE 2026-02-07
- ~~**Fichier** : `repository.py`~~
- **Correction** : Remplace par `logger.warning()` aux lignes 599, 612, 635

#### 5. Index manquant sur `is_synonym`
- **Fichier** : `db/models.py` (ligne 46)
- **Impact** : Full table scan sur 1.5M+ lignes quand filtre sur is_synonym
- **Fix** : Ajouter `index=True` sur la colonne

#### 6. Pas de debouncing sur la recherche
- **Fichier** : `app.py` (lignes 1388-1467)
- **Impact** : Chaque frappe clavier = 1 requete DB. "guepard" = 7 requetes, race conditions, flickering
- **Fix** : Ajouter delai 300ms apres derniere frappe avant de chercher

### Problemes importants (a corriger bientot)

#### 7. Duplication massive dans app.py — ~200 lignes
- **Fichier** : `app.py` (lignes 225-296, 1214-1300, 1643-1732)
- 3 methodes quasi-identiques : `load_animal_from_history`, `load_animal_from_favorite`, `load_animal_from_search`
- Tout bug doit etre corrige 3 fois, deja divergence entre les 3
- **Fix** : Extraire methode unique `_load_and_display_animal(taxon_id, source)`

#### 8. Pas de pagination dans l'UI History/Favoris
- **Fichier** : `app.py` (lignes 881, 1078)
- Hardcode `per_page=50`, le backend supporte la pagination mais l'UI ne l'expose pas
- Utilisateurs ne peuvent pas voir au-dela des 50 premiers

#### 9. Settings charge de facon synchrone
- **Fichier** : `app.py` (lignes 2100-2103)
- Bloque le thread UI pendant la requete DB, contrairement aux autres vues
- **Fix** : Utiliser `asyncio.to_thread()` comme les autres vues

#### 10. Gestion d'erreurs HTTP inconsistante
- **Fichiers** : `sources/wikidata.py`, `sources/wikipedia.py`, `sources/commons.py`
- Pas de retry sur 429 (rate limit) ou 503
- Wikidata gere gracieusement, les autres crashent
- Pas de degradation gracieuse quand APIs down

#### 11. Fuite de ressources : Repository pas toujours ferme
- **Fichier** : `app.py` (lignes 38-42, 468-469)
- Repository cree on-demand, fermeture depend des handlers cleanup (on_disconnect, on_close)
- Si force quit ou crash, connexions restent ouvertes

#### 12. CLI History : double parsing inutile
- **Fichier** : `main.py` (lignes 194-286, 334-381)
- Argparse parse `--page` en int, puis reconvertit en string, puis `cmd_history()` re-parse en int
- **Fix** : Passer `args.page` directement a `cmd_history()`

#### 13. Mutation globale des settings dans CLI
- **Fichier** : `main.py` (lignes 353-354)
- `--db` flag mute `settings.database_url` globalement, peut polluer les tests

#### 14. app.py est un monolithe de 2200 lignes
- Classe unique gerant 6 vues, tout le state, toutes les interactions API
- Tester les vues individuellement est impossible
- A refactorer en composants separes quand on aura le temps

### Couverture de tests : ~27%

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

**Trous critiques** :
- Repository : `get_by_id()`, `get_by_name()`, `search()`, `get_random()`, `get_animal_of_the_day()`, tous les favoris, settings, cache
- Attribution : module entier non teste malgre obligation legale
- GUI : 0 test sur 2200 lignes

**Effort estime pour atteindre 70%** : 2-3 jours de tests, en priorisant repository et attribution

---

## Partie 2 : Roadmap

### Ce qui est bien dans le plan

- Decoupage en phases clair et logique (Desktop done > Mobile features > Build > Post-MVP)
- Estimations de temps presentes pour chaque feature
- Details techniques preserves (schemas SQL, chemins cache, patterns de code)
- Strategie de monetisation reflechie (freemium avec DB legere vs complete)
- Decisions strategiques documentees (tout local, pas de cloud pour le MVP)

### Preoccupations

#### 1. Phase 2 surchargee (4-5 semaines estimees, probablement 8-10 en realite)

13 features dans la Phase 2, dont 4 sont des mini-projets :
- Monetisation avec achats in-app (SDK pub + IAP = complexe)
- Notifications (FCM/APNs = integration specifique par plateforme)
- Internationalisation (i18n complet)
- Mode hors ligne (detection connectivite, queue de sync)

L'estimation "4-5 semaines" pour les 13 features est tres optimiste en solo.

#### 2. La dette technique n'est pas dans la roadmap

Aucune mention de :
- Corriger les 6 bugs critiques identifies
- Augmenter la couverture de tests (27% actuellement)
- Refactorer app.py (monolithe 2200 lignes)
- Corriger le singleton engine

Passer aux features mobiles sur des fondations fragiles amplifie les problemes. Un bug de thread safety en desktop est genant ; sur mobile avec contraintes memoire, c'est un crash.

#### 3. L'ordre des priorites n'est pas optimal

**Resequenciation recommandee :**

**Phase 2a — Stabilisation (1 semaine) :**
- Corriger les bugs critiques (datetime, engine, thread safety, index)
- Ajouter les tests manquants pour repository et attribution
- Refactorer app.py (extraire `_load_and_display_animal()`, debouncing)

**Phase 2b — Features essentielles (2-3 semaines) :**
- Cache d'images (prerequis mobile)
- Distribution DB mobile (prerequis mobile)
- Notes personnelles
- Mode hors ligne basique

**Phase 2c — Features secondaires (2 semaines) :**
- Notifications
- Partage
- Statistiques avancees

**Phase 2d — Monetisation (2 semaines, apres validation du produit) :**
- Publicites + IAP seulement apres avoir des utilisateurs
- Internationalisation

#### 4. Le build mobile devrait etre teste plus tot

Attendre toute la Phase 2 avant de builder pour mobile est risque. Un "hello world" Flet compile en APK des maintenant permettrait de :
- Valider que Flet compile bien pour Android
- Identifier les problemes specifiques mobile (performance, permissions)
- Eviter des surprises de derniere minute

#### 5. Certaines features premium trop ambitieuses pour un MVP

"Badges et achievements", "Export PDF/CSV", "Collections personnalisees illimitees", "Statistiques avancees" — tout cela peut attendre la Phase 4. Le MVP premium devrait etre simple : sans pub + DB complete.

---

## Plan d'action recommande

### Semaine de stabilisation (avant toute nouvelle feature)

**Ordre de correction :**

1. ~~`datetime.utcnow()` → `datetime.now(UTC)` (6 occurrences, 2 fichiers)~~ FAIT
2. Engine singleton dans `db/session.py`
3. Index sur `is_synonym` dans `db/models.py`
4. ~~`print()` → `logger.warning()` dans `repository.py`~~ FAIT
5. Thread safety dans `_enrich()` (session par thread)
6. Debouncing recherche dans `app.py`
7. Extraction methode dupliquee `_load_and_display_animal()` dans `app.py`
8. Tests repository (core methods + favoris + settings)
9. Tests attribution.py
10. Test build APK "hello world" avec Flet

**Effort estime** : 5-7 jours

### Apres stabilisation

Suivre la resequenciation Phase 2a/2b/2c/2d decrite ci-dessus.

---

## Reference rapide des fichiers a modifier

| Fichier | Problemes | Priorite |
|---------|-----------|----------|
| `db/session.py` | Engine recree a chaque appel | Critique |
| `db/models.py` | ~~datetime.utcnow() x3~~, index manquant | Critique |
| `attribution.py` | ~~datetime.utcnow() x3~~ | ~~Critique~~ Corrige |
| `repository.py` | Thread safety, ~~print()~~, error handling | Critique |
| `app.py` | Debouncing, duplication, pagination, sync settings, resource leak | Important |
| `main.py` | Double parsing history, mutation settings | Mineur |
| `sources/*.py` | HTTP error handling inconsistant | Mineur |

---

*Ce document sert de reference pour les sessions de travail futures. Mettre a jour au fur et a mesure que les corrections sont appliquees.*
