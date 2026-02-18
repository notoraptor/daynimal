"""Tests for AnimalCard and card factory functions."""

from unittest.mock import MagicMock

import flet as ft

from daynimal.schemas import AnimalInfo, Taxon
from daynimal.ui.components.animal_card import (
    AnimalCard,
    create_favorite_card,
    create_history_card,
    create_search_card,
)


def _make_animal(
    taxon_id: int = 1,
    scientific_name: str = "Panthera leo",
    canonical_name: str = "Panthera",
    vernacular: dict | None = None,
) -> AnimalInfo:
    """Create a minimal AnimalInfo for testing."""
    return AnimalInfo(
        taxon=Taxon(
            taxon_id=taxon_id,
            scientific_name=scientific_name,
            canonical_name=canonical_name,
            rank="species",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            family="Felidae",
            genus="Panthera",
            parent_id=None,
            vernacular_names=vernacular or {},
        )
    )


def test_animal_card_creation():
    """Test AnimalCard can be created with minimal parameters."""
    animal = _make_animal()
    on_click = MagicMock()

    card = AnimalCard(animal=animal, on_click=on_click)

    assert isinstance(card, ft.Card)
    assert card.content is not None


def test_animal_card_displays_name():
    """Test AnimalCard displays the canonical name."""
    animal = _make_animal(canonical_name="Panthera", scientific_name="Panthera leo")
    on_click = MagicMock()

    card = AnimalCard(animal=animal, on_click=on_click)

    # The content is a Container wrapping a Column
    column = card.content.content
    assert isinstance(column, ft.Column)

    # First control is a Row with the name
    name_row = column.controls[0]
    assert isinstance(name_row, ft.Row)
    name_text = name_row.controls[0]
    assert name_text.value == "Panthera"


def test_animal_card_displays_scientific_name():
    """Test AnimalCard displays scientific name in italics."""
    animal = _make_animal(scientific_name="Panthera leo")
    on_click = MagicMock()

    card = AnimalCard(animal=animal, on_click=on_click)

    column = card.content.content
    sci_text = column.controls[1]
    assert isinstance(sci_text, ft.Text)
    assert sci_text.value == "Panthera leo"
    assert sci_text.italic is True


def test_animal_card_stores_taxon_id():
    """Test AnimalCard stores taxon_id in content data for click handling."""
    animal = _make_animal(taxon_id=42)
    on_click = MagicMock()

    card = AnimalCard(animal=animal, on_click=on_click)

    assert card.content.data == 42


def test_animal_card_on_click_callback():
    """Test AnimalCard on_click transmits the correct taxon_id."""
    animal = _make_animal(taxon_id=99)
    on_click = MagicMock()

    card = AnimalCard(animal=animal, on_click=on_click)

    # Simulate click by calling the on_click lambda
    mock_event = MagicMock()
    mock_event.control.data = 99
    card.content.on_click(mock_event)

    on_click.assert_called_once_with(99)


def test_animal_card_with_metadata():
    """Test AnimalCard displays metadata icon and text."""
    animal = _make_animal()
    on_click = MagicMock()

    card = AnimalCard(
        animal=animal,
        on_click=on_click,
        metadata_icon=ft.Icons.HISTORY,
        metadata_text="08/02/2026 14:30",
        metadata_icon_color=ft.Colors.GREY_500,
    )

    column = card.content.content
    metadata_row = column.controls[2]
    assert isinstance(metadata_row, ft.Row)
    # Should contain: icon, text, spacer, arrow
    icons = [c for c in metadata_row.controls if isinstance(c, ft.Icon)]
    texts = [c for c in metadata_row.controls if isinstance(c, ft.Text)]
    assert len(icons) == 2  # metadata icon + arrow
    assert len(texts) == 1
    assert texts[0].value == "08/02/2026 14:30"


def test_create_search_card_with_vernacular():
    """Test create_search_card shows vernacular name as primary and family as metadata."""
    animal = _make_animal(
        vernacular={"fr": ["Lion", "Lion d'Afrique", "Lion de l'Atlas"]}
    )
    on_click = MagicMock()

    card = create_search_card(animal, on_click)

    assert isinstance(card, AnimalCard)
    column = card.content.content
    # Primary name should be the first vernacular name
    primary_text = column.controls[0].controls[0]
    assert primary_text.value == "Lion"
    # Metadata should be the family name
    metadata_row = column.controls[2]
    texts = [c for c in metadata_row.controls if isinstance(c, ft.Text)]
    assert len(texts) == 1
    assert texts[0].value == "Felidae"


def test_create_search_card_without_vernacular():
    """Test create_search_card falls back to canonical name and still shows family."""
    animal = _make_animal(vernacular={})
    on_click = MagicMock()

    card = create_search_card(animal, on_click)

    column = card.content.content
    # Primary name falls back to canonical name
    primary_text = column.controls[0].controls[0]
    assert primary_text.value == "Panthera"
    # Metadata is the family
    metadata_row = column.controls[2]
    texts = [c for c in metadata_row.controls if isinstance(c, ft.Text)]
    assert len(texts) == 1
    assert texts[0].value == "Felidae"


def test_create_history_card():
    """Test create_history_card shows timestamp with history icon."""
    animal = _make_animal()
    on_click = MagicMock()

    card = create_history_card(animal, on_click, "08/02/2026 14:30")

    assert isinstance(card, AnimalCard)
    column = card.content.content
    metadata_row = column.controls[2]
    texts = [c for c in metadata_row.controls if isinstance(c, ft.Text)]
    assert len(texts) == 1
    assert texts[0].value == "08/02/2026 14:30"


def test_create_favorite_card():
    """Test create_favorite_card shows favorite icon in red."""
    animal = _make_animal()
    on_click = MagicMock()

    card = create_favorite_card(animal, on_click)

    assert isinstance(card, AnimalCard)
    column = card.content.content
    metadata_row = column.controls[2]
    icons = [c for c in metadata_row.controls if isinstance(c, ft.Icon)]
    # First icon should be the favorite icon (red), second is arrow
    assert len(icons) == 2
    favorite_icon = icons[0]
    assert favorite_icon.color == ft.Colors.RED
    texts = [c for c in metadata_row.controls if isinstance(c, ft.Text)]
    assert texts[0].value == "Favori"
