# Phase 3: Refonte du champ de recherche + Corrections + Tests

**Date**: 2026-02-08
**Commit**: TBD
**Statut**: ✅ Complété

## Contexte

La revue post-commit du refactoring Phase 1 & 2 (d288084) a identifié plusieurs bugs critiques dans le code de recherche :

1. **Race conditions** dans `SearchView` (data races sur `_search_id`)
2. **Type annotation invalide** dans `animal_card.py` (`ft.Icons | None` au lieu de `str | None`)
3. **Thread safety manquante** dans `AppState.repository` (propriété lazy sans lock)
4. **`page.update()` sans protection** dans `BaseView` (peut crasher si la page est fermée)
5. **Logging incohérent** dans `BaseView` (pas de fallback `print()` si `debugger` est `None`)
6. **Manque de tests** pour `SearchView` et `AnimalCard`

## Solution : Recherche classique (Enter/Button)

Plutôt que de corriger le système de debouncing complexe, on le remplace par une recherche classique plus simple et fiable :
- L'utilisateur tape sa requête
- Il appuie sur **Entrée** ou clique sur le **bouton de recherche**
- Une seule recherche est déclenchée, pas de concurrence possible

### Avantages
- **Plus simple** : pas de gestion de timers ou d'ID de recherche
- **Plus fiable** : pas de race conditions
- **Adapté desktop & mobile** : le bouton est accessible sur tous les devices
- **Moins de requêtes** : évite les requêtes inutiles pendant la frappe

## Changements implémentés

### 1. `daynimal/ui/views/search_view.py` — Refonte complète

**Supprimé** :
- Import et usage du `Debouncer`
- `on_search_change()` (callback sur chaque frappe)
- Gestion de `_search_id` et vérifications de concurrence

**Ajouté** :
- `TextField` avec `on_submit` (touche Entrée) au lieu de `on_change`
- `IconButton(ft.Icons.SEARCH)` à côté du champ (dans un `Row`)
- Méthodes `_on_submit()` et `_on_search_click()` déclenchent `perform_search()`
- Validation : ignore les requêtes vides

**Conservé** :
- `asyncio.to_thread()` pour la requête DB (non-bloquant)
- États : empty, loading, results, no results, error
- Logging et gestion d'erreurs

### 2. `daynimal/ui/components/animal_card.py:33` — Fix type annotation

```python
# Avant (invalide)
metadata_icon: ft.Icons | None = None,

# Après (correct)
metadata_icon: str | None = None,
```

**Raison** : `ft.Icons` est un module, pas un type. Les icônes sont passées comme strings (ex: `ft.Icons.SEARCH`).

### 3. `daynimal/ui/state.py` — Thread safety

**Ajout** :
```python
import threading

_repo_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

@property
def repository(self) -> AnimalRepository:
    if self._repository is None:
        with self._repo_lock:
            if self._repository is None:  # Double-check locking
                self._repository = AnimalRepository()
    return self._repository

def close_repository(self):
    with self._repo_lock:
        if self._repository:
            self._repository.close()
            self._repository = None
```

**Pattern** : Double-check locking pour éviter les race conditions lors de la création du repository.

### 4. `daynimal/ui/views/base.py` — Robustesse

**Protection `page.update()`** :
```python
def show_loading(self, message: str = "Chargement..."):
    self.container.controls = [LoadingWidget(message)]
    try:
        self.page.update()
    except Exception:
        pass  # Page peut être fermée
```

**Logging avec fallback** :
```python
def log_info(self, message: str):
    if self.debugger:
        self.debugger.logger.info(message)
    else:
        print(f"[INFO] {message}")  # Fallback
```

### 5. Tests — 2 nouveaux fichiers (20 tests)

**`tests/ui/test_search_view.py`** (10 tests) :
- ✅ `build()` retourne un `ft.Column` avec champ + bouton
- ✅ Champ de recherche et bouton sont présents
- ✅ État initial : empty state
- ✅ `perform_search()` avec résultats → affiche les cards
- ✅ `perform_search()` sans résultat → affiche "Aucun résultat"
- ✅ `perform_search()` avec exception → affiche erreur
- ✅ `_on_submit()` déclenche la recherche
- ✅ `_on_submit()` ignore les requêtes vides
- ✅ `_on_search_click()` déclenche la recherche
- ✅ `_on_search_click()` ignore les requêtes vides

**`tests/ui/test_animal_card.py`** (10 tests) :
- ✅ Création d'un `AnimalCard` basique
- ✅ Affiche le nom canonical
- ✅ Affiche le nom scientifique en italique
- ✅ Stocke `taxon_id` dans `data`
- ✅ Callback `on_click` transmet le bon `taxon_id`
- ✅ Affiche metadata (icon + texte)
- ✅ `create_search_card()` avec noms vernaculaires
- ✅ `create_search_card()` sans noms vernaculaires (fallback)
- ✅ `create_history_card()` avec timestamp
- ✅ `create_favorite_card()` avec icône rouge

### 6. `pyproject.toml` — Entry point GUI

**Changement** :
```toml
[project.scripts]
daynimal = "daynimal.main:main"
# ... autres scripts CLI ...

[project.gui-scripts]
daynimal-app = "daynimal.app:main"  # Déplacé ici
```

**Raison** : Sur Windows, `[project.gui-scripts]` évite l'ouverture d'une fenêtre console lors du lancement de l'application GUI.

## Résultats

### Tests
```bash
$ uv run pytest tests/ui/ -v
============================= test session starts =============================
collected 37 items

tests/ui/test_animal_card.py::... PASSED (10/10)
tests/ui/test_search_view.py::... PASSED (10/10)
tests/ui/test_state.py::... PASSED (6/6)
tests/ui/test_widgets.py::... PASSED (6/6)
tests/ui/test_debouncer.py::... PASSED (5/5)

============================== 37 passed in 1.90s =============================
```

### Lint
```bash
$ uv run ruff check daynimal/ui/ tests/ui/
All checks passed!
```

## Migration pour les utilisateurs

**Aucun changement** dans l'utilisation de l'application. Le comportement UX change légèrement :
- **Avant** : La recherche se déclenchait automatiquement 300ms après l'arrêt de frappe
- **Après** : L'utilisateur appuie sur Entrée ou clique sur le bouton de recherche

## Fichiers modifiés

- `daynimal/ui/views/search_view.py` (refonte)
- `daynimal/ui/components/animal_card.py` (type fix)
- `daynimal/ui/state.py` (thread safety)
- `daynimal/ui/views/base.py` (robustesse)
- `pyproject.toml` (GUI entry point)

## Fichiers créés

- `tests/ui/test_search_view.py` (10 tests)
- `tests/ui/test_animal_card.py` (10 tests)
- `docs/changes/2026-02-08-phase3-search-refactor.md` (ce document)

## Notes techniques

### Pourquoi pas de fix du Debouncer ?

Le Debouncer lui-même fonctionne correctement (5 tests passent). Le problème était dans son **utilisation** dans `SearchView` :
- Data race sur `_search_id` (incrément non atomique)
- Complexité de gestion des recherches concurrentes
- Risque de fuites mémoire (coroutines non awaited)

Plutôt que de complexifier davantage le code, la recherche classique est plus maintenable et tout aussi efficace pour ce use case.

### Double-check locking dans AppState

Le pattern double-check locking est thread-safe en Python grâce au GIL, mais on l'implémente explicitement pour :
1. Clarté d'intention (code auto-documenté)
2. Protection future si le GIL est supprimé (PEP 703)
3. Conformité aux bonnes pratiques de concurrence

### Fallback print() dans BaseView

Le fallback `print()` garantit que les logs sont toujours visibles même si le debugger n'est pas initialisé. Utile pour :
- Développement local sans debugger
- Tests unitaires
- Débogage rapide

## Références

- Commit précédent : d288084 "Refactor: Phase 1 & 2 - UI Infrastructure + Search View"
- Issue GitHub : N/A (refactoring interne)
- Tests : `tests/ui/test_search_view.py`, `tests/ui/test_animal_card.py`
