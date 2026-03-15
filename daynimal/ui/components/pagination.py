"""Reusable pagination bar component."""

import math
from typing import Callable

import flet as ft


class PaginationBar:
    """Pagination bar: [|<] [<] Page X / Y [>] [>|]"""

    def __init__(
        self,
        page: int,
        total: int,
        per_page: int,
        on_page_change: Callable[[int], None],
    ):
        self.current_page = page
        self.total = total
        self.per_page = per_page
        self.on_page_change = on_page_change

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(self.total / self.per_page))

    def build(self) -> ft.Control:
        if self.total_pages <= 1:
            return ft.Container()

        is_first = self.current_page <= 1
        is_last = self.current_page >= self.total_pages

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.FIRST_PAGE,
                        disabled=is_first,
                        on_click=lambda _: self.on_page_change(1),
                        tooltip="Première page",
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT,
                        disabled=is_first,
                        on_click=lambda _: self.on_page_change(self.current_page - 1),
                        tooltip="Page précédente",
                    ),
                    ft.Text(
                        f"Page {self.current_page} / {self.total_pages}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT,
                        disabled=is_last,
                        on_click=lambda _: self.on_page_change(self.current_page + 1),
                        tooltip="Page suivante",
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LAST_PAGE,
                        disabled=is_last,
                        on_click=lambda _: self.on_page_change(self.total_pages),
                        tooltip="Dernière page",
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.Padding.symmetric(vertical=5),
        )
