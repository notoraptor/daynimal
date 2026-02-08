"""Debouncing utility for UI inputs.

This module provides a Debouncer class to prevent excessive function calls
when user input changes rapidly (e.g., search field).
"""

import asyncio
from typing import Callable, Optional


class Debouncer:
    """Debouncer to delay function execution until input stabilizes.

    Example usage:
        debouncer = Debouncer(delay=0.3)  # 300ms

        def on_search_change(e):
            query = e.control.value
            asyncio.create_task(debouncer.debounce(perform_search, query))

    This ensures perform_search() is only called once the user stops typing
    for 300ms, reducing unnecessary database queries.
    """

    def __init__(self, delay: float = 0.3):
        """Initialize debouncer.

        Args:
            delay: Delay in seconds before executing function (default: 0.3s).
        """
        self.delay = delay
        self._task: Optional[asyncio.Task] = None

    async def debounce(self, func: Callable, *args, **kwargs):
        """Execute function after delay, cancelling previous pending calls.

        Args:
            func: Async function to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.
        """
        # Cancel previous task if still pending
        if self._task and not self._task.done():
            self._task.cancel()

        # Create new task
        self._task = asyncio.create_task(self._debounced_call(func, *args, **kwargs))

    async def _debounced_call(self, func: Callable, *args, **kwargs):
        """Internal method to wait and execute function.

        Args:
            func: Function to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.
        """
        try:
            await asyncio.sleep(self.delay)
            await func(*args, **kwargs)
        except asyncio.CancelledError:
            # Task was cancelled (user kept typing)
            pass
