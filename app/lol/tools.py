import time
import win32gui
import win32con
import win32api
import ctypes

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication

from ..common.config import cfg, Language
from ..lol.connector import LolClientConnector, connector


class PositionTranslator(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.top = self.tr("TOP")
        self.jungle = self.tr("JUG")
        self.middle = self.tr("MID")
        self.bottom = self.tr("BOT")
        self.support = self.tr("SUP")


def translateTier(orig: str, short=False) -> str:
    if orig == '':
        return "--"

    maps = {
        'Iron': ['坚韧黑铁', '黑铁'],
        'Bronze': ['英勇黄铜', '黄铜'],
        'Silver': ['不屈白银', '白银'],
        'Gold': ['荣耀黄金', '黄金'],
        'Platinum': ['华贵铂金', '铂金'],
        'Emerald': ['流光翡翠', '翡翠'],
        'Diamond': ['璀璨钻石', '钻石'],
        'Master': ['超凡大师', '大师'],
        'Grandmaster': ['傲世宗师', '宗师'],
        'Challenger': ['最强王者', '王者'],
    }

    index = 1 if short else 0

    if cfg.language.value == Language.ENGLISH:
        return orig.capitalize()
    else:
        return maps[orig.capitalize()][index]


def timeStampToStr(stamp):
    """
    @param stamp: Millisecond timestamp
    """
    timeArray = time.localtime(stamp / 1000)
    return time.strftime("%Y/%m/%d %H:%M", timeArray)


def timeStampToShortStr(stamp):
    timeArray = time.localtime(stamp / 1000)
    return time.strftime("%m/%d", timeArray)


def secsToStr(secs):
    return time.strftime("%M:%S", time.gmtime(secs))


def processGameData(game):
    timeStamp = game["gameCreation"]  # 毫秒级时间戳
    time = timeStampToStr(game['gameCreation'])
    shortTime = timeStampToShortStr(game['gameCreation'])
    gameId = game['gameId']
    duration = secsToStr(game['gameDuration'])
    queueId = game['queueId']

    nameAndMap = connector.manager.getNameMapByQueueId(queueId)
    modeName = nameAndMap['name']

    if queueId != 0:
        mapName = nameAndMap['map']
    else:
        mapName = connector.manager.getMapNameById(game['mapId'])

    participant = game['participants'][0]
    championId = participant['championId']
    championIcon = connector.getChampionIcon(championId)
    spell1Id = participant['spell1Id']
    spell2Id = participant['spell2Id']
    spell1Icon = connector.getSummonerSpellIcon(spell1Id)
    spell2Icon = connector.getSummonerSpellIcon(spell2Id)
    stats = participant['stats']

    champLevel = stats['champLevel']
    kills = stats['kills']
    deaths = stats['deaths']
    assists = stats['assists']
    itemIds = [
        stats['item0'],
        stats['item1'],
        stats['item2'],
        stats['item3'],
        stats['item4'],
        stats['item5'],
        stats['item6'],
    ]

    itemIcons = [connector.getItemIcon(itemId) for itemId in itemIds]
    runeId = stats['perk0']
    runeIcon = connector.getRuneIcon(runeId)

    cs = stats['totalMinionsKilled'] + stats['neutralMinionsKilled']
    gold = stats['goldEarned']
    remake = stats['gameEndedInEarlySurrender']
    win = stats['win']

    timeline = participant['timeline']
    lane = timeline['lane']
    role = timeline['role']

    position = None

    pt = PositionTranslator()

    if queueId in [420, 440]:
        if lane == 'TOP':
            position = pt.top
        elif lane == "JUNGLE":
            position = pt.jungle
        elif lane == 'MIDDLE':
            position = pt.middle
        elif role == 'SUPPORT':
            position = pt.support
        elif lane == 'BOTTOM' and role == 'CARRY':
            position = pt.bottom

    return {
        'queueId': queueId,
        'gameId': gameId,
        'time': time,
        'shortTime': shortTime,
        'name': modeName,
        'map': mapName,
        'duration': duration,
        'remake': remake,
        'win': win,
        'championId': championId,
        'championIcon': championIcon,
        'spell1Icon': spell1Icon,
        'spell2Icon': spell2Icon,
        'champLevel': champLevel,
        'kills': kills,
        'deaths': deaths,
        'assists': assists,
        'itemIcons': itemIcons,
        'runeIcon': runeIcon,
        'cs': cs,
        'gold': gold,
        'timeStamp': timeStamp,
        'position': position,
    }


def processGameDetailData(puuid, game):
    queueId = game['queueId']
    mapId = game['mapId']

    names = connector.manager.getNameMapByQueueId(queueId)
    modeName = names['name']
    if queueId != 0:
        mapName = names['map']
    else:
        mapName = connector.manager.getMapNameById(mapId)

    teams = {
        100: {
            'win': None,
            'bans': [],
            'baronKills': 0,
            'baronIcon': "app/resource/images/baron-100.png",
            'dragonKills': 0,
            'dragonIcon': 'app/resource/images/dragon-100.png',
            'riftHeraldKills': 0,
            'riftHeraldIcon': 'app/resource/images/herald-100.png',
            'inhibitorKills': 0,
            'inhibitorIcon': 'app/resource/images/inhibitor-100.png',
            'towerKills': 0,
            'towerIcon': 'app/resource/images/tower-100.png',
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'gold': 0,
            'summoners': []
        },
        200: {
            'win': None,
            'bans': [],
            'baronKills': 0,
            'baronIcon': "app/resource/images/baron-200.png",
            'dragonKills': 0,
            'dragonIcon': 'app/resource/images/dragon-200.png',
            'riftHeraldKills': 0,
            'riftHeraldIcon': 'app/resource/images/herald-200.png',
            'inhibitorKills': 0,
            'inhibitorIcon': 'app/resource/images/inhibitor-200.png',
            'towerKills': 0,
            'towerIcon': 'app/resource/images/tower-200.png',
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'gold': 0,
            'summoners': []
        },
        300: {
            'win': None,
            'bans': [],
            'baronKills': 0,
            'baronIcon': "app/resource/images/baron-100.png",
            'dragonKills': 0,
            'dragonIcon': 'app/resource/images/dragon-100.png',
            'riftHeraldKills': 0,
            'riftHeraldIcon': 'app/resource/images/herald-100.png',
            'inhibitorKills': 0,
            'inhibitorIcon': 'app/resource/images/inhibitor-100.png',
            'towerKills': 0,
            'towerIcon': 'app/resource/images/tower-100.png',
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'gold': 0,
            'summoners': []
        },
        400: {
            'win': None,
            'bans': [],
            'baronKills': 0,
            'baronIcon': "app/resource/images/baron-200.png",
            'dragonKills': 0,
            'dragonIcon': 'app/resource/images/dragon-200.png',
            'riftHeraldKills': 0,
            'riftHeraldIcon': 'app/resource/images/herald-200.png',
            'inhibitorKills': 0,
            'inhibitorIcon': 'app/resource/images/inhibitor-200.png',
            'towerKills': 0,
            'towerIcon': 'app/resource/images/tower-200.png',
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'gold': 0,
            'summoners': []
        }
    }

    cherryResult = None

    for team in game['teams']:
        teamId = team['teamId']

        if teamId == 0:
            teamId = 200

        teams[teamId]['win'] = team['win']
        teams[teamId]['bans'] = [
            connector.getChampionIcon(item['championId'])
            for item in team['bans']
        ]
        teams[teamId]['baronKills'] = team['baronKills']
        teams[teamId]['dragonKills'] = team['dragonKills']
        teams[teamId]['riftHeraldKills'] = team['riftHeraldKills']
        teams[teamId]['towerKills'] = team['towerKills']
        teams[teamId]['inhibitorKills'] = team['inhibitorKills']

    for participant in game['participantIdentities']:
        participantId = participant['participantId']
        summonerName = participant['player'].get(
            'gameName') or participant['player'].get('summonerName')  # 兼容外服
        summonerPuuid = participant['player']['puuid']
        isCurrent = (summonerPuuid == puuid)

        if summonerPuuid == '00000000-0000-0000-0000-000000000000':  # AI
            isPublic = True
        else:
            isPublic = connector.getSummonerByPuuid(
                summonerPuuid)["privacy"] == "PUBLIC"

        for summoner in game['participants']:
            if summoner['participantId'] == participantId:
                stats = summoner['stats']

                if queueId != 1700:
                    subteamPlacement = None
                    tid = summoner['teamId']
                else:
                    subteamPlacement = stats['subteamPlacement']
                    tid = subteamPlacement * 100

                if isCurrent:
                    remake = stats['gameEndedInEarlySurrender']
                    win = stats['win']

                    if queueId == 1700:
                        cherryResult = subteamPlacement

                championId = summoner['championId']
                championIcon = connector.getChampionIcon(championId)

                spell1Id = summoner['spell1Id']
                spell1Icon = connector.getSummonerSpellIcon(spell1Id)
                spell2Id = summoner['spell2Id']
                spell2Icon = connector.getSummonerSpellIcon(spell2Id)

                kills = stats['kills']
                deaths = stats['deaths']
                assists = stats['assists']
                gold = stats['goldEarned']

                teams[tid]['kills'] += kills
                teams[tid]['deaths'] += deaths
                teams[tid]['assists'] += assists
                teams[tid]['gold'] += gold

                runeIcon = connector.getRuneIcon(stats['perk0'])

                itemIds = [
                    stats['item0'],
                    stats['item1'],
                    stats['item2'],
                    stats['item3'],
                    stats['item4'],
                    stats['item5'],
                    stats['item6'],
                ]

                itemIcons = [
                    connector.getItemIcon(itemId) for itemId in itemIds
                ]

                getRankInfo = cfg.get(cfg.showTierInGameInfo)

                tier, division, lp, rankIcon = None, None, None, None
                if getRankInfo:
                    rank = connector.getRankedStatsByPuuid(
                        summonerPuuid).get('queueMap')

                    try:
                        if queueId != 1700 and rank:
                            rankInfo = rank[
                                'RANKED_FLEX_SR'] if queueId == 440 else rank['RANKED_SOLO_5x5']

                            tier = rankInfo['tier']
                            division = rankInfo['division']
                            lp = rankInfo['leaguePoints']

                            if tier == '':
                                rankIcon = 'app/resource/images/unranked.png'
                            else:
                                rankIcon = f'app/resource/images/{tier.lower()}.png'
                                tier = translateTier(tier, True)

                            if division == 'NA':
                                division = ''
                        else:
                            rankInfo = rank["CHERRY"]
                            lp = rankInfo['ratedRating']
                    except KeyError:
                        ...

                item = {
                    'summonerName': summonerName,
                    'puuid': summonerPuuid,
                    'isCurrent': isCurrent,
                    'championIcon': championIcon,
                    'rankInfo': getRankInfo,
                    'tier': tier,
                    'division': division,
                    'lp': lp,
                    'rankIcon': rankIcon,
                    'spell1Icon': spell1Icon,
                    'spell2Icon': spell2Icon,
                    'itemIcons': itemIcons,
                    'kills': kills,
                    'deaths': deaths,
                    'assists': assists,
                    'cs': stats['totalMinionsKilled'] + stats['neutralMinionsKilled'],
                    'gold': gold,
                    'runeIcon': runeIcon,
                    'champLevel': stats['champLevel'],
                    'demage': stats['totalDamageDealtToChampions'],
                    'subteamPlacement': subteamPlacement,
                    'isPublic': isPublic
                }
                teams[tid]['summoners'].append(item)

                break

    mapIcon = connector.manager.getMapIconByMapId(mapId, win)

    return {
        'gameId': game['gameId'],
        'mapIcon': mapIcon,
        'gameCreation': timeStampToStr(game['gameCreation']),
        'gameDuration': secsToStr(game['gameDuration']),
        'modeName': modeName,
        'mapName': mapName,
        'queueId': queueId,
        'win': win,
        'cherryResult': cherryResult,
        'remake': remake,
        'teams': teams,
    }


def getTeammates(game, targetPuuid):
    """
    通过game信息获取目标召唤师的队友

    @param game: @see connector.getGameDetailByGameId
    @param targetPuuid: 目标召唤师puuid
    @return: @see res
    """
    targetParticipantId = None

    for participant in game['participantIdentities']:
        puuid = participant['player']['puuid']

        if puuid == targetPuuid:
            targetParticipantId = participant['participantId']
            break

    assert targetParticipantId is not None

    for player in game['participants']:
        if player['participantId'] == targetParticipantId:
            if game['queueId'] != 1700:
                tid = player['teamId']
            else:  # 斗魂竞技场
                tid = player['stats']['subteamPlacement']

            win = player['stats']['win']
            remake = player['stats']['teamEarlySurrendered']

            break

    res = {
        'queueId': game['queueId'],
        'win': win,
        'remake': remake,
        'summoners': [],  # 队友召唤师 (由于兼容性, 未修改字段名)
        'enemies': []  # 对面召唤师, 若有多个队伍会全放这里面
    }

    for player in game['participants']:

        if game['queueId'] != 1700:
            cmp = player['teamId']
        else:
            cmp = player['stats']['subteamPlacement']

        p = player['participantId']
        s = game['participantIdentities'][p - 1]['player']

        if cmp == tid:
            if s['puuid'] != targetPuuid:
                res['summoners'].append(
                    {'summonerId': s['summonerId'], 'name': s['summonerName'], 'puuid': s['puuid'], 'icon': s['profileIcon']})
            else:
                # 当前召唤师在该对局使用的英雄, 自定义对局没有该字段
                res["championId"] = player.get('championId', -1)
        else:
            res['enemies'].append(
                {'summonerId': s['summonerId'], 'name': s['summonerName'], 'puuid': s['puuid'],
                 'icon': s['profileIcon']})

    return res


def markTeam(summoners):
    """
    标记预组队的召唤师

    在summoners中, teamId是int型数据, 若有效, 则不小于0, 若无此信息, 则被标记为-1;

    该方法会将所有 teamId >= 0 的召唤师名称, 放入一个dict中, key是teamId, value是召唤师名称组成的list;

    如果结果中一个teamId的成员大于1个召唤师, 则判定为是预组队;

    该方法的结果会直接作用于 summoners 上, 以字段teamInfo存储.

    @param summoners:
    @return:
    """

    teamInfo = {}

    # 完整迭代一次
    for summoner in summoners:
        team_id = summoner.get("teamId", -1)
        if team_id >= 0:
            teamInfo.setdefault(team_id, []).append(summoner["name"])

    # 将队伍信息添加到对应的召唤师
    for summoner in summoners:
        tmp = teamInfo.get(summoner["teamId"])
        summoner["teamInfo"] = tmp if len(tmp) > 1 else []

    return summoners


def assignTeamId(summoners):
    """
    分配队伍ID

    存储于teamId字段, 自1递增的数字, 若无队伍则为None

    ---
    较此前完善判断逻辑:
    1. A单向B, B单向C -> ABC都记为 None
    2. A双向B, B双向C -> ABC记为同一 teamId
    3. A双向B且单向C -> AB记为同一 teamId, C记为None
    ---

    @param summoners: 召唤师信息
     [{
        "summonerId": 123456,
        "teammatesMarker": [{'summonerId': 333333, 'cnt': 3, 'name': "召唤师1"}]
    }, ... ]

    @return: 变更直接作用于入参 :summoners: 同时会return; 两者为同一实例;

    """
    raise DeprecationWarning(
        "The method has been enabled, and currently, the \"teamParticipantId\" field is being used to determine team "
        "information."
    )

    team_id = 1
    summoner_to_team = {}

    # 123456: [333333]
    # key=summonerId
    # value=teammates
    summoner_to_teammates = {
        summoner["summonerId"]: [teammate["summonerId"] for teammate in summoner["teammatesMarker"]] for summoner in
        summoners}

    for summoner_id, teammates in summoner_to_teammates.items():
        for teammate_id in teammates:
            # 检查双向队友
            if summoner_id in summoner_to_teammates[teammate_id]:
                # 检查teamId
                if summoner_id not in summoner_to_team and teammate_id not in summoner_to_team:
                    summoner_to_team[summoner_id] = team_id
                    summoner_to_team[teammate_id] = team_id
                    team_id += 1
                # summoner已有teamId, 但队友没有时, 为队友分配相同的teamId
                elif summoner_id in summoner_to_team and teammate_id not in summoner_to_team:
                    summoner_to_team[teammate_id] = summoner_to_team[summoner_id]
                # 队友已有teamId, 但summoner没有时, 为summoner分配相同的teamId
                elif teammate_id in summoner_to_team and summoner_id not in summoner_to_team:
                    summoner_to_team[summoner_id] = summoner_to_team[teammate_id]

    # 将teamId添加到原始数据中
    for summoner in summoners:
        if summoner["summonerId"] in summoner_to_team:
            summoner["teamId"] = summoner_to_team[summoner["summonerId"]]
        else:
            # 无队伍以及单向的标记为 None
            summoner["teamId"] = None

    return summoners


def getRecentChampions(games):
    champions = {}

    for game in games:
        championId = game['championId']

        if championId not in champions:
            champions[championId] = {
                'icon': game['championIcon'], 'wins': 0, 'losses': 0, 'total': 0}

        champions[championId]['total'] += 1

        if not game['remake']:
            if game['win']:
                champions[championId]['wins'] += 1
            else:
                champions[championId]['losses'] += 1

    ret = [item for item in champions.values()]
    ret.sort(key=lambda x: x['total'], reverse=True)

    maxLen = 10

    return ret if len(ret) < maxLen else ret[:maxLen]


def processRankInfo(info):
    soloRankInfo = info["queueMap"]["RANKED_SOLO_5x5"]
    flexRankInfo = info["queueMap"]["RANKED_FLEX_SR"]

    soloTier = soloRankInfo["tier"]
    soloDivision = soloRankInfo["division"]

    if soloTier == "":
        soloIcon = "app/resource/images/UNRANKED.svg"
        soloTier = "Unranked" if cfg.language.value == Language.ENGLISH else "未定级"
    else:
        soloIcon = f"app/resource/images/{soloTier}.svg"
        soloTier = translateTier(soloTier, True)
    if soloDivision == "NA":
        soloDivision = ""

    flexTier = flexRankInfo["tier"]
    flexDivision = flexRankInfo["division"]

    if flexTier == "":
        flexIcon = "app/resource/images/UNRANKED.svg"
        flexTier = "Unranked" if cfg.language.value == Language.ENGLISH else "未定级"
    else:
        flexIcon = f"app/resource/images/{flexTier}.svg"
        flexTier = translateTier(flexTier, True)
    if flexDivision == "NA":
        flexDivision = ""

    return {
        "solo": {
            "tier": soloTier,
            "icon": soloIcon,
            "division": soloDivision,
            "lp": soloRankInfo["leaguePoints"],
        },
        "flex": {
            "tier": flexTier,
            "icon": flexIcon,
            "division": flexDivision,
            "lp": flexRankInfo["leaguePoints"],
        },
    }


def parseGames(games, targetId=0):
    f"""
    解析Games数据

    @param targetId: 需要查询的游戏模式, 不传则收集所有模式的数据
    @param games: 由 @see: {processGameData} 获取到的games数据
    @return: hitGame, K, D, A, win, loss
    @rtype: tuple[list, int, int, int, int, int, int]
    """

    kills, deaths, assists, wins, losses = 0, 0, 0, 0, 0
    hitGames = []

    for game in games:
        if not targetId or game['queueId'] == targetId:
            hitGames.append(game)

            if not game['remake']:
                kills += game['kills']
                deaths += game['deaths']
                assists += game['assists']

                if game['win']:
                    wins += 1
                else:
                    losses += 1

    return hitGames, kills, deaths, assists, wins, losses


def fixLeagueClientWindow():
    """
    #### 需要管理员权限

    调用 Win API 手动调整窗口大小 / 位置
    详情请见 https://github.com/LeagueTavern/fix-lcu-window

    @return: 当且仅当需要修复且权限不足时返回 `False`
    """

    windowHWnd = win32gui.FindWindow("RCLIENT", "League of Legends")

    # 客户端只有在 DX 9 模式下这个玩意才不是 0
    windowCefHWnd = win32gui.FindWindowEx(
        windowHWnd, 0, "CefBrowserWindow", None)

    if not windowHWnd or not windowCefHWnd:
        return True

    # struct WINDOWPLACEMENT {
    #     UINT  length; (事实上并没有该字段)
    #     UINT  flags;
    #     UINT  showCmd;
    #     POINT ptMinPosition;
    #     POINT ptMaxPosition;
    #     RECT  rcNormalPosition;
    # } ;
    placement = win32gui.GetWindowPlacement(windowHWnd)

    if placement[1] == win32con.SW_SHOWMINIMIZED:
        return True

    # struct RECT {
    #     LONG left;
    #     LONG top;
    #     LONG right;
    #     LONG bottom;
    # }
    windowRect = win32gui.GetWindowRect(windowHWnd)
    windowCefRect = win32gui.GetWindowRect(windowCefHWnd)

    def needResize(rect):
        return (rect[3] - rect[1]) / (rect[2] - rect[0]) != 0.5625

    if not needResize(windowRect) and not needResize(windowCefRect):
        return True

    clientZoom = int(connector.getClientZoom())

    screenWidth = win32api.GetSystemMetrics(0)
    screenHeight = win32api.GetSystemMetrics(1)

    targetWindowWidth = 1280 * clientZoom
    targetWindowHeight = 720 * clientZoom

    def patchDpiChangedMessage(hWnd):
        dpi = ctypes.windll.user32.GetDpiForWindow(hWnd)
        wParam = win32api.MAKELONG(dpi, dpi)
        lParam = ctypes.pointer((ctypes.c_int * 4)(0, 0, 0, 0))

        WM_DPICHANGED = 0x02E0
        win32api.SendMessage(hWnd, WM_DPICHANGED, wParam, lParam)

    try:
        patchDpiChangedMessage(windowHWnd)
        patchDpiChangedMessage(windowCefHWnd)

        SWP_SHOWWINDOW = 0x0040
        win32gui.SetWindowPos(
            windowHWnd,
            0,
            (screenWidth - targetWindowWidth) // 2,
            (screenHeight - targetWindowHeight) // 2,
            targetWindowWidth, targetWindowHeight,
            SWP_SHOWWINDOW
        )

        win32gui.SetWindowPos(
            windowCefHWnd,
            0,
            0,
            0,
            targetWindowWidth,
            targetWindowHeight,
            SWP_SHOWWINDOW
        )

    except:
        # 需要管理员权限
        return False

    return True
