import json
import os
import re
from functools import lru_cache, wraps

import requests

from app.common.config import cfg, LOCAL_PATH
from app.common.logger import logger
from app.common.util import getLolClientVersion


class ChampionAlias:
    CHAMPION_CFG_PATH = f"{LOCAL_PATH}/ChampionAlias.json"
    URL = 'https://game.gtimg.cn/images/lol/act/img/js/heroList/hero_list.js'

    data = None
    leastSearched = ""

    # @classmethod
    # async def checkAndUpdate(cls):
    #     m = cls()
    #     if m.__needUpdate():
    #         m.__update()

    def __update(self):
        res = requests.get(self.URL).json()
        champions = {}

        for champion in res['hero']:
            championId = champion['heroId']
            championAlias = champion['alias']
            keywords = champion['keywords']
            key = f"{keywords.lower()},{championAlias.lower()}"

            champions[championId] = key

        self.data = {
            'champions': champions,
            'version': res['version']
        }

        with open(self.CHAMPION_CFG_PATH, 'w') as f:
            json.dump(self.data, f)

    def __load(self):
        with open(self.CHAMPION_CFG_PATH, 'r') as f:
            self.data = json.loads(f.read())

    def __needUpdate(self):
        try:
            lolVersion = getLolClientVersion()
        except:
            return True

        if not os.path.exists(self.CHAMPION_CFG_PATH):
            return True

        with open(self.CHAMPION_CFG_PATH, 'r') as f:
            self.data = json.loads(f.read)

            return self.data['version'] != lolVersion
