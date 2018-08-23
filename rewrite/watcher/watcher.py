class Watcher:
    def __init__(self):
        pass

    def register(self, stream):
        self.stream = stream

    async def start(self):
        async for item in self.stream:
            if hasattr(self, "async_execute"):
                await self.async_execute(item)
            else:
                self.execute(item)

    def execute(self, item):
        pass

