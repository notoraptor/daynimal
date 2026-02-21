# Flet API Guide for Daynimal

**Version Flet : 0.80.5** — Ce guide documente l'API telle qu'utilisee dans le projet.
**IMPORTANT** : Claude Code DOIT consulter ce fichier avant toute modification de code UI.

---

## Changements critiques (Flet 0.80 vs anciennes versions)

| Ancien (OBSOLETE)                          | Nouveau (CORRECT)                                |
|--------------------------------------------|--------------------------------------------------|
| `page.open(snackbar)`                      | `page.show_dialog(snackbar)`                     |
| `page.snack_bar = sb; sb.open = True`      | `page.show_dialog(sb)`                           |
| `page.close_dialog()`                      | `page.pop_dialog()`                              |
| `ft.app(target=main)`                      | `ft.run(main=main)`                              |
| `page.update_async()`                      | `page.update()`                                  |
| `ft.ImageFit.CONTAIN`                      | `ft.BoxFit.CONTAIN` (enum)                       |
| `ft.colors.GREY_700` (lowercase)           | `ft.Colors.GREY_700` (Enum majuscule)            |
| `ft.icons.TODAY` (lowercase)               | `ft.Icons.CALENDAR_TODAY` (Enum majuscule)       |
| `ft.ElevatedButton("text")`                | `ft.Button("text")`                              |
| `ft.TextButton("text")`                    | `ft.Button("text")`                              |
| `ft.alignment.center`                      | `ft.Alignment.CENTER` ou `ft.Alignment(0, 0)`   |
| `page.launch_url(url)` (sync)              | `await page.launch_url(url)` (async)             |
| `page.window_width = 420`                  | `page.window.width = 420`                        |

**Proprietes supprimees de Page** : `page.snack_bar`, `page.dialog`, `page.open()`.

**BUG decorateur @deprecated dans Flet 0.80** :
Le decorateur `@deprecated` wrappe les fonctions async dans un wrapper **sync**.
Consequence : `page.launch_url()` retourne une coroutine non-executee.
- **NE PAS** faire `await page.launch_url(url)` (ne fonctionne pas)
- **FAIRE** : `page.run_task(ft.UrlLauncher().launch_url, url)`
  (`run_task` attend une **fonction coroutine + args**, pas une coroutine deja appelee)

**Deprecations annoncees (0.90+)** :
- `page.launch_url()` → `UrlLauncher().launch_url()` (service)
- `page.window` → possiblement renomme (verifier lors de la migration)

---

## Page — Methodes et proprietes

### Methodes

| Methode              | Async | Description                                         |
|----------------------|-------|-----------------------------------------------------|
| `page.add(*controls)`| Non   | Ajoute des controles a la page                      |
| `page.update()`      | Non   | Rafraichit l'UI (toujours sync, meme dans async)    |
| `page.show_dialog(d)`| Non   | Affiche un dialog/snackbar                          |
| `page.pop_dialog()`  | Non   | Ferme le dernier dialog ouvert                      |
| `page.launch_url(u)` | **Oui**\* | Ouvre une URL — voir bug @deprecated ci-dessus  |
| `page.go(route)`     | Non   | Change la route                                     |
| `page.run_task(coro)` | Non  | Execute une coroutine dans l'event loop             |
| `page.run_thread(fn)` | Non  | Execute une fonction dans un thread pool            |

### Proprietes

| Propriete             | Type                    | Description                            |
|-----------------------|-------------------------|----------------------------------------|
| `page.title`          | `str`                   | Titre de la fenetre                    |
| `page.padding`        | `int` ou `Padding`      | Padding de la page                     |
| `page.scroll`         | `ScrollMode` ou `None`  | Mode de scroll                         |
| `page.theme_mode`     | `ThemeMode`             | DARK, LIGHT, SYSTEM                    |
| `page.navigation_bar` | `NavigationBar`         | Barre de navigation en bas             |
| `page.controls`       | `list`                  | Liste des controles enfants            |
| `page.overlay`        | `list`                  | Controles en superposition             |
| `page.data`           | `any`                   | Donnees libres (pour passer du contexte) |
| `page.route`          | `str`                   | Route actuelle (read-only)             |
| `page.platform`       | `PagePlatform`          | OS de l'app (read-only)               |
| `page.web`            | `bool`                  | True si web (read-only)               |

### Fenetre (desktop)

```python
page.window.width = 420
page.window.height = 820
await page.window.close()  # async!
```

Proprietes : `width`, `height`, `resizable`, `maximized`, `minimized`.

### Evenements Page

```python
page.on_route_change = handler       # changement de route
page.on_keyboard_event = handler     # touche pressee
page.on_disconnect = handler         # utilisateur ferme l'onglet web
page.on_close = handler              # session expire
```

---

## SnackBar

**IMPORTANT** : Afficher avec `page.show_dialog()`, PAS `page.open()`.

```python
# Basique
page.show_dialog(ft.SnackBar(ft.Text("Message !")))

# Avec couleur de fond
page.show_dialog(
    ft.SnackBar(ft.Text("Erreur !"), bgcolor=ft.Colors.ERROR)
)

# Avec action
page.show_dialog(
    ft.SnackBar(
        content=ft.Text("Fichier supprime"),
        action=ft.SnackBarAction(
            label="Annuler",
            on_click=lambda e: print("Annule !"),
        ),
        duration=4000,       # ms (defaut: 4000)
        persist=False,       # True = reste jusqu'a interaction
    )
)
```

Proprietes : `content`, `action`, `duration`, `bgcolor`, `persist`, `behavior` (FIXED/FLOATING), `show_close_icon`, `dismiss_direction`.

---

## AlertDialog

```python
dialog = ft.AlertDialog(
    title=ft.Text("Confirmer"),
    content=ft.Text("Voulez-vous continuer ?"),
    actions=[
        ft.Button("Oui", on_click=lambda e: page.pop_dialog()),
        ft.Button("Non", on_click=lambda e: page.pop_dialog()),
    ],
    modal=True,  # True = clic exterieur ne ferme pas
)
page.show_dialog(dialog)

# Fermer :
page.pop_dialog()
```

---

## Clipboard

Le clipboard est un **service async**. Il doit etre utilise dans des handlers async.

```python
# Copier du texte
await ft.Clipboard().set("texte a copier")

# Lire le clipboard
text = await ft.Clipboard().get()
```

Les deux methodes (`set` et `get`) sont **async**.

---

## Boutons

### Button (bouton standard)

```python
ft.Button(
    content="Mon bouton",        # ou text direct : ft.Button("Mon bouton")
    icon=ft.Icons.CALENDAR_TODAY,
    on_click=self.handler,
    disabled=False,
    tooltip="Info-bulle",
    style=ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.PRIMARY,
        padding=ft.Padding.all(10),
        shape=ft.RoundedRectangleBorder(radius=10),
    ),
)
```

Variantes : `ft.FilledButton`, `ft.OutlinedButton`, `ft.FilledTonalButton`.

### IconButton

```python
ft.IconButton(
    icon=ft.Icons.FAVORITE,
    icon_size=24,               # defaut: 24
    icon_color=ft.Colors.RED,
    on_click=self.handler,
    disabled=False,
    tooltip="Ajouter aux favoris",
    selected=False,                        # toggle state
    selected_icon=ft.Icons.FAVORITE_BORDER,  # icone quand selected=True
)
```

### Evenements communs aux boutons

`on_click`, `on_long_press`, `on_hover`, `on_focus`, `on_blur`.

---

## TextField

```python
ft.TextField(
    label="Rechercher",
    hint_text="Nom d'animal...",
    value="",                    # valeur initiale
    prefix_icon=ft.Icons.SEARCH,
    autofocus=True,
    expand=True,                 # remplit l'espace disponible
    on_submit=self._on_submit,   # touche Entree
    on_change=self._on_change,   # a chaque caractere
    on_focus=self._on_focus,
    on_blur=self._on_blur,
    read_only=False,
    password=False,
    multiline=False,
    max_length=100,
)
```

---

## Image

```python
ft.Image(
    src="https://example.com/image.jpg",  # URL, chemin local, ou base64
    width=400,
    height=300,
    fit=ft.BoxFit.CONTAIN,   # enum : CONTAIN, COVER, FILL, FIT_WIDTH, FIT_HEIGHT, etc.
    border_radius=10,
    error_content=ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.GREY_500),
            ft.Text("Image non disponible"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=400,
        height=300,
        bgcolor=ft.Colors.GREY_200,
    ),
)
```

Proprietes : `src`, `width`, `height`, `fit`, `border_radius`, `error_content`, `placeholder_src`, `semantics_label`.

---

## NavigationBar

```python
page.navigation_bar = ft.NavigationBar(
    selected_index=0,
    on_change=self.on_nav_change,
    label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_HIDE,
    destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Accueil"),
        ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Historique"),
        ft.NavigationBarDestination(icon=ft.Icons.FAVORITE, label="Favoris"),
        ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="Recherche"),
        ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Stats"),
        ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Parametres"),
    ],
)
```

`NavigationBarLabelBehavior` : `ALWAYS_SHOW`, `ALWAYS_HIDE`, `ONLY_SHOW_SELECTED`.

---

## Switch

```python
ft.Switch(
    label="Mode sombre",
    value=False,
    on_change=self._on_theme_toggle,
    label_position=ft.LabelPosition.LEFT,  # ou RIGHT
)

# Dans le handler :
def _on_theme_toggle(self, e):
    is_dark = e.control.value  # bool
```

---

## Layout

### Container

```python
ft.Container(
    content=ft.Text("Contenu"),
    padding=20,                       # int ou ft.Padding(...)
    margin=ft.Margin(left=10),
    bgcolor=ft.Colors.GREY_200,
    border_radius=10,
    border=ft.Border.all(1, ft.Colors.GREY_400),
    alignment=ft.Alignment.CENTER,
    width=300,
    height=200,
    expand=False,
    ink=True,                         # ripple effect au clic
    on_click=self.handler,
)
```

### Column

```python
ft.Column(
    controls=[...],
    spacing=10,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    scroll=ft.ScrollMode.AUTO,        # rend la colonne scrollable
    expand=True,
    tight=True,                       # hauteur minimum
)
```

### Row

```python
ft.Row(
    controls=[...],
    spacing=10,
    alignment=ft.MainAxisAlignment.CENTER,
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
    wrap=True,                        # wrap sur plusieurs lignes
)
```

### Padding et Margin

```python
ft.Padding(left=10, top=5, right=10, bottom=5)
ft.Padding.symmetric(horizontal=20, vertical=10)
ft.Padding.all(15)

ft.Margin(left=10, top=5, right=10, bottom=5)
ft.Margin.symmetric(horizontal=20, vertical=10)
```

### Alignment

```python
ft.Alignment.CENTER              # centre
ft.Alignment(0, 0)               # equivalent, (x, y) de -1 a 1
ft.MainAxisAlignment.CENTER      # pour Row/Column
ft.MainAxisAlignment.SPACE_BETWEEN
ft.CrossAxisAlignment.CENTER
ft.CrossAxisAlignment.STRETCH
```

---

## Indicateurs de progression

### ProgressRing (circulaire)

```python
# Indetermine (spinner)
ft.ProgressRing(width=40, height=40)

# Avec progression
ft.ProgressRing(value=0.5, width=40, height=40, stroke_width=4)
```

### ProgressBar (lineaire)

```python
# Indetermine
ft.ProgressBar(width=400)

# Avec progression
ft.ProgressBar(value=0.7, width=400)
```

---

## Themes et couleurs

### ThemeMode

```python
page.theme_mode = ft.ThemeMode.DARK    # sombre
page.theme_mode = ft.ThemeMode.LIGHT   # clair
page.theme_mode = ft.ThemeMode.SYSTEM  # suit l'OS
```

### Couleurs garanties

```python
# Theme
ft.Colors.PRIMARY
ft.Colors.ERROR

# Basiques
ft.Colors.WHITE
ft.Colors.BLACK

# Palettes (50 a 900)
ft.Colors.GREY_50, ft.Colors.GREY_200, ft.Colors.GREY_500, ft.Colors.GREY_700, ft.Colors.GREY_900
ft.Colors.BLUE, ft.Colors.BLUE_400, ft.Colors.BLUE_700
ft.Colors.RED, ft.Colors.RED_500
ft.Colors.GREEN_500
ft.Colors.AMBER_500
```

### A EVITER (causent des erreurs)

```python
ft.Colors.OUTLINE            # non garanti
ft.Colors.SURFACE_VARIANT    # n'existe pas
ft.Colors.SECONDARY          # acces direct non fiable
```

---

## Icones garanties

```python
# Navigation
ft.Icons.HOME, ft.Icons.HISTORY, ft.Icons.SEARCH, ft.Icons.SETTINGS
ft.Icons.CALENDAR_TODAY, ft.Icons.SHUFFLE, ft.Icons.BAR_CHART
ft.Icons.ARROW_BACK, ft.Icons.ARROW_FORWARD

# Favoris
ft.Icons.FAVORITE, ft.Icons.FAVORITE_BORDER

# Media
ft.Icons.IMAGE, ft.Icons.CONTENT_COPY, ft.Icons.LANGUAGE

# Status
ft.Icons.ERROR, ft.Icons.INFO, ft.Icons.WARNING, ft.Icons.CHECK_CIRCLE

# Actions
ft.Icons.CLOSE, ft.Icons.REFRESH, ft.Icons.ADD, ft.Icons.PETS

# Divers
ft.Icons.WIFI_OFF, ft.Icons.ACCOUNT_TREE, ft.Icons.SEARCH_OFF
```

### Icones qui N'EXISTENT PAS

```python
ft.Icons.HIDE_IMAGE
ft.Icons.IMAGE_NOT_SUPPORTED
ft.Icons.BROKEN_IMAGE
```

---

## Architecture async/await

### Regles fondamentales

1. `page.update()` est **toujours sync**, meme dans une fonction async
2. Apres `page.update()`, faire `await asyncio.sleep(0.1)` pour forcer le refresh UI
3. Utiliser `asyncio.to_thread(fn)` pour les operations bloquantes (DB, I/O)
4. Les event handlers UI peuvent etre `async def handler(self, e)`
5. `page.launch_url()` est async mais cassé par `@deprecated` — utiliser `page.run_task(ft.UrlLauncher().launch_url, url)`
6. `ft.Clipboard().set()` et `.get()` sont **async** — toujours `await`
7. `page.window.close()` est **async** — toujours `await`
8. `page.show_dialog()` est **sync** — pas de `await`
9. `page.pop_dialog()` est **sync** — pas de `await`
10. `page.update()` est **sync** — pas de `await`

### Pattern chargement async

```python
async def load_data(self, e=None):
    # 1. Afficher loading
    self.container.controls = [ft.ProgressRing(width=40, height=40)]
    self.page.update()
    await asyncio.sleep(0.1)  # laisser Flet rafraichir

    try:
        # 2. Operation bloquante dans un thread
        data = await asyncio.to_thread(self._fetch_data)

        # 3. Afficher le resultat
        self.container.controls = [ft.Text(data.name)]
    except Exception as error:
        self.container.controls = [
            ft.Icon(ft.Icons.ERROR, color=ft.Colors.ERROR),
            ft.Text(f"Erreur: {error}"),
        ]
    finally:
        self.page.update()
```

---

## Entree de l'application

```python
import flet as ft

def main(page: ft.Page):
    page.title = "Daynimal"
    page.add(ft.Text("Hello"))

ft.run(main=main)

# Ou avec async main :
async def main(page: ft.Page):
    page.title = "Daynimal"
    page.add(ft.Text("Hello"))

ft.run(main=main)
```

---

## ScrollMode

```python
ft.ScrollMode.AUTO       # scroll si contenu depasse
ft.ScrollMode.ALWAYS     # scrollbar toujours visible
ft.ScrollMode.HIDDEN     # scroll possible, scrollbar cachee
ft.ScrollMode.ADAPTIVE   # scrollbar visible au survol
```

---

## FontWeight

```python
ft.FontWeight.BOLD       # gras
ft.FontWeight.NORMAL     # normal
ft.FontWeight.W_500      # medium
ft.FontWeight.W_300      # light
# W_100 a W_900 disponibles
```

---

## Debugging

### `'super' object has no attribute '__getattr__'`

Cause : icone ou couleur inexistante. Verifier dans les listes garanties ci-dessus.

### Indicateur de chargement invisible

Cause : code synchrone bloque l'UI. Solution : async/await + `asyncio.to_thread()`.

### SnackBar ne s'affiche pas

Cause : utilisation de l'ancien API (`page.open()` ou `page.snack_bar`).
Solution : `page.show_dialog(ft.SnackBar(ft.Text("...")))`.

---

## Ressources

- **Flet Docs** : https://docs.flet.dev/
- **Icons Browser** : https://flet-icons-browser.fly.dev/
- **Colors Reference** : https://docs.flet.dev/types/colors/
- **Icons Reference** : https://docs.flet.dev/types/icons/
