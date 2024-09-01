import json
import os

import aiohttp

from app.common.config import LOCAL_PATH
from app.common.logger import logger
from app.common.util import getLolClientVersion


class ChampionAlias:
    CHAMPION_CFG_PATH = f"{LOCAL_PATH}/ChampionAlias.json"
    URL = 'https://game.gtimg.cn/images/lol/act/img/js/heroList/hero_list.js'
    TAG = "ChampionAlias"

    data = None
    leastResult = []
    leastSearched = ''

    @classmethod
    async def checkAndUpdate(cls):
        m = cls()
        if m.__needUpdate():
            await m.__update()

    async def __update(self):
        logger.info("Update champions alias", self.TAG)

        try:
            async with aiohttp.ClientSession() as session:
                res = await session.get(self.URL, proxy=None, ssl=False)

                # 不知道为什么这样子不行：
                # res = await res.json()

                s = str(await res.read(), encoding='utf-8')
                res = json.loads(s)

            champions = {}

            for champion in res['hero']:
                championId = champion['heroId']
                championAlias = champion['alias']
                keywords = champion['keywords']
                key = f"{keywords.lower()},{championAlias.lower()}"

                champions[championId] = key

            ChampionAlias.data = {
                'champions': champions,
                'version': res['version']
            }

            with open(self.CHAMPION_CFG_PATH, 'w') as f:
                json.dump(ChampionAlias.data, f)
        except:
            logger.info("Update champions alias FAILED", self.TAG)
            ChampionAlias.data = None

    def __needUpdate(self):
        try:
            lolVersion = getLolClientVersion()
        except:
            return True

        if not os.path.exists(self.CHAMPION_CFG_PATH):
            return True

        with open(self.CHAMPION_CFG_PATH, 'r') as f:
            try:
                ChampionAlias.data = json.loads(f.read())
            except:
                return True

        return ChampionAlias.getDataVersion() != lolVersion

    @staticmethod
    def computeDict(dic: dict, key, fun: callable):
        dic[key] = fun(key, dic.get(key))

    @classmethod
    def getChampionsAlias(cls) -> dict:
        champions = ChampionAlias.data['champions']
        cls.computeDict(champions, "901", lambda x, y: y + ",小火龙")# 斯莫德
        cls.computeDict(champions, "950", lambda x, y: y + ",狗")# 纳亚菲利
        cls.computeDict(champions, "902", lambda x, y: y + ",丁真")# 米利欧
        cls.computeDict(champions, "897", lambda x, y: y + ",黑龙,n-word")# 奎桑提
        return champions

    @classmethod
    def isAvailable(cls) -> bool:
        return ChampionAlias.data != None

    @classmethod
    def getDataVersion(cls) -> str:
        return ChampionAlias.data.get("version")

    @classmethod
    def getChampionIdsByAliasFuzzily(cls, alias):
        data = ChampionAlias.getChampionsAlias()
        res = []

        if alias == '':
            return [int(i) for i in data.keys()]

        if len(ChampionAlias.leastResult) == 0 \
                or ChampionAlias.leastSearched not in alias:

            for id, aliases in data.items():
                if alias in aliases:
                    res.append(id)
        else:
            for id in ChampionAlias.leastResult:
                aliases = data[id]

                if alias in aliases:
                    res.append(id)

        ChampionAlias.leastResult = res
        ChampionAlias.leastSearched = alias

        return [int(id) for id in res]
