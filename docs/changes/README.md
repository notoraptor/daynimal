# Historique des changements et rapports techniques

Ce dossier contient les rapports détaillés des améliorations, optimisations et corrections apportées au projet Daynimal.

## 📋 Index des rapports (ordre chronologique)

### Février 2026

#### [2026-02-performance-sql.md](2026-02-performance-sql.md)
**Optimisation des performances SQL**
- **Problème** : Temps de chargement de 25-28 secondes pour "animal du jour"
- **Solution** : Optimisation des requêtes MIN/MAX sans filtres sur colonnes non indexées
- **Résultat** : Réduction de 93% (25s → 1.8s)
- **Impact** : Expérience utilisateur grandement améliorée

#### [2026-02-error-logging.md](2026-02-error-logging.md)
**Système de logging des erreurs**
- **Problème** : Erreurs visibles uniquement dans l'UI Flet, pas dans les logs
- **Solution** : Ajout de logging complet avec stack traces dans tous les blocs except
- **Résultat** : Débogage facilité, erreurs tracées avec contexte complet
- **Impact** : Maintenance et diagnostic simplifiés

#### [2026-02-parallel-api-calls.md](2026-02-parallel-api-calls.md)
**Parallélisation des appels API**
- **Problème** : Appels séquentiels à Wikidata, Wikipedia et Commons
- **Solution** : ThreadPoolExecutor pour paralléliser Wikidata et Wikipedia
- **Résultat** : Réduction de ~33% du temps d'enrichissement
- **Impact** : Chargement plus rapide des données externes

#### [2026-02-08-refactor-distribution-pipeline.md](2026-02-08-refactor-distribution-pipeline.md)
**Plan de refactoring du pipeline de distribution**
- **Problème** : Scripts mélangés (extraction, filtrage, import) et noms TAXREF absents des TSV
- **Solution** : Séparer en `generate-distribution` + `build-db`, intégrer TAXREF dans les TSV
- **Résultat** : Pipeline clair en deux étapes, noms TAXREF fusionnés dès la génération
- **Impact** : Fichiers de distribution mobile 6x plus légers, +104% de noms français

#### [2026-02-08-refactor-distribution-pipeline-results.md](2026-02-08-refactor-distribution-pipeline-results.md)
**Résultats du refactoring du pipeline de distribution**
- **Problème** : Mesurer l'impact réel du refactoring
- **Solution** : Génération et comparaison des nouvelles DBs (full et minimal)
- **Résultat** : DB minimale -26% (117 MB), DB full -40% (1.08 GB), noms FR +104%
- **Impact** : 100 tests passent, aucune régression

## 📊 Vue d'ensemble des améliorations

### Performance
- ⚡ Chargement des animaux : **93% plus rapide** (25s → 2s)
- 🔄 Appels API parallélisés : **33% plus rapide**
- 🎯 Temps de réponse global : **< 2 secondes**

### Qualité du code
- 🔍 Logging complet avec stack traces
- 🐛 Correction de bugs (ImageFit, artist/author)
- 📱 Navigation fixe et ergonomique

### Documentation
- 📚 Guides techniques détaillés
- 🔧 Patterns de débogage documentés
- 💡 Leçons apprises sauvegardées

## 🔗 Liens utiles

### Documentation générale
- [Guide API Flet](../FLET_API_GUIDE.md) - Référence des APIs Flet utilisées
- [Roadmap Mobile/Desktop](../MOBILE_DESKTOP_ROADMAP.md) - Feuille de route

### Mémoire et apprentissage
- [Mémoire Auto](../../memory/MEMORY.md) - Leçons globales du projet
- [CLAUDE.md](../../CLAUDE.md) - Instructions pour Claude Code

## 📝 Convention de nommage

Les fichiers de ce dossier suivent la convention :
```
YYYY-MM-<description-courte>.md
```

Exemples :
- `2026-02-performance-sql.md` - Optimisation SQL (février 2026)
- `2026-03-feature-search.md` - Nouvelle fonctionnalité (mars 2026)

## 🆕 Ajouter un nouveau rapport

Lors de l'ajout d'un nouveau rapport :
1. Créer le fichier avec le format de date approprié
2. Ajouter une entrée dans ce README (section chronologique)
3. Inclure : problème, solution, résultat, impact
4. Ajouter des liens vers les fichiers modifiés si pertinent

## 📈 Statistiques

**Total des rapports** : 5
**Dernière mise à jour** : 8 février 2026
**Améliorations documentées** : Performance SQL, Logging, Parallélisation, Refactoring pipeline
