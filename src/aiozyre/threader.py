import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Mapping, Union

class Threader:
    __slots__ = ('loop',)

    # Do not increase max_workers; the zyre node has one actor, which runs on a single thread.
    # The various blocking zyre functions communicate with that thread.
    # By having a single worker in this threadpool, we ensure that we are communicating with the
    # zactor in an atomic way, which is what the zyre code seems to expect.
    # We run the code in a separate thread
    executor = ThreadPoolExecutor(max_workers=1)

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
