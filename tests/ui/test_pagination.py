"""Tests for PaginationBar component."""

from daynimal.ui.components.pagination import PaginationBar


def test_build_first_page():
    """First page: Précédent disabled, Suivant enabled."""
    bar = PaginationBar(page=1, total=100, per_page=20, on_page_change=lambda p: None)
    control = bar.build()
    row = control.content
    prev_btn, _, next_btn = row.controls
    assert prev_btn.disabled is True
    assert next_btn.disabled is False


def test_build_last_page():
    """Last page: Suivant disabled, Précédent enabled."""
    bar = PaginationBar(page=5, total=100, per_page=20, on_page_change=lambda p: None)
    control = bar.build()
    row = control.content
    prev_btn, _, next_btn = row.controls
    assert prev_btn.disabled is False
    assert next_btn.disabled is True


def test_build_middle_page():
    """Middle page: both buttons enabled."""
    bar = PaginationBar(page=3, total=100, per_page=20, on_page_change=lambda p: None)
    control = bar.build()
    row = control.content
    prev_btn, _, next_btn = row.controls
    assert prev_btn.disabled is False
    assert next_btn.disabled is False


def test_single_page():
    """Single page: returns empty container (no pagination needed)."""
    bar = PaginationBar(page=1, total=10, per_page=20, on_page_change=lambda p: None)
    control = bar.build()
    assert control.content is None  # Empty ft.Container


def test_page_text():
    """Page text shows correct format."""
    bar = PaginationBar(page=2, total=100, per_page=20, on_page_change=lambda p: None)
    control = bar.build()
    text = control.content.controls[1]
    assert text.value == "Page 2 / 5"


def test_on_page_change_callback():
    """Callback is called with correct page number."""
    received = []
    bar = PaginationBar(
        page=2, total=100, per_page=20, on_page_change=lambda p: received.append(p)
    )
    control = bar.build()
    row = control.content
    prev_btn, _, next_btn = row.controls

    # Click previous
    prev_btn.on_click(None)
    assert received == [1]

    # Click next
    next_btn.on_click(None)
    assert received == [1, 3]
