"""Reusable pagination bar component."""

import math
from typing import Callable

import flet as ft


class PaginationBar:
    """Pagination bar: [< Précédent]  Page X / Y  [Suivant >]"""

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

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Button(
                        "< Précédent",
                        disabled=self.current_page <= 1,
                        on_click=lambda _: self.on_page_change(self.current_page - 1),
                    ),
                    ft.Text(
                        f"Page {self.current_page} / {self.total_pages}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Button(
                        "Suivant >",
                        disabled=self.current_page >= self.total_pages,
                        on_click=lambda _: self.on_page_change(self.current_page + 1),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=ft.Padding.symmetric(vertical=10),
        )
