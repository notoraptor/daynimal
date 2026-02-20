"""Tests pour daynimal/ui/views/setup_view.py -- Vue Setup premier lancement.

Couvre: SetupView (build, _show_welcome, _on_start_click, _start_setup,
_update_progress), _global_progress.

Strategie: on mock download_and_setup_db et ft.Page. _global_progress
est une fonction pure directement testable. Pour _start_setup, on mock
asyncio.to_thread pour executer synchronement.
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import flet as ft
import pytest

from daynimal.ui.views.setup_view import _global_progress, SetupView


# =============================================================================
# Helpers
# =============================================================================


def _make_setup_view(on_complete=None):
    """Create a SetupView with mocked page and app_state."""
    page = MagicMock(spec=ft.Page)
    page.update = MagicMock()
    app_state = MagicMock()
    if on_complete is None:
        on_complete = MagicMock()
    view = SetupView(page=page, app_state=app_state, on_setup_complete=on_complete)
    return view, page, app_state, on_complete


def _find_controls_by_type(control, control_type):
    """Recursively find all controls of a given type in a control tree."""
    results = []
    if isinstance(control, control_type):
        results.append(control)
    for attr in ("controls", "content"):
        child = getattr(control, attr, None)
        if child is None:
            continue
        if isinstance(child, list):
            for c in child:
                results.extend(_find_controls_by_type(c, control_type))
        else:
            results.extend(_find_controls_by_type(child, control_type))
    return results


def _find_texts(container):
    """Find all ft.Text controls in the container tree."""
    return _find_controls_by_type(container, ft.Text)


def _find_icons(container):
    """Find all ft.Icon controls in the container tree."""
    return _find_controls_by_type(container, ft.Icon)


def _find_buttons(container):
    """Find all ft.Button controls in the container tree."""
    return _find_controls_by_type(container, ft.Button)


# =============================================================================
# SECTION 1 : _global_progress (fonction pure)
# =============================================================================


class TestGlobalProgress:
    """Tests pour _global_progress(stage, local_progress).

    Actual weights from source:
    - download_manifest: 0.02
    - download_taxa: 0.35
    - download_vernacular: 0.33
    - decompress: 0.05
    - build_db: 0.15
    - build_fts: 0.08
    - cleanup: 0.02
    Total: 1.00
    """

    def test_download_manifest_start(self):
        """Verifie que _global_progress('download_manifest', 0.0) retourne 0.0
        (debut du premier stage)."""
        result = _global_progress("download_manifest", 0.0)
        assert result == pytest.approx(0.0)

    def test_download_manifest_end(self):
        """Verifie que _global_progress('download_manifest', 1.0) retourne 0.02
        (fin du premier stage = poids du stage)."""
        result = _global_progress("download_manifest", 1.0)
        assert result == pytest.approx(0.02)

    def test_download_taxa_half(self):
        """Verifie que _global_progress('download_taxa', 0.5) retourne
        0.02 + 0.35 * 0.5 = 0.195 (milieu du deuxieme stage)."""
        result = _global_progress("download_taxa", 0.5)
        assert result == pytest.approx(0.02 + 0.35 * 0.5)

    def test_download_vernacular_complete(self):
        """Verifie que _global_progress('download_vernacular', 1.0) retourne
        0.02 + 0.35 + 0.33 = 0.70."""
        result = _global_progress("download_vernacular", 1.0)
        assert result == pytest.approx(0.02 + 0.35 + 0.33)

    def test_build_db_start(self):
        """Verifie que _global_progress('build_db', 0.0) retourne
        0.02 + 0.35 + 0.33 + 0.05 = 0.75."""
        result = _global_progress("build_db", 0.0)
        assert result == pytest.approx(0.02 + 0.35 + 0.33 + 0.05)

    def test_build_fts_complete(self):
        """Verifie que _global_progress('build_fts', 1.0) retourne
        0.02 + 0.35 + 0.33 + 0.05 + 0.15 + 0.08 = 0.98."""
        result = _global_progress("build_fts", 1.0)
        assert result == pytest.approx(0.02 + 0.35 + 0.33 + 0.05 + 0.15 + 0.08)

    def test_cleanup_complete(self):
        """Verifie que _global_progress('cleanup', 1.0) retourne 1.0
        (tous les stages completes)."""
        result = _global_progress("cleanup", 1.0)
        assert result == pytest.approx(1.0)

    def test_unknown_stage_returns_none(self):
        """Verifie que _global_progress('invalid_stage', 0.5) retourne None."""
        result = _global_progress("invalid_stage", 0.5)
        assert result is None

    def test_progress_none_returns_base(self):
        """Verifie que _global_progress('download_taxa', None) retourne
        la base du stage (0.02) sans ajouter de progression locale."""
        result = _global_progress("download_taxa", None)
        assert result == pytest.approx(0.02)


# =============================================================================
# SECTION 2 : SetupView.build / _show_welcome
# =============================================================================


class TestSetupViewBuild:
    """Tests pour build() et _show_welcome()."""

    def test_build_calls_show_welcome(self):
        """Verifie que build() appelle _show_welcome() et retourne
        self.container."""
        view, page, app_state, on_complete = _make_setup_view()
        result = view.build()
        # build() must return self.container
        assert result is view.container
        # container should have controls populated by _show_welcome
        assert len(view.container.controls) > 0

    def test_show_welcome_has_app_icon(self):
        """Verifie que _show_welcome affiche l'icone PETS de l'application."""
        view, page, app_state, on_complete = _make_setup_view()
        view.build()
        icons = _find_icons(view.container)
        pets_icons = [i for i in icons if i.icon == ft.Icons.PETS]
        assert len(pets_icons) >= 1
        assert pets_icons[0].size == 80

    def test_show_welcome_has_title(self):
        """Verifie que _show_welcome affiche le titre 'Bienvenue dans Daynimal !'
        ou equivalent."""
        view, page, app_state, on_complete = _make_setup_view()
        view.build()
        texts = _find_texts(view.container)
        title_texts = [t for t in texts if "Bienvenue" in (t.value or "")]
        assert len(title_texts) >= 1
        assert "Daynimal" in title_texts[0].value

    def test_show_welcome_has_commencer_button(self):
        """Verifie que _show_welcome cree un bouton 'Commencer' avec
        on_click connecte a _on_start_click."""
        view, page, app_state, on_complete = _make_setup_view()
        view.build()
        buttons = _find_buttons(view.container)
        commencer_buttons = [
            b
            for b in buttons
            if getattr(b, "text", None) == "Commencer"
            or getattr(b, "content", None) == "Commencer"
        ]
        assert len(commencer_buttons) == 1
        assert commencer_buttons[0].on_click == view._on_start_click


# =============================================================================
# SECTION 3 : _on_start_click / _start_setup
# =============================================================================


class TestSetupViewStartSetup:
    """Tests pour _on_start_click et _start_setup."""

    @patch("asyncio.create_task")
    def test_on_start_click_creates_async_task(self, mock_create_task):
        """Verifie que _on_start_click lance _start_setup via
        asyncio.create_task."""
        view, page, app_state, on_complete = _make_setup_view()
        view.build()
        view._on_start_click(MagicMock())
        mock_create_task.assert_called_once()
        # The argument should be a coroutine from _start_setup()
        coro = mock_create_task.call_args[0][0]
        assert asyncio.iscoroutine(coro)
        # Clean up the coroutine to avoid RuntimeWarning
        coro.close()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    @patch("daynimal.db.first_launch.download_and_setup_db")
    async def test_start_setup_success(self, mock_download, mock_to_thread, mock_sleep):
        """Verifie le parcours succes de _start_setup:
        1. Affiche un ecran de progression avec ProgressBar
        2. Appelle download_and_setup_db(self._update_progress) en thread
        3. Affiche l'icone CHECK_CIRCLE et 'Tout est pret !'
        4. Attend puis appelle on_setup_complete()"""
        on_complete = MagicMock()
        view, page, app_state, _ = _make_setup_view(on_complete=on_complete)
        view.build()

        await view._start_setup()

        # to_thread was called with download_and_setup_db and progress cb
        mock_to_thread.assert_called_once_with(mock_download, view._update_progress)

        # After success, container should show CHECK_CIRCLE icon
        icons = _find_icons(view.container)
        check_icons = [i for i in icons if i.icon == ft.Icons.CHECK_CIRCLE]
        assert len(check_icons) >= 1

        # Should show "Tout est pret !" text
        texts = _find_texts(view.container)
        pret_texts = [
            t
            for t in texts
            if "pret" in (t.value or "").lower()
            or "pr\u00eat" in (t.value or "").lower()
        ]
        assert len(pret_texts) >= 1

        # on_setup_complete should have been called
        on_complete.assert_called_once()

        # page.update should have been called multiple times
        assert page.update.call_count >= 1

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    @patch("daynimal.db.first_launch.download_and_setup_db")
    async def test_start_setup_calls_on_complete(
        self, mock_download, mock_to_thread, mock_sleep
    ):
        """Verifie que on_setup_complete (callback) est bien appele
        a la fin du setup reussi."""
        on_complete = MagicMock()
        view, page, app_state, _ = _make_setup_view(on_complete=on_complete)
        view.build()

        await view._start_setup()
        on_complete.assert_called_once()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    @patch("daynimal.db.first_launch.download_and_setup_db")
    async def test_start_setup_error_shows_retry(
        self, mock_download, mock_to_thread, mock_sleep
    ):
        """Verifie le parcours erreur de _start_setup:
        1. download_and_setup_db leve une exception
        2. Affiche l'icone ERROR et le message d'erreur
        3. Affiche un bouton 'Reessayer' qui relance _start_setup."""
        mock_to_thread.side_effect = Exception("Network error")

        on_complete = MagicMock()
        view, page, app_state, _ = _make_setup_view(on_complete=on_complete)
        view.build()

        await view._start_setup()

        # on_setup_complete should NOT have been called
        on_complete.assert_not_called()

        # Should show ERROR icon
        icons = _find_icons(view.container)
        error_icons = [i for i in icons if i.icon == ft.Icons.ERROR]
        assert len(error_icons) >= 1

        # Should show the error message text
        texts = _find_texts(view.container)
        error_texts = [t for t in texts if "Network error" in (t.value or "")]
        assert len(error_texts) >= 1

        # Should show "Reessayer" button
        buttons = _find_buttons(view.container)
        retry_buttons = [
            b
            for b in buttons
            if "essayer"
            in (getattr(b, "text", None) or getattr(b, "content", None) or "").lower()
        ]
        assert len(retry_buttons) == 1
        # The retry button should be wired to _on_start_click
        assert retry_buttons[0].on_click == view._on_start_click


# =============================================================================
# SECTION 4 : _update_progress
# =============================================================================


class TestSetupViewUpdateProgress:
    """Tests pour _update_progress(stage, progress)."""

    def _setup_progress_view(self):
        """Create a SetupView with progress bar and status text initialized."""
        view, page, app_state, on_complete = _make_setup_view()
        view.build()
        # Manually set up progress_bar and status_text as _start_setup would
        view.progress_bar = ft.ProgressBar(value=0, width=400)
        view.status_text = ft.Text("", size=14)
        return view, page

    def test_sets_progress_bar_value(self):
        """Verifie que _update_progress appelle _global_progress(stage, progress)
        et met a jour self.progress_bar.value avec le resultat."""
        view, page = self._setup_progress_view()

        view._update_progress("download_taxa", 0.5)

        expected = _global_progress("download_taxa", 0.5)
        assert view.progress_bar.value == pytest.approx(expected)

    def test_sets_status_text(self):
        """Verifie que _update_progress met a jour self.status_text.value
        avec le label correspondant au stage (ex: 'Telechargement des donnees...'
        pour 'download_taxa')."""
        view, page = self._setup_progress_view()

        view._update_progress("download_taxa", 0.5)
        assert "chargement" in view.status_text.value.lower()

        view._update_progress("build_db", 0.0)
        assert (
            "base" in view.status_text.value.lower()
            or "connaissance" in view.status_text.value.lower()
        )

        view._update_progress("cleanup", None)
        assert "Finalisation" in view.status_text.value

    def test_calls_page_update(self):
        """Verifie que _update_progress appelle page.update() pour
        rafraichir l'affichage."""
        view, page = self._setup_progress_view()
        page.update.reset_mock()

        view._update_progress("download_manifest", 0.5)

        page.update.assert_called()
