"""Reusable UI widgets for Daynimal app.

This module eliminates code duplication by providing common widgets
used across multiple views.
"""

import flet as ft


class LoadingWidget(ft.Container):
    """Loading indicator widget.

    Displays a progress ring with a message. Used when loading data asynchronously.
    Replaces 6 duplicated implementations in the original app.py.
    """

    def __init__(
        self,
        message: str = "Chargement en cours...",
        subtitle: str | None = None,
        **kwargs,
    ):
        """Initialize loading widget.

        Args:
            message: Loading message to display.
            subtitle: Optional subtitle text below the message.
            **kwargs: Additional Container properties.
        """
        controls = [
            ft.ProgressRing(width=60, height=60),
            ft.Text(message, size=18, weight=ft.FontWeight.BOLD),
        ]
        if subtitle:
            controls.append(ft.Text(subtitle, size=14))

        super().__init__(
            content=ft.Column(
                controls=controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=40,
            expand=True,
            alignment=ft.Alignment(0, 0),
            **kwargs,
        )


class ErrorWidget(ft.Container):
    """Error display widget.

    Displays an error icon, title, and optional details.
    Replaces 7 duplicated implementations in the original app.py.
    """

    def __init__(self, title: str, details: str = "", **kwargs):
        """Initialize error widget.

        Args:
            title: Error title (short description).
            details: Optional error details (longer description).
            **kwargs: Additional Container properties.
        """
        controls = [
            ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
            ft.Text(title, size=20, color=ft.Colors.ERROR, weight=ft.FontWeight.BOLD),
        ]
        if details:
            controls.append(
                ft.Text(
                    details,
                    size=14,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        super().__init__(
            content=ft.Column(
                controls=controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=40,
            expand=True,
            alignment=ft.Alignment(0, 0),
            **kwargs,
        )


def view_header(
    title: str, actions: list[ft.Control] | None = None
) -> ft.Container:
    """Standard page header used by all views.

    Args:
        title: Title string, typically starting with an emoji (e.g. "🦁 Animal du jour").
        actions: Optional list of action controls displayed on the right side.

    Returns:
        A Container with bold primary-colored text and optional action buttons.
    """
    title_text = ft.Text(
        title, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY
    )

    if actions:
        row = ft.Row(
            controls=[title_text, ft.Row(controls=actions, spacing=5)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    else:
        row = ft.Row(
            controls=[title_text],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    return ft.Container(content=row, padding=10)


class EmptyStateWidget(ft.Container):
    """Empty state widget.

    Displays an icon, title, and description when a list/view is empty.
    Replaces 3 duplicated implementations in the original app.py.
    """

    def __init__(
        self,
        icon,
        title: str,
        description: str,
        icon_size: int = 80,
        icon_color: str = ft.Colors.GREY_500,
        **kwargs,
    ):
        """Initialize empty state widget.

        Args:
            icon: Flet icon to display.
            title: Title text.
            description: Description text.
            icon_size: Icon size in pixels.
            icon_color: Icon color (Flet color enum).
            **kwargs: Additional Container properties.
        """
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=icon_size, color=icon_color),
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        description,
                        size=14,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=40,
            expand=True,
            **kwargs,
        )
