# Audit UI/UX

Historique des revues UI et décisions de design.
Outil : `uv run python scripts/screenshot_ui.py` (Playwright headless + Flet web mode → `tmp/screenshots/`).

---

## Audit 2026-03-14 — Polissage desktop (tous points résolus)

### Décisions de design

| Sujet | Décision | Fichier(s) |
|-------|----------|------------|
| Alignement titres | `view_header()` : layout 3 colonnes `[spacer \| titre \| actions]` quand il y a des actions, centré sinon | `widgets.py` |
| Écran d'accueil Découverte | CTA central `FilledButton` "Découvrir un animal" + icône PETS (remplace message passif) | `today_view.py` |
| Suppression dans listes | SnackBar "Annuler" + X (pattern undo Material Design), pas de dialog bloquant | `history_view.py`, `favorites_view.py` |
| Cartes Favoris | Coeur rouge conservé (repère visuel), texte "Favori" remplacé par date d'ajout | `animal_card.py` |
| Bouton recherche | Flèche `ARROW_FORWARD` (distingue le CTA de la loupe décorative dans le champ) | `search_view.py` |
| Stats utilisateur | Cartes "Animaux consultés" et "Favoris" ajoutées, "Animaux enrichis" retiré (technique, pas pertinent pour l'utilisateur) | `stats_view.py`, `repository.py` |
| Navbar | `ONLY_SHOW_SELECTED` — label visible uniquement sur l'onglet actif (compromis lisibilité/espace avec 6 onglets) | `app_controller.py` |
| Crédits | En bas de Paramètres (scroll) — placement standard, pas de changement nécessaire | `settings_view.py` |

### Points évalués sans changement

- Pagination Historique/Favoris : fonctionne, simplement hors-écran initial (scroll)
- État vide Recherche : bien géré (icône + texte explicatif)
- Structure Paramètres : sections claires (Préférences, Notifications, Cache, Crédits, DB)
