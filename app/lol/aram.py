import json
import os
import re
from functools import lru_cache, wraps

import requests

from app.common.config import cfg, LOCAL_PATH
from app.common.logger import logger
from app.common.util import getLolClientVersion


class AramHome:
    """
    #### 数据使用已获得授权
    Powered by: 大乱斗之家
    Site: http://www.jddld.com
    """
    ARAM_CFG_PATH = f"{LOCAL_PATH}/AramBuff.json"
    URL = "http://www.jddld.com"
    TAG = "AramHome"
    APPID = 1
    APP_SECRET = "PHPCMFBBC77AF8E8FA5"
    data = None

    @staticmethod
    def needData(func):
        """
        TODO 如何优雅地使用它? -- By Hpero4
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if AramHome.data is None:
                m = AramHome()
                m.__loadData()
            return func(*args, **kwargs)

        return wrapper

    @classmethod
    async def checkAndUpdate(cls):
        m = cls()
        if m.__checkUpdate():
            await m.__update()

    @classmethod
    def getInfoByChampionId(cls, championId: str):
        return cls.getInfoByField("heroid", championId)

    @classmethod
    def getInfoByChampionName(cls, name: str):
        return cls.getInfoByField("name", name)

    @classmethod
    def getInfoByCatName(cls, name: str):
        return cls.getInfoByField("catname", name)

    @classmethod
    def getInfoByCatNameLoose(cls, name: str):
        return cls.getInfoByFieldLoose("catname", name)

    @classmethod
    # @needData
    @lru_cache(maxsize=None)
    def getInfoByField(cls, field: str, val: str):
        """
        通过字段值匹配一个item

        找不到返回 None
        """
        if cls.data is None:
            m = cls()
            m.__loadData()
        for item in cls.data.values():
            if item[field] == val:
                return item
        return None

    @classmethod
    # @needData
    @lru_cache(maxsize=None)
    def getInfoByFieldLoose(cls, field: str, val: str):
        """
        通过字段值匹配一个item

        宽松匹配, 只要val在field内都认为找到

        找不到返回 None
        """
        if cls.data is None:
            m = cls()
            m.__loadData()
        for item in cls.data.values():
            if val in item[field]:
                return item
        return None

    def __loadData(self):
        with open(self.ARAM_CFG_PATH, 'r') as f:
            AramHome.data = json.loads(f.read())

    async def __update(self):
        logger.info("update info", self.TAG)
        url = f"{self.URL}/index.php"
        params = {
            'appid': self.APPID,
            'appsecret': self.APP_SECRET,
            's': 'news',
            'c': 'search',
            'api_call_function': 'module_list',
            'pagesize': '200'  # FIXME 超过200个英雄会拿不完 -- By Hpero4
        }
        data = requests.get(url, params=params, proxies=None,
                            verify=False).json()  # 它不需要代理
        if data.get("code") == 1:
            with open(self.ARAM_CFG_PATH, "w") as f:
                data = data.get("data")
                json.dump(data, f)
                AramHome.data = data
        else:
            logger.warning(f"update err: {data}", self.TAG)

    def __checkUpdate(self):
        """
        检查缓存的数据与当前版本是否匹配, 若不匹配尝试更新

        尽可能在游戏启动后再调用, 否则当存在多个客户端时, cfg.lolFolder不一定是准确的(外服国服可能版本不同)

        @return :
            True -> 需要更新
            False -> 无需更新

        TODO: 暂未提供历史版本数据查询接口
        """

        try:
            lolVersion = getLolClientVersion()
        except:
            return True

        # 检查一下版本号是否相同, 如果一样, 就不更新了
        if os.path.exists(self.ARAM_CFG_PATH):
            with open(self.ARAM_CFG_PATH, "r") as f:
                data = json.loads(f.read())
                AramHome.data = data
                dataVer = re.search(
                    r"\d+\.\d+", data.get("banben", "")).group(0)
                if dataVer and dataVer == lolVersion:
                    return False

        return True
