import pytest

from evaluation.retry_logic import exponential_backoff_retry


@pytest.mark.asyncio
async def test_async_retry_success():
    call_count = 0

    @exponential_backoff_retry(max_retries=3, base_delay=0.01)
    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await success_func()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_async_retry_fail_then_success():
    call_count = 0

    @exponential_backoff_retry(max_retries=3, base_delay=0.01)
    async def retry_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Retry me")
        return "finally success"

    result = await retry_func()
    assert result == "finally success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_max_reached():
    call_count = 0

    @exponential_backoff_retry(max_retries=2, base_delay=0.01)
    async def fail_func():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Always fail")

    with pytest.raises(ConnectionError):
        await fail_func()
    assert call_count == 3  # 0, 1, 2 attempts


def test_sync_retry_success():
    call_count = 0

    @exponential_backoff_retry(max_retries=3, base_delay=0.01)
    def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = success_func()
    assert result == "success"
    assert call_count == 1


def test_sync_retry_fail_then_success():
    call_count = 0

    @exponential_backoff_retry(max_retries=3, base_delay=0.01)
    def retry_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Retry me")
        return "finally success"

    result = retry_func()
    assert result == "finally success"
    assert call_count == 3
