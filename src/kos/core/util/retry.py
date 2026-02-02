"""Retry utilities for resilient operations."""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar, Awaitable

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_error: Exception | None = None):
        super().__init__(message)
        self.last_error = last_error


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """Retry an async function with exponential backoff.

    Args:
        func: Async function to retry.
        *args: Positional arguments for func.
        max_attempts: Maximum retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Exception types to catch and retry.
        **kwargs: Keyword arguments for func.

    Returns:
        Result of successful function call.

    Raises:
        RetryError: If all attempts fail.
    """
    last_error: Exception | None = None
    current_delay = delay

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_error = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    raise RetryError(
        f"Failed after {max_attempts} attempts",
        last_error=last_error,
    )


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator to add retry logic to async functions.

    Args:
        max_attempts: Maximum retry attempts.
        delay: Initial delay between retries.
        backoff: Multiplier for delay after each retry.
        exceptions: Exception types to catch and retry.

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_async(
                func,
                *args,
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions,
                **kwargs,
            )

        return wrapper

    return decorator
