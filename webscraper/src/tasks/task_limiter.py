from asyncio import Semaphore
from typing import Callable


class TaskLimiter:
    def __init__(self, max_concurrent_tasks: int = 5):
        self._semaphore = Semaphore(max_concurrent_tasks)

    async def limited_task(self, task: Callable, *args):
        async with self._semaphore:
            return await task(*args)
