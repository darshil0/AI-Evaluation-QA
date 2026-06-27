import pytest

from evaluation.retry_logic import exponential_backoff_retry


@pytest.mark.asyncio
async def test_exponential_backoff_retry_async_failure():
    attempts = 0

    @exponential_backoff_retry(max_retries=2, base_delay=0.01)
    async def fail_func():
        nonlocal attempts
        attempts += 1
        raise ConnectionError("Async failure")

    with pytest.raises(ConnectionError):
        await fail_func()
    assert attempts == 3


def test_exponential_backoff_retry_sync_failure():
    attempts = 0

    @exponential_backoff_retry(max_retries=2, base_delay=0.01)
    def fail_func():
        nonlocal attempts
        attempts += 1
        raise ConnectionError("Sync failure")

    with pytest.raises(ConnectionError):
        fail_func()
    assert attempts == 3


def test_exponential_backoff_retry_sync_success():
    attempts = 0

    @exponential_backoff_retry(max_retries=2, base_delay=0.01)
    def success_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Try again")
        return "success"

    result = success_func()
    assert result == "success"
    assert attempts == 2


def test_exponential_backoff_retry_sync_non_retriable_error():
    @exponential_backoff_retry(max_retries=2, base_delay=0.01)
    def fail_func():
        raise ValueError("Non-retriable")

    with pytest.raises(ValueError):
        fail_func()


@pytest.mark.asyncio
async def test_exponential_backoff_retry_async_non_retriable_error():
    @exponential_backoff_retry(max_retries=2, base_delay=0.01)
    async def fail_func():
        raise ValueError("Non-retriable")

    with pytest.raises(ValueError):
        await fail_func()


@pytest.mark.asyncio
async def test_exponential_backoff_retry_async_no_retry_needed():
    @exponential_backoff_retry(max_retries=2)
    async def success_func():
        return "instant success"

    assert await success_func() == "instant success"


def test_exponential_backoff_retry_sync_no_retry_needed():
    @exponential_backoff_retry(max_retries=2)
    def success_func():
        return "instant success"

    assert success_func() == "instant success"
