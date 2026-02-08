"""Tests for reusable UI widgets."""

import flet as ft

from daynimal.ui.components.widgets import (
    EmptyStateWidget,
    ErrorWidget,
    LoadingWidget,
)


def test_loading_widget_creation():
    """Test LoadingWidget can be created with default message."""
    widget = LoadingWidget()

    assert isinstance(widget, ft.Container)
    assert widget.content is not None
    assert isinstance(widget.content, ft.Column)

    # Should contain ProgressRing and Text
    controls = widget.content.controls
    assert len(controls) == 2
    assert isinstance(controls[0], ft.ProgressRing)
    assert isinstance(controls[1], ft.Text)
    assert controls[1].value == "Chargement..."


def test_loading_widget_custom_message():
    """Test LoadingWidget with custom message."""
    custom_message = "Chargement de l'animal..."
    widget = LoadingWidget(message=custom_message)

    controls = widget.content.controls
    assert controls[1].value == custom_message


def test_error_widget_creation():
    """Test ErrorWidget can be created with title only."""
    widget = ErrorWidget(title="Erreur")

    assert isinstance(widget, ft.Container)
    assert widget.content is not None
    assert isinstance(widget.content, ft.Column)

    # Should contain Icon and title Text
    controls = widget.content.controls
    assert len(controls) == 2
    assert isinstance(controls[0], ft.Icon)
    # Icon created with ft.Icons.ERROR
    assert isinstance(controls[1], ft.Text)
    assert controls[1].value == "Erreur"


def test_error_widget_with_details():
    """Test ErrorWidget with title and details."""
    widget = ErrorWidget(title="Erreur", details="Détails de l'erreur")

    controls = widget.content.controls
    # Should contain Icon, title Text, and details Text
    assert len(controls) == 3
    assert isinstance(controls[0], ft.Icon)
    assert isinstance(controls[1], ft.Text)
    assert controls[1].value == "Erreur"
    assert isinstance(controls[2], ft.Text)
    assert controls[2].value == "Détails de l'erreur"


def test_empty_state_widget_creation():
    """Test EmptyStateWidget can be created."""
    widget = EmptyStateWidget(
        icon=ft.Icons.INBOX,
        title="Aucun résultat",
        description="La liste est vide",
    )

    assert isinstance(widget, ft.Container)
    assert widget.content is not None
    assert isinstance(widget.content, ft.Column)

    # Should contain Icon, title Text, and description Text
    controls = widget.content.controls
    assert len(controls) == 3
    assert isinstance(controls[0], ft.Icon)
    # Icon created with ft.Icons.INBOX
    assert isinstance(controls[1], ft.Text)
    assert controls[1].value == "Aucun résultat"
    assert isinstance(controls[2], ft.Text)
    assert controls[2].value == "La liste est vide"


def test_empty_state_widget_custom_icon_properties():
    """Test EmptyStateWidget with custom icon size and color."""
    widget = EmptyStateWidget(
        icon=ft.Icons.SEARCH,
        title="Test",
        description="Test description",
        icon_size=100,
        icon_color=ft.Colors.BLUE_500,
    )

    icon = widget.content.controls[0]
    assert icon.size == 100
    assert icon.color == ft.Colors.BLUE_500
