# Flet API Guide for Daynimal

Guide pratique pour l'API Flet basé sur l'expérience du développement de l'application Daynimal.

## Version Flet

Daynimal utilise **Flet >=0.25.0** qui a introduit des changements majeurs :
- Migration de variables vers **Enums**
- Syntaxe : `ft.Colors.PRIMARY` (pas `ft.colors.PRIMARY`)
- Syntaxe : `ft.Icons.FAVORITE` (pas `ft.icons.FAVORITE`)

## Quick Reference

### ✅ Couleurs garanties

```python
# Theme colors (toujours disponibles)
ft.Colors.PRIMARY
ft.Colors.ERROR

# Basic colors
ft.Colors.WHITE
ft.Colors.BLACK

# Grey palette (50-900)
ft.Colors.GREY_50
ft.Colors.GREY_200   # Light grey for backgrounds
ft.Colors.GREY_500   # Medium grey for text
ft.Colors.GREY_700
ft.Colors.GREY_900

# Blue palette (50-900)
ft.Colors.BLUE
ft.Colors.BLUE_400
ft.Colors.BLUE_700

# Other full palettes
ft.Colors.RED_500
ft.Colors.GREEN_500
ft.Colors.AMBER_500
```

### ✅ Icônes confirmées

```python
# Navigation
ft.Icons.CALENDAR_TODAY  # Pour "Animal du jour"
ft.Icons.SHUFFLE         # Pour "Animal aléatoire"
ft.Icons.SEARCH
ft.Icons.HISTORY
ft.Icons.SETTINGS

# Media & Content
ft.Icons.IMAGE          # Générique pour toutes images
ft.Icons.FAVORITE       # Cœur, likes, favoris

# Status
ft.Icons.ERROR          # Erreurs
ft.Icons.INFO           # Informations
ft.Icons.WARNING        # Avertissements

# Actions
ft.Icons.CLOSE
ft.Icons.REFRESH
ft.Icons.ADD
```

### ❌ À ÉVITER

```python
# Ces couleurs ont causé des erreurs dans Daynimal
ft.Colors.OUTLINE           # Non garanti
ft.Colors.SURFACE_VARIANT   # N'existe pas
ft.Colors.SECONDARY         # Accès direct non fiable

# Ces icônes n'existent pas
ft.Icons.HIDE_IMAGE
ft.Icons.IMAGE_NOT_SUPPORTED
ft.Icons.BROKEN_IMAGE
```

## Architecture Async/Await

### Pattern pour indicateurs de chargement

**❌ Problème : Code synchrone**
```python
def load_data(self):
    # L'UI reste figée pendant tout le traitement
    data = fetch_from_database()  # Bloque l'UI
    self.display(data)
```

**✅ Solution : Async/await**
```python
async def load_data(self):
    # 1. Afficher l'indicateur de chargement
    self.container.controls = [
        ft.ProgressRing(),
        ft.Text("Chargement en cours...")
    ]
    self.page.update()  # ← Toujours synchrone même dans async

    # 2. IMPORTANT: Forcer le refresh de l'UI
    await asyncio.sleep(0.1)  # Donne le temps à Flet de rafraîchir

    # 3. Traiter dans un thread séparé
    def fetch():
        with Repository() as repo:
            return repo.get_data()

    data = await asyncio.to_thread(fetch)  # Non-bloquant

    # 4. Afficher le résultat
    self.display(data)
    self.page.update()
```

### Règles importantes

1. **`self.page.update()` reste synchrone** même dans les fonctions async
2. **Toujours `await asyncio.sleep(0.1)`** après un `.update()` pour forcer le refresh
3. **Utiliser `asyncio.to_thread()`** pour les opérations bloquantes (DB, I/O)
4. **Déclarer les event handlers comme `async`** : `async def on_click(self, e)`

### Exemple complet : Bouton avec loading

```python
class MyApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.button = ft.Button(
            "Charger",
            on_click=self.load_data  # ← async handler
        )
        self.content = ft.Column()
        self.page.add(self.button, self.content)

    async def load_data(self, e):
        # Show loading
        self.content.controls = [
            ft.Container(
                content=ft.Column([
                    ft.ProgressRing(width=60, height=60),
                    ft.Text("Chargement...", size=18, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch data in background
            def fetch():
                with AnimalRepository() as repo:
                    return repo.get_animal_of_the_day()

            animal = await asyncio.to_thread(fetch)

            # Display result
            self.content.controls = [
                ft.Text(animal.display_name, size=24),
                ft.Text(animal.taxon.scientific_name, italic=True),
            ]

        except Exception as error:
            # Show error
            self.content.controls = [
                ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                ft.Text(f"Erreur: {error}", color=ft.Colors.ERROR),
            ]

        finally:
            self.page.update()
```

## Gestion des images

### Affichage avec fallback

```python
ft.Image(
    src=image_url,
    width=400,
    height=300,
    fit="contain",
    border_radius=10,
    error_content=ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.ERROR),
            ft.Text("Erreur de chargement", color=ft.Colors.ERROR),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=400,
        height=300,
        bgcolor=ft.Colors.GREY_200,
        border_radius=10,
        padding=20,
    ),
)
```

### Placeholder quand aucune image

```python
if animal.images:
    # Afficher l'image
    controls.append(ft.Image(src=animal.images[0].url, ...))
else:
    # Placeholder
    controls.append(
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.GREY_500),
                ft.Text("Aucune image disponible", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Cet animal n'a pas encore d'image", size=12, color=ft.Colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=30,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
        )
    )
```

## Layout & Styling

### Container avec padding et background

```python
ft.Container(
    content=ft.Text("Contenu"),
    padding=20,
    bgcolor=ft.Colors.GREY_200,
    border_radius=10,
)
```

### Column avec spacing

```python
ft.Column(
    controls=[
        ft.Text("Titre"),
        ft.Text("Sous-titre"),
    ],
    spacing=10,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
)
```

### Row pour boutons

```python
ft.Row(
    controls=[
        ft.Button("Action 1", on_click=handler1),
        ft.Button("Action 2", on_click=handler2),
    ],
    spacing=10,
)
```

### Boutons stylisés

```python
ft.Button(
    "Mon bouton",
    icon=ft.Icons.CALENDAR_TODAY,
    on_click=self.handler,
    style=ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.PRIMARY,
    ),
)
```

## Debugging

### Erreur : `'super' object has no attribute '__getattr__'`

**Cause :** Icône ou couleur inexistante dans votre version de Flet

**Solutions :**
1. Vérifier dans [Flet Icons Browser](https://flet-icons-browser.fly.dev/)
2. Consulter la liste des icônes/couleurs garanties ci-dessus
3. Remplacer par une alternative :
   - `HIDE_IMAGE` → `IMAGE`
   - `OUTLINE` → `GREY_500`
   - `SURFACE_VARIANT` → `GREY_200`

### Indicateur de chargement invisible

**Cause :** Code synchrone bloque l'UI

**Solution :** Utiliser async/await + `asyncio.to_thread()` (voir section Architecture)

### Print ne s'affiche pas

**Cause :** Flet ne redirige pas stdout vers l'UI

**Solutions :**
1. Regarder le terminal où `flet run` est lancé
2. Ajouter des `ft.Text()` dans l'UI pour debug visuel
3. Utiliser des fichiers de log

## Resources

- **Icons Browser** : https://flet-icons-browser.fly.dev/
- **Flet Docs** : https://docs.flet.dev/
- **Colors Reference** : https://docs.flet.dev/types/colors/
- **Icons Reference** : https://docs.flet.dev/types/icons/
- **Flutter Icons** (base de Flet) : https://api.flutter.dev/flutter/material/Icons-class.html

## Patterns Daynimal

### Structure de l'app

```python
class DaynimalApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Daynimal"
        self.page.padding = 20
        self.page.scroll = ft.ScrollMode.AUTO

        self.current_animal = None
        self.build()

    def build(self):
        # Créer les composants
        self.header = ft.Text("🦁 Daynimal", size=32, weight=ft.FontWeight.BOLD)
        self.container = ft.Column(controls=[], spacing=10)

        # Layout principal
        self.page.add(
            ft.Column([
                self.header,
                ft.Divider(),
                self.container,
            ], spacing=20)
        )

    async def load_animal(self, mode: str):
        # Pattern de chargement async (voir section Architecture)
        pass

def main():
    def app_main(page: ft.Page):
        DaynimalApp(page)

    ft.run(main=app_main)  # ← Syntaxe moderne
```

### Attribution légale

```python
# Toujours afficher les crédits (requis par licences)
controls.append(
    ft.Text(
        "Données: GBIF Backbone Taxonomy (CC-BY 4.0)",
        size=12,
        color=ft.Colors.GREY_500,
        italic=True,
    )
)
```

## Migrations API historiques

Corrections appliquees lors de migrations Flet :

| Ancien (obsolete) | Nouveau (correct) |
|---|---|
| `ft.app(target=main)` | `ft.run(main=main)` |
| `page.update_async()` | `page.update()` |
| `ft.ImageFit.CONTAIN` | `"contain"` (string) |
| `ft.colors.GREY_700` (lowercase) | `ft.Colors.GREY_700` (Enum) |
| `ft.icons.TODAY` (lowercase) | `ft.Icons.CALENDAR_TODAY` (Enum) |

## Checklist mise a jour Flet

Lors de futures mises a jour de Flet, verifier :
1. Compatibilite des icones utilisees
2. Compatibilite des couleurs utilisees
3. API async/await (changements de signature)
4. Documentation : https://docs.flet.dev/

## Notes importantes

1. **Enum syntax** : Toujours `ft.Colors.XXX` et `ft.Icons.XXX` (majuscules)
2. **Async/await** : Nécessaire pour indicateurs de chargement
3. **`asyncio.to_thread()`** : Pour opérations bloquantes (DB, I/O)
4. **`page.update()`** : Reste synchrone même dans async
5. **Icons Browser** : Votre meilleur ami pour vérifier les icônes
6. **Palettes complètes** : `GREY_50-900`, `BLUE_50-900` sont garanties
7. **Error handling** : Toujours wrapper dans try/except et afficher dans l'UI
