"""Reusable animal card component for list views.

This module provides a clickable card widget used in History, Favorites, and Search views.
Eliminates 3 duplications from the original app.py.
"""

from typing import Callable

import flet as ft

from daynimal.config import settings
from daynimal.schemas import AnimalInfo, Taxon


def _get_display_name(taxon: Taxon) -> str:
    """Return the best display name for a taxon.

    Priority: first vernacular name in preferred language > canonical name > scientific name.

    Args:
        taxon: The taxon to get a display name for.

    Returns:
        The best available display name string.
    """
    if taxon.vernacular_names:
        for lang in settings.wikipedia_languages:
            names = taxon.vernacular_names.get(lang, [])
            if names:
                return names[0]
    return taxon.canonical_name or taxon.scientific_name


class AnimalCard(ft.Card):
    """Reusable animal card for displaying an animal in a list.

    Used in:
    - History view (with timestamp)
    - Favorites view (with favorite icon)
    - Search view (with taxonomic family)

    The card displays:
    - Vernacular name if available, else canonical/scientific name (bold)
    - Scientific name in italics (blue)
    - Context-specific metadata (timestamp, favorite, family, etc.)
    - Arrow icon on right for navigation hint
    """

    def __init__(
        self,
        animal: AnimalInfo,
        on_click: Callable[[int], None],
        metadata_icon: str | None = None,
        metadata_text: str | None = None,
        metadata_icon_color: str | None = None,
        **kwargs,
    ):
        """Initialize animal card.

        Args:
            animal: The animal to display.
            on_click: Callback when card is clicked. Receives taxon_id as parameter.
            metadata_icon: Optional icon for metadata row (e.g., HISTORY, FAVORITE).
            metadata_text: Optional text for metadata row (e.g., timestamp, family name).
            metadata_icon_color: Optional color for metadata icon.
            **kwargs: Additional Card properties.
        """
        display_name = _get_display_name(animal.taxon)

        # Build metadata controls (icon + text)
        metadata_controls = []
        if metadata_icon:
            metadata_controls.append(
                ft.Icon(
                    metadata_icon,
                    size=16,
                    color=metadata_icon_color or ft.Colors.GREY_500,
                )
            )
        if metadata_text:
            metadata_controls.append(
                ft.Text(metadata_text, size=12, color=ft.Colors.GREY_500)
            )

        # Add spacer and arrow
        metadata_controls.extend(
            [
                ft.Container(expand=True),  # Spacer
                ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=ft.Colors.GREY_400),
            ]
        )

        # Build card content
        content = ft.Container(
            content=ft.Column(
                controls=[
                    # Primary name (vernacular if available, else canonical/scientific)
                    ft.Row(
                        controls=[
                            ft.Text(display_name, size=18, weight=ft.FontWeight.BOLD)
                        ]
                    ),
                    # Scientific name (always shown in italics)
                    ft.Text(
                        animal.taxon.scientific_name,
                        size=14,
                        italic=True,
                        color=ft.Colors.BLUE,
                    ),
                    # Metadata row (timestamp, favorite, family, etc.)
                    ft.Row(controls=metadata_controls, spacing=5),
                ],
                spacing=5,
            ),
            padding=15,
            data=animal.taxon.taxon_id,  # Store taxon_id for click handler
            on_click=lambda e: on_click(e.control.data),
            ink=True,  # Add ink ripple effect on click
        )

        super().__init__(content=content, **kwargs)


def create_history_card(
    animal: AnimalInfo, on_click: Callable[[int], None], viewed_at_str: str
) -> AnimalCard:
    """Create an animal card for History view.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked. Receives taxon_id.
        viewed_at_str: Formatted timestamp string (e.g., "08/02/2026 14:30").

    Returns:
        AnimalCard configured for History view.
    """
    return AnimalCard(
        animal=animal,
        on_click=on_click,
        metadata_icon=ft.Icons.HISTORY,
        metadata_text=viewed_at_str,
        metadata_icon_color=ft.Colors.GREY_500,
    )


def create_favorite_card(
    animal: AnimalInfo, on_click: Callable[[int], None]
) -> AnimalCard:
    """Create an animal card for Favorites view.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked. Receives taxon_id.

    Returns:
        AnimalCard configured for Favorites view.
    """
    return AnimalCard(
        animal=animal,
        on_click=on_click,
        metadata_icon=ft.Icons.FAVORITE,
        metadata_text="Favori",
        metadata_icon_color=ft.Colors.RED,
    )


def create_history_card_with_delete(
    animal: AnimalInfo,
    on_click: Callable[[int], None],
    viewed_at_str: str,
    on_delete: Callable[[int, str], None],
) -> ft.Row:
    """Create a history card with a delete button.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked. Receives taxon_id.
        viewed_at_str: Formatted timestamp string.
        on_delete: Callback when delete is clicked. Receives (history_id, display_name).

    Returns:
        ft.Row containing the AnimalCard (expand) and a delete IconButton.
    """
    card = create_history_card(animal, on_click, viewed_at_str)
    card.expand = True
    history_id = animal.history_id
    display_name = _get_display_name(animal.taxon)

    delete_btn = ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_color=ft.Colors.GREY_500,
        tooltip="Supprimer de l'historique",
        on_click=lambda e: on_delete(history_id, display_name),
    )

    return ft.Row(
        controls=[card, delete_btn],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def create_favorite_card_with_delete(
    animal: AnimalInfo,
    on_click: Callable[[int], None],
    on_delete: Callable[[int, str], None],
) -> ft.Row:
    """Create a favorite card with a delete button.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked. Receives taxon_id.
        on_delete: Callback when delete is clicked. Receives (taxon_id, display_name).

    Returns:
        ft.Row containing the AnimalCard (expand) and a delete IconButton.
    """
    card = create_favorite_card(animal, on_click)
    card.expand = True
    taxon_id = animal.taxon.taxon_id
    display_name = _get_display_name(animal.taxon)

    delete_btn = ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_color=ft.Colors.GREY_500,
        tooltip="Retirer des favoris",
        on_click=lambda e: on_delete(taxon_id, display_name),
    )

    return ft.Row(
        controls=[card, delete_btn],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def create_search_card(
    animal: AnimalInfo, on_click: Callable[[int], None]
) -> AnimalCard:
    """Create an animal card for Search view.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked. Receives taxon_id.

    Returns:
        AnimalCard configured for Search view (with taxonomic family as metadata).
    """
    family = animal.taxon.family or animal.taxon.order or ""
    return AnimalCard(
        animal=animal,
        on_click=on_click,
        metadata_icon=ft.Icons.ACCOUNT_TREE,
        metadata_text=family,
        metadata_icon_color=ft.Colors.GREY_500,
    )
