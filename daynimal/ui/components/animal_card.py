"""Reusable animal card component for list views.

This module provides a clickable card widget used in History, Favorites, and Search views.
Eliminates 3 duplications from the original app.py.
"""

from typing import Callable

import flet as ft

from daynimal.schemas import AnimalInfo


class AnimalCard(ft.Card):
    """Reusable animal card for displaying an animal in a list.

    Used in:
    - History view (with timestamp)
    - Favorites view (with favorite icon)
    - Search view (with vernacular names)

    The card displays:
    - Canonical/scientific name (bold)
    - Scientific name in italics (blue)
    - Context-specific metadata (timestamp, favorite, vernacular names)
    - Arrow icon on right for navigation hint
    """

    def __init__(
        self,
        animal: AnimalInfo,
        on_click: Callable[[int], None],
        metadata_icon: ft.Icons | None = None,
        metadata_text: str | None = None,
        metadata_icon_color: str | None = None,
        **kwargs,
    ):
        """Initialize animal card.

        Args:
            animal: The animal to display.
            on_click: Callback when card is clicked. Receives taxon_id as parameter.
            metadata_icon: Optional icon for metadata row (e.g., HISTORY, FAVORITE).
            metadata_text: Optional text for metadata row (e.g., timestamp, vernacular names).
            metadata_icon_color: Optional color for metadata icon.
            **kwargs: Additional Card properties.
        """
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
                ft.Text(
                    metadata_text,
                    size=12,
                    color=ft.Colors.GREY_500,
                )
            )

        # Add spacer and arrow
        metadata_controls.extend(
            [
                ft.Container(expand=True),  # Spacer
                ft.Icon(
                    ft.Icons.ARROW_FORWARD,
                    size=16,
                    color=ft.Colors.GREY_400,
                ),
            ]
        )

        # Build card content
        content = ft.Container(
            content=ft.Column(
                controls=[
                    # Name row (canonical or scientific)
                    ft.Row(
                        controls=[
                            ft.Text(
                                animal.taxon.canonical_name
                                or animal.taxon.scientific_name,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            )
                        ]
                    ),
                    # Scientific name (always shown)
                    ft.Text(
                        animal.taxon.scientific_name,
                        size=14,
                        italic=True,
                        color=ft.Colors.BLUE,
                    ),
                    # Metadata row (timestamp, favorite, vernacular, etc.)
                    ft.Row(
                        controls=metadata_controls,
                        spacing=5,
                    ),
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
    animal: AnimalInfo,
    on_click: Callable[[int], None],
    viewed_at_str: str,
) -> AnimalCard:
    """Create an animal card for History view.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked.
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
    animal: AnimalInfo,
    on_click: Callable[[int], None],
) -> AnimalCard:
    """Create an animal card for Favorites view.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked.

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


def create_search_card(
    animal: AnimalInfo,
    on_click: Callable[[int], None],
) -> AnimalCard:
    """Create an animal card for Search view.

    Args:
        animal: The animal to display.
        on_click: Callback when card is clicked.

    Returns:
        AnimalCard configured for Search view (with vernacular names).
    """
    # Get vernacular names (first 2 from first language)
    vernacular = "Pas de nom vernaculaire"
    if animal.taxon.vernacular_names:
        first_lang = next(iter(animal.taxon.vernacular_names))
        names = animal.taxon.vernacular_names[first_lang][:2]
        if names:
            vernacular = ", ".join(names)
            if len(animal.taxon.vernacular_names[first_lang]) > 2:
                vernacular += "..."

    return AnimalCard(
        animal=animal,
        on_click=on_click,
        metadata_icon=None,  # No icon for search
        metadata_text=vernacular,
    )
