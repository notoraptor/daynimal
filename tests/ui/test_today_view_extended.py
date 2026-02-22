"""Tests pour daynimal/ui/views/today_view.py — Vue Aujourd'hui.

Couvre: TodayView (build, _load_random_animal, _display_animal,
_on_favorite_toggle, _open_gallery, _on_copy_text, _on_open_wikipedia).

Note: test_sharing.py teste déjà _build_share_text (5 tests). Ce fichier
couvre le reste de TodayView (103 lignes manquantes).

Stratégie: on mock AppState.repository et ft.Page. Pour les méthodes
async, on utilise pytest-asyncio. On vérifie que les handlers appellent
les bonnes méthodes du repository et mettent à jour l'UI.
"""

from unittest.mock import MagicMock, patch, AsyncMock

import flet as ft
import pytest

from daynimal.schemas import (
    AnimalInfo,
    CommonsImage,
    License,
    Taxon,
    TaxonomicRank,
    WikipediaArticle,
    WikidataEntity,
    ConservationStatus,
)
from daynimal.ui.views.today_view import TodayView
from daynimal.ui.components.widgets import LoadingWidget, ErrorWidget


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page():
    """Mock de ft.Page."""
    page = MagicMock(spec=ft.Page)
    page.update = MagicMock()
    page.show_dialog = MagicMock()
    page.pop_dialog = MagicMock()
    page.run_task = MagicMock()
    return page


@pytest.fixture
def mock_app_state():
    """Mock d'AppState avec repository, image_cache, is_online."""
    state = MagicMock()
    state.repository = MagicMock()
    state.repository.is_favorite = MagicMock(return_value=False)
    state.image_cache = MagicMock()
    state.image_cache.get_local_path = MagicMock(return_value=None)
    state.image_cache.are_all_cached = MagicMock(return_value=False)
    state.is_online = True
    state.current_animal = None
    return state


@pytest.fixture
def sample_animal():
    """Crée un AnimalInfo pour les tests d'affichage."""
    taxon = Taxon(
        taxon_id=12345,
        scientific_name="Canis lupus",
        canonical_name="Canis lupus",
        rank=TaxonomicRank.SPECIES,
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Canidae",
        genus="Canis",
        vernacular_names={"fr": ["Loup gris"], "en": ["Grey Wolf"]},
    )
    wikipedia = WikipediaArticle(
        title="Loup gris",
        language="fr",
        page_id=1234,
        summary="Le loup gris est un mammifère carnivore.",
        url="https://fr.wikipedia.org/wiki/Loup_gris",
    )
    wikidata = WikidataEntity(
        qid="Q18498",
        labels={"fr": "Loup gris", "en": "Grey Wolf"},
        descriptions={"fr": "mammifère carnivore"},
        iucn_status=ConservationStatus.LEAST_CONCERN,
        mass="40 kg",
        lifespan="13 ans",
    )
    images = [
        CommonsImage(
            filename="Wolf1.jpg",
            url="https://upload.wikimedia.org/wolf1.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/wolf1.jpg",
            author="John Doe",
            license=License.CC_BY_SA,
            description="A grey wolf",
        ),
        CommonsImage(
            filename="Wolf2.jpg",
            url="https://upload.wikimedia.org/wolf2.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/wolf2.jpg",
            author="Jane Doe",
            license=License.CC_BY,
            description="Another wolf",
        ),
    ]
    return AnimalInfo(
        taxon=taxon,
        wikidata=wikidata,
        wikipedia=wikipedia,
        images=images,
        is_enriched=True,
    )


def _make_view(mock_page, mock_app_state, on_favorite_toggle=None):
    """Helper to create a TodayView with mocked dependencies."""
    view = TodayView(
        page=mock_page, app_state=mock_app_state, on_favorite_toggle=on_favorite_toggle
    )
    return view


def _find_controls_recursive(control, predicate, results=None):
    """Recursively search for controls matching a predicate."""
    if results is None:
        results = []
    if predicate(control):
        results.append(control)
    # Check common container attributes
    for attr in ("controls", "content"):
        child = getattr(control, attr, None)
        if child is not None:
            if isinstance(child, list):
                for c in child:
                    _find_controls_recursive(c, predicate, results)
            else:
                _find_controls_recursive(child, predicate, results)
    return results


def _find_text_values(control):
    """Recursively collect all ft.Text.value strings from a control tree."""
    texts = []
    if isinstance(control, ft.Text):
        texts.append(control.value)
    for attr in ("controls", "content"):
        child = getattr(control, attr, None)
        if child is not None:
            if isinstance(child, list):
                for c in child:
                    texts.extend(_find_text_values(c))
            else:
                texts.extend(_find_text_values(child))
    return texts


# =============================================================================
# SECTION 1 : TodayView.build
# =============================================================================


class TestTodayViewBuild:
    """Tests pour TodayView.build()."""

    def test_shows_welcome_when_no_animal(self, mock_page, mock_app_state):
        """Vérifie que build() sans current_animal dans app_state affiche
        un message de bienvenue (texte contenant 'Bienvenue' ou 'Découvrez')
        dans today_animal_container."""
        view = _make_view(mock_page, mock_app_state)
        view.current_animal = None
        view.build()

        # The today_animal_container should have welcome text
        container_controls = view.today_animal_container.controls
        assert len(container_controls) > 0

        # Collect all text values from the container
        all_texts = []
        for ctrl in container_controls:
            all_texts.extend(_find_text_values(ctrl))

        text_blob = " ".join(t for t in all_texts if t)
        assert "Bienvenue" in text_blob or "Découvrez" in text_blob

    def test_restores_animal_if_cached(self, mock_page, mock_app_state, sample_animal):
        """Vérifie que build() avec app_state.current_animal défini appelle
        _display_animal pour restaurer l'affichage de l'animal en cours."""
        view = _make_view(mock_page, mock_app_state)
        view.current_animal = sample_animal
        view.build()

        # After build with a cached animal, _display_animal should have been called
        # which populates today_animal_container with the animal's controls
        container_controls = view.today_animal_container.controls
        assert len(container_controls) > 0

        # Should contain the animal's display name (uppercase)
        all_texts = []
        for ctrl in container_controls:
            all_texts.extend(_find_text_values(ctrl))
        text_blob = " ".join(t for t in all_texts if t)
        assert sample_animal.display_name.upper() in text_blob

    def test_has_random_button_in_title_actions(self, mock_page, mock_app_state):
        """Vérifie que view_title_actions contient un IconButton SHUFFLE
        avec le handler _load_random_animal."""
        view = _make_view(mock_page, mock_app_state)

        assert len(view.view_title_actions) == 1
        btn = view.view_title_actions[0]
        assert isinstance(btn, ft.IconButton)
        assert btn.icon == ft.Icons.SHUFFLE
        assert btn.on_click == view._load_random_animal


# =============================================================================
# SECTION 2 : Loading animals
# =============================================================================


class TestTodayViewLoadAnimal:
    """Tests pour _load_random_animal."""

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.asyncio.to_thread")
    async def test_load_random_animal_calls_get_random(
        self, mock_to_thread, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _load_random_animal appelle repo.get_random()
        via asyncio.to_thread."""
        mock_app_state.repository.get_random.return_value = sample_animal
        view = _make_view(mock_page, mock_app_state)
        view.build()

        async def run_closure(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = run_closure
        await view._load_random_animal(None)

        mock_app_state.repository.get_random.assert_called_once()

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.asyncio.to_thread")
    async def test_load_random_animal_adds_to_history(
        self, mock_to_thread, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que repo.add_to_history est appelé avec command='random'."""
        mock_app_state.repository.get_random.return_value = sample_animal
        view = _make_view(mock_page, mock_app_state)
        view.build()

        async def run_closure(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = run_closure
        await view._load_random_animal(None)

        mock_app_state.repository.add_to_history.assert_called_once_with(
            sample_animal.taxon.taxon_id, command="random"
        )

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.today_view.asyncio.to_thread")
    async def test_shows_loading_during_fetch(
        self, mock_to_thread, _mock_sleep, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que pendant le chargement, today_animal_container.controls
        contient un LoadingWidget."""
        loading_captured = []

        mock_app_state.repository.get_random.return_value = sample_animal

        view = _make_view(mock_page, mock_app_state)
        view.build()

        def capture_loading(*args, **kwargs):
            # Capture controls at the moment page.update is called
            controls = list(view.today_animal_container.controls)
            loading_captured.append(controls)

        mock_page.update.side_effect = capture_loading

        async def run_closure(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = run_closure

        await view._load_random_animal(None)

        # The first page.update() call should have a LoadingWidget
        assert len(loading_captured) > 0
        first_update_controls = loading_captured[0]
        assert any(isinstance(c, LoadingWidget) for c in first_update_controls)

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.today_view.asyncio.to_thread")
    async def test_error_shows_error_widget(
        self, mock_to_thread, _mock_sleep, mock_page, mock_app_state
    ):
        """Vérifie que si repo.get_random lève une exception,
        un ErrorWidget est affiché dans today_animal_container."""
        mock_app_state.repository.get_random.side_effect = RuntimeError("DB error")

        view = _make_view(mock_page, mock_app_state)
        view.build()

        async def run_closure(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = run_closure

        await view._load_random_animal(None)

        # After error, today_animal_container should contain an ErrorWidget
        controls = view.today_animal_container.controls
        assert any(isinstance(c, ErrorWidget) for c in controls)

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.today_view.asyncio.to_thread")
    async def test_none_result_shows_error(
        self, mock_to_thread, _mock_sleep, mock_page, mock_app_state
    ):
        """Vérifie que si le repository retourne None,
        un message d'erreur est affiché."""
        # When get_random returns None, calling .taxon.taxon_id
        # on None will raise AttributeError, which triggers the error path
        mock_app_state.repository.get_random.return_value = None

        view = _make_view(mock_page, mock_app_state)
        view.build()

        async def run_closure(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = run_closure

        await view._load_random_animal(None)

        # Should show error because None doesn't have .taxon
        controls = view.today_animal_container.controls
        assert any(isinstance(c, ErrorWidget) for c in controls)

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.today_view.asyncio.to_thread")
    async def test_calls_on_load_complete(
        self, mock_to_thread, _mock_sleep, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que on_load_complete() est appelé après le chargement
        réussi (callback optionnel défini par AppController)."""
        mock_app_state.repository.get_random.return_value = sample_animal
        view = _make_view(mock_page, mock_app_state)
        view.build()

        on_load_complete_mock = MagicMock()
        view.on_load_complete = on_load_complete_mock

        async def run_closure(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        mock_to_thread.side_effect = run_closure

        await view._load_random_animal(None)

        on_load_complete_mock.assert_called_once()


# =============================================================================
# SECTION 3 : Display animal
# =============================================================================


class TestTodayViewDisplayAnimal:
    """Tests pour _display_animal."""

    def test_shows_animal_display_controls(
        self, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _display_animal ajoute les contrôles de AnimalDisplay
        dans today_animal_container (titre, classification, etc.)."""
        view = _make_view(mock_page, mock_app_state)
        view.build()
        view._display_animal(sample_animal)

        controls = view.today_animal_container.controls
        assert len(controls) > 0

        # Collect all text values
        all_texts = []
        for ctrl in controls:
            all_texts.extend(_find_text_values(ctrl))

        text_blob = " ".join(t for t in all_texts if t)

        # Should contain the display name in uppercase
        assert sample_animal.display_name.upper() in text_blob
        # Should contain classification info
        assert "Classification" in text_blob
        # Should contain the scientific name
        assert sample_animal.taxon.scientific_name in text_blob

    def test_shows_favorite_button(self, mock_page, mock_app_state, sample_animal):
        """Vérifie qu'un bouton favori (IconButton avec FAVORITE/FAVORITE_BORDER)
        est créé. Si l'animal est favori, l'icône est FAVORITE (plein),
        sinon FAVORITE_BORDER (contour)."""
        # Test when NOT favorite
        mock_app_state.repository.is_favorite.return_value = False
        view = _make_view(mock_page, mock_app_state)
        view.build()
        view._display_animal(sample_animal)

        icon_buttons = _find_controls_recursive(
            view.today_animal_container,
            lambda c: (
                isinstance(c, ft.IconButton)
                and getattr(c, "icon", None)
                in (ft.Icons.FAVORITE, ft.Icons.FAVORITE_BORDER)
            ),
        )
        assert len(icon_buttons) >= 1
        fav_btn = icon_buttons[0]
        assert fav_btn.icon == ft.Icons.FAVORITE_BORDER

        # Test when IS favorite
        mock_app_state.repository.is_favorite.return_value = True
        view2 = _make_view(mock_page, mock_app_state)
        view2.build()
        view2._display_animal(sample_animal)

        icon_buttons2 = _find_controls_recursive(
            view2.today_animal_container,
            lambda c: (
                isinstance(c, ft.IconButton)
                and getattr(c, "icon", None)
                in (ft.Icons.FAVORITE, ft.Icons.FAVORITE_BORDER)
            ),
        )
        assert len(icon_buttons2) >= 1
        fav_btn2 = icon_buttons2[0]
        assert fav_btn2.icon == ft.Icons.FAVORITE

    def test_shows_share_buttons(self, mock_page, mock_app_state, sample_animal):
        """Vérifie que les boutons de partage (copier texte, ouvrir Wikipedia)
        sont présents dans les contrôles."""
        view = _make_view(mock_page, mock_app_state)
        view.build()
        view._display_animal(sample_animal)

        # Find all icon buttons
        icon_buttons = _find_controls_recursive(
            view.today_animal_container, lambda c: isinstance(c, ft.IconButton)
        )

        icons = [getattr(b, "icon", None) for b in icon_buttons]
        assert ft.Icons.CONTENT_COPY in icons, "Copy text button not found"
        assert ft.Icons.LANGUAGE in icons, "Wikipedia button not found"

    def test_shows_image_when_available(self, mock_page, mock_app_state):
        """Vérifie que quand l'animal a des images, un ft.Image est affiché
        avec l'URL/chemin local de la première image."""
        taxon = Taxon(
            taxon_id=999,
            scientific_name="Testus imagus",
            canonical_name="Testus imagus",
            rank=TaxonomicRank.SPECIES,
            vernacular_names={"en": ["Test Image Animal"]},
        )
        image = CommonsImage(
            filename="test.jpg",
            url="https://example.com/test.jpg",
            thumbnail_url="https://example.com/thumb/test.jpg",
            author="Tester",
            license=License.CC_BY,
        )
        animal = AnimalInfo(taxon=taxon, images=[image])

        view = _make_view(mock_page, mock_app_state)
        view.build()
        view._display_animal(animal)

        # Find ft.Image controls
        images_found = _find_controls_recursive(
            view.today_animal_container, lambda c: isinstance(c, ft.Image)
        )
        assert len(images_found) >= 1
        assert images_found[0].src == "https://example.com/test.jpg"

    def test_no_images_no_gallery_button(self, mock_page, mock_app_state):
        """Vérifie que quand images est vide, le bouton 'Plus d'images'
        n'est PAS affiché."""
        taxon = Taxon(
            taxon_id=888,
            scientific_name="Testus noimago",
            canonical_name="Testus noimago",
            rank=TaxonomicRank.SPECIES,
            vernacular_names={"en": ["No Image Animal"]},
        )
        animal = AnimalInfo(taxon=taxon, images=[])

        view = _make_view(mock_page, mock_app_state)
        view.build()
        view._display_animal(animal)

        # Should not have a "Plus d'images" button
        buttons = _find_controls_recursive(
            view.today_animal_container, lambda c: isinstance(c, ft.Button)
        )
        gallery_buttons = [
            b
            for b in buttons
            if b.content and isinstance(b.content, str) and "Plus d'images" in b.content
        ]
        assert len(gallery_buttons) == 0

        # Should show "Aucune image disponible"
        all_texts = []
        for ctrl in view.today_animal_container.controls:
            all_texts.extend(_find_text_values(ctrl))
        text_blob = " ".join(t for t in all_texts if t)
        assert "Aucune image disponible" in text_blob

    def test_multiple_images_shows_gallery_button(self, mock_page, mock_app_state):
        """Vérifie que quand l'animal a plus d'une image, un bouton
        'Plus d'images' est affiché pour ouvrir la galerie."""
        taxon = Taxon(
            taxon_id=777,
            scientific_name="Testus multimago",
            canonical_name="Testus multimago",
            rank=TaxonomicRank.SPECIES,
            vernacular_names={"en": ["Multi Image Animal"]},
        )
        images = [
            CommonsImage(
                filename="img1.jpg",
                url="https://example.com/img1.jpg",
                author="Author1",
                license=License.CC_BY,
            ),
            CommonsImage(
                filename="img2.jpg",
                url="https://example.com/img2.jpg",
                author="Author2",
                license=License.CC_BY_SA,
            ),
        ]
        animal = AnimalInfo(taxon=taxon, images=images)

        view = _make_view(mock_page, mock_app_state)
        view.build()
        view._display_animal(animal)

        buttons = _find_controls_recursive(
            view.today_animal_container, lambda c: isinstance(c, ft.Button)
        )
        gallery_buttons = [
            b
            for b in buttons
            if b.content and isinstance(b.content, str) and "Plus d'images" in b.content
        ]
        assert len(gallery_buttons) == 1

    def test_updates_current_animal_on_display(
        self, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _display_animal met à jour today_animal_container
        avec les contrôles de l'animal affiché. Note: current_animal est
        mis à jour dans _load_animal_for_today_view, pas dans _display_animal."""
        view = _make_view(mock_page, mock_app_state)
        view.build()

        # Manually set current_animal as _load_animal_for_today_view would
        view.current_animal = sample_animal
        view._display_animal(sample_animal)

        # Verify the display was populated
        controls = view.today_animal_container.controls
        assert len(controls) > 0


# =============================================================================
# SECTION 4 : Favorite toggle
# =============================================================================


class TestTodayViewFavoriteToggle:
    """Tests pour _on_favorite_toggle."""

    def test_calls_callback_with_correct_args(
        self, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _on_favorite_toggle appelle on_favorite_toggle_callback
        avec (taxon_id, is_favorite). Le callback est fourni par AppController."""
        callback = MagicMock()
        view = _make_view(mock_page, mock_app_state, on_favorite_toggle=callback)
        view.build()
        view.current_animal = sample_animal

        # is_favorite returns False
        mock_app_state.repository.is_favorite.return_value = False

        # Simulate click event with data = taxon_id
        event = MagicMock()
        event.control = MagicMock()
        event.control.data = sample_animal.taxon.taxon_id

        view._on_favorite_toggle(event)

        callback.assert_called_once_with(sample_animal.taxon.taxon_id, False)

    def test_refreshes_display_after_toggle(
        self, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que après le toggle, _display_animal est rappelé pour
        mettre à jour l'icône favori (plein ↔ contour)."""
        callback = MagicMock()
        view = _make_view(mock_page, mock_app_state, on_favorite_toggle=callback)
        view.build()
        view.current_animal = sample_animal

        mock_app_state.repository.is_favorite.return_value = False

        event = MagicMock()
        event.control = MagicMock()
        event.control.data = sample_animal.taxon.taxon_id

        # Spy on _display_animal — must remain with patch.object since `view` is local
        with patch.object(
            view, "_display_animal", wraps=view._display_animal
        ) as mock_display:
            view._on_favorite_toggle(event)
            mock_display.assert_called_once_with(sample_animal)


# =============================================================================
# SECTION 5 : Gallery and sharing
# =============================================================================


class TestTodayViewGalleryAndSharing:
    """Tests pour _open_gallery, _on_copy_text, _on_open_wikipedia."""

    @patch("daynimal.ui.views.today_view.ImageGalleryDialog")
    def test_open_gallery_creates_dialog(
        self, MockDialog, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _open_gallery instancie ImageGalleryDialog avec
        les images de l'animal et appelle dialog.open()."""
        view = _make_view(mock_page, mock_app_state)
        view.build()

        mock_dialog_instance = MagicMock()
        MockDialog.return_value = mock_dialog_instance

        view._open_gallery(sample_animal.images, sample_animal)

        MockDialog.assert_called_once_with(
            images=sample_animal.images,
            image_cache=mock_app_state.image_cache,
            page=mock_page,
            animal_display_name=sample_animal.display_name,
            animal_taxon_id=sample_animal.taxon.taxon_id,
        )
        mock_dialog_instance.open.assert_called_once()

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.today_view.ft.Clipboard")
    async def test_on_copy_text_copies_to_clipboard(
        self, MockClipboard, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _on_copy_text crée un ft.Clipboard et appelle
        clipboard.set(text) avec le texte de partage formaté.
        Puis un SnackBar 'Copié' est affiché."""
        view = _make_view(mock_page, mock_app_state)
        view.build()
        view.current_animal = sample_animal

        mock_clipboard_instance = MagicMock()
        mock_clipboard_instance.set = AsyncMock()
        MockClipboard.return_value = mock_clipboard_instance

        await view._on_copy_text(None)

        # Verify clipboard was called with share text
        expected_text = TodayView._build_share_text(sample_animal)
        mock_clipboard_instance.set.assert_awaited_once_with(expected_text)

        # Verify SnackBar was shown
        mock_page.show_dialog.assert_called_once()
        dialog_arg = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dialog_arg, ft.SnackBar)

    @patch("daynimal.ui.views.today_view.ft.UrlLauncher")
    def test_on_open_wikipedia_launches_url(
        self, MockUrlLauncher, mock_page, mock_app_state, sample_animal
    ):
        """Vérifie que _on_open_wikipedia appelle page.run_task avec
        ft.UrlLauncher().launch_url et l'URL Wikipedia de l'animal."""
        view = _make_view(mock_page, mock_app_state)
        view.build()
        view.current_animal = sample_animal

        mock_launcher_instance = MagicMock()
        MockUrlLauncher.return_value = mock_launcher_instance

        view._on_open_wikipedia(None)

        mock_page.run_task.assert_called_once_with(
            mock_launcher_instance.launch_url, sample_animal.wikipedia.article_url
        )

    def test_on_open_wikipedia_no_article(self, mock_page, mock_app_state):
        """Vérifie que _on_open_wikipedia ne fait rien si l'animal
        n'a pas d'article Wikipedia."""
        taxon = Taxon(
            taxon_id=666,
            scientific_name="Testus nowiki",
            canonical_name="Testus nowiki",
            rank=TaxonomicRank.SPECIES,
            vernacular_names={"en": ["No Wiki Animal"]},
        )
        animal_no_wiki = AnimalInfo(taxon=taxon, wikipedia=None)

        view = _make_view(mock_page, mock_app_state)
        view.build()
        view.current_animal = animal_no_wiki

        view._on_open_wikipedia(None)

        # page.run_task should NOT have been called
        mock_page.run_task.assert_not_called()
