import sys, asyncio
if sys.version_info < (3, 11) and not hasattr(asyncio, "TaskGroup"):
    class TaskGroup:
        def __init__(self): self._tasks=[]
        async def __aenter__(self): return self
        async def __aexit__(self, *exc):
            await asyncio.gather(*self._tasks, return_exceptions=True)
        def create_task(self, coro):
            self._tasks.append(asyncio.create_task(coro))
    asyncio.TaskGroup = TaskGroup            # patch
