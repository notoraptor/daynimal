"""Tests for NotificationService with async callback scheduling."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from daynimal.notifications import NotificationService, _parse_period


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
    """Create a NotificationService with mock repo and mocked notifier."""
    svc = NotificationService(mock_repo)
    svc._notifier = MagicMock()
    svc._notifier.send = AsyncMock()
    return svc


# =============================================================================
# SECTION 1: _parse_period
# =============================================================================


def test_parse_period_daily():
    assert _parse_period("24:00") == 1440


def test_parse_period_5min():
    assert _parse_period("00:05") == 5


def test_parse_period_large_hours():
    assert _parse_period("123:37") == 123 * 60 + 37


def test_parse_period_invalid_returns_default():
    assert _parse_period("invalid") == 1440


def test_parse_period_minimum_1_minute():
    assert _parse_period("00:00") == 1


# =============================================================================
# SECTION 2: Properties and defaults
# =============================================================================


def test_enabled_default_is_false(service):
    """Notifications disabled by default."""
    assert service.enabled is False


def test_enabled_when_set_to_true(service, mock_repo):
    """Notifications enabled when setting is 'true'."""
    mock_repo._settings["notifications_enabled"] = "true"
    assert service.enabled is True


def test_notification_start_default(service):
    """Default start is today 08:00."""
    start = service.notification_start
    now = datetime.now()
    assert start.hour == 8
    assert start.minute == 0
    assert start.date() == now.date()


def test_notification_start_from_setting(service, mock_repo):
    """Reads notification_start from settings."""
    mock_repo._settings["notification_start"] = "2026-03-15T14:30"
    start = service.notification_start
    assert start == datetime(2026, 3, 15, 14, 30)


def test_notification_start_legacy_fallback(service, mock_repo):
    """Falls back to notification_time if notification_start absent."""
    mock_repo._settings["notification_time"] = "09:15"
    start = service.notification_start
    assert start.hour == 9
    assert start.minute == 15


def test_notification_period_default(service):
    """Default period is 1440 minutes (24h)."""
    assert service.notification_period == 1440


def test_notification_period_custom(service, mock_repo):
    """Custom period from settings."""
    mock_repo._settings["notification_period"] = "00:05"
    assert service.notification_period == 5


# =============================================================================
# SECTION 3: _compute_next_notification()
# =============================================================================


@patch("daynimal.notifications.datetime")
def test_compute_next_start_in_future(mock_dt, service):
    """When start is in the future, return start."""
    mock_dt.now.return_value = datetime(2026, 2, 22, 7, 0)
    start = datetime(2026, 2, 22, 8, 0)
    result = service._compute_next_notification(start, 1440)
    assert result == start


@patch("daynimal.notifications.datetime")
def test_compute_next_between_cycles(mock_dt, service):
    """When now is between two cycles, return next cycle start."""
    mock_dt.now.return_value = datetime(2026, 2, 22, 10, 30)
    start = datetime(2026, 2, 22, 8, 0)
    # Period = 60 min → cycles at 8:00, 9:00, 10:00, 11:00
    # now = 10:30 → next = 11:00
    result = service._compute_next_notification(start, 60)
    assert result == datetime(2026, 2, 22, 11, 0)


@patch("daynimal.notifications.datetime")
def test_compute_next_exactly_on_cycle(mock_dt, service):
    """When now is exactly at a cycle boundary, return next cycle (N+1)."""
    mock_dt.now.return_value = datetime(2026, 2, 22, 10, 0)
    start = datetime(2026, 2, 22, 8, 0)
    # Period = 60 min → cycles at 8:00, 9:00, 10:00, 11:00
    # now = 10:00 exactly → complete_periods = 2, return 8:00 + 3*60 = 11:00
    result = service._compute_next_notification(start, 60)
    assert result == datetime(2026, 2, 22, 11, 0)


@patch("daynimal.notifications.datetime")
def test_compute_next_short_period(mock_dt, service):
    """Short 5-minute period works correctly."""
    mock_dt.now.return_value = datetime(2026, 2, 22, 8, 7)
    start = datetime(2026, 2, 22, 8, 0)
    # Period = 5 min → cycles at 8:00, 8:05, 8:10, ...
    # now = 8:07 → complete_periods = 1, return 8:00 + 2*5 = 8:10
    result = service._compute_next_notification(start, 5)
    assert result == datetime(2026, 2, 22, 8, 10)


@patch("daynimal.notifications.datetime")
def test_compute_next_now_equals_start(mock_dt, service):
    """When now == start, return start (now <= start)."""
    now = datetime(2026, 2, 22, 8, 0)
    mock_dt.now.return_value = now
    start = datetime(2026, 2, 22, 8, 0)
    result = service._compute_next_notification(start, 1440)
    assert result == start


# =============================================================================
# SECTION 4: _send_notification()
# =============================================================================


async def test_send_notification_calls_desktop_notifier(service):
    """Should call notifier.send() with animal info."""
    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"

    await service._send_notification(mock_animal)

    service._notifier.send.assert_called_once()
    call_kwargs = service._notifier.send.call_args[1]
    assert call_kwargs["title"] == "Découvrez cet animal!"
    assert call_kwargs["message"] == "Lion"


async def test_send_notification_no_last_ts_saved(service, mock_repo):
    """Should NOT save last_notification_ts anymore."""
    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"

    await service._send_notification(mock_animal)

    # set_setting should NOT be called (no more last_notification_ts saving)
    mock_repo.set_setting.assert_not_called()


async def test_send_notification_handles_error(service):
    """Should catch and log errors without crashing."""
    service._notifier.send = AsyncMock(side_effect=RuntimeError("Send error"))
    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"

    # Should not raise
    await service._send_notification(mock_animal)


# =============================================================================
# SECTION 5: Lifecycle (start/stop)
# =============================================================================


async def test_start_creates_task_when_enabled(service, mock_repo):
    """Start should create an asyncio task when enabled."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_start"] = "2099-01-01T00:00"
    mock_repo._settings["notification_period"] = "24:00"

    service.start()
    assert service._task is not None

    # Cleanup
    service.stop()
    await asyncio.sleep(0.05)


async def test_start_does_nothing_when_disabled(service):
    """Start should not create a task when notifications disabled."""
    service.start()
    assert service._task is None


async def test_stop_cancels_task(service, mock_repo):
    """Stop should cancel the running task."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_start"] = "2099-01-01T00:00"

    service.start()
    task = service._task
    service.stop()

    assert service._task is None

    # Wait for cancellation to propagate
    await asyncio.sleep(0.05)
    assert task.cancelled() or task.done()


async def test_start_replaces_existing_task(service, mock_repo):
    """Calling start twice should cancel the first task and create a new one."""
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_start"] = "2099-01-01T00:00"

    service.start()
    first_task = service._task
    service.start()
    second_task = service._task

    assert second_task is not first_task

    # Cleanup
    service.stop()
    await asyncio.sleep(0.05)


async def test_stop_when_no_task(service):
    """Stop should be safe to call when no task exists."""
    service.stop()  # Should not raise
    assert service._task is None


# =============================================================================
# SECTION 6: _wait_and_notify()
# =============================================================================


@pytest.mark.asyncio
async def test_wait_and_notify_sleeps_then_sends(service, mock_repo):
    """Should sleep until next_time, fetch random animal, then send notification."""
    mock_repo._settings["notifications_enabled"] = "true"
    start = datetime(2026, 2, 22, 8, 0)
    mock_repo._settings["notification_start"] = start.isoformat()
    mock_repo._settings["notification_period"] = "24:00"

    mock_animal = MagicMock()
    mock_repo.get_random.return_value = mock_animal

    next_time = datetime.now() + timedelta(seconds=0.01)

    with patch.object(
        service, "_send_notification", new_callable=AsyncMock
    ) as mock_send:
        await service._wait_and_notify(next_time, start, 1440)

    mock_send.assert_called_once_with(mock_animal)


@pytest.mark.asyncio
async def test_wait_and_notify_skips_when_disabled(service, mock_repo):
    """Should not notify if enabled becomes False during sleep."""
    start = datetime(2026, 2, 22, 8, 0)
    mock_repo._settings["notification_start"] = start.isoformat()
    mock_repo._settings["notification_period"] = "24:00"

    # Start enabled, then disable before the check
    call_count = 0

    def enabled_side_effect(key, default=None):
        nonlocal call_count
        if key == "notifications_enabled":
            call_count += 1
            return "false"  # disabled
        return mock_repo._settings.get(key, default)

    mock_repo.get_setting.side_effect = enabled_side_effect

    next_time = datetime.now() - timedelta(seconds=1)  # already past

    with patch.object(
        service, "_send_notification", new_callable=AsyncMock
    ) as mock_send:
        await service._wait_and_notify(next_time, start, 1440)

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_wait_and_notify_skips_when_start_changed(service, mock_repo):
    """Should not notify if start changes during sleep."""
    original_start = datetime(2026, 2, 22, 8, 0)
    new_start = datetime(2026, 2, 22, 9, 0)

    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_start"] = new_start.isoformat()
    mock_repo._settings["notification_period"] = "24:00"

    next_time = datetime.now() - timedelta(seconds=1)

    with patch.object(
        service, "_send_notification", new_callable=AsyncMock
    ) as mock_send:
        # Pass original_start as expected, but settings now show new_start
        await service._wait_and_notify(next_time, original_start, 1440)

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_wait_and_notify_skips_when_period_changed(service, mock_repo):
    """Should not notify if period changes during sleep."""
    start = datetime(2026, 2, 22, 8, 0)

    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_start"] = start.isoformat()
    mock_repo._settings["notification_period"] = "00:05"  # changed to 5 min

    next_time = datetime.now() - timedelta(seconds=1)

    with patch.object(
        service, "_send_notification", new_callable=AsyncMock
    ) as mock_send:
        # Pass period=1440 as expected, but settings now show 5 min
        await service._wait_and_notify(next_time, start, 1440)

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_wait_and_notify_schedules_next(service, mock_repo):
    """Should schedule the next notification after sending."""
    start = datetime(2026, 2, 22, 8, 0)
    mock_repo._settings["notifications_enabled"] = "true"
    mock_repo._settings["notification_start"] = start.isoformat()
    mock_repo._settings["notification_period"] = "24:00"
    mock_repo.get_random.return_value = MagicMock()

    next_time = datetime.now() - timedelta(seconds=1)

    with patch.object(service, "_send_notification", new_callable=AsyncMock):
        await service._wait_and_notify(next_time, start, 1440)

    # A new task should be created for the next notification
    assert service._task is not None

    # Cleanup
    service.stop()
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_wait_and_notify_handles_cancelled_error(service, mock_repo):
    """Should handle CancelledError gracefully."""
    start = datetime(2026, 2, 22, 8, 0)
    next_time = datetime.now() + timedelta(hours=1)

    async def raise_cancelled(_):
        raise asyncio.CancelledError()

    with patch("asyncio.sleep", side_effect=raise_cancelled):
        # Should not raise
        await service._wait_and_notify(next_time, start, 1440)


# =============================================================================
# SECTION 7: Retrocompatibility
# =============================================================================


def test_no_settings_uses_defaults(service):
    """With no settings at all, properties return sensible defaults."""
    assert service.enabled is False
    assert service.notification_start.hour == 8
    assert service.notification_period == 1440


def test_invalid_start_uses_default(service, mock_repo):
    """Invalid notification_start falls back to legacy or default."""
    mock_repo._settings["notification_start"] = "not-a-date"
    start = service.notification_start
    assert start.hour == 8  # default fallback


# =============================================================================
# SECTION 8: desktop-notifier unavailable
# =============================================================================


@pytest.mark.asyncio
async def test_send_notification_notifier_not_available(service):
    """Verify _send_notification doesn't crash when notifier is None."""
    service._notifier = None
    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"
    await service._send_notification(mock_animal)  # Should not raise


@pytest.mark.asyncio
async def test_send_notification_creates_per_notification_closure(mock_repo):
    """Verify on_clicked creates a closure that passes the animal to the callback."""
    callback = MagicMock()
    svc = NotificationService(mock_repo, on_clicked=callback)
    svc._notifier = MagicMock()
    svc._notifier.send = AsyncMock()

    mock_animal = MagicMock()
    mock_animal.display_name = "Tigre"

    await svc._send_notification(mock_animal)

    # Extract the on_clicked closure passed to send()
    call_kwargs = svc._notifier.send.call_args[1]
    on_clicked = call_kwargs["on_clicked"]
    assert on_clicked is not None

    # Call the closure — it should forward the animal to the original callback
    on_clicked()
    callback.assert_called_once_with(mock_animal)


@pytest.mark.asyncio
async def test_send_notification_no_closure_when_no_callback(mock_repo):
    """Verify on_clicked is None when no callback is configured."""
    svc = NotificationService(mock_repo, on_clicked=None)
    svc._notifier = MagicMock()
    svc._notifier.send = AsyncMock()

    mock_animal = MagicMock()
    mock_animal.display_name = "Lion"

    await svc._send_notification(mock_animal)

    call_kwargs = svc._notifier.send.call_args[1]
    assert call_kwargs["on_clicked"] is None


@pytest.mark.asyncio
async def test_wait_and_notify_skips_when_no_animal(service, mock_repo):
    """Should skip notification when get_random returns None."""
    mock_repo._settings["notifications_enabled"] = "true"
    start = datetime(2026, 2, 22, 8, 0)
    mock_repo._settings["notification_start"] = start.isoformat()
    mock_repo._settings["notification_period"] = "24:00"
    mock_repo.get_random.return_value = None

    next_time = datetime.now() - timedelta(seconds=1)

    with patch.object(
        service, "_send_notification", new_callable=AsyncMock
    ) as mock_send:
        await service._wait_and_notify(next_time, start, 1440)

    mock_send.assert_not_called()
