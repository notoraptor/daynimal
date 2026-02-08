# TAXREF - Noms Vernaculaires Français

Guide complet pour intégrer les noms français depuis TAXREF, le référentiel taxonomique officiel français.

---

## Table des Matières

1. [Démarrage Rapide](#démarrage-rapide)
2. [Qu'est-ce que TAXREF ?](#quest-ce-que-taxref-)
3. [Licence et Attribution](#licence-et-attribution)
4. [Documentation Technique](#documentation-technique)
5. [Dépannage](#dépannage)
6. [Maintenance](#maintenance)
7. [Références](#références)

---

## Démarrage Rapide

### Ce que vous allez obtenir
- **~45 000 noms français** pour les animaux
- **Temps requis :** 10-15 minutes
- **Couverture française :** 0.4% -> 35%

### Étapes

#### 1. Télécharger TAXREF

**Organisation des fichiers :**
- Placez le fichier TAXREF téléchargé dans le dossier **`data/`** (créez-le si nécessaire)
- Les fichiers extraits du ZIP peuvent aller dans **`tmp/`** (optionnel)
- Ces dossiers sont dans `.gitignore` et ne seront jamais commités

**Téléchargement :**

Visitez : https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353

Téléchargez **"TAXREF_v18_2025.zip"** (~100 MB) et extrayez **"TAXREFv18.txt"** dans `data/`.

**Alternative avec ligne de commande :**
```bash
# Créer le dossier data/ si nécessaire
mkdir -p data

# Windows PowerShell
Invoke-WebRequest -Uri "https://assets.patrinat.fr/files/referentiel/TAXREF_v18_2025.zip" -OutFile "data/TAXREF_v18_2025.zip"
Expand-Archive -Path "data/TAXREF_v18_2025.zip" -DestinationPath "tmp/"
Copy-Item "tmp/TAXREFv18.txt" "data/"

# Linux/Mac
wget https://assets.patrinat.fr/files/referentiel/TAXREF_v18_2025.zip -O data/TAXREF_v18_2025.zip
unzip data/TAXREF_v18_2025.zip -d tmp/
cp tmp/TAXREFv18.txt data/
```

#### 2. Générer les fichiers de distribution avec TAXREF

Les noms TAXREF sont fusionnés directement dans les fichiers de distribution TSV via le flag `--taxref` :

```bash
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt
```

Cela génère :
- `data/animalia_taxa_minimal.tsv` (~23 MB, 163K espèces)
- `data/animalia_vernacular_minimal.tsv` (~33 MB, 1.1M noms dont ~45K noms TAXREF)

#### 3. Construire la base de données

```bash
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv
```

#### 4. Construire l'index FTS5

**IMPORTANT :** Obligatoire pour que les noms français soient cherchables !

```bash
uv run init-fts
```

#### 5. Tester

```bash
uv run daynimal search guépard
uv run daynimal search lion
uv run daynimal-app  # Interface graphique
```

---

## Qu'est-ce que TAXREF ?

**TAXREF** (Référentiel Taxonomique pour la France) est le référentiel taxonomique officiel français maintenu par le **Muséum national d'Histoire naturelle (MNHN)**.

### Caractéristiques

| Aspect | Détails |
|--------|---------|
| Nombre de taxons | ~600 000 (faune, flore, fonge) |
| Noms français | Pour la majorité des espèces animales |
| Couverture | Mondiale (pas seulement France) |
| Mise à jour | Annuelle (v18 = janvier 2025) |
| Coût | Gratuit et open data |
| Format | CSV/texte (tab-separated) |

### Pourquoi TAXREF + GBIF ?

| Critère | GBIF | TAXREF | GBIF + TAXREF |
|---------|------|--------|---------------|
| Couverture mondiale | Oui | Limitée | Oui |
| Noms français | Limité | Excellent | Oui |
| Noms multilingues | Oui | Limité | Oui |
| Qualité (France) | Oui | Oui | Excellente |

---

## Licence et Attribution

### Licence : Etalab Open License 2.0

TAXREF est distribué sous **Licence Ouverte / Open License Etalab 2.0**, compatible avec **CC-BY 4.0**.

**Autorisé :**
- Usage commercial
- Modification
- Redistribution

**Obligation :**
- **Attribution requise**

### Attribution Requise

**Format texte :**
```
Noms vernaculaires français issus de TAXREF v18,
Muséum national d'Histoire naturelle,
sous licence Etalab Open License 2.0.
https://inpn.mnhn.fr/
```

**Format HTML :**
```html
Noms vernaculaires français issus de
<a href="https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref">TAXREF v18</a>,
Muséum national d'Histoire naturelle,
sous licence <a href="https://github.com/etalab/licence-ouverte/blob/master/LO.md">Etalab Open License 2.0</a>.
```

**Note :** Cette attribution est **automatiquement incluse** dans `uv run daynimal credits`.

---

## Documentation Technique

### Structure du Fichier TAXREF

TAXREF est un fichier CSV avec séparateur **tabulation** (`\t`).

**Colonnes importantes :**

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `CD_NOM` | ID unique TAXREF | 60015 |
| `REGNE` | Règne | Animalia |
| `LB_NOM` | Nom scientifique complet | Panthera leo (Linnaeus, 1758) |
| `NOM_VERN` | **Nom vernaculaire français** | **lion** |
| `NOM_VERN_ENG` | Nom anglais | lion |

**Exemple d'entrée :**
```
CD_NOM  REGNE     LB_NOM                          NOM_VERN
60015   Animalia  Panthera leo (Linnaeus, 1758)   lion
```

### Stratégie de Matching

Le script `generate_distribution.py` (avec le flag `--taxref`) associe TAXREF avec GBIF :

1. **Extraction du nom canonique**
   - Supprime auteur/année : `Panthera leo (Linnaeus, 1758)` -> `Panthera leo`
   - Garde Genre + Espèce uniquement

2. **Recherche dans les taxa GBIF extraits**
   - Match exact sur `canonical_name`
   - Filtre : `rank='species'` uniquement (mode minimal)

3. **Fusion dans le fichier vernaculaire TSV**
   - Ajoute les noms TAXREF avec `language='fr'`
   - Évite automatiquement les doublons

### Statistiques Attendues

Après construction de la base minimale avec TAXREF :

| Métrique | Sans TAXREF | Avec TAXREF | Gain |
|----------|-------------|-------------|------|
| Noms français | ~44 000 (GBIF) | ~89 000 (GBIF + TAXREF) | **+104%** |
| Total noms vernaculaires | ~1.07M | ~1.12M | +5% |
| Taille DB (après VACUUM) | ~120 MB | ~117 MB | -2% |

**Note :** Pas 100% de couverture car TAXREF se concentre sur les espèces observées en France/Europe.

---

## Dépannage

### "File not found" pour le fichier TAXREF

**Solution :** Vérifier que le fichier est dans le dossier `data/`
```bash
# Le fichier doit être dans data/
ls data/TAXREFv18.txt

# Utiliser le chemin relatif (recommandé)
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt

# OU le chemin absolu
uv run generate-distribution --mode minimal --taxref "C:\data\git\daynimal\data\TAXREFv18.txt"
```

### Fichier TAXREF corrompu ou illisible

**Causes possibles :**
- Fichier corrompu
- Mauvais fichier (PDF au lieu du TXT)
- Fichier non décompressé

**Solutions :**
1. Re-télécharger depuis https://www.patrinat.fr/
2. Vérifier que c'est le fichier `.txt` (pas le ZIP ou PDF)
3. Extraire `TAXREFv18.txt` du ZIP si nécessaire
4. Placer dans le dossier `data/` du projet

### La recherche ne trouve pas les noms français

**Cause :** Index FTS5 pas construit ou pas reconstruit

**Solution :**
```bash
uv run init-fts  # Construire/reconstruire l'index
uv run daynimal-app  # Relancer l'app
```

### Certains noms TAXREF ne sont pas importés

**C'est normal !** Cela signifie :
- Ces espèces TAXREF ne sont pas dans le GBIF Backbone
- Ou elles sont hors de votre base minimale (mode minimal = species uniquement)

Le script match automatiquement ce qui est possible et ignore le reste.

---

## Maintenance

### Mise à Jour Annuelle

TAXREF sort une nouvelle version chaque année (v18, v19, etc.).

**Procédure :**
```bash
# 1. Télécharger la nouvelle version dans data/
# (depuis https://www.patrinat.fr/)

# 2. Regénérer les fichiers de distribution avec la nouvelle version
uv run generate-distribution --mode minimal --taxref data/TAXREFv19.txt

# 3. Reconstruire la DB
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv

# 4. Reconstruire l'index
uv run init-fts
```

### Vérification de Version

Pour savoir quelle version vous utilisez :
- Nom du fichier téléchargé (`TAXREFv18.txt` = version 18)
- Documentation PDF dans le ZIP téléchargé (`TAXREFv18.pdf`)
- Site officiel : dernière version disponible sur https://www.patrinat.fr/

---

## Références

### Liens Officiels TAXREF

- **Téléchargement (temporaire) :** https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353
- **Fichier direct v18 :** https://assets.patrinat.fr/files/referentiel/TAXREF_v18_2025.zip
- **Site officiel INPN :** https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref
- **GitHub :** https://github.com/MNHN-TAXREF

**Note :** Suite à une cyberattaque du MNHN en janvier 2025, les téléchargements ont été temporairement déplacés vers PatriNat.

### Licence

- **Licence Etalab :** https://github.com/etalab/licence-ouverte/blob/master/LO.md
- **Compatible avec :** CC-BY 4.0

### Support

- **Support TAXREF :** inpn@mnhn.fr
- **Issues Daynimal :** https://github.com/notoraptor/daynimal/issues

### Citation

**GARGOMINY O. et al., 2025.** TAXREF v18, référentiel taxonomique pour la France.
Muséum national d'Histoire naturelle. https://inpn.mnhn.fr/

---

## Résumé Complet des Commandes

```bash
# 0. Créer le dossier data/ si nécessaire
mkdir -p data

# 1. Télécharger TAXREF (navigateur ou commande)
# https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353
# Placer le fichier dans data/TAXREFv18.txt

# 2. Générer les fichiers de distribution (intègre TAXREF)
uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt

# 3. Construire la base de données
uv run build-db --taxa data/animalia_taxa_minimal.tsv \
                --vernacular data/animalia_vernacular_minimal.tsv

# 4. Construire l'index FTS5 (OBLIGATOIRE)
uv run init-fts

# 5. Tester
uv run daynimal search guépard
uv run daynimal-app
```

**Temps total : 10-15 minutes**
**Résultat : ~89 000 noms français dans votre base !**

**Organisation des fichiers :**
- `data/` -> Fichiers TAXREF et TSV de distribution (gitignored)
- `tmp/` -> Fichiers temporaires/extraits (gitignored)
- `daynimal.db` -> Base de données SQLite
