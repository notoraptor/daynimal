# PhyloPic - Silhouettes Animales

Guide pour le téléchargement et la mise à jour des silhouettes PhyloPic utilisées dans Daynimal.

---

## Table des Matières

1. [Démarrage Rapide](#démarrage-rapide)
2. [Qu'est-ce que PhyloPic ?](#quest-ce-que-phylopic-)
3. [Licence et Attribution](#licence-et-attribution)
4. [Architecture Technique](#architecture-technique)
5. [Maintenance](#maintenance)
6. [Dépannage](#dépannage)
7. [Références](#références)

---

## Démarrage Rapide

### Ce que vous avez déjà

Le fichier `daynimal/resources/phylopic_metadata.csv` est **commité dans le dépôt**. Il contient ~11 950 entrées de silhouettes. Aucune action n'est nécessaire pour utiliser PhyloPic — ça fonctionne out of the box.

### Mettre à jour les silhouettes

Si vous voulez rafraîchir les données (nouvelles silhouettes ajoutées sur PhyloPic) :

```bash
# 1. Télécharger toutes les silhouettes depuis l'API PhyloPic (~30 min)
uv run python scripts/download_phylopic.py

# 2. Extraire le CSV du zip généré
python -c "
import zipfile
zipfile.ZipFile('data/phylopic_dump.zip').extract('phylopic_metadata.csv', 'daynimal/resources')
"

# 3. Vérifier
uv run daynimal-app  # Les silhouettes sont visibles dans les fiches animales
```

**Temps total :** ~30 minutes (téléchargement API)
**Résultat :** CSV mis à jour avec les dernières silhouettes PhyloPic

---

## Qu'est-ce que PhyloPic ?

**PhyloPic** (https://www.phylopic.org/) est une base de données libre de silhouettes d'organismes vivants.

### Caractéristiques

| Aspect | Détails |
|--------|---------|
| Nombre de silhouettes | ~12 000 |
| Format | SVG (vectoriel) |
| Couverture | Tous les êtres vivants (animaux, plantes, champignons) |
| Coût | Gratuit et open data |
| Licences | Variées (CC0, CC-BY, CC-BY-SA, etc.) |

### Pourquoi PhyloPic dans Daynimal ?

PhyloPic sert de **fallback visuel** quand aucune photo n'est disponible via Wikimedia Commons ou GBIF Media. Plutôt qu'une fiche vide, l'utilisateur voit au moins une silhouette de l'animal (ou d'un taxon parent).

---

## Licence et Attribution

### Licences Acceptées

Le code filtre automatiquement les licences. Seules les licences compatibles avec un usage libre sont acceptées :

| Licence | Acceptée | Attribution requise |
|---------|----------|---------------------|
| CC0 / Public Domain | Oui | Non |
| CC-BY | Oui | Oui |
| CC-BY-SA | Oui | Oui |
| CC-BY-NC | **Non** | - |
| CC-BY-ND | **Non** | - |

Le filtrage est fait dans `phylopic_local.py` (`_parse_phylopic_license()`).

### Attribution

L'attribution est incluse automatiquement dans chaque `CommonsImage` retournée, avec :
- Le nom de l'auteur (champ `attribution` du CSV)
- La licence
- Un lien vers la page source PhyloPic

---

## Architecture Technique

### Vue d'ensemble du pipeline

```
[PhyloPic API]                       [App Daynimal]
     |                                     |
     v                                     v
scripts/download_phylopic.py     daynimal/sources/phylopic_local.py
     |                                     |
     v                                     |
data/phylopic_dump.zip                     |
     |                                     |
     v                                     v
daynimal/resources/           ← lecture →  CSV lookup par nom de taxon
  phylopic_metadata.csv                    (genus → family → order → ...)
  (commité dans git)
```

### Fichiers impliqués

| Fichier | Rôle |
|---------|------|
| `scripts/download_phylopic.py` | Télécharge toutes les silhouettes + métadonnées depuis l'API |
| `data/phylopic_dump.zip` | Archive complète (SVGs + CSV), gitignored |
| `daynimal/resources/phylopic_metadata.csv` | CSV de métadonnées, commité dans le repo |
| `daynimal/sources/phylopic_local.py` | Lookup local par nom de taxon au runtime |
| `daynimal/sources/legacy/phylopic.py` | Ancien client API (remplacé par le lookup local) |

### Indépendance du pipeline DB

PhyloPic est **complètement indépendant** du pipeline GBIF/TAXREF :
- Pas de lien avec `generate-distribution`, `build-db`, `init-fts`, `setup`, ou `rebuild`
- Pas d'entry point dans `pyproject.toml` — c'est un script lancé manuellement
- Le CSV est un asset statique dans `resources/`, pas dans la base SQLite

### Fonctionnement du lookup local

`phylopic_local.py` charge le CSV en mémoire (lazy singleton) et cherche une silhouette en remontant la hiérarchie taxonomique :

1. Nom d'espèce exact (ex: `panthera leo`)
2. Genre (`panthera`)
3. Famille (`felidae`)
4. Ordre (`carnivora`)
5. Classe (`mammalia`)
6. Embranchement (`chordata`)

Chaque nom est cherché d'abord dans `specific_node`, puis dans `general_node` du CSV.

---

## Maintenance

### Quand mettre à jour ?

PhyloPic n'a pas de cycle de release régulier. Une mise à jour occasionnelle (tous les quelques mois) suffit pour capter les nouvelles silhouettes.

### Procédure complète

```bash
# 1. Télécharger depuis l'API (~30 min, ~12 000 images)
uv run python scripts/download_phylopic.py

# 2. Vérifier le résultat
python -c "
import zipfile
zf = zipfile.ZipFile('data/phylopic_dump.zip')
svg_count = sum(1 for n in zf.namelist() if n.endswith('.svg'))
print(f'{svg_count} SVGs dans le zip')
"

# 3. Extraire le CSV dans resources/
python -c "
import zipfile
zipfile.ZipFile('data/phylopic_dump.zip').extract('phylopic_metadata.csv', 'daynimal/resources')
"

# 4. Commiter le CSV mis à jour
git add daynimal/resources/phylopic_metadata.csv
git commit -m "Update PhyloPic metadata CSV"
```

### Vérification

```bash
# Compter les entrées dans le CSV
python -c "
lines = open('daynimal/resources/phylopic_metadata.csv', encoding='utf-8').readlines()
print(f'{len(lines) - 1} entrées (hors header)')
"
```

---

## Dépannage

### Le script download_phylopic.py est lent

**C'est normal.** Le script télécharge ~12 000 silhouettes individuellement depuis l'API avec un délai de 50ms entre chaque requête. Comptez ~30 minutes.

### Erreurs "Rate limited" dans les logs

Le script gère automatiquement les erreurs 429 (rate limiting) avec des retries. Quelques warnings sont normaux et n'affectent pas le résultat final.

### Silhouette non trouvée pour un animal

**C'est normal.** PhyloPic ne couvre pas tous les taxons. Le lookup remonte la hiérarchie taxonomique, mais certains embranchements n'ont aucune silhouette.

### Le CSV n'est pas à jour après download

Vérifiez que vous avez bien extrait le CSV du zip vers `daynimal/resources/` (étape 2 de la procédure). Le zip est dans `data/` (gitignored), le CSV doit être dans `daynimal/resources/` (commité).

---

## Références

- **Site officiel :** https://www.phylopic.org/
- **API documentation :** https://api.phylopic.org/
- **GitHub :** https://github.com/keesey/phylopic
- **Licence des données :** Variée par image (CC0, CC-BY, CC-BY-SA)
- **Issues Daynimal :** https://github.com/notoraptor/daynimal/issues

---

## Voir Aussi

- [TAXREF Integration](TAXREF.md) - Noms français depuis TAXREF
- [Distribution Release](DISTRIBUTION_RELEASE.md) - Publication des fichiers DB
- [Mobile Roadmap](MOBILE_DESKTOP_ROADMAP.md) - Feuille de route
