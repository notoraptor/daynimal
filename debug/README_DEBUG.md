# 🐛 Système de Debugging Daynimal Flet

> **TL;DR** : Lance `python run_app_debug.py --quiet`, puis utilise `python debug_filter.py` pour voir les logs.

## 🎯 Problème résolu

Les applications Flet sont difficiles à debugger :
- Les `print()` n'apparaissent pas
- Les erreurs peuvent être silencieuses
- Difficile de tracer l'exécution async

**Solution** : Système de logging automatique avec fichiers horodatés + outils de filtrage.

---

## 📦 Outils disponibles

### 1. `run_app_debug.py` - Launcher avec logging

```bash
# Mode recommandé (logs dans fichier, console propre)
python run_app_debug.py --quiet

# Mode verbose (logs dans fichier + console)
python run_app_debug.py

# Mode web
python run_app_debug.py --web
```

**Résultat** : Crée `logs/daynimal_YYYYMMDD_HHMMSS.log` automatiquement

---

### 2. `debug_filter.py` - Filtre intelligent ⭐

**L'outil le plus utile !** Élimine 87% du bruit Flet.

```bash
# Voir les logs filtrés
python debug_filter.py

# Seulement les erreurs
python debug_filter.py --errors-only

# Suivre en temps réel
python debug_filter.py --tail

# Chercher un mot-clé
python debug_filter.py --search "wikidata"

# Statistiques
python debug_filter.py --stats
```

---

### 3. `view_logs.py` - Utilitaire logs

```bash
# Voir le dernier log (brut, sans filtre)
python view_logs.py

# Lister tous les logs
python view_logs.py --list

# Tout concaténer
python view_logs.py --all
```

---

## 📊 Ce qui est loggé automatiquement

✅ **Démarrage/Arrêt** de l'application
✅ **Navigation** entre vues (Today, History, Search, Stats)
✅ **Chargement d'animaux** avec nom (mode today/random)
✅ **Recherches** avec nombre de résultats
✅ **Erreurs** avec stack traces complètes
✅ **Appels réseau** (httpcore debug)

**Exemple de logs** :
```
2026-02-07 03:50:40 - daynimal - INFO - Daynimal Flet Application Starting
2026-02-07 03:50:41 - daynimal - INFO - DaynimalApp initialized
2026-02-07 03:50:47 - daynimal - INFO - View changed to: Today
2026-02-07 03:51:19 - daynimal - INFO - Loading animal (today)...
2026-02-07 03:51:31 - daynimal - INFO - Loading animal (today): Panthera leo
2026-02-07 03:52:00 - daynimal - INFO - Search: 'lion' - 5 results
2026-02-07 03:52:15 - daynimal - ERROR - Error in load_animal: ConnectionError...
```

---

## 🔥 Workflow recommandé

### Développement quotidien

```bash
python run_app_debug.py --quiet
```

Aucun log dans la console, app propre. Les logs sont dans `logs/`.

### Debugger un problème

```bash
# Reproduire le problème dans l'app
# Puis voir les logs filtrés
python debug_filter.py
```

### Analyser une erreur

```bash
python debug_filter.py --errors-only
```

### Suivre en temps réel

```bash
# Terminal 1
python run_app_debug.py

# Terminal 2
python debug_filter.py --tail
```

---

## 📈 Statistiques (test réel)

**Session de 30 secondes** :
- Lignes totales : 1,375
- Logs Daynimal : 32 (2.3%)
- Logs Flet internes : 1,208 (87.9%)

➡️ **Sans filtre** : 1,375 lignes difficiles à lire
➡️ **Avec `debug_filter.py`** : 32 lignes pertinentes

---

## 🎨 Comment ça marche ?

### Architecture

```
run_app_debug.py
    └─> Initialise FletDebugger (daynimal/debug.py)
         └─> Configure logging vers logs/daynimal_TIMESTAMP.log
              └─> Passe debugger à l'app via page.data

app.py
    └─> Récupère debugger depuis page.data
         └─> Log les événements aux points clés
              └─> Navigation, chargement, recherche, erreurs
```

### Intégration dans app.py

Le code a été modifié pour logger automatiquement :

```python
# Exemple dans app.py
if self.debugger:
    self.debugger.log_view_change("Today")

if self.debugger:
    self.debugger.log_animal_load("today", animal.display_name)

if self.debugger:
    self.debugger.log_error("load_animal", error)
```

**Important** : L'app fonctionne avec ou sans debugger (import optionnel).

---

## 🆘 Cas d'usage

### Cas 1 : L'animal ne se charge pas

```bash
python run_app_debug.py --quiet
# Cliquer "Animal du jour" dans l'app
python debug_filter.py
```

Chercher :
```
Loading animal (today)...
# Si succès:
Loading animal (today): Panthera leo
# Si échec:
ERROR - Error in load_animal_for_today_view
```

### Cas 2 : La recherche ne retourne rien

```bash
python debug_filter.py --search "Search"
```

Voir :
```
Search: 'lion' - 0 results  ← Problème
Search: 'lion' - 5 results  ← OK
```

### Cas 3 : Crash silencieux

```bash
python debug_filter.py --errors-only
```

Voir la stack trace complète.

---

## 📚 Documentation

| Fichier | Contenu |
|---------|---------|
| **`README_DEBUG.md`** | Ce fichier (vue d'ensemble) |
| **`QUICK_START_DEBUG.md`** | Usage rapide avec exemples |
| **`DEBUGGING.md`** | Guide complet et détaillé |
| **`TEST_RESULTS.md`** | Résultats des tests |

---

## 🔧 Bonus : Analyse de repository.py

Un changement a été fait dans `repository.py` pour **paralléliser les appels API** :

**Avant (séquentiel)** :
```
fetch_wikidata()    # 1s
fetch_wikipedia()   # 1s
fetch_images()      # 1s
Total: 3s
```

**Après (parallèle)** :
```python
with ThreadPoolExecutor(max_workers=2) as executor:
    futures['wikidata'] = executor.submit(fetch_wikidata)
    futures['wikipedia'] = executor.submit(fetch_wikipedia)
    # Attendre les deux
fetch_images()  # Toujours après (dépend de wikidata)
Total: ~2s (33% plus rapide!)
```

Tu peux voir les appels parallèles dans les logs :
```bash
python debug_filter.py --search "httpcore.connection"
```

---

## ✅ Checklist

- [x] Système de logging fonctionnel
- [x] Logs automatiques dans `logs/`
- [x] Filtre intelligent pour éliminer le bruit Flet
- [x] Scripts utilitaires (view_logs, debug_filter)
- [x] Intégration dans app.py (non-intrusive)
- [x] Documentation complète
- [x] Tests réalisés avec succès
- [x] Gestion encodage Windows

---

## 🎉 Conclusion

Le système est **prêt à l'emploi** et **non-intrusif**.

**Commande par défaut** :
```bash
python run_app_debug.py --quiet
```

**Pour voir ce qui se passe** :
```bash
python debug_filter.py
```

C'est tout ! 🚀
