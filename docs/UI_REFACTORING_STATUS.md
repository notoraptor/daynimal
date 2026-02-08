# UI Refactoring Status - app.py vers architecture modulaire

**Objectif** : Refactorer `app.py` (2190 lignes) vers une architecture modulaire, maintenable et testable.

**Progression** : Phase 3/10 complétée ✅

---

## Vue d'ensemble

| Phase | Description | Status | Gain (lignes) |
|-------|-------------|--------|---------------|
| **Phase 1** | Infrastructure (AppState, BaseView, widgets, debouncer) | ✅ **Complété** | +400 (nouveau code) |
| **Phase 2** | Vue pilote - Search (avec debouncing) | ✅ **Complété** | -241 (app.py) |
| **Phase 3** | Refonte Search + Corrections + Tests | ✅ **Complété** | +20 tests, 5 bugs fixés |
| **Phase 4** | Méthode unifiée `load_and_display_animal()` | ⏳ À faire | -240 estimé |
| **Phase 5** | Vues History et Favorites | ⏳ À faire | -300 estimé |
| **Phase 6** | Vue Settings | ⏳ À faire | -150 estimé |
| **Phase 7** | Vue Stats | ⏳ À faire | -120 estimé |
| **Phase 8** | Vue Today + composants | ⏳ À faire | -500 estimé |
| **Phase 9** | Finalisation - AppController | ⏳ À faire | -600 estimé |
| **Phase 10** | Cleanup et documentation | ⏳ À faire | N/A |

**Total estimé** : 2190 lignes (app.py) → ~50 lignes (entry point) + ~1200 lignes (17 fichiers modulaires)

---

## Phase 1 : Infrastructure ✅

**Fichiers créés** : 7 fichiers + 3 fichiers de tests

### Structure
```
daynimal/ui/
├── state.py                    # AppState (état partagé + repository lifecycle)
├── components/
│   └── widgets.py              # LoadingWidget, ErrorWidget, EmptyStateWidget
├── views/
│   └── base.py                 # BaseView (classe abstraite)
└── utils/
    └── debounce.py             # Debouncer (300ms)

tests/ui/
├── test_state.py               # 6 tests
├── test_widgets.py             # 6 tests
└── test_debouncer.py           # 5 tests
```

### Corrections apportées
1. **Resource leak résolu** : Repository fermé proprement (AppState.close_repository)
2. **Widgets réutilisables** : 16 duplications éliminées (3 widgets × 3-7 usages)
3. **Debouncer implémenté** : Prêt pour Phase 2 (Search)

### Tests
- **17/17 tests passés** (100%)
- **117/117 tests existants passés** (non-régression)

**Documentation** : `docs/changes/2026-02-08-phase1-infrastructure-ui.md`

---

## Phase 2 : Vue pilote - Search ✅

**Fichiers créés** : 2 fichiers

### Structure
```
daynimal/ui/
├── components/
│   └── animal_card.py          # AnimalCard + 3 helpers
└── views/
    └── search_view.py          # SearchView (avec debouncing)
```

### Corrections apportées
1. **Debouncing actif** : 1 requête DB au lieu de 4-8 pour un mot tapé
2. **AnimalCard réutilisable** : 3 duplications éliminées (History, Favorites, Search)
3. **SearchView modulaire** : 241 lignes supprimées de app.py

### Changements dans app.py
- **Imports ajoutés** : AppState, SearchView
- **Lazy init** : SearchView créée on-demand
- **show_search_view()** : ~260 lignes → 20 lignes (**92% de réduction**)
- **Méthodes supprimées** : `on_search_change`, `perform_search`

### Tests
- **117/117 tests existants passés** (non-régression)
- **Tests manuels requis** : Debouncing, états de la vue, navigation

**Documentation** : `docs/changes/2026-02-08-phase2-search-view.md`

---

## Phase 3 : Refonte Search + Corrections ✅

**Fichiers créés** : 2 fichiers de tests

### Problèmes identifiés et corrigés

1. **Race conditions** : Data race sur `_search_id` dans SearchView
2. **Type annotation invalide** : `metadata_icon: ft.Icons | None` → `str | None`
3. **Thread safety manquante** : `AppState.repository` sans lock
4. **`page.update()` non protégé** : Peut crasher si page fermée
5. **Logging incohérent** : Pas de fallback si `debugger` est `None`

### Solution : Recherche classique (Enter/Button)

**Remplacement du debouncing** :
- ❌ Recherche automatique après 300ms (complexe, race conditions)
- ✅ Recherche manuelle sur Enter ou clic bouton (simple, fiable)

### Fichiers modifiés

1. **`search_view.py`** : Refonte complète (debouncer → Enter/Button)
2. **`animal_card.py`** : Fix type annotation
3. **`state.py`** : Thread safety avec `threading.Lock`
4. **`base.py`** : Protection `page.update()` + fallback logging
5. **`pyproject.toml`** : Entry point GUI

### Structure tests
```
tests/ui/
├── test_search_view.py         # 10 tests
└── test_animal_card.py         # 10 tests
```

### Tests
- **37/37 tests UI passés** (17 existants + 20 nouveaux)
- **117/117 tests existants passés** (non-régression)
- **Lint propre** : `ruff check` sans erreurs

**Documentation** : `docs/changes/2026-02-08-phase3-search-refactor.md`

---

## Phase 4 : Méthode unifiée ⏳

**Objectif** : Éliminer la duplication des 3 méthodes `load_animal_from_*`.

### Méthodes à unifier
1. `load_animal_from_search(taxon_id)` - ligne 1391 (~90 lignes)
2. `load_animal_from_history(taxon_id)` - ligne 234 (~70 lignes)
3. `load_animal_from_favorite(taxon_id)` - ligne 1219 (~85 lignes)

**Total** : ~240 lignes (95% identiques)

### Méthode cible
```python
async def load_and_display_animal(
    self,
    taxon_id: int,
    source: str,  # "history", "favorite", "search", "today", "random"
    enrich: bool = True,
    add_to_history: bool = False
):
    """Unified method to load and display an animal."""
    # Switch to Today view
    # Show loading
    # Fetch animal
    # Update app_state.current_animal
    # Add to history (if requested)
    # Display animal
```

### Gain estimé
- **240 lignes supprimées** de app.py
- **1 méthode au lieu de 3**
- **Facile à tester** unitairement

---

## Phase 5 : Vues History et Favorites ⏳

**Objectif** : Migrer History et Favorites vers architecture modulaire.

### Fichiers à créer
```
daynimal/ui/views/
├── history_view.py             # HistoryView (~150 lignes)
└── favorites_view.py           # FavoritesView (~150 lignes)
```

### Composants utilisés
- `create_history_card(animal, on_click, viewed_at_str)` (déjà créé)
- `create_favorite_card(animal, on_click)` (déjà créé)
- `LoadingWidget`, `ErrorWidget`, `EmptyStateWidget` (déjà créés)

### Gain estimé
- **~300 lignes supprimées** de app.py
- **2 vues modulaires** (120-150 lignes chacune)
- **Utilisation complète de AnimalCard** dans 3 vues

---

## Phase 5 : Vue Settings ⏳

**Objectif** : Migrer Settings avec amélioration de la logique de thème.

### Fichiers à créer
```
daynimal/ui/views/
└── settings_view.py            # SettingsView (~120 lignes)
```

### Fonctionnalités
- Toggle thème clair/sombre (callback vers app.py pour application globale)
- Affichage des crédits
- Affichage des stats DB

### Gain estimé
- **~150 lignes supprimées** de app.py
- **Vue Settings testable** unitairement

---

## Phase 6 : Vue Stats ⏳

**Objectif** : Migrer Stats (déjà async, améliorer le cache).

### Fichiers à créer
```
daynimal/ui/views/
└── stats_view.py               # StatsView (~100 lignes)
```

### Améliorations
- Cache des stats dans AppState
- Refresh en arrière-plan
- 4 cartes avec icônes

### Gain estimé
- **~120 lignes supprimées** de app.py
- **Cache centralisé** dans AppState

---

## Phase 7 : Vue Today + composants ⏳

**Objectif** : Migrer la vue la plus complexe (Today avec carousel).

### Fichiers à créer
```
daynimal/ui/components/
├── image_carousel.py           # ImageCarousel (~100 lignes)
└── animal_display.py           # AnimalDisplay (~150 lignes)

daynimal/ui/views/
└── today_view.py               # TodayView (~200 lignes)
```

### Composants
- **ImageCarousel** : Carousel d'images avec prev/next
- **AnimalDisplay** : Affichage complet (taxonomie, Wikidata, Wikipedia, images, attributions)
- **TodayView** : Orchestre le tout + boutons "Animal du jour" et "Aléatoire"

### Gain estimé
- **~500 lignes supprimées** de app.py
- **3 composants réutilisables**
- **Vue Today modulaire**

---

## Phase 8 : Finalisation - AppController ⏳

**Objectif** : Remplacer complètement DaynimalApp par AppController.

### Fichiers à créer
```
daynimal/ui/
└── app_controller.py           # AppController (~300 lignes)
```

### AppController
- Orchestre toutes les vues (lazy init)
- Gère la navigation (on_nav_change)
- Fournit `load_and_display_animal()` (unifié)
- Gère le lifecycle (cleanup, on_disconnect, on_close)

### app.py final
```python
# app.py (~50 lignes)
import flet as ft
from daynimal.ui.app_controller import AppController

def main():
    """Main entry point for the Flet app."""
    def app_main(page: ft.Page):
        AppController(page)

    ft.app(target=app_main)

if __name__ == "__main__":
    main()
```

### Gain estimé
- **~600 lignes supprimées** de app.py
- **app.py réduit à entry point** (~50 lignes)
- **Architecture complètement modulaire**

---

## Phase 9 : Cleanup et documentation ⏳

**Objectif** : Nettoyer le code et documenter la nouvelle architecture.

### Actions
1. Supprimer code mort (ancien imports, méthodes non utilisées)
2. Ajouter docstrings complètes à toutes les classes
3. Mettre à jour `CLAUDE.md` (section "Architecture" + "File Structure")
4. Créer `docs/UI_ARCHITECTURE.md` (patterns, guidelines)

### Vérification
```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

---

## Statistiques

### Lignes de code

| Fichier | Avant | Après (Phase 2) | Après (Phase 8) |
|---------|-------|-----------------|-----------------|
| **app.py** | 2190 | 1949 (-241) | ~50 (-2140) |
| **UI modules** | 0 | 630 | ~1200 |
| **Tests UI** | 0 | 17 tests | ~40 tests estimés |

### Couverture de tests

| Phase | Tests UI | Tests totaux | Status |
|-------|----------|--------------|--------|
| Phase 1 | 17 | 134 (117+17) | ✅ 100% passés |
| Phase 2 | 17 | 134 | ✅ 100% passés |
| Phase 3 | TBD | TBD | ⏳ À faire |

---

## Checklist globale

### Infrastructure
- [x] AppState créé (état partagé + repository lifecycle)
- [x] BaseView créé (classe abstraite pour vues)
- [x] Widgets réutilisables créés (Loading, Error, EmptyState)
- [x] Debouncer créé (300ms)
- [x] Tests infrastructure (17/17 passés)

### Composants
- [x] AnimalCard créé (History, Favorites, Search)
- [ ] ImageCarousel créé (Today)
- [ ] AnimalDisplay créé (Today)

### Vues
- [x] SearchView créée (avec debouncing)
- [ ] HistoryView créée
- [ ] FavoritesView créée
- [ ] SettingsView créée
- [ ] StatsView créée
- [ ] TodayView créée

### Méthodes unifiées
- [ ] load_and_display_animal() créée
- [ ] 3 méthodes dupliquées supprimées

### Finalisation
- [ ] AppController créé
- [ ] DaynimalApp remplacé
- [ ] app.py réduit à entry point
- [ ] Documentation mise à jour (CLAUDE.md, UI_ARCHITECTURE.md)

---

## Prochaine étape immédiate

**Phase 3 : Méthode unifiée**

1. Créer `load_and_display_animal()` dans app.py
2. Remplacer les 3 méthodes dupliquées
3. Tester les workflows History, Favorites, Search
4. Documenter dans `docs/changes/2026-02-08-phase3-unified-method.md`

**Durée estimée** : 1 jour

---

**Dernière mise à jour** : 2026-02-08 (Phase 2 complétée)
