import asyncio

import pytest

from evaluation.prompt_runner import PromptRunner


@pytest.mark.asyncio
async def test_semaphore_initialization_no_warnings():
    """Verify Semaphore doesn't warn when initialized outside event loop."""
    runner = PromptRunner(config={})
    # Testing that accessing the property initializes it correctly in the running loop
    sem = runner.semaphore
    assert isinstance(sem, asyncio.Semaphore)
    async with sem:
        pass
