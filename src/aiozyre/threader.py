import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Mapping, Union


class Threader:
    __slots__ = ('loop',)

    executor = ThreadPoolExecutor()

    def __init__(self, loop: Union[None, asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

    async def spawn(self, func: Callable, args: Iterable = None, kwargs: Mapping = None):
        """
        Run the given func in a separate thread and return a future for its result.

        This is useful for calling code in a C extension which releases the GIL
        while it performs socket or other blocking actions.
        """

        def call():
            return func(*args or tuple(), **kwargs or {})

        return await self.loop.run_in_executor(self.executor, call)
