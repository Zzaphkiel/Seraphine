import json
import os
import re
from functools import lru_cache, wraps

import aiohttp

from app.common.config import cfg, LOCAL_PATH
from app.common.logger import logger
from app.common.util import getLolClientVersion


class AramBuff:
    """
    #### 数据使用已获得授权
    Powered by: 大乱斗之家
    Site: http://www.jddld.com
    """
    ARAM_CFG_PATH = f"{LOCAL_PATH}/AramBuff.json"
    URL = "http://www.jddld.com"
    TAG = "AramBuff"
    APPID = 1
    APP_SECRET = "PHPCMFBBC77AF8E8FA5"
    data = None

    @classmethod
    async def checkAndUpdate(cls):
        m = cls()
        if m.__needUpdate():
            await m.__update()

    def __needUpdate(self):
        """
        检查缓存的数据与当前版本是否匹配, 若不匹配尝试更新

        尽可能在游戏启动后再调用, 否则当存在多个客户端时, `cfg.lolFolder` 不一定是准确的
        （外服国服可能版本不同）

        @return :
        - `True` -> 需要更新
        - `False` -> 无需更新

        TODO: 暂未提供历史版本数据查询接口
        """
        try:
            lolVersion = getLolClientVersion()
        except:
            return True

        if not os.path.exists(self.ARAM_CFG_PATH):
            return True

        with open(self.ARAM_CFG_PATH, 'r') as f:
            try:
                AramBuff.data = json.loads(f.read())
            except:
                return True

            # 兼容老版本的 json
            if AramBuff.data.get('version') == None:
                return True

            return AramBuff.getDataVersion() != lolVersion

    @classmethod
    def getDataVersion(cls):
        return AramBuff.data.get("version")

    async def __update(self):
        url = f'{self.URL}/index.php'
        params = {
            'appid': self.APPID,
            'appsecret': self.APP_SECRET,
            's': 'news',
            'c': 'search',
            'api_call_function': 'module_list',
            'pagesize': '200'
        }

        try:
            async with aiohttp.ClientSession() as session:
                res = await session.get(url, params=params, proxy=None, ssl=False)
                data = await res.json()
        except:
            logger.warning(f"Getting Aram buff failed, data: {data}", self.TAG)
            return

        if data.get('code') != 1:
            logger.warning(f"Update Aram buff failed, data: {data}", self.TAG)
            return

        try:
            data: dict = data['data']

            version = data.pop('banben')
            champions = {item['heroid']: item for item in data.values()}

            AramBuff.data = {
                'champions': champions,
                'version': version
            }

            with open(self.ARAM_CFG_PATH, 'w') as f:
                json.dump(AramBuff.data, f)

        except:
            logger.warning(f"Parse Aram buff failed, data: {data}", self.TAG)
            return

    @classmethod
    def isAvailable(cls) -> bool:
        return AramBuff.data != None

    @classmethod
    @lru_cache(maxsize=None)
    def getInfoByChampionId(cls, championId):
        if not AramBuff.isAvailable():
            return None

        return AramBuff.data['champions'].get(str(championId))
