# Debugging Daynimal Flet

Outils de logging pour debugger l'application Flet. Les `print()` n'apparaissent pas dans Flet et les erreurs peuvent etre silencieuses. Ce systeme ajoute un logging automatique dans des fichiers horodates.

## Quick Start

```bash
# Lancer l'app avec debug (depuis la racine du projet)
python debug/run_app_debug.py --quiet

# Voir les logs filtres (elimine ~87% du bruit Flet)
python debug/debug_filter.py

# Seulement les erreurs
python debug/debug_filter.py --errors-only

# Suivre en temps reel
python debug/debug_filter.py --tail

# Chercher un mot-cle
python debug/debug_filter.py --search "wikidata"

# Statistiques
python debug/debug_filter.py --stats
```

## Scripts disponibles

| Script | Description |
|--------|-------------|
| `run_app_debug.py` | Launcher avec logging automatique (`--quiet`, `--web`) |
| `debug_filter.py` | Filtre intelligent des logs Flet |
| `view_logs.py` | Utilitaire pour lister/voir les logs (`--list`, `--all`) |

## Ce qui est logge automatiquement

- Demarrage/arret de l'application
- Navigation entre vues (Today, History, Favorites, Search, Stats, Settings)
- Chargement d'animaux avec nom (mode today/random)
- Recherches avec nombre de resultats
- Erreurs avec stack traces completes
- Appels reseau (httpcore debug)

Les logs sont ecrits dans `logs/daynimal_YYYYMMDD_HHMMSS.log`.

## Ajouter des logs personnalises

```python
from daynimal.debug import get_debugger

debugger = get_debugger()
debugger.logger.info("Mon message")
```

Ou avec les fonctions raccourcies :

```python
from daynimal.debug import log_info, log_error, log_debug

log_info("Operation reussie")
log_error("Erreur survenue")
```

## Architecture

```
run_app_debug.py
    -> Initialise FletDebugger (daynimal/debug.py)
        -> Configure logging vers logs/daynimal_TIMESTAMP.log
            -> Passe debugger a l'app via page.data

app.py
    -> Recupere debugger depuis page.data
        -> Log les evenements aux points cles
```

L'app fonctionne avec ou sans debugger (import optionnel).

## Troubleshooting

- **Logs pas dans la console** : Verifier que vous utilisez `run_app_debug.py` (pas `app.py`) et que `--quiet` n'est pas active
- **Fichier de log vide** : L'app a peut-etre crashe avant l'ecriture. Verifier permissions sur `logs/`
- **UnicodeEncodeError sur Windows** : Les emojis dans les logs causent `'charmap' codec can't encode character`. Solution : remplacer les emojis par du texte dans les fonctions de log.
- **`--tail` ne fonctionne pas** : Necessite PowerShell (Windows). Alternative manuelle : `powershell -Command "Get-Content -Path 'logs\daynimal_TIMESTAMP.log' -Wait"`

## Gestion des logs

```bash
# Supprimer tous les logs
del logs\*.log                     # Windows
rm logs/*.log                      # Linux/Mac

# Garder seulement les 5 derniers (PowerShell)
Get-ChildItem logs\*.log | Sort-Object -Property LastWriteTime -Descending | Select-Object -Skip 5 | Remove-Item
```
