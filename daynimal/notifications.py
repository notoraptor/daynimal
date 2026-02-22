"""Notification service for periodic animal reminders."""

import asyncio
import functools
import logging
from datetime import datetime, timedelta

try:
    from desktop_notifier import DesktopNotifier
except ImportError:
    DesktopNotifier = None

from daynimal.repository import AnimalRepository

logger = logging.getLogger(__name__)


def _parse_period(period_str: str) -> int:
    """Parse a period string 'HH:MM' into total minutes.

    Supports hours > 23 (e.g. '123:37' = 7417 minutes).
    Returns 1440 (24h) on invalid input. Minimum 1 minute.
    """
    try:
        parts = period_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        total = hours * 60 + minutes
        return max(total, 1)
    except (ValueError, AttributeError, IndexError):
        return 1440  # 24h default


class NotificationService:
    """In-app notification service that sends periodic desktop notifications."""

    def __init__(self, repository: AnimalRepository, on_clicked=None):
        self.repository = repository
        self._task: asyncio.Task | None = None
        self._on_clicked = on_clicked
        self._notifier = (
            DesktopNotifier(app_name="Daynimal") if DesktopNotifier else None
        )

    @property
    def enabled(self) -> bool:
        """Whether notifications are enabled."""
        return self.repository.get_setting("notifications_enabled", "false") == "true"

    @property
    def notification_start(self) -> datetime:
        """Configured notification start datetime.

        Falls back to notification_time (legacy) + today's date, or today 08:00.
        """
        raw = self.repository.get_setting("notification_start", None)
        if raw:
            try:
                return datetime.fromisoformat(raw)
            except (ValueError, TypeError):
                pass

        # Legacy fallback: read old notification_time
        legacy_time = self.repository.get_setting("notification_time", "08:00")
        try:
            parts = legacy_time.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, AttributeError, IndexError):
            hour, minute = 8, 0

        today = datetime.now().replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        return today

    @property
    def notification_period(self) -> int:
        """Configured notification period in minutes. Default: 1440 (24h)."""
        raw = self.repository.get_setting("notification_period", "24:00")
        return _parse_period(raw)

    def _compute_next_notification(
        self, start: datetime, period_minutes: int
    ) -> datetime:
        """Compute the next notification time >= now."""
        now = datetime.now()
        if now <= start:
            return start
        period = timedelta(minutes=period_minutes)
        elapsed = now - start
        complete_periods = int(elapsed / period)
        return start + (complete_periods + 1) * period

    def start(self):
        """Schedule next notification. Cancels any existing schedule."""
        self.stop()
        if not self.enabled:
            return
        start = self.notification_start
        period = self.notification_period
        next_time = self._compute_next_notification(start, period)
        self._task = asyncio.create_task(
            self._wait_and_notify(next_time, start, period)
        )

    def stop(self):
        """Cancel scheduled notification."""
        if self._task:
            self._task.cancel()
            self._task = None

    async def _wait_and_notify(
        self, next_time: datetime, expected_start: datetime, expected_period: int
    ):
        """Sleep until next_time, verify settings unchanged, notify, schedule next."""
        try:
            delay = (next_time - datetime.now()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)

            # Verify settings haven't changed during sleep
            if not self.enabled:
                return
            current_start = self.notification_start
            current_period = self.notification_period
            if current_start != expected_start or current_period != expected_period:
                return  # Another task handles the new config

            # Fetch a random animal for this notification
            animal = await asyncio.to_thread(self.repository.get_random)
            if animal is not None:
                await self._send_notification(animal)

            # Schedule the next notification
            next_next = next_time + timedelta(minutes=current_period)
            self._task = asyncio.create_task(
                self._wait_and_notify(next_next, current_start, current_period)
            )
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Error in notification scheduler")

    async def _send_notification(self, animal):
        """Send a notification for the given animal."""
        try:
            if self._notifier is None:
                logger.debug("desktop-notifier not available, skipping")
                return

            display_name = animal.display_name

            # Per-notification click handler capturing this specific animal
            on_clicked = (
                functools.partial(self._on_clicked, animal)
                if self._on_clicked
                else None
            )

            await self._notifier.send(
                title="Découvrez cet animal!",
                message=display_name,
                on_clicked=on_clicked,
            )

            logger.info("Notification sent for: %s", display_name)
        except Exception:
            logger.exception("Failed to send notification")
