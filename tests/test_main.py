import asyncio
import pytest

from main import main

@pytest.mark.asyncio
async def test_main_runs():
    try:
        task = asyncio.create_task(main())
        await asyncio.sleep(1)
        task.cancel()
    except Exception as e:
        pytest.fail(f"Bot failed to start: {e}")
