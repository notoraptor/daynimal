# TAXREF - Noms Vernaculaires Français

Guide complet pour importer les noms français depuis TAXREF, le référentiel taxonomique officiel français.

---

## 📋 Table des Matières

1. [Démarrage Rapide](#démarrage-rapide-5-étapes)
2. [Qu'est-ce que TAXREF ?](#quest-ce-que-taxref-)
3. [Licence et Attribution](#licence-et-attribution)
4. [Documentation Technique](#documentation-technique)
5. [Dépannage](#dépannage)
6. [Maintenance](#maintenance)
7. [Références](#références)

---

## Démarrage Rapide (5 étapes)

### Ce que vous allez obtenir
- 🇫🇷 **~45 000 noms français** pour les animaux
- ⏱️ **Temps requis :** 10-15 minutes
- ✅ **Couverture française :** 0.4% → 35%

### Étapes

#### 1. Télécharger TAXREF (5 min)

**⚠️ IMPORTANT : Organisation des fichiers**
- Placez le fichier TAXREF téléchargé dans le dossier **`data/`** (créez-le si nécessaire)
- Les fichiers extraits du ZIP peuvent aller dans **`tmp/`** (optionnel)
- Ces dossiers sont dans `.gitignore` et ne seront jamais commités

**Téléchargement :**

Visitez : https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353

Téléchargez **"TAXREF_v18_2025.zip"** (~100 MB) et extrayez **"TAXREFv18.txt"**

**Alternative avec ligne de commande :**
```bash
# Créer le dossier data/ si nécessaire
mkdir -p data

# Windows PowerShell
Invoke-WebRequest -Uri "https://assets.patrinat.fr/files/referentiel/TAXREF_v18_2025.zip" -OutFile "data/TAXREF_v18_2025.zip"
Expand-Archive -Path "data/TAXREF_v18_2025.zip" -DestinationPath "tmp/"

# Linux/Mac
wget https://assets.patrinat.fr/files/referentiel/TAXREF_v18_2025.zip -O data/TAXREF_v18_2025.zip
unzip data/TAXREF_v18_2025.zip -d tmp/
```

#### 2. Prévisualiser (1 min)

```bash
cd C:\data\git\daynimal
uv run import-taxref-french-fast --file data/TAXREFv18.txt --dry-run
```

Vous verrez :
```
[INFO] Found 156,432 animal taxa with French names in TAXREF
[OK] Will add: panthera leo -> lion
[OK] Will add: acinonyx jubatus -> guépard
[DRY RUN] Would add 49,269 French vernacular names
```

#### 3. Importer (~30 secondes)

```bash
uv run import-taxref-french-fast --file data/TAXREFv18.txt
```

Attendez :
```
[SUCCESS] Added 49,269 French names!
```

#### 4. Reconstruire l'index FTS5 (2-3 min)

**IMPORTANT :** Obligatoire pour que les nouveaux noms soient cherchables !

```bash
uv run init-fts
```

#### 5. Tester 🎉

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
| 🔢 Nombre de taxons | ~600 000 (faune, flore, fonge) |
| 🇫🇷 Noms français | Pour la majorité des espèces animales |
| 🌍 Couverture | Mondiale (pas seulement France) |
| 🔄 Mise à jour | Annuelle (v17 = décembre 2023) |
| 💰 Coût | Gratuit et open data |
| 📄 Format | CSV/texte (tab-separated) |

### Pourquoi TAXREF + GBIF ?

| Critère | GBIF | TAXREF | GBIF + TAXREF |
|---------|------|--------|---------------|
| Couverture mondiale | ✅ | ⚠️ | ✅ |
| Noms français | ⚠️ Limité | ✅ Excellent | ✅ |
| Noms multilingues | ✅ | ⚠️ | ✅ |
| Qualité (France) | ✅ | ✅ | ✅✅ |

**Résultat :** La meilleure couverture possible !

---

## Licence et Attribution

### Licence : Etalab Open License 2.0

TAXREF est distribué sous **Licence Ouverte / Open License Etalab 2.0**, compatible avec **CC-BY 4.0**.

✅ **Autorisé :**
- Usage commercial
- Modification
- Redistribution

⚠️ **Obligation :**
- **Attribution requise**

### Attribution Requise

**Format texte :**
```
Noms vernaculaires français issus de TAXREF v17,
Muséum national d'Histoire naturelle,
sous licence Etalab Open License 2.0.
https://inpn.mnhn.fr/
```

**Format HTML :**
```html
Noms vernaculaires français issus de
<a href="https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref">TAXREF v17</a>,
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

Le script `import_taxref_french.py` associe TAXREF avec GBIF :

1. **Extraction du nom canonique**
   - Supprime auteur/année : `Panthera leo (Linnaeus, 1758)` → `Panthera leo`
   - Garde Genre + Espèce uniquement

2. **Recherche dans GBIF**
   - Match exact sur `canonical_name`
   - Sinon LIKE sur `scientific_name`
   - Filtre : `rank='species'` uniquement

3. **Ajout du nom français**
   - Insère dans `vernacular_names` avec `language='fr'`
   - Évite automatiquement les doublons

### Statistiques Attendues

Après import dans une base avec ~127k espèces :

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Espèces avec nom français | ~500 | ~49 000 | **98x** |
| Total noms vernaculaires | ~1M | ~1.05M | +5% |
| Couverture française | 0.4% | 38% | **95x** |

**Note :** Pas 100% car TAXREF se concentre sur les espèces observées en France/Europe.

**Import rapide avec TAXREF v18 :**
- Temps d'import : ~30 secondes (vs 2-3 heures avec version non optimisée)
- Noms ajoutés : 49,269
- Script : `import-taxref-french-fast` (bulk insert optimisé)

### Options du Script

**⚠️ IMPORTANT : Toujours utiliser `import-taxref-french-fast`**

Le script standard `import-taxref-french` est très lent (~2-3 heures). Utilisez toujours la version optimisée :

```bash
# Prévisualisation sans modification
uv run import-taxref-french-fast --file data/TAXREFv18.txt --dry-run

# Import réel (~30 secondes)
uv run import-taxref-french-fast --file data/TAXREFv18.txt

# Aide
uv run import-taxref-french-fast --help
```

**Scripts disponibles :**
- `import-taxref-french-fast` → **RECOMMANDÉ** - Optimisé avec bulk insert (~30s)
- `import-taxref-french` → Version lente (conservée pour référence, ~2-3h)

---

## Dépannage

### ❌ "File not found"

```bash
[ERROR] File not found: TAXREFv18.txt
```

**Solution :** Vérifier que le fichier est dans le dossier `data/`
```bash
# Le fichier doit être dans data/
ls data/TAXREFv18.txt

# Utiliser le chemin relatif (recommandé)
uv run import-taxref-french-fast --file data/TAXREFv18.txt

# OU le chemin absolu
uv run import-taxref-french-fast --file "C:\\data\\git\\daynimal\\data\\TAXREFv18.txt"
```

### ❌ "Failed to parse TAXREF file"

**Causes possibles :**
- Fichier corrompu
- Mauvais fichier (PDF au lieu du TXT)
- Fichier non décompressé

**Solutions :**
1. Re-télécharger depuis https://www.patrinat.fr/
2. Vérifier que c'est le fichier `.txt` (pas le ZIP ou PDF)
3. Extraire `TAXREFv18.txt` du ZIP si nécessaire
4. Placer dans le dossier `data/` du projet

### ❌ La recherche ne trouve pas les noms français

**Cause :** Index FTS5 pas reconstruit

**Solution :**
```bash
uv run init-fts  # Reconstruire l'index
uv run daynimal-app  # Relancer l'app
```

### ℹ️ "No match found for X TAXREF taxa"

**C'est normal !** Cela signifie :
- Ces espèces TAXREF ne sont pas dans GBIF
- Ou elles sont hors de votre base minimale

Le script match automatiquement ce qui est possible et ignore le reste.

---

## Maintenance

### Mise à Jour Annuelle

TAXREF sort une nouvelle version chaque année (v18, v19, etc.).

**Procédure :**
```bash
# 1. Télécharger la nouvelle version dans data/
# (depuis https://www.patrinat.fr/)

# 2. Importer (les doublons sont automatiquement évités)
uv run import-taxref-french-fast --file data/TAXREFv19.txt

# 3. Reconstruire l'index
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
- **Issues Daynimal :** https://github.com/yourusername/daynimal/issues

### Alternatives et Compléments

**Autres sources de noms français :**

1. **Wikidata** (déjà intégré dans Daynimal)
   - Noms multilingues dont français
   - Moins exhaustif que TAXREF

2. **Wikipédia français**
   - Articles en français
   - Extraction automatique via API

3. **Canadensys** (faune canadienne)
   - Bilingue français/anglais
   - https://data.canadensys.net/

### Citation

**GARGOMINY O. et al., 2025.** TAXREF v18, référentiel taxonomique pour la France.
Muséum national d'Histoire naturelle. https://inpn.mnhn.fr/

**Note de version :**
- Version actuelle : **v18** (janvier 2025)
- Version précédente mentionnée dans docs : v17 (décembre 2023)

---

## Résumé Complet des Commandes

```bash
# 0. Créer le dossier data/ si nécessaire
mkdir -p data

# 1. Télécharger TAXREF (navigateur ou commande)
# https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353
# Placer le fichier dans data/TAXREFv18.txt

# 2. Prévisualiser
uv run import-taxref-french-fast --file data/TAXREFv18.txt --dry-run

# 3. Importer (~30 secondes)
uv run import-taxref-french-fast --file data/TAXREFv18.txt

# 4. Reconstruire l'index (OBLIGATOIRE)
uv run init-fts

# 5. Tester
uv run daynimal search guépard
uv run daynimal-app
```

**Temps total : 5-10 minutes**
**Résultat : 49 000+ noms français dans votre base !** 🇫🇷🎉

**Organisation des fichiers :**
- `data/` → Fichiers TAXREF bruts (gitignored)
- `tmp/` → Fichiers temporaires/extraits (gitignored)
- `daynimal.db` → Base de données SQLite
