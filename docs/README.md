# Documentation Daynimal

Documentation technique et guides pour le projet Daynimal.

## 📁 Organisation

### 📊 Rapports de changements
**[changes/](changes/)** - Historique détaillé des améliorations et optimisations
- Rapports techniques organisés par date (YYYY-MM-description.md)
- [Index complet des rapports](changes/README.md)
- Performance, bugs, nouvelles fonctionnalités

### 📱 Guides Flet
- **[FLET_API_GUIDE.md](FLET_API_GUIDE.md)** - Référence des APIs Flet utilisées dans le projet
  - Couleurs, icônes, composants confirmés
  - Patterns et bonnes pratiques
  - Erreurs courantes à éviter

### 🔍 Revue de code
- **[CODE_REVIEW_2026-02.md](CODE_REVIEW_2026-02.md)** - Analyse complete du code (fevrier 2026)
  - Bugs critiques identifies (6) et corrections recommandees
  - Couverture de tests (27%) et trous critiques
  - Avis sur la roadmap et resequenciation recommandee
  - Plan d'action : semaine de stabilisation

### 🗺️ Roadmap
- **[MOBILE_DESKTOP_ROADMAP.md](MOBILE_DESKTOP_ROADMAP.md)** - Feuille de route du développement
  - Fonctionnalités prévues
  - Architecture cible
  - Priorisation des tâches

## 🔗 Liens vers d'autres documentations

### Documentation projet
- [CLAUDE.md](../CLAUDE.md) - Instructions pour Claude Code
- [README.md](../README.md) - Documentation utilisateur principale

### Code et architecture
- [daynimal/](../daynimal/) - Code source avec docstrings
- [tests/](../tests/) - Tests unitaires documentés

### Debugging
- [debug/](../debug/) - Outils et guides de debogage

## 📝 Conventions

### Rapports de changements
Les fichiers dans `changes/` suivent la convention :
```
YYYY-MM-<description>.md
```
Exemple : `2026-02-performance-sql.md`

### Structure des rapports
Chaque rapport technique doit inclure :
- **Problème** : Situation initiale
- **Solution** : Approche adoptée
- **Résultat** : Mesures/gains obtenus
- **Impact** : Effet sur le projet

## 🆕 Ajouter de la documentation

### Pour un nouveau guide
1. Créer le fichier `.md` dans `docs/`
2. Ajouter une entrée dans ce README
3. Mettre à jour [CLAUDE.md](../CLAUDE.md) si pertinent

### Pour un rapport de changement
1. Créer le fichier dans `docs/changes/` avec le format de date
2. Ajouter une entrée dans [changes/README.md](changes/README.md)
3. Inclure problème, solution, résultat, impact

## 📊 Statistiques

**Guides** : 3 (Flet API, Roadmap, Code Review)
**Rapports de changements** : 4 (voir [changes/](changes/))
**Dernière mise à jour** : 7 février 2026
