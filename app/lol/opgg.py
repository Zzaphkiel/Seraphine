import aiohttp
import asyncio

from app.common.config import cfg


class Opgg:
    def __init__(self):
        self.tierList: list = []

        self.defaultTier = cfg.get(cfg.opggTier)
        self.defaultRegion = cfg.get(cfg.opggRegion)

        self.session = aiohttp.ClientSession("https://lol-api-champion.op.gg")

    async def update(self):
        pass

    async def close(self):
        await self.session.close()


opgg = Opgg()
