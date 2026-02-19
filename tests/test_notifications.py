"""Tests for NotificationService."""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from daynimal.notifications import NotificationService


@pytest.fixture
def mock_repo():
    """Create a mock repository with default settings."""
    repo = MagicMock()
    settings = {}

    def get_setting(key, default=None):
        return settings.get(key, default)

    def set_setting(key, value):
        settings[key] = value

    repo.get_setting = MagicMock(side_effect=get_setting)
    repo.set_setting = MagicMock(side_effect=set_setting)
    repo._settings = settings  # exposed for test manipulation
    return repo


@pytest.fixture
def service(mock_repo):
    """Create a NotificationService with mock repo."""
    return NotificationService(mock_repo)


# =============================================================================
# SECTION 1: Properties and defaults
# =============================================================================


def test_enabled_default_is_false(service):
    """Notifications disabled by default."""
    assert service.enabled is False


def test_enabled_when_set_to_true(service, mock_repo):
    """Notifications enabled when setting is 'true'."""
    mock_repo._settings["notifications_enabled"] = "true"
    assert service.enabled is True


def test_notification_time_default(service):
    """Default notification time is 08:00."""
    assert service.notification_time == "08:00"


def test_notification_time_custom(service, mock_repo):
    """Custom notification time from settings."""
    mock_repo._settings["notification_time"] = "14:30"
    assert service.notification_time == "14:30"


# =============================================================================
# SECTION 2: _should_notify()
# =============================================================================


def test_should_not_notify_when_disabled(service):
    """Should not notify when notifications are disabled."""
    assert service._should_notify() is False


def test_should_not_notify_already_sent_today(service, mock_repo):
    """Should not notify if already sent today."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_time"] = "00:00"
    today_str = datetime.now().strftime("%Y-%m-%d")
    mock_repo._settings["last_notification_date"] = today_str
    assert service._should_notify() is False


@patch("daynimal.notifications.datetime")
def test_should_not_notify_before_time(mock_dt, service, mock_repo):
    """Should not notify before the configured time."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_time"] = "23:59"

    mock_now = MagicMock()
    mock_now.hour = 0
    mock_now.minute = 0
    mock_now.strftime.return_value = "2026-02-10"
    mock_dt.now.return_value = mock_now
    assert service._should_notify() is False


@patch("daynimal.notifications.datetime")
def test_should_notify_when_enabled_and_time_reached(mock_dt, service, mock_repo):
    """Should notify when enabled, time reached, and not yet sent today."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_time"] = "08:00"

    mock_now = MagicMock()
    mock_now.hour = 10
    mock_now.minute = 30
    mock_now.strftime.return_value = "2026-02-10"
    mock_dt.now.return_value = mock_now
    assert service._should_notify() is True


@patch("daynimal.notifications.datetime")
def test_should_notify_handles_invalid_time_format(mock_dt, service, mock_repo):
    """Should fallback to 08:00 on invalid time format."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_time"] = "invalid"

    mock_now = MagicMock()
    mock_now.hour = 9
    mock_now.minute = 0
    mock_now.strftime.return_value = "2026-02-10"
    mock_dt.now.return_value = mock_now
    assert service._should_notify() is True


# =============================================================================
# SECTION 3: _send_notification()
# =============================================================================


@patch("daynimal.notifications.notification")
async def test_send_notification_calls_plyer(mock_notif, service, mock_repo):
    """Should call plyer notification.notify with animal info."""
    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"
    mock_repo.get_animal_of_the_day.return_value = mock_animal

    await service._send_notification()

    mock_notif.notify.assert_called_once_with(
        title="Animal du jour",
        message="Découvrez Lion !",
        app_name="Daynimal",
        timeout=10,
    )


@patch("daynimal.notifications.notification")
async def test_send_notification_updates_last_date(_mock_notif, service, mock_repo):
    """Should update last_notification_date after sending."""
    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"
    mock_repo.get_animal_of_the_day.return_value = mock_animal

    await service._send_notification()

    today_str = datetime.now().strftime("%Y-%m-%d")
    mock_repo.set_setting.assert_called_with("last_notification_date", today_str)


@patch("daynimal.notifications.notification")
async def test_send_notification_skips_when_no_animal(mock_notif, service, mock_repo):
    """Should do nothing if get_animal_of_the_day returns None."""
    mock_repo.get_animal_of_the_day.return_value = None

    await service._send_notification()
    mock_notif.notify.assert_not_called()


async def test_send_notification_handles_error(service, mock_repo):
    """Should catch and log errors without crashing."""
    mock_repo.get_animal_of_the_day.side_effect = RuntimeError("DB error")

    # Should not raise
    await service._send_notification()


# =============================================================================
# SECTION 4: Lifecycle (start/stop)
# =============================================================================


async def test_start_creates_task(service):
    """Start should create an asyncio task."""
    service.start()
    assert service._running is True
    assert service._task is not None

    # Cleanup
    service.stop()
    await asyncio.sleep(0.05)


async def test_stop_cancels_task(service):
    """Stop should cancel the running task."""
    service.start()
    task = service._task
    service.stop()

    assert service._running is False
    assert service._task is None

    # Wait for cancellation to propagate
    await asyncio.sleep(0.05)
    assert task.cancelled() or task.done()


async def test_start_is_idempotent(service):
    """Calling start twice should not create a second task."""
    service.start()
    first_task = service._task
    service.start()
    assert service._task is first_task

    service.stop()
    await asyncio.sleep(0.05)


# =============================================================================
# SECTION ÉTENDUE : Couverture lignes manquantes (82% → ~95%)
# Lignes: 9-10 (import plyer), 53-61 (_check_loop), 90-91 (_send_notification)
# =============================================================================


@pytest.mark.asyncio
async def test_check_loop_calls_send_when_should_notify(service):
    """Vérifie que _check_loop appelle _send_notification() quand
    _should_notify() retourne True. On mock _should_notify pour retourner
    True une fois, puis on arrête la boucle, et on vérifie que
    _send_notification est appelé exactement une fois."""
    from unittest.mock import AsyncMock

    iteration = 0

    async def fake_sleep(_):
        nonlocal iteration
        iteration += 1
        if iteration >= 2:
            service._running = False

    with (
        patch("asyncio.sleep", side_effect=fake_sleep),
        patch.object(service, "_should_notify", side_effect=[True, False]),
        patch.object(
            service, "_send_notification", new_callable=AsyncMock
        ) as mock_send,
    ):
        service._running = True
        await service._check_loop()

    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_check_loop_skips_when_should_not_notify(service):
    """Vérifie que _check_loop N'appelle PAS _send_notification()
    quand _should_notify() retourne False."""
    from unittest.mock import AsyncMock

    iteration = 0

    async def fake_sleep(_):
        nonlocal iteration
        iteration += 1
        if iteration >= 2:
            service._running = False

    with (
        patch("asyncio.sleep", side_effect=fake_sleep),
        patch.object(service, "_should_notify", return_value=False),
        patch.object(
            service, "_send_notification", new_callable=AsyncMock
        ) as mock_send,
    ):
        service._running = True
        await service._check_loop()

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification_plyer_not_available(service):
    """Vérifie que _send_notification() ne plante pas quand
    daynimal.notifications.notification est None (plyer non disponible)."""
    with patch("daynimal.notifications.notification", None):
        await service._send_notification()  # Should not raise


@pytest.mark.asyncio
async def test_send_notification_no_animal(service, mock_repo):
    """Vérifie que si le repository ne retourne aucun animal
    (get_animal_of_the_day retourne None), _send_notification()
    retourne sans essayer d envoyer une notification."""
    mock_repo.get_animal_of_the_day.return_value = None

    with patch("daynimal.notifications.notification") as mock_notif:
        await service._send_notification()
        mock_notif.notify.assert_not_called()
