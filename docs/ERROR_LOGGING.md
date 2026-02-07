# Système de logging des erreurs

## Vue d'ensemble

Le système de logging a été amélioré pour garantir que **toutes les erreurs** sont visibles à la fois dans l'interface utilisateur ET dans les logs/console.

## Problème résolu

**Avant** : Les erreurs étaient affichées uniquement dans l'interface Flet, mais n'apparaissaient pas dans les logs ni dans la console, rendant le débogage difficile.

**Après** : Chaque erreur est maintenant :
- ✅ Loggée avec la stack trace complète dans le fichier de log
- ✅ Affichée dans l'interface utilisateur
- ✅ Imprimée dans la console (fallback si pas de debugger)

## Implémentation

### Import requis

```python
import traceback
```

### Pattern standard pour les blocs except

Tous les blocs `except` suivent maintenant ce pattern :

```python
except Exception as error:
    # Log error with full traceback
    error_msg = f"Error in {function_name}: {error}"
    error_traceback = traceback.format_exc()

    if self.debugger:
        self.debugger.log_error(function_name, error)
        self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
    else:
        # Fallback: print to console if no debugger
        print(f"ERROR: {error_msg}")
        print(f"Traceback:\n{error_traceback}")

    # Show error in UI
    self.container.controls = [error_display]
    self.page.update()
```

### Méthodes avec logging amélioré

1. **`load_animal_for_today_view`** - Chargement animal du jour/aléatoire
2. **`load_history_view`** - Chargement historique
3. **`perform_search`** - Recherche d'animaux
4. **`load_stats_view`** - Chargement statistiques
5. **`cleanup`** - Nettoyage des ressources
6. **`on_disconnect`** - Déconnexion de la page
7. **`on_close`** - Fermeture de l'application

## Exemple d'utilisation

### Avant (erreur invisible)

```
[UI Flet] Erreur lors du chargement: module flet has no attribute imagefit
[Logs]    (rien)
[Console] (rien)
```

### Après (erreur complète)

```
[UI Flet] Erreur lors du chargement: module flet has no attribute imagefit

[Logs]
2026-02-07 05:00:00 - daynimal - ERROR - Error in load_animal_for_today_view
2026-02-07 05:00:00 - daynimal - ERROR - Full traceback:
Traceback (most recent call last):
  File "C:\data\git\daynimal\daynimal\app.py", line 266, in load_animal_for_today_view
    animal = await asyncio.to_thread(fetch_animal)
  File "...\asyncio\tasks.py", line 485, in to_thread
    return await loop.run_in_executor(None, func_call)
  File "C:\data\git\daynimal\daynimal\app.py", line 455, in display_animal_in_today_view
    fit=ft.ImageFit.CONTAIN,
AttributeError: module 'flet' has no attribute 'ImageFit'

[Console]
ERROR: Error in load_animal_for_today_view (today): module flet has no attribute imagefit
Traceback:
Traceback (most recent call last):
  ...
AttributeError: module 'flet' has no attribute 'ImageFit'
```

## Vérification des logs

### En mode debug

```bash
python debug/run_app_debug.py --quiet
```

Les erreurs apparaissent dans :
- `logs/daynimal_YYYYMMDD_HHMMSS.log`
- Console (si lancé sans `--quiet`)

### Filtrer les erreurs

```bash
python debug/debug_filter.py --errors-only
```

## Cas d'usage

### Erreur intermittente

Si une erreur se produit de manière sporadique (comme "imagefit" qui apparaît parfois), vous pouvez maintenant :

1. Reproduire l'erreur dans l'app
2. Consulter les logs : `debug/debug_filter.py --errors-only`
3. Voir la stack trace complète
4. Identifier la ligne exacte qui cause le problème

### Débogage en production

Si l'app est utilisée sans le debugger (mode normal), les erreurs sont automatiquement imprimées dans la console, permettant de les capturer avec une redirection :

```bash
python -m daynimal.app 2> errors.log
```

## Bonnes pratiques

1. **Toujours inclure la stack trace** : Utiliser `traceback.format_exc()`
2. **Contexte clair** : Nom de la fonction dans le message d'erreur
3. **Double logging** : Debugger.logger + print (fallback)
4. **Message utilisateur** : Garder un message simple dans l'UI, détails dans les logs

## Références

- `daynimal/app.py` - Implémentation complète
- `daynimal/debug.py` - Module de debugging
- `debug/debug_filter.py` - Filtrage des logs

## Problèmes connus

### `AttributeError: module flet has no attribute ImageFit`

**Cause possible** : Version de Flet incompatible ou import incorrect

**Diagnostic** : Avec le nouveau logging, la stack trace complète révèlera :
- Quelle ligne exacte cause l'erreur
- Le contexte d'exécution
- La version de Flet utilisée

**Solution temporaire** : Si ImageFit n'existe pas, utiliser une image sans le paramètre `fit` :

```python
try:
    fit_value = ft.ImageFit.CONTAIN
except AttributeError:
    fit_value = None  # Flet plus ancien sans ImageFit

ft.Image(
    src=url,
    fit=fit_value,  # None si pas disponible
)
```
