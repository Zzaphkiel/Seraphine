import aiohttp
import asyncio
from async_lru import alru_cache

from PyQt5.QtCore import QObject
from app.common.config import cfg
from app.lol.connector import connector

TAG = "opgg"


class Opgg(QObject):
    def __init__(self):
        self.session = None

        self.defaultModes = ['ranked', 'aram', 'arena']
        self.defaultTier = cfg.get(cfg.opggTier)
        self.defaultRegion = cfg.get(cfg.opggRegion)

    async def start(self):
        self.session = aiohttp.ClientSession("https://lol-api-champion.op.gg")

    @alru_cache(maxsize=128)
    async def __fetchTierList(self, region, mode, tier):
        url = f"/api/{region}/champions/{mode}"
        params = {"tier": tier}

        return await self.__get(url, params)

    @alru_cache(maxsize=128)
    async def __fetchChampionBuild(self, region, mode, championId, position, tier):
        url = f"/api/{region}/champions/{mode}/{championId}/{position}"
        params = {"tier": tier}

        return await self.__get(url, params)

    @alru_cache(maxsize=128)
    async def getChampionBuild(self, region, mode, championId, position, tier):
        raw = await self.__fetchChampionBuild(region, mode, championId, position, tier)
        version = raw['meta']['version']

        map = {
            'ranked': OpggDataParser.parseRankedChampionBuild(raw, position)
        }

        res = await map[mode]

        return {
            'data': res,
            'version': version
        }

    @alru_cache(maxsize=128)
    async def getTierList(self, region, mode, tier):
        raw = await self.__fetchTierList(region, mode, tier)

        version = raw['meta']['version']

        if mode == 'ranked':
            res = await OpggDataParser.parseRankedTierList(raw)
        else:
            res = await OpggDataParser.parseOtherTierList(raw)

        return {
            'data': res,
            'version': version
        }

    async def initDefalutTier(self):
        region = self.defaultRegion

        for mode in self.defaultModes:
            # 只在召唤师峡谷模式下按照默认段位取梯队

            if mode == 'ranked':
                tier = self.defaultTier
            else:
                tier = 'all'

            # 因为这函数有 cache，直接无脑调用一下妥了
            _ = await self.getTierList(region, mode, tier)

    async def __get(self, url, params=None):
        res = await self.session.get(url, params=params, ssl=False, proxy=None)
        return await res.json()

    async def close(self):
        if self.session:
            await self.session.close()


class OpggDataParser:
    @staticmethod
    async def parseRankedTierList(data):
        '''
        召唤师峡谷模式下的原始梯队数据，是所有英雄所有位置一起返回的

        在此函数内按照分路位置将它们分开
        '''

        data = data['data']
        res = {p: []
               for p in ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT']}

        for item in data:
            championId = item['id']
            name = connector.manager.getChampionNameById(championId)
            icon = await connector.getChampionIcon(championId)

            for p in item['positions']:
                position = p['name']

                stats = p['stats']
                tier = stats['tier_data']

                counters = [{
                    'championId': c['champion_id'],
                    'icon': await connector.getChampionIcon(c['champion_id'])
                } for c in p['counters']]

                res[position].append({
                    'championId': championId,
                    'name': name,
                    'icon': icon,
                    'winRate': stats.get('win_rate'),
                    'pickRate': stats.get('pick_rate'),
                    'banRate': stats.get('ban_rate'),
                    'kda': stats.get('kda'),
                    'tier': tier.get('tier'),
                    'rank': tier.get('rank'),
                    'position': position,
                    'counters': counters,
                })

        # 排名 / 梯队是乱的，所以排个序
        for tier in res.values():
            tier.sort(key=lambda x: x['rank'])

        return res

    @staticmethod
    async def parseOtherTierList(data):
        '''
        处理其他模式下的原始梯队数据
        '''

        data = data['data']
        res = []

        for item in data:
            stats = item['average_stats']

            if stats == None:
                continue

            if stats.get('rank') == None:
                continue

            championId = item['id']
            name = connector.manager.getChampionNameById(championId)
            icon = await connector.getChampionIcon(championId)

            res.append({
                'championId': championId,
                'name': name,
                'icon': icon,
                'winRate': stats.get('win_rate'),
                'pickRate': stats.get('pick_rate'),
                'banRate': stats.get('ban_rate'),
                'kda': stats.get('kda'),
                'tier': stats.get('tier'),
                'rank': stats.get('rank'),
                "position": None,
                'counters': [],
            })

        return sorted(res, key=lambda x: x['rank'])

    @staticmethod
    async def parseRankedChampionBuild(data, position):
        '''
        TODO
        处理排位模式下的英雄 Build
        '''

        data = data['data']

        summary = data['summary']
        championId = summary['id']
        icon = await connector.getChampionIcon(championId)
        name = connector.manager.getChampionNameById(championId)

        positions = summary['positions']

        for p in positions:
            if p['name'] != position:
                continue

            stats: dict = p['stats']
            winRate = stats.get('win_rate')
            pickRate = stats.get('pick_rate')
            banRate = stats.get('ban_rate')
            kda = stats.get('kda')

            tierData: dict = stats['tier_data']
            tier = tierData.get("tier")
            rank = tierData.get("rank")

        summonerSpells = []
        for s in data['summoner_spells']:
            icons = [await connector.getSummonerSpellIcon(id)
                     for id in s['ids']]

            summonerSpells.append({
                'ids': s['ids'],
                'icons': icons,
                'win': s['win'],
                'play': s['play'],
                'pickRate': s['pick_rate']
            })

        skills = {
            "masteries": data['skill_masteries'][0]['ids'],
            "order": data['skills'][0]['order'],
            'play': data['skills'][0]['play'],
            'win': data['skills'][0]['win'],
            'pickRate': data['skills'][0]['pick_rate']
        }

        boots = []
        for i in data['boots'][:3]:
            icons = [await connector.getItemIcon(id) for id in i['ids']]
            boots.append({
                "icons": icons,
                "play": i['play'],
                "win": i['win'],
                'pickRate': i['pick_rate']
            })

        startItems = []
        for i in data['starter_items'][:3]:
            icons = [await connector.getItemIcon(id) for id in i['ids']]
            startItems.append({
                "icons": icons,
                "play": i['play'],
                "win": i['win'],
                'pickRate': i['pick_rate']
            })

        coreItems = []
        for i in data['core_items'][:5]:
            icons = [await connector.getItemIcon(id) for id in i['ids']]
            coreItems.append({
                "icons": icons,
                "play": i['play'],
                "win": i['win'],
                'pickRate': i['pick_rate']
            })

        lastItems = []
        for i in data['last_items'][:16]:
            lastItems.append(await connector.getItemIcon(i['ids'][0]))

        strongAgainst = []
        weakAgainst = []

        for c in data['counters']:
            winRate = c['win'] / c['play']
            arr = strongAgainst if winRate >= 0.5 else weakAgainst

            arr.append({
                'championId': (id := c['champion_id']),
                'name': connector.manager.getChampionNameById(id),
                'icon': await connector.getChampionIcon(id),
                'play': c['play'],
                'win': c['win'],
                'winRate': winRate
            })

        strongAgainst.sort(key=lambda x: -x['winRate'])
        weakAgainst.sort(key=lambda x: x['winRate'])

        perks = [{
            'primaryId': (mainId := perk['primary_page_id']),
            "primaryIcon": await connector.getRuneIcon(mainId),
            'secondaryId': (subId := perk['secondary_page_id']),
            "secondaryIcon": await connector.getRuneIcon(subId),
            'perks': (perkIds := perk['primary_rune_ids']+perk['secondary_rune_ids']+perk['stat_mod_ids']),
            "icons": [await connector.getRuneIcon(id) for id in perkIds],
            'play': perk['play'],
            'win': perk['win'],
            'pickRate': perk['pick_rate'],
        } for perk in data['runes']
        ]

        return {
            "summary": {
                'name': name,
                'championId': championId,
                'icon': icon,
                'position': position,
                'winRate': winRate,
                'pickRate': pickRate,
                'banRate': banRate,
                'kda': kda,
                'tier': tier,
                'rank': rank
            },
            "summonerSpells": summonerSpells,
            "championSkills": skills,
            "items": {
                "boots": boots,
                "startItems": startItems,
                "coreItems": coreItems,
                "lastItems": lastItems,
            },
            "counters": {
                "strongAgainst": strongAgainst,
                "weakAgainst": weakAgainst,
            },
            "perks": perks
        }


opgg = Opgg()
