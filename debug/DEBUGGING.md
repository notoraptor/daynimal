# 🐛 Guide de Debugging de Daynimal Flet

Ce guide explique comment utiliser le système de debugging intégré pour tester et debugger l'application Flet Daynimal.

## 🎯 Problème résolu

Les applications Flet ont des particularités qui rendent le debugging difficile :
- Les `print()` n'apparaissent pas dans l'UI
- Les erreurs peuvent être silencieuses
- Difficile de suivre le flux d'exécution des opérations async

**Solution** : Système de logging centralisé avec fichiers de logs horodatés.

## 🚀 Utilisation rapide

### Méthode 1 : Lancement avec debug complet

```bash
# Lancer l'app avec logs dans console + fichier
python run_app_debug.py

# Lancer l'app sans logs console (fichier seulement)
python run_app_debug.py --quiet

# Lancer en mode web
python run_app_debug.py --web
```

À chaque lancement, un nouveau fichier de log est créé dans `logs/` avec timestamp :
```
logs/daynimal_20260207_143025.log
```

### Méthode 2 : Suivre les logs en temps réel

**Option A - Fenêtre séparée (Windows)** :
```bash
python run_app_debug.py --tail
```

Cela ouvre une nouvelle fenêtre PowerShell qui affiche les logs en temps réel.

**Option B - Terminal séparé** :
```bash
# Terminal 1 : Lancer l'app
python run_app_debug.py --quiet

# Terminal 2 : Suivre les logs
# (Copier le chemin affiché au démarrage)
powershell -Command "Get-Content -Path 'logs\daynimal_TIMESTAMP.log' -Wait"
```

## 📋 Que contiennent les logs ?

Le système capture automatiquement :

### ✅ Événements capturés

1. **Démarrage/Arrêt de l'app**
   ```
   2026-02-07 14:30:25 - daynimal - INFO - Daynimal Flet Application Starting
   ```

2. **Navigation entre vues**
   ```
   2026-02-07 14:30:30 - daynimal - INFO - View changed to: History
   ```

3. **Chargement d'animaux**
   ```
   2026-02-07 14:30:35 - daynimal - INFO - Loading animal (today)...
   2026-02-07 14:30:38 - daynimal - INFO - Loading animal (today): Panthera leo
   ```

4. **Recherches**
   ```
   2026-02-07 14:31:00 - daynimal - DEBUG - Search started: 'lion'
   2026-02-07 14:31:01 - daynimal - INFO - Search: 'lion' - 5 results
   ```

5. **Erreurs avec stack traces**
   ```
   2026-02-07 14:32:00 - daynimal - ERROR - Error in load_animal_for_today_view (today): ConnectionError: ...
   Traceback (most recent call last):
     File "...", line X, in load_animal_for_today_view
       ...
   ```

6. **Exceptions non capturées**
   ```
   2026-02-07 14:33:00 - daynimal - CRITICAL - Uncaught exception
   ```

## 🔧 Ajouter des logs personnalisés

### Dans `app.py`

```python
# Les imports sont déjà faits
# Utiliser self.debugger dans la classe DaynimalApp

if self.debugger:
    self.debugger.logger.info("Mon message info")
    self.debugger.logger.debug("Détails de debug")
    self.debugger.logger.warning("Avertissement")
    self.debugger.logger.error("Erreur")
```

### Dans d'autres modules

```python
from daynimal.debug import get_debugger

debugger = get_debugger()
debugger.logger.info("Message depuis un autre module")
```

### Fonctions raccourcies

```python
from daynimal.debug import log_info, log_error, log_debug

log_info("Opération réussie")
log_error("Une erreur est survenue")
log_debug(f"Variable x = {x}")
```

## 📊 Structure des fichiers de log

```
logs/
├── daynimal_20260207_143025.log  # Premier lancement du jour
├── daynimal_20260207_151230.log  # Deuxième lancement
└── daynimal_20260207_163445.log  # Troisième lancement
```

**Format des lignes** :
```
TIMESTAMP - LOGGER_NAME - LEVEL - MESSAGE
2026-02-07 14:30:25 - daynimal - INFO - View changed to: Today
```

## 🧪 Debugging de problèmes spécifiques

### Problème : L'animal ne se charge pas

1. Lancer avec `python run_app_debug.py`
2. Cliquer sur "Animal du jour"
3. Vérifier les logs pour :
   - `Loading animal (today)...` (appel initié)
   - Erreurs de base de données
   - Erreurs d'API (Wikidata, Wikipedia, Commons)
   - `Loading animal (today): NOM` (succès)

### Problème : La recherche ne fonctionne pas

1. Lancer avec `python run_app_debug.py`
2. Taper dans le champ de recherche
3. Vérifier les logs pour :
   - `Search started: 'QUERY'`
   - Requête SQL FTS5
   - `Search: 'QUERY' - N results`

### Problème : Crash silencieux

1. Lancer avec `python run_app_debug.py`
2. Reproduire le crash
3. Chercher dans les logs :
   - `CRITICAL - Uncaught exception`
   - Stack trace complète

## 💡 Conseils pratiques

### Mode quiet pour performances

Si les logs console ralentissent l'app :
```bash
python run_app_debug.py --quiet
```

Les logs sont toujours écrits dans le fichier.

### Nettoyage des logs

Les logs s'accumulent dans `logs/`. Pour nettoyer :
```bash
# Windows
del logs\*.log

# PowerShell
Remove-Item logs\*.log

# Garder seulement les 5 derniers
Get-ChildItem logs\*.log | Sort-Object -Property LastWriteTime -Descending | Select-Object -Skip 5 | Remove-Item
```

### Filtrer les logs

Pour voir seulement les erreurs :
```bash
# Windows PowerShell
Select-String -Path logs\daynimal_*.log -Pattern "ERROR|CRITICAL"

# Afficher les 50 dernières lignes
Get-Content logs\daynimal_TIMESTAMP.log | Select-Object -Last 50
```

## 📝 Architecture du système de debug

```
run_app_debug.py          # Script de lancement avec debug
    └─> debug.py          # Module de logging
         └─> FletDebugger # Classe principale
              ├─> File handler (logs/*.log)
              └─> Console handler (optionnel)

app.py                    # Application Flet
    └─> self.debugger     # Instance récupérée via page.data
         └─> Logging des événements UI
```

## 🔥 Mode production

Pour lancer l'app sans debug (mode normal) :
```bash
# Méthode classique
uv run python -m daynimal.app

# Ou directement
python daynimal/app.py
```

Aucun log ne sera généré.

## 🆘 Troubleshooting

### Les logs ne s'affichent pas dans la console

- Vérifiez que vous utilisez `run_app_debug.py` (pas `app.py` directement)
- Vérifiez que `--quiet` n'est pas activé

### Le fichier de log est vide

- Peut-être que l'app a crashé avant l'écriture
- Vérifiez les permissions sur le dossier `logs/`

### `--tail` ne fonctionne pas

- Nécessite PowerShell (Windows)
- Utilisez la méthode manuelle avec 2 terminaux

## 📚 Références

- [Flet Documentation](https://flet.dev/)
- [Python logging](https://docs.python.org/3/library/logging.html)
- [Debugging Async Python](https://realpython.com/async-io-python/#debugging)
