import asyncio
from collections import defaultdict
from typing import Any, AsyncGenerator


class InMemoryEventBus:
    def __init__(self):
        self.topics = defaultdict(list)
        self.loop = None

    async def subscribe(self, topic: str) -> AsyncGenerator[Any, None]:
        # Capture the ASGI loop when the first person subscribes
        self.loop = asyncio.get_running_loop()

        queue = asyncio.Queue()
        self.topics[topic].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self.topics[topic].remove(queue)

    def emit(self, topic: str, payload: Any):
        if not self.loop:
            return  # No active subscribers

        # This is the bridge that makes 'runserver' work with signals
        self.loop.call_soon_threadsafe(self._put_in_queues, topic, payload)

    def _put_in_queues(self, topic, payload):
        for queue in self.topics[topic]:
            queue.put_nowait(payload)


event_bus = InMemoryEventBus()
