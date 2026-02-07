# 🚀 Quick Start - Debugging Daynimal Flet

## ⚡ Usage rapide (TL;DR)

```bash
# Lancer l'app avec debug
python run_app_debug.py --quiet

# Voir les logs filtrés (sans bruit Flet)
python debug_filter.py

# Voir seulement les erreurs
python debug_filter.py --errors-only

# Suivre les logs en temps réel
python debug_filter.py --tail

# Statistiques des logs
python debug_filter.py --stats
```

## 📊 Résultat des statistiques

Sur un test de 30 secondes :
- **Total**: 1,375 lignes de logs
- **Logs Daynimal**: 32 (2.3%)
- **Logs Flet internes**: 1,208 (87.9%)

➡️ **Conclusion** : Utilisez `debug_filter.py` pour voir uniquement les logs applicatifs !

## 🎯 Événements capturés automatiquement

✅ **Navigation** : Changements de vue (Today, History, Search, Stats)
✅ **Chargements** : Animaux du jour / aléatoires avec nom
✅ **Recherches** : Requête + nombre de résultats
✅ **Erreurs** : Stack traces complètes avec contexte
✅ **Performance** : Appels réseau parallèles (httpcore)

## 🔍 Exemples pratiques

### Débugger un animal qui ne charge pas

```bash
# Lancer l'app
python run_app_debug.py --quiet

# Dans l'app : cliquer "Animal du jour"

# Voir les logs
python debug_filter.py
```

Cherchez :
```
Loading animal (today)...
Loading animal (today): Panthera leo  ← succès
```

### Voir seulement les problèmes

```bash
python debug_filter.py --errors-only
```

### Chercher un mot spécifique

```bash
python debug_filter.py --search "wikidata"
python debug_filter.py --search "enrichment"
```

## 📁 Fichiers créés

| Fichier | Description |
|---------|-------------|
| `daynimal/debug.py` | Module de logging |
| `run_app_debug.py` | Launcher avec debug |
| `debug_filter.py` | Filtre intelligent des logs |
| `view_logs.py` | Utilitaire pour voir/lister logs |
| `DEBUGGING.md` | Guide complet (documentation) |
| `TEST_RESULTS.md` | Résultats des tests |

## 🔧 Analyse du changement dans repository.py

**Objectif** : Paralléliser les appels API externes

**Avant** (séquentiel) :
```python
wikidata = fetch_wikidata()   # 1s
wikipedia = fetch_wikipedia()  # 1s
images = fetch_images()        # 1s
# Total: 3s
```

**Après** (parallèle) :
```python
with ThreadPoolExecutor(max_workers=2) as executor:
    wikidata_future = executor.submit(fetch_wikidata)
    wikipedia_future = executor.submit(fetch_wikipedia)
    # Attendre les deux en parallèle
images = fetch_images()  # Toujours après (dépend de wikidata)
# Total: ~2s
```

**Gain** : ~33% de réduction du temps d'enrichissement

## 💡 Recommandations

### Pour le développement quotidien
```bash
python run_app_debug.py --quiet
```
- Pas de pollution dans la console
- Logs complets disponibles dans `logs/`

### Pour debugger un problème
```bash
# Terminal 1: App
python run_app_debug.py

# Terminal 2: Logs filtrés
python debug_filter.py --tail
```

### Pour analyser les performances
```bash
python debug_filter.py --search "httpcore"
```
Vous verrez les connexions réseau parallèles.

## 📚 Documentation complète

➡️ Voir `DEBUGGING.md` pour le guide complet avec tous les détails.

---

**Note** : Le système de logging est optionnel. Pour lancer l'app normalement sans logs :
```bash
python daynimal/app.py
```
