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

- **[FLET_APP_VALIDATION.md](FLET_APP_VALIDATION.md)** - Checklist de validation de l'app
  - Tests fonctionnels
  - Validation UI/UX
  - Performance et stabilité

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
- [debug/](../debug/) - Outils et guides de débogage
- [memory/MEMORY.md](../memory/MEMORY.md) - Leçons apprises

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

**Guides** : 3 (Flet API, Validation, Roadmap)
**Rapports de changements** : 4 (voir [changes/](changes/))
**Dernière mise à jour** : 7 février 2026
