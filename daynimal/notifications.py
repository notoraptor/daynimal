"""Notification service for daily animal reminders."""

import asyncio
import logging
from datetime import datetime

try:
    from plyer import notification
except ImportError:
    notification = None

from daynimal.repository import AnimalRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """In-app notification service that sends a daily desktop notification."""

    CHECK_INTERVAL = 60  # seconds

    def __init__(self, repository: AnimalRepository):
        self.repository = repository
        self._task: asyncio.Task | None = None
        self._running = False

    @property
    def enabled(self) -> bool:
        """Whether notifications are enabled."""
        return self.repository.get_setting("notifications_enabled", "false") == "true"

    @property
    def notification_time(self) -> str:
        """Configured notification time (HH:MM format)."""
        return self.repository.get_setting("notification_time", "08:00")

    def start(self):
        """Start the periodic check loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._check_loop())

    def stop(self):
        """Stop the periodic check loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _check_loop(self):
        """Periodically check if it's time to send a notification."""
        while self._running:
            try:
                await asyncio.sleep(self.CHECK_INTERVAL)
                if self._should_notify():
                    await self._send_notification()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in notification check loop")

    def _should_notify(self) -> bool:
        """Check if a notification should be sent now."""
        if not self.enabled:
            return False

        today_str = datetime.now().strftime("%Y-%m-%d")
        last_date = self.repository.get_setting("last_notification_date", "")
        if last_date == today_str:
            return False

        now = datetime.now()
        try:
            target_hour, target_minute = (
                int(x) for x in self.notification_time.split(":")
            )
        except (ValueError, AttributeError):
            target_hour, target_minute = 8, 0

        current_minutes = now.hour * 60 + now.minute
        target_minutes = target_hour * 60 + target_minute

        return current_minutes >= target_minutes

    async def _send_notification(self):
        """Send the daily animal notification."""
        try:
            if notification is None:
                logger.debug("plyer not available, skipping notification")
                return

            animal = await asyncio.to_thread(self.repository.get_animal_of_the_day)
            if animal is None:
                return

            display_name = animal.display_name

            await asyncio.to_thread(
                notification.notify,
                title="Animal du jour",
                message=f"Découvrez {display_name} !",
                app_name="Daynimal",
                timeout=10,
            )

            today_str = datetime.now().strftime("%Y-%m-%d")
            self.repository.set_setting("last_notification_date", today_str)

            logger.info("Notification sent for: %s", display_name)
        except Exception:
            logger.exception("Failed to send notification")
