"""Retry with exponential backoff for API calls."""

import time
import random
import functools
from typing import Callable, Any, Tuple, Type

from .logger import get_logger

log = get_logger("vedang.retry")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator: retries the wrapped function with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_retries:
                        log.error(
                            "%s failed after %d retries: %s",
                            func.__name__, max_retries, exc,
                        )
                        raise
                    wait = min(delay, max_delay)
                    if jitter:
                        wait *= 0.5 + random.random()
                    log.warning(
                        "%s attempt %d/%d failed: %s — retrying in %.1fs",
                        func.__name__, attempt + 1, max_retries, exc, wait,
                    )
                    time.sleep(wait)
                    delay *= backoff_factor
            raise RuntimeError("unreachable")

        return wrapper
    return decorator
