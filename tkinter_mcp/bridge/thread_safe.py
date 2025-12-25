"""Thread-safe utilities for Tkinter operations."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ThreadSafeResult:
    """Container for thread-safe operation results.

    Args:
        success: Whether the operation completed successfully
        value: The return value if successful
        error: Exception if operation failed
    """

    success: bool
    value: Any = None
    error: Exception | None = None


def execute_on_main_thread(
    root: Any,
    callback: Callable[[], T],
    timeout: float = 5.0,
) -> T:
    """Execute a callback on the Tkinter main thread.

    Uses root.after(0, callback) to schedule execution on the main thread
    and a queue to communicate the result back to the calling thread.

    Args:
        root: The Tkinter root window
        callback: Function to execute on main thread
        timeout: Maximum seconds to wait for result

    Returns:
        The return value of the callback

    Raises:
        TimeoutError: If callback doesn't complete within timeout
        Exception: Re-raises any exception from the callback
    """
    result_queue: queue.Queue[ThreadSafeResult] = queue.Queue()

    def wrapper() -> None:
        try:
            result = callback()
            result_queue.put(ThreadSafeResult(success=True, value=result))
        except Exception as e:
            result_queue.put(ThreadSafeResult(success=False, error=e))

    root.after(0, wrapper)

    try:
        result = result_queue.get(timeout=timeout)
    except queue.Empty as e:
        raise TimeoutError(
            f"Tkinter operation timed out after {timeout} seconds"
        ) from e

    if not result.success:
        raise result.error  # type: ignore[misc]

    return result.value


def is_main_thread() -> bool:
    """Check if current thread is the main thread.

    Returns:
        True if running on main thread
    """
    return threading.current_thread() is threading.main_thread()
