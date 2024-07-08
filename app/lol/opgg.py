import aiohttp
import asyncio
from async_lru import alru_cache

from app.common.config import cfg

TAG = "opgg"


class Opgg:
    def __init__(self):
        self.session = aiohttp.ClientSession("https://lol-api-champion.op.gg")

        self.defaultModes = ['ranked', 'aram', 'arena']
        self.tierList = {mode: None for mode in self.defaultModes}
        self.version = None

        self.defaultTier = cfg.get(cfg.opggTier)
        self.defaultRegion = cfg.get(cfg.opggRegion)

    @alru_cache(maxsize=20)
    async def __fetchTierList(self, region, mode, tier, version):
        url = f"/api/{region}/champions/{mode}"
        params = {"tier": tier, "version": version}

        return await self.__get(url, params)

    @alru_cache(maxsize=20)
    async def __fetchChampionBuild(self, region, mode, championId, position, tier, version):
        url = f"/api/{region}/champions/{mode}/{championId}/{position}"
        params = {"tier": tier, "version": version}

        return await self.__get(url, params)

    @alru_cache(maxsize=20)
    async def getDataVersion(self, region, mode):
        url = f"/api/{region}/champions/{mode}/versions"
        return await self.__get(url)

    @alru_cache(maxsize=20)
    async def getTierList(self, region, mode, tier, version):
        raw = await self.__fetchTierList(region, mode, tier, version)

        if mode == 'ranked':
            res = self.__parseRankedTierList(raw)
        else:
            res = self.__parseOtherTierList(raw)

        return res

    async def initDefalutTier(self):
        region = self.defaultRegion
        version = await self.getDataVersion(region, 'ranked')
        self.version = version['data'][0]

        for mode in self.defaultModes:
            # 只在召唤师峡谷模式下按照默认段位取梯队
            if mode == 'ranked':
                tier = self.defaultTier
            else:
                tier = 'all'

            res = await self.getTierList(region, mode, tier, self.version)
            self.tierList[mode] = res

    def __parseRankedTierList(self, data):
        '''
        召唤师峡谷模式下的原始梯队数据，是所有英雄所有位置一起返回的

        在此函数内按照分路位置将它们分开
        '''
        data = data['data']
        res = {p: [] for p in ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT']}

        for item in data:
            for p in item['positions']:
                position = p['name']

                stats = p['stats']
                tier = stats['tier_data']

                res[position].append({
                    'championId': item['id'],
                    'winRate': stats.get('win_rate'),
                    'pickRate': stats.get('pick_rate'),
                    'banRate': stats.get('ban_rate'),
                    'kda': stats.get('kda'),
                    'tier': tier.get('tier'),
                    'rank': tier.get('rank'),
                    'counters': [c['champion_id'] for c in p['counters']]
                })

        # 排名 / 梯队是乱的，所以排个序
        for tier in res.values():
            tier.sort(key=lambda x: x['rank'])

        return res

    def __parseOtherTierList(self, data):
        '''
        处理其他模式下的原始梯队数据
        '''

        data = data['data']
        res = []

        for item in data:
            stats = item['average_stats']

            res.append({
                'championId': item['id'],
                'winRate': stats.get('win_rate'),
                'pickRate': stats.get('pick_rate'),
                'banRate': stats.get('ban_rate'),
                'kda': stats.get('kda'),
                'tier': stats.get('tier'),
                'rank': stats.get('rank'),
            })

        return sorted(res, key=lambda x: x['rank'])

    async def __get(self, url, params=None):
        res = await self.session.get(url, params=params, ssl=False, proxy=None)
        return await res.json()

    async def close(self):
        await self.session.close()


opgg = Opgg()
