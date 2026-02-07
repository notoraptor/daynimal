# Optimisation des performances - Sélection aléatoire

## Problème identifié

L'application prenait **~25 secondes** pour charger "l'animal du jour" ou un animal aléatoire.

### Analyse

L'investigation des logs a révélé que le temps était perdu dans la requête SQL, pas dans les appels API externes :
- **25 secondes** : Entre "Loading animal" et le premier appel réseau
- **< 1 seconde** : Appels API (Wikidata + Wikipedia en parallèle)

### Cause racine

La méthode originale utilisait :
```sql
SELECT MIN(taxon_id), MAX(taxon_id)
FROM taxa
WHERE rank = 'species' AND is_synonym = 0
```

**Problème** : SQLite n'a pas d'index sur `rank` et `is_synonym`, donc cette requête **parcourt toute la table** (3M+ lignes) pour calculer MIN/MAX.

**Temps mesuré** : 27.5 secondes

## Solution implémentée

### Approche optimisée

1. Calculer MIN/MAX sur **toute la table** (rapide - utilise l'index de la clé primaire)
2. Générer un ID aléatoire dans cette plage
3. Sélectionner le premier taxon correspondant aux filtres avec `taxon_id >= random_id`

### Code

```python
def _get_random_by_id_range(self, rank: str, is_enriched: bool | None = None):
    # MIN/MAX sans filtres (rapide avec index PK)
    id_range = self.session.query(
        func.min(TaxonModel.taxon_id),
        func.max(TaxonModel.taxon_id)
    ).first()

    min_id, max_id = id_range

    # Générer ID aléatoire
    random_id = random.randint(min_id, max_id)

    # Sélectionner avec filtres
    taxon_model = self.session.query(TaxonModel)\
        .filter(TaxonModel.rank == rank)\
        .filter(TaxonModel.taxon_id >= random_id)\
        .first()

    return taxon_model
```

### Résultats

**Avant** :
- MIN/MAX avec filtres : **27.5s**
- SELECT : 0.001s
- **Total : ~27.5s**

**Après** :
- MIN/MAX sans filtres : **1.8s**
- SELECT avec filtres : 0.016s
- **Total : ~1.86s**

**Amélioration : 93% (27.5s → 1.86s)**

## Alternative future : Indexation

Pour optimiser davantage (réduire à < 0.1s), nous pourrions créer des index :

```sql
CREATE INDEX idx_taxa_rank ON taxa(rank);
CREATE INDEX idx_taxa_is_synonym ON taxa(is_synonym);
CREATE INDEX idx_taxa_rank_synonym ON taxa(rank, is_synonym);
```

**Avantages** :
- MIN/MAX avec filtres serait instantané (< 0.01s)
- Toutes les requêtes filtrées seraient plus rapides

**Inconvénients** :
- Augmentation de la taille de la base de données (~10-15%)
- Temps d'import plus long (reconstruction des index)
- Nécessite une migration de schéma

## Méthodes affectées

- `AnimalRepository.get_random()` - Sélection aléatoire
- `AnimalRepository.get_animal_of_the_day()` - Animal du jour déterministe
- `AnimalRepository._get_random_by_id_range()` - Méthode interne

## Commit

Référence : `repository.py` - Optimisation des requêtes aléatoires (février 2026)

## Tests

Pour vérifier les performances :

```python
from daynimal.db.session import get_session
from sqlalchemy import func
from daynimal.db.models import TaxonModel
import time

session = get_session()

# Test MIN/MAX
start = time.time()
result = session.query(
    func.min(TaxonModel.taxon_id),
    func.max(TaxonModel.taxon_id)
).first()
print(f"MIN/MAX: {time.time() - start:.3f}s")

# Test SELECT aléatoire
import random
random_id = random.randint(result[0], result[1])
start = time.time()
taxon = session.query(TaxonModel)\
    .filter(TaxonModel.rank == 'species')\
    .filter(TaxonModel.is_synonym.is_(False))\
    .filter(TaxonModel.taxon_id >= random_id)\
    .first()
print(f"SELECT: {time.time() - start:.3f}s")
```

Résultat attendu : < 2 secondes total
