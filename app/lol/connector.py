import inspect
import os
import json
import threading
import traceback

import requests
import time

import psutil
from ..common.config import cfg, Language
from .exceptions import *
from ..common.logger import logger

requests.packages.urllib3.disable_warnings()

TAG = "Connector"

def slowly():
    def decorator(func):
        def wrapper(*args, **kwargs):
            while connector.tackleFlag.is_set():
                time.sleep(.2)

            res = func(*args, **kwargs)
            return res

        return wrapper

    return decorator


def tackle():
    def decorator(func):
        def wrapper(*args, **kwargs):
            connector.tackleFlag.set()
            res = func(*args, **kwargs)
            connector.tackleFlag.clear()
            return res

        return wrapper

    return decorator


def retry(count=5, retry_sep=0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"call %s" % func.__name__, TAG)

            # 获取函数的参数信息
            func_params = inspect.signature(func).parameters
            param_names = list(func_params.keys())

            tmp_args = args
            if param_names[0] == "self":  # args[0]是self(connector)的实例, 兼容静态方法
                param_names = param_names[1:]
                tmp_args = args[1:]

            # 构建参数字典，将参数名与对应的实参值一一对应
            params_dict = {param: arg for param, arg in zip(param_names, tmp_args)}

            logger.debug(f"args = {params_dict}|kwargs = {kwargs}", TAG)

            # logger.debug(f"args = {args[1:]}|kwargs = {kwargs}", TAG)
            exce = None
            for _ in range(count):
                while connector.ref_cnt >= 2:
                    time.sleep(.2)

                connector.ref_cnt += 1
                try:
                    res = func(*args, **kwargs)
                except BaseException as e:
                    connector.ref_cnt -= 1
                    time.sleep(retry_sep)
                    exce = e
                    continue
                else:
                    connector.ref_cnt -= 1
                    break
            else:
                # 有异常抛异常, 没异常抛 RetryMaximumAttempts
                exce = exce if exce else RetryMaximumAttempts(
                    "Exceeded maximum retry attempts.")

                # ReferenceError为LCU未就绪仍有请求发送时抛出, 直接吞掉不用提示
                # 其余异常弹一个提示
                if type(exce) is not ReferenceError:
                    connector.ref_cnt -= 1
                    connector.exceptApi = func.__name__
                    connector.exceptObj = exce

                logger.exception(f"exit {func.__name__}", exce, TAG)

                raise exce

            logger.info(f"exit {func.__name__}", TAG)
            logger.debug(f"result = {res}", TAG)

            return res

        return wrapper

    return decorator


def needLcu():
    def decorator(func):
        def wrapper(*args, **kwargs):
            if connector.sess is None:
                raise ReferenceError
            res = func(*args, **kwargs)
            return res

        return wrapper

    return decorator


def getPortTokenServerByPid(pid):
    '''
    通过进程 id 获得启动命令行参数中的 port、token 以及登录服务器
    '''
    port, token, server = None, None, None

    process = psutil.Process(pid)
    cmdline = process.cmdline()

    for cmd in cmdline:
        p = cmd.find("--app-port=")
        if p != -1:
            port = cmd[11:]

        p = cmd.find("--remoting-auth-token=")
        if p != -1:
            token = cmd[22:]

        p = cmd.find("--rso_platform_id=")
        if p != -1:
            server = cmd[18:]

        if port and token and server:
            break
    
    return port, token, server

class LolClientConnector:
    def __init__(self):
        self.sess = None
        self.slowlySess = None
        self.port = None
        self.token = None
        self.url = None

        # 并发数过高时会导致LCU闪退
        # 通过引用计数避免 (不大于3个并发)
        self.ref_cnt = 0
        self.tackleFlag = threading.Event()
        self.manager = None

        self.exceptApi = None
        self.exceptObj = None

    def start(self, port, token):
        self.sess = requests.session()
        self.port, self.token = port, token

        self.url = f"https://riot:{self.token}@127.0.0.1:{self.port}"

        self.__initManager()
        self.__initFolder()

    def close(self):
        self.sess.close()
        self.__init__()

    def __initFolder(self):
        if not os.path.exists("app/resource/game"):
            os.mkdir("app/resource/game")

        for folder in [
            "champion icons",
            "item icons",
            "profile icons",
            "rune icons",
            "summoner spell icons",
        ]:
            p = f"app/resource/game/{folder}"
            if not os.path.exists(p):
                os.mkdir(p)

    @retry()
    def __initManager(self):
        items = self.__json_retry_get("/lol-game-data/assets/v1/items.json")
        spells = self.__json_retry_get(
            "/lol-game-data/assets/v1/summoner-spells.json")
        runes = self.__json_retry_get("/lol-game-data/assets/v1/perks.json")
        queues = self.__json_retry_get("/lol-game-queues/v1/queues")
        champions = self.__json_retry_get(
            "/lol-game-data/assets/v1/champion-summary.json")
        skins = self.__json_retry_get("/lol-game-data/assets/v1/skins.json")

        self.manager = JsonManager(
            items, spells, runes, queues, champions, skins)

    def __json_retry_get(self, url, max_retries=5):
        """
        根据 httpStatus 字段值, retry 获取数据

        用于软件初始化阶段

        @param url:
        @param max_retries:
        @return: json
        @rtype: dict
        """
        retries = 0
        while retries < max_retries:
            try:
                result = self.__get(url).json()
            except ConnectionError:  # 客户端刚打开, Service正在初始化, 有部分请求可能会ConnectionError, 直接忽略重试
                retries += 1
                time.sleep(.5)
                continue

            if type(result) is list:
                return result
            # 如果有才判定, 有部分相应成功时没有httpStatus
            elif result.get("httpStatus") and result.get("httpStatus") != 200:
                time.sleep(.5)
                retries += 1
            else:
                return result

        # 最大重试次数, 抛异常
        raise RetryMaximumAttempts("Exceeded maximum retry attempts.")

    @retry()
    def getRuneIcon(self, runeId):
        if runeId == 0:
            return "app/resource/images/rune-0.png"

        icon = f"app/resource/game/rune icons/{runeId}.png"
        if not os.path.exists(icon):
            path = self.manager.getRuneIconPath(runeId)
            res = self.__get(path)

            with open(icon, "wb") as f:
                f.write(res.content)

        return icon

    @retry()
    def getCurrentSummoner(self):
        res = self.__get("/lol-summoner/v1/current-summoner").json()

        if not "summonerId" in res:
            raise Exception()

        return res

    @retry()
    def getInstallFolder(self):
        res = self.__get("/data-store/v1/install-dir").json()
        return res

    @retry()
    def getProfileIcon(self, iconId):
        icon = f"./app/resource/game/profile icons/{iconId}.jpg"

        if not os.path.exists(icon):
            path = self.manager.getSummonerProfileIconPath(iconId)
            res = self.__get(path)
            with open(icon, "wb") as f:
                f.write(res.content)

        return icon

    @retry()
    def getItemIcon(self, iconId):
        if iconId == 0:
            return "app/resource/images/item-0.png"

        icon = f"app/resource/game/item icons/{iconId}.png"

        if not os.path.exists(icon):
            path = self.manager.getItemIconPath(iconId)
            res = self.__get(path)

            with open(icon, "wb") as f:
                f.write(res.content)

        return icon

    @retry()
    def getSummonerSpellIcon(self, spellId):
        icon = f"app/resource/game/summoner spell icons/{spellId}.png"

        if not os.path.exists(icon):
            path = self.manager.getSummonerSpellIconPath(spellId)
            res = self.__get(path)

            with open(icon, "wb") as f:
                f.write(res.content)

        return icon

    @retry()
    def getChampionIcon(self, championId) -> str:
        """

        @param championId:
        @return: path
        @rtype: str
        """

        if championId == -1:
            return "app/resource/images/champion-0.png"

        icon = f"app/resource/game/champion icons/{championId}.png"

        if not os.path.exists(icon):
            path = self.manager.getChampionIconPath(championId)
            res = self.__get(path)

            with open(icon, "wb") as f:
                f.write(res.content)

        return icon

    @retry()
    def getSummonerByName(self, name):
        params = {"name": name}
        res = self.__get(f"/lol-summoner/v1/summoners", params).json()

        if "errorCode" in res:
            raise SummonerNotFound()

        return res

    @retry()
    def getSummonerByPuuid(self, puuid):
        res = self.__get(f"/lol-summoner/v2/summoners/puuid/{puuid}").json()

        if "errorCode" in res:
            raise SummonerNotFound()

        return res

    @slowly()
    @retry(5, 1)
    def getSummonerGamesByPuuidSlowly(self, puuid, begIndex=0, endIndex=4):
        """
        Retrieves a list of summoner games by puuid using a slow and retry mechanism.

        Parameters:
            puuid (str): The puuid of the summoner.
            begIndex (int): The beginning index of the games to retrieve. Default is 0.
            endIndex (int): The ending index of the games to retrieve. Default is 4.

        Returns:
            list: A list of summoner games.

        Raises:
            SummonerGamesNotFound: If the summoner games are not found.
        """
        params = {"begIndex": begIndex, "endIndex": endIndex}
        res = self.__slowlyGet(
            f"/lol-match-history/v1/products/lol/{puuid}/matches", params
        ).json()

        if "games" not in res:
            raise SummonerGamesNotFound()

        return res["games"]

    @tackle()
    @retry()
    def getSummonerGamesByPuuid(self, puuid, begIndex=0, endIndex=4):
        """
        Retrieves a list of summoner games by PUUID.

        Args:
            puuid (str): The PUUID of the summoner.
            begIndex (int, optional): The starting index of the games to retrieve. Defaults to 0.
            endIndex (int, optional): The ending index of the games to retrieve. Defaults to 4.

        Returns:
            list: A list of summoner games.

        Raises:
            SummonerGamesNotFound: If the summoner games are not found.
        """
        params = {"begIndex": begIndex, "endIndex": endIndex}
        res = self.__get(
            f"/lol-match-history/v1/products/lol/{puuid}/matches", params
        ).json()

        if "games" not in res:
            raise SummonerGamesNotFound()

        return res["games"]

    @tackle()
    @retry()
    def getGameDetailByGameId(self, gameId):
        res = self.__get(f"/lol-match-history/v1/games/{gameId}").json()

        return res

    @tackle()
    @retry()
    def getRankedStatsByPuuid(self, puuid):
        res = self.__get(f"/lol-ranked/v1/ranked-stats/{puuid}").json()

        return res

    @retry()
    def setProfileBackground(self, skinId):
        data = {
            "key": "backgroundSkinId",
            "value": skinId,
        }
        res = self.__post(
            "/lol-summoner/v1/current-summoner/summoner-profile", data=data
        ).json()

        return res

    @retry()
    def setOnlineStatus(self, message):
        data = {"statusMessage": message}
        res = self.__put("/lol-chat/v1/me", data=data).json()

        return res

    @retry()
    def setTierShowed(self, queue, tier, division):
        data = {
            "lol": {
                "rankedLeagueQueue": queue,
                "rankedLeagueTier": tier,
                "rankedLeagueDivision": division,
            }
        }

        res = self.__put("/lol-chat/v1/me", data=data).json()

        return res

    @retry()
    def reconnect(self):
        """
        重新连接

        @return:
        """
        return self.__post("/lol-gameflow/v1/reconnect")

    @retry()
    def removeTokens(self):
        reference = self.__get("/lol-chat/v1/me").json()
        banner = reference['lol']['bannerIdSelected']

        data = {"challengeIds": [], "bannerAccent": str(banner)}
        res = self.__post(
            "/lol-challenges/v1/update-player-preferences/", data=data
        ).content
        return res

    @retry()
    def create5v5PracticeLobby(self, lobbyName, password):
        data = {
            "customGameLobby": {
                "configuration": {
                    "gameMode": "PRACTICETOOL",
                    "gameMutator": "",
                    "gameServerRegion": "",
                    "mapId": 11,
                    "mutators": {"id": 1},
                    "spectatorPolicy": "AllAllowed",
                    "teamSize": 5,
                },
                "lobbyName": lobbyName,
                "lobbyPassword": password,
            },
            "isCustom": True,
        }
        res = self.__post("/lol-lobby/v2/lobby", data=data).json()

        return res

    @retry()
    def setOnlineAvailability(self, availability):
        data = {"availability": availability}

        res = self.__put("/lol-chat/v1/me", data=data)
        return res

    @retry()
    def acceptMatchMaking(self):
        res = self.__post("/lol-matchmaking/v1/ready-check/accept")
        return res

    @retry()
    def getGameflowSession(self):
        # FIXME
        #  若刚进行完一场对局, 随后开启一盘自定义, 玩家在红色方且蓝色方没人时, 该接口会返回上一局中蓝色方的队员信息(teamOne or teamTwo)
        res = self.__get("/lol-gameflow/v1/session").json()
        return res

    def getChampSelectSession(self):
        res = self.__get("/lol-champ-select/v1/session").json()

        return res

    # 选择英雄
    def selectChampion(self, championId):
        session = self.__get("/lol-champ-select/v1/session").json()

        if not session['hasSimultaneousPicks'] or session['isSpectating']:
            return

        localPlayerCellId = session["localPlayerCellId"]

        for action in session["actions"][0]:
            if action["actorCellId"] == localPlayerCellId:
                id = action["id"]
                break

        data = {
            "championId": championId,
            'type': 'pick',
            # 'completed': True,
        }

        res = self.__patch(
            f"/lol-champ-select/v1/session/actions/{id}", data=data).content

        return res

    @retry()
    def getSummonerById(self, summonerId):
        res = self.__get(f"/lol-summoner/v1/summoners/{summonerId}").json()

        return res

    @retry()
    def getGameStatus(self):
        res = self.__get("/lol-gameflow/v1/gameflow-phase").text[1:-1]
        return res

    @retry()
    def getMapSide(self):
        js = self.__get("/lol-champ-select/v1/pin-drop-notification").json()

        return js.get("mapSide", "")

    @retry()
    def getReadyCheckStatus(self):
        res = self.__get("/lol-matchmaking/v1/ready-check").json()

        return res

    def spectate(self, summonerName):
        info = self.getSummonerByName(summonerName)

        data = {
            'allowObserveMode': 'ALL',
            'dropInSpectateGameId': summonerName,
            'gameQueueType': "",
            'puuid': info['puuid'],
        }

        res = self.__post(
            f"/lol-spectator/v1/spectate/launch", data=data).content

        if res != b'':
            raise SummonerNotInGame()

        return res

    def getConversations(self):
        res = self.__get("/lol-chat/v1/conversations").json()

        return res

    def dodge(self):
        res = self.__post(
            '/lol-login/v1/session/invoke?destination=lcdsServiceProxy&method=call&args=["","teambuilder-draft","quitV2",""])').content

        return res

    @retry()
    def sendNotificationMsg(self, title, content):
        data = {
            "critical": True,
            "data": {
                "details": content,
                "title": title,
            },
            "detailKey": 'pre_translated_details',
            "dismissible": True,
            "id": 0,
            "state": 'toast',
            "titleKey": 'pre_translated_title',
            "type": 'ranked_summary',
        }

        res = self.__post(
            "/player-notifications/v1/notifications", data=data).json()

        return res

    @retry()
    def playAgain(self):
        res = self.__post("/lol-lobby/v2/play-again").content

        return res

    @retry()
    def getClientZoom(self):
        res = self.__get("/riotclient/zoom-scale").json()

        return res

    @needLcu()
    def __get(self, path, params=None):
        url = self.url + path
        return self.sess.get(url, params=params, verify=False)

    @needLcu()
    def __slowlyGet(self, path, params=None):
        url = self.url + path
        if not self.slowlySess:
            self.slowlySess = requests.session()
        return self.slowlySess.get(url, params=params, verify=False)

    @needLcu()
    def __post(self, path, data=None):
        url = self.url + path
        headers = {"Content-type": "application/json"}
        return self.sess.post(url, json=data, headers=headers, verify=False)

    @needLcu()
    def __put(self, path, data=None):
        url = self.url + path
        return self.sess.put(url, json=data, verify=False)

    @needLcu()
    def __patch(self, path, data=None):
        url = self.url + path
        return self.sess.patch(url, json=data, verify=False)


class JsonManager:
    # 曾经奥恩可以升级的杰作装备
    masterpieceItemsMap = {
        7003: 6664,  # 涡轮炼金罐
        7004: 3068,  # 日炎圣盾
        7007: 6672,  # 海妖杀手
        7008: 6673,  # 不朽盾弓
        7022: 4005,  # 帝国指令
    }

    def __init__(self, itemData, spellData, runeData, queueData, champions, skins):
        self.items = {item["id"]: item["iconPath"] for item in itemData}
        self.spells = {item["id"]: item["iconPath"] for item in spellData[:-3]}
        self.runes = {item["id"]: item["iconPath"] for item in runeData}

        self.champs = {item["id"]: item["name"] for item in champions}

        self.champions = {item: {"skins": {}} for item in self.champs.values()}
        self.queues = {
            item["id"]: {"mapId": item["mapId"], "name": item["name"]}
            for item in queueData
        }

        for item in skins.values():
            championId = item["id"] // 1000
            self.champions[self.champs[championId]
                           ]["skins"][item["name"]] = item["id"]
            self.champions[self.champs[championId]]["id"] = championId

        for oldId, nowId in JsonManager.masterpieceItemsMap.items():
            self.items[oldId] = self.items[nowId]

    def getItemIconPath(self, iconId):
        if iconId != 0:
            try:
                return self.items[iconId]
            except:
                logger.error(f"getItemIconPath, iconId: {iconId}", tag=TAG)
        
        return "/lol-game-data/assets/ASSETS/Items/Icons2D/gp_ui_placeholder.png"

    def getSummonerSpellIconPath(self, spellId):
        if spellId != 0:
            return self.spells[spellId]
        else:
            return "/lol-game-data/assets/data/spells/icons2d/summoner_empty.png"

    def getRuneIconPath(self, runeId):
        return self.runes[runeId]

    def getSummonerProfileIconPath(self, iconId):
        return f"/lol-game-data/assets/v1/profile-icons/{iconId}.jpg"

    def getChampionIconPath(self, championId):
        return f"/lol-game-data/assets/v1/champion-icons/{championId}.png"

    def getMapNameById(self, mapId):
        maps = {
            -1: ("特殊地图", "Special map"),
            11: ("召唤师峡谷", "Summoner's Rift"),
            12: ("嚎哭深渊", "Howling Abyss"),
            21: ("极限闪击", "Nexus Blitz"),
            30: ("斗魂竞技场", "Arena"),
        }

        key = mapId if mapId in maps else -1
        index = 1 if cfg.language.value == Language.ENGLISH else 0

        return maps[key][index]

    def getNameMapByQueueId(self, queueId):
        if queueId == 0:
            return {
                "name": "Custom" if cfg.language.value == Language.ENGLISH else "自定义"
            }

        data = self.queues[queueId]
        mapId = data["mapId"]
        name = data["name"]

        if cfg.language.value == Language.ENGLISH:
            with open("app/resource/i18n/gamemodes.json", encoding="utf-8") as f:
                translate = json.loads(f.read())
                name = translate[name]

        map = self.getMapNameById(mapId)

        return {"map": map, "name": name}

    def getMapIconByMapId(self, mapId, win):
        result = "victory" if win else "defeat"
        if mapId == 11:
            mapName = "sr"
        elif mapId == 12:
            mapName = "ha"
        elif mapId == 30:
            mapName = "arena"
        else:
            mapName = "other"

        return f"app/resource/images/{mapName}-{result}.png"

    def getChampionList(self):
        return [item for item in self.champions.keys()]

    def getSkinListByChampionName(self, championName):
        try:
            return [item for item in self.champions[championName]["skins"]]
        except:
            return []

    def getSkinIdByChampionAndSkinName(self, championName, skinName):
        return self.champions[championName]["skins"][skinName]

    def getChampionIdByName(self, championName):
        return self.champions[championName]["id"]


connector = LolClientConnector()
