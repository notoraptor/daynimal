# 🐛 Système de Debugging Daynimal Flet

Ce dossier contient tous les outils nécessaires pour debugger l'application Flet Daynimal.

## 🚀 Quick Start

```bash
# Depuis la racine du projet

# 1. Lancer l'app avec debug
python debug/run_app_debug.py --quiet

# 2. Voir les logs (filtrés)
python debug/debug_filter.py
```

## 📦 Contenu du dossier

### Scripts exécutables

- **`run_app_debug.py`** - Launcher avec logging automatique
- **`debug_filter.py`** ⭐ - Filtre intelligent (élimine 87% du bruit Flet)
- **`view_logs.py`** - Utilitaire pour voir/lister les logs

### Documentation

- **`README_DEBUG.md`** ⭐ - **Lire en premier** - Vue d'ensemble complète
- **`QUICK_START_DEBUG.md`** - Usage rapide avec exemples
- **`DEBUGGING.md`** - Guide détaillé (350+ lignes)
- **`TEST_RESULTS.md`** - Résultats des tests

## 🎯 Commandes principales

Toutes les commandes doivent être exécutées **depuis la racine du projet** :

```bash
# Lancer l'app avec debug (mode recommandé)
python debug/run_app_debug.py --quiet

# Voir les logs filtrés
python debug/debug_filter.py

# Voir seulement les erreurs
python debug/debug_filter.py --errors-only

# Suivre les logs en temps réel
python debug/debug_filter.py --tail

# Statistiques
python debug/debug_filter.py --stats

# Lister tous les logs
python debug/view_logs.py --list
```

## 📊 Ce qui est loggé automatiquement

✅ Démarrage/Arrêt de l'application
✅ Navigation entre vues (Today, History, Search, Stats)
✅ Chargement d'animaux avec nom (mode today/random)
✅ Recherches avec nombre de résultats
✅ Erreurs avec stack traces complètes
✅ Appels réseau (httpcore debug)

## 📁 Emplacement des logs

Les logs sont écrits dans `logs/daynimal_YYYYMMDD_HHMMSS.log` à la racine du projet.

## 📚 Documentation

Pour plus de détails, consulter :
1. **`README_DEBUG.md`** - Commencer ici
2. **`QUICK_START_DEBUG.md`** - Exemples pratiques
3. **`DEBUGGING.md`** - Guide complet

---

**Note** : Le module Python `daynimal/debug.py` est utilisé en interne par ces scripts mais peut aussi être importé directement dans d'autres modules si nécessaire.
