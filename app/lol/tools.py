import itertools
import time
import ctypes
from copy import deepcopy

import asyncio
from PyQt5.QtCore import QObject

from .exceptions import SummonerRankInfoNotFound
from ..common.config import cfg, Language
from ..lol.connector import connector
from ..common.signals import signalBus


SERVERS_NAME = {
    "NJ100": "联盟一区", "GZ100": "联盟二区", "CQ100": "联盟三区", "TJ100": "联盟四区", "TJ101": "联盟五区",
    "HN10": "黑色玫瑰", "HN1": "艾欧尼亚", "BGP2": "峡谷之巅"
}

SERVERS_SUBSET = {
    "NJ100": ["祖安", "皮尔特沃夫", "巨神峰", "教育网", "男爵领域", "均衡教派", "影流", "守望之海"],
    "GZ100": ["卡拉曼达", "暗影岛", "征服之海", "诺克萨斯", "战争学院", "雷瑟守备"],
    "CQ100": ["班德尔城", "裁决之地", "水晶之痕", "钢铁烈阳", "皮城警备"],
    "TJ100": ["比尔吉沃特", "弗雷尔卓德", "扭曲丛林"],
    "TJ101": ["德玛西亚", "无畏先锋", "恕瑞玛", "巨龙之巢"]
}


class ToolsTranslator(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.top = self.tr("TOP")
        self.jungle = self.tr("JUG")
        self.middle = self.tr("MID")
        self.bottom = self.tr("BOT")
        self.support = self.tr("SUP")

        self.positionMap = {
            "TOP": self.top,
            "JUNGLE": self.jungle,
            "MID": self.middle,
            "ADC": self.bottom,
            "SUPPORT": self.support
        }

        self.rankedSolo = self.tr('Ranked Solo')
        self.rankedFlex = self.tr("Ranked Flex")

        self.unranked = self.tr("Unranked")
        self.unknown = self.tr("Unknown")


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


async def getRecentTeammates(games, puuid):
    summoners = {}

    for game in games:
        gameId = game['gameId']
        game = await connector.getGameDetailByGameId(gameId)
        teammates = getTeammates(game, puuid)

        for p in teammates['summoners']:
            if p['summonerId'] == 0:
                continue

            if p['puuid'] not in summoners:
                summonerIcon = await connector.getProfileIcon(p['icon'])
                summoners[p['puuid']] = {
                    "name": p['name'], 'icon': summonerIcon,
                    "total": 0, "wins": 0, "losses": 0, "puuid": p["puuid"]}

            summoners[p['puuid']]['total'] += 1

            if not teammates['remake']:
                if teammates['win']:
                    summoners[p['puuid']]['wins'] += 1
                else:
                    summoners[p['puuid']]['losses'] += 1

    ret = {"puuid": puuid, "summoners": [
        item for item in summoners.values()]}

    ret['summoners'] = sorted(ret['summoners'],
                              key=lambda x: x['total'], reverse=True)[:5]

    return ret


async def parseSummonerData(summoner, rankTask, gameTask):
    iconId = summoner['profileIconId']
    icon = await connector.getProfileIcon(iconId)
    level = summoner['summonerLevel']
    xpSinceLastLevel = summoner['xpSinceLastLevel']
    xpUntilNextLevel = summoner['xpUntilNextLevel']

    try:
        gamesInfo = await gameTask
    except:
        champions = []
        games = {}
    else:
        games = {
            "gameCount": gamesInfo["gameCount"],
            "wins": 0,
            "losses": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "games": [],
        }
        for game in gamesInfo["games"]:
            info = await parseGameData(game)
            if time.time() - info["timeStamp"] / 1000 > 60 * 60 * 24 * 365:
                continue
            if not info["remake"] and info["queueId"] != 0:
                games["kills"] += info["kills"]
                games["deaths"] += info["deaths"]
                games["assists"] += info["assists"]
                if info["win"]:
                    games["wins"] += 1
                else:
                    games["losses"] += 1
            games["games"].append(info)

        champions = getRecentChampions(games['games'])

    try:
        rankInfo = await rankTask
    except SummonerRankInfoNotFound:
        rankInfo = {}

    return {
        'name': summoner.get("gameName") or summoner['displayName'],
        'icon': icon,
        'level': level,
        'xpSinceLastLevel': xpSinceLastLevel,
        'xpUntilNextLevel': xpUntilNextLevel,
        'puuid': summoner['puuid'],
        'rankInfo': rankInfo,
        'games': games,
        'champions': champions,
        'isPublic': summoner['privacy'] == "PUBLIC",
        'tagLine': summoner.get("tagLine"),
    }


async def parseGameData(game):
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
    championIcon = await connector.getChampionIcon(championId)
    spell1Id = participant['spell1Id']
    spell2Id = participant['spell2Id']
    spell1Icon = await connector.getSummonerSpellIcon(spell1Id)
    spell2Icon = await connector.getSummonerSpellIcon(spell2Id)
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

    itemIcons = [await connector.getItemIcon(itemId) for itemId in itemIds]
    runeId = stats['perk0']
    runeIcon = await connector.getRuneIcon(runeId)

    cs = stats['totalMinionsKilled'] + stats['neutralMinionsKilled']
    gold = stats['goldEarned']
    remake = stats['gameEndedInEarlySurrender']
    win = stats['win']

    timeline = participant['timeline']
    lane = timeline['lane']
    role = timeline['role']

    position = None

    tt = ToolsTranslator()

    if queueId in [420, 440]:
        if lane == 'TOP':
            position = tt.top
        elif lane == "JUNGLE":
            position = tt.jungle
        elif lane == 'MIDDLE':
            position = tt.middle
        elif role == 'SUPPORT':
            position = tt.support
        elif lane == 'BOTTOM' and role == 'CARRY':
            position = tt.bottom

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


async def parseGameDetailData(puuid, game):
    queueId = game['queueId']
    mapId = game['mapId']

    names = connector.manager.getNameMapByQueueId(queueId)
    modeName = names['name']
    if queueId != 0:
        mapName = names['map']
    else:
        mapName = connector.manager.getMapNameById(mapId)

    def origTeam(teamId):
        return {
            'win': None,
            'bans': [],
            'baronKills': 0,
            'baronIcon': f"app/resource/images/baron-{teamId}.png",
            'dragonKills': 0,
            'dragonIcon': f'app/resource/images/dragon-{teamId}.png',
            'riftHeraldKills': 0,
            'riftHeraldIcon': f'app/resource/images/herald-{teamId}.png',
            'inhibitorKills': 0,
            'inhibitorIcon': f'app/resource/images/inhibitor-{teamId}.png',
            'towerKills': 0,
            'towerIcon': f'app/resource/images/tower-{teamId}.png',
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'gold': 0,
            'summoners': []
        }

    teams = {
        100: origTeam("100"),
        200: origTeam("200"),
        300: origTeam("100"),
        400: origTeam("200"),
        500: origTeam("100"),
        600: origTeam("200"),
        700: origTeam("100"),
        800: origTeam("200"),
    }

    cherryResult = None
    win = None

    for team in game['teams']:
        teamId = team['teamId']

        if teamId == 0:
            teamId = 200

        teams[teamId]['win'] = team['win']
        teams[teamId]['bans'] = [
            await connector.getChampionIcon(item['championId'])
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
            t = await connector.getSummonerByPuuid(summonerPuuid)
            isPublic = t.get("privacy") == "PUBLIC"

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
                championIcon = await connector.getChampionIcon(championId)

                spell1Id = summoner['spell1Id']
                spell1Icon = await connector.getSummonerSpellIcon(spell1Id)
                spell2Id = summoner['spell2Id']
                spell2Icon = await connector.getSummonerSpellIcon(spell2Id)

                kills = stats['kills']
                deaths = stats['deaths']
                assists = stats['assists']
                gold = stats['goldEarned']

                teams[tid]['kills'] += kills
                teams[tid]['deaths'] += deaths
                teams[tid]['assists'] += assists
                teams[tid]['gold'] += gold

                runeIcon = await connector.getRuneIcon(stats['perk0'])

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
                    await connector.getItemIcon(itemId) for itemId in itemIds
                ]

                getRankInfo = cfg.get(cfg.showTierInGameInfo)

                tier = division = lp = rankIcon = ""
                if getRankInfo:
                    try:
                        rank = await connector.getRankedStatsByPuuid(
                            summonerPuuid)
                    except SummonerRankInfoNotFound:
                        ...
                    else:
                        rank = rank['queueMap']

                        if queueId == 1700 and 'CHERRY' in rank:
                            rankInfo = rank["CHERRY"]
                            lp = rankInfo['ratedRating']
                        else:
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

    if win == None:
        return None

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
    通过 game 信息获取目标召唤师的队友

    @param game: @see connector.getGameDetailByGameId
    @param targetPuuid: 目标召唤师 puuid
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


def getRecentChampions(games):
    champions = {}

    for game in games:
        if game['queueId'] == 0:
            continue

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


def parseRankInfo(info):
    """
    解析 `connector.getRankedStatsByPuuid()` 的数据。


    api: `/lol-ranked/v1/ranked-stats/{puuid}`

    :param info: 接口返回值, 允许为空（接口异常时抛出 `SummonerRankInfoNotFound`, 需要捕获置空）

    """
    tt = ToolsTranslator()

    soloIcon = flexIcon = "app/resource/images/UNRANKED.svg"
    soloTier = flexTier = tt.unknown
    soloDivision = flexDivision = ""
    soloRankInfo = flexRankInfo = {"leaguePoints": ""}

    if info:
        soloRankInfo = info["queueMap"]["RANKED_SOLO_5x5"]
        flexRankInfo = info["queueMap"]["RANKED_FLEX_SR"]

        soloTier = soloRankInfo["tier"]
        soloDivision = soloRankInfo["division"]

        if soloTier == "":
            soloIcon = "app/resource/images/UNRANKED.svg"
            soloTier = tt.unranked
        else:
            soloIcon = f"app/resource/images/{soloTier}.svg"
            soloTier = translateTier(soloTier, True)
        if soloDivision == "NA":
            soloDivision = ""

        flexTier = flexRankInfo["tier"]
        flexDivision = flexRankInfo["division"]

        if flexTier == "":
            flexIcon = "app/resource/images/UNRANKED.svg"
            flexTier = tt.unranked
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


def parseRankInfoFromSGP(info):
    '''解析来自 `connector.getRankedStatsByPuuidViaSGP()` 的数据'''

    tt = ToolsTranslator()

    soloIcon = flexIcon = "app/resource/images/UNRANKED.svg"
    soloTier = flexTier = tt.unknown
    soloDivision = flexDivision = ""
    soloRankInfo = flexRankInfo = {"leaguePoints": ""}

    if info:
        for queue in info['queues']:
            type = queue['queueType']
            if type == 'RANKED_FLEX_SR':
                flexRankInfo = queue
            elif type == 'RANKED_SOLO_5x5':
                soloRankInfo = queue

        soloTier = soloRankInfo.get("tier", "")
        soloDivision = soloRankInfo.get("rank", "NA")

        if soloTier == "":
            soloIcon = "app/resource/images/UNRANKED.svg"
            soloTier = tt.unranked
        else:
            soloIcon = f"app/resource/images/{soloTier}.svg"
            soloTier = translateTier(soloTier, True)
        if soloDivision == "NA":
            soloDivision = ""

        flexTier = flexRankInfo.get("tier", "")
        flexDivision = flexRankInfo.get("rank", "NA")

        if flexTier == "":
            flexIcon = "app/resource/images/UNRANKED.svg"
            flexTier = tt.unranked
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


def parseDetailRankInfo(rankInfo):
    soloRankInfo = rankInfo['queueMap']['RANKED_SOLO_5x5']
    soloTier = translateTier(soloRankInfo['tier'])
    soloDivision = soloRankInfo['division']
    if soloTier == '--' or soloDivision == 'NA':
        soloDivision = ""

    soloHighestTier = translateTier(soloRankInfo['highestTier'])
    soloHighestDivision = soloRankInfo['highestDivision']
    if soloHighestTier == '--' or soloHighestDivision == 'NA':
        soloHighestDivision = ""

    solxPreviousSeasonEndTier = translateTier(
        soloRankInfo['previousSeasonEndTier'])
    soloPreviousSeasonDivision = soloRankInfo[
        'previousSeasonEndDivision']
    if solxPreviousSeasonEndTier == '--' or soloPreviousSeasonDivision == 'NA':
        soloPreviousSeasonDivision = ""

    soloWins = soloRankInfo['wins']
    soloLosses = soloRankInfo['losses']
    soloTotal = soloWins + soloLosses
    soloWinRate = soloWins * 100 // soloTotal if soloTotal != 0 else 0
    soloLp = soloRankInfo['leaguePoints']

    flexRankInfo = rankInfo['queueMap']['RANKED_FLEX_SR']
    flexTier = translateTier(flexRankInfo['tier'])
    flexDivision = flexRankInfo['division']
    if flexTier == '--' or flexDivision == 'NA':
        flexDivision = ""

    flexHighestTier = translateTier(flexRankInfo['highestTier'])
    flexHighestDivision = flexRankInfo['highestDivision']
    if flexHighestTier == '--' or flexHighestDivision == 'NA':
        flexHighestDivision = ""

    flexPreviousSeasonEndTier = translateTier(
        flexRankInfo['previousSeasonEndTier'])
    flexPreviousSeasonEndDivision = flexRankInfo[
        'previousSeasonEndDivision']

    if flexPreviousSeasonEndTier == '--' or flexPreviousSeasonEndDivision == 'NA':
        flexPreviousSeasonEndDivision = ""

    flexWins = flexRankInfo['wins']
    flexLosses = flexRankInfo['losses']
    flexTotal = flexWins + flexLosses
    flexWinRate = flexWins * 100 // flexTotal if flexTotal != 0 else 0
    flexLp = flexRankInfo['leaguePoints']

    pt = ToolsTranslator()

    return [
        [
            pt.rankedSolo,
            str(soloTotal),
            str(soloWinRate) + ' %' if soloTotal != 0 else '--',
            str(soloWins),
            str(soloLosses),
            f'{soloTier} {soloDivision}',
            str(soloLp),
            f'{soloHighestTier} {soloHighestDivision}',
            f'{solxPreviousSeasonEndTier} {soloPreviousSeasonDivision}',
        ],
        [
            pt.rankedFlex,
            str(flexTotal),
            str(flexWinRate) + ' %' if flexTotal != 0 else '--',
            str(flexWins),
            str(flexLosses),
            f'{flexTier} {flexDivision}',
            str(flexLp),
            f'{flexHighestTier} {flexHighestDivision}',
            f'{flexPreviousSeasonEndTier} {flexPreviousSeasonEndDivision}',
        ],
    ]


def parseGames(games, targetId=0):
    f"""
    解析 Games 数据

    @param targetId: 需要查询的游戏模式, 不传则收集所有模式的数据
    @param games: 由 @see: {parseGameData} 获取到的games数据
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


async def parseAllyGameInfo(session, currentSummonerId, useSGP=False):
    # 排位会有预选位
    isRank = bool(session["myTeam"][0]["assignedPosition"])

    if useSGP and connector.isInMainland():
        # 如果是国服就优先尝试 SGP
        try:
            tasks = [getSummonerGamesInfoViaSGP(item, isRank, currentSummonerId)
                     for item in session['myTeam']]
            summoners = await asyncio.gather(*tasks)
        except:
            tasks = [parseSummonerGameInfo(item, isRank, currentSummonerId)
                     for item in session['myTeam']]
            summoners = await asyncio.gather(*tasks)

    else:
        tasks = [parseSummonerGameInfo(item, isRank, currentSummonerId)
                 for item in session['myTeam']]
        summoners = await asyncio.gather(*tasks)

    summoners = [summoner for summoner in summoners if summoner]

    # 按照楼层排序
    summoners = sorted(
        summoners, key=lambda x: x["cellId"])

    champions = {summoner['summonerId']: summoner['championId']
                 for summoner in summoners}
    order = [summoner['summonerId'] for summoner in summoners]

    return {'summoners': summoners, 'champions': champions, 'order': order, "isAram": session.get('benchEnabled', False)}


def parseSummonerOrder(team):
    summoners = [{
        'summonerId': s['summonerId'],
        'cellId': s['cellId']
    } for s in team]

    summoners.sort(key=lambda x: x['cellId'])
    return [s['summonerId'] for s in summoners if s['summonerId'] != 0]


async def parseGameInfoByGameflowSession(session, currentSummonerId, side, useSGP=False):
    data = session['gameData']
    queueId = data['queue']['id']

    if queueId in (1700, 1090, 1100, 1110, 1130, 1160):  # 斗魂 云顶匹配 (排位)
        return None

    isRank = queueId in (420, 440)

    if side == 'enemy':
        _, team = separateTeams(data, currentSummonerId)
    else:
        team, _ = separateTeams(data, currentSummonerId)

    if useSGP and connector.isInMainland():
        # 如果是国服就优先尝试 SGP
        try:
            tasks = [getSummonerGamesInfoViaSGP(item, isRank, currentSummonerId)
                     for item in team]
            summoners = await asyncio.gather(*tasks)

        except:
            tasks = [parseSummonerGameInfo(item, isRank, currentSummonerId)
                     for item in team]
            summoners = await asyncio.gather(*tasks)

    else:
        tasks = [parseSummonerGameInfo(item, isRank, currentSummonerId)
                 for item in team]
        summoners = await asyncio.gather(*tasks)

    summoners = [summoner for summoner in summoners if summoner]

    if isRank:
        s = sortedSummonersByGameRole(summoners)

        if s != None:
            summoners = s

    champions = {summoner['summonerId']: summoner['championId']
                 for summoner in summoners}
    order = [summoner['summonerId'] for summoner in summoners]

    return {'summoners': summoners, 'champions': champions, 'order': order}


def sortedSummonersByGameRole(summoners: list):
    position = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

    if any(x['selectedPosition'] not in position for x in summoners):
        return None

    return sorted(summoners,
                  key=lambda x: position.index(x['selectedPosition']))


def getAllyOrderByGameRole(session, currentSummonerId):
    data = session['gameData']
    queueId = data['queue']['id']

    # 只有排位模式下有返回值
    if queueId not in (420, 440):
        return None

    ally, _ = separateTeams(data, currentSummonerId)
    ally = sortedSummonersByGameRole(ally)

    if ally == None:
        return None

    return [x['summonerId'] for x in ally]


def getTeamColor(session, currentSummonerId):
    '''
    输入 session 以及当前召唤师 id，输出 summonerId -> 颜色的映射
    '''
    data = session['gameData']
    ally, enemy = separateTeams(data, currentSummonerId)

    def makeTeam(team):
        # teamParticipantId => [summonerId]
        tIdToSIds = {}

        for s in team:
            summonerId = s.get('summonerId')
            if not summonerId:
                continue

            teamParticipantId = s.get('teamParticipantId')
            if not teamParticipantId:
                continue

            summoners = tIdToSIds.get(teamParticipantId)

            if not summoners:
                tIdToSIds[teamParticipantId] = [summonerId]
            else:
                tIdToSIds[teamParticipantId].append(summonerId)

        # summonerId => color
        res = {}

        currentColor = 0

        for ids in tIdToSIds.values():
            if len(ids) == 1:
                res[ids[0]] = -1
            else:
                for id in ids:
                    res[id] = currentColor

                currentColor += 1

        return res

    return makeTeam(ally), makeTeam(enemy)


def separateTeams(data, currentSummonerId):
    team1 = data['teamOne']
    team2 = data['teamTwo']
    ally = None
    enemy = None

    for summoner in team1:
        if summoner.get('summonerId') == currentSummonerId:
            ally = team1
            enemy = team2
            break
    else:
        ally = team2
        enemy = team1

    return ally, enemy


async def parseGamesDataConcurrently(games):
    tasks = [parseGameData(game) for game in games]
    return await asyncio.gather(*tasks)


async def parseSummonerGameInfo(item, isRank, currentSummonerId):
    summonerId = item.get('summonerId', None)

    if item.get('nameVisibilityType') == 'HIDDEN':
        return None

    if summonerId == 0 or summonerId == None:
        return None

    summoner = await connector.getSummonerById(summonerId)

    championId = item.get('championId') or 0
    icon = await connector.getChampionIcon(championId)

    puuid = summoner.get("puuid", None)

    if puuid == "00000000-0000-0000-0000-000000000000" or not puuid:
        return None

    try:
        origRankInfo = await connector.getRankedStatsByPuuid(puuid)
    except SummonerRankInfoNotFound:
        origRankInfo = None

    rankInfo = parseRankInfo(origRankInfo)

    try:
        origGamesInfo = await connector.getSummonerGamesByPuuid(
            puuid, 0, 14)

        if cfg.get(cfg.gameInfoFilter) and isRank:
            origGamesInfo["games"] = [
                game for game in origGamesInfo["games"] if game["queueId"] in (420, 440)]

            begIdx = 15
            while len(origGamesInfo["games"]) < 11 and begIdx <= 95:
                endIdx = begIdx + 5
                new = (await connector.getSummonerGamesByPuuid(puuid, begIdx, endIdx))["games"]

                for game in new:
                    if game["queueId"] in (420, 440):
                        origGamesInfo['games'].append(game)

                begIdx = endIdx + 1
    except:
        gamesInfo = []
    else:
        tasks = [parseGameData(game)
                 for game in origGamesInfo["games"][:11]]
        gamesInfo = await asyncio.gather(*tasks)

    _, kill, deaths, assists, _, _ = parseGames(gamesInfo)

    teammatesInfo = [
        getTeammates(
            await connector.getGameDetailByGameId(game["gameId"]),
            puuid
        ) for game in gamesInfo[:1]  # 避免空报错, 查上一局的队友(对手)
    ]

    recentlyChampionName = ""
    fateFlag = None

    if teammatesInfo:  # 判个空, 避免太久没有打游戏的玩家或新号引发异常
        if currentSummonerId in [t['summonerId'] for t in teammatesInfo[0]['summoners']]:
            # 上把队友
            fateFlag = "ally"
        elif currentSummonerId in [t['summonerId'] for t in teammatesInfo[0]['enemies']]:
            # 上把对面
            fateFlag = "enemy"
        recentlyChampionId = max(
            teammatesInfo and teammatesInfo[0]['championId'], 0)  # 取不到时是-1, 如果-1置为0
        recentlyChampionName = connector.manager.champs.get(
            recentlyChampionId)

    return {
        "name": summoner.get("gameName") or summoner.get("internalName"),
        'tagLine': summoner.get("tagLine"),
        "icon": icon,
        'championId': championId,
        "level": summoner["summonerLevel"],
        "rankInfo": rankInfo,
        "gamesInfo": gamesInfo,
        "xpSinceLastLevel": summoner["xpSinceLastLevel"],
        "xpUntilNextLevel": summoner["xpUntilNextLevel"],
        "puuid": puuid,
        "summonerId": summonerId,
        "kda": [kill, deaths, assists],
        "cellId": item.get("cellId"),
        "selectedPosition": item.get("selectedPosition"),
        "fateFlag": fateFlag,
        "isPublic": summoner["privacy"] == "PUBLIC",
        # 最近游戏的英雄 (用于上一局与与同一召唤师游玩之后显示)
        "recentlyChampionName": recentlyChampionName
    }


async def getSummonerGamesInfoViaSGP(item, isRank, currentSummonerId):
    '''
    使用 SGP 接口取战绩信息
    '''
    puuid = item.get('puuid')

    if item.get('nameVisibilityType') == 'HIDDEN':
        return None

    if puuid == "00000000-0000-0000-0000-000000000000" or not puuid:
        return None

    championId = item.get('championId') or 0
    icon = await connector.getChampionIcon(championId)
    summoner = await connector.getSummonerByPuuidViaSGP(puuid)

    try:
        origRankInfo = await connector.getRankedStatsByPuuidViaSGP(puuid)
    except SummonerRankInfoNotFound:
        origRankInfo = None

    rankInfo = parseRankInfoFromSGP(origRankInfo)

    try:
        origGamesInfo = await connector.getSummonerGamesByPuuidViaSGP(puuid, 0, 14)

        if cfg.get(cfg.gameInfoFilter) and isRank:
            origGamesInfo["games"] = [
                game for game in origGamesInfo["games"] if game['json']["queueId"] in (420, 440)]

            begIdx = 15
            while len(origGamesInfo["games"]) < 11 and begIdx <= 95:
                endIdx = begIdx + 10
                new = (await connector.getSummonerGamesByPuuidViaSGP(puuid, begIdx, endIdx))["games"]

                for game in new:
                    if game['json']["queueId"] in (420, 440):
                        origGamesInfo['games'].append(game)

                begIdx = endIdx + 1
    except:
        gamesInfo = []
    else:
        summonerName, tagLine = getNameTagLineFromGame(
            origGamesInfo['games'][0], puuid)

        tasks = [parseGamesDataFromSGP(game, puuid)
                 for game in origGamesInfo["games"][:11]]
        gamesInfo = await asyncio.gather(*tasks)

    _, kill, deaths, assists, _, _ = parseGames(gamesInfo)

    teammatesInfo = [
        getTeammatesFromSGPGame(
            game,
            puuid
        ) for game in origGamesInfo['games'][:1]  # 避免空报错, 查上一局的队友(对手)
    ]

    recentlyChampionName = ""
    fateFlag = None

    if teammatesInfo:  # 判个空, 避免太久没有打游戏的玩家或新号引发异常
        if currentSummonerId in [t['summonerId'] for t in teammatesInfo[0]['summoners']]:
            # 上把队友
            fateFlag = "ally"
        elif currentSummonerId in [t['summonerId'] for t in teammatesInfo[0]['enemies']]:
            # 上把对面
            fateFlag = "enemy"
        recentlyChampionId = max(
            teammatesInfo and teammatesInfo[0]['championId'], 0)  # 取不到时是-1, 如果-1置为0
        recentlyChampionName = connector.manager.champs.get(
            recentlyChampionId)

    # 适用于 LCU API 返回值
    # return {
    #     "name": summoner.get("gameName"),
    #     'tagLine': summoner.get('tagLine'),
    #     "icon": icon,
    #     'championId': championId,
    #     "level": summoner["summonerLevel"],
    #     "rankInfo": rankInfo,
    #     "gamesInfo": gamesInfo,
    #     "xpSinceLastLevel": summoner["xpSinceLastLevel"],
    #     "xpUntilNextLevel": summoner["xpUntilNextLevel"],
    #     "puuid": puuid,
    #     "summonerId": summoner['summonerId'],
    #     "kda": [kill, deaths, assists],
    #     "cellId": item.get("cellId"),
    #     "selectedPosition": item.get("selectedPosition"),
    #     "fateFlag": fateFlag,
    #     "isPublic": summoner["privacy"] == "PUBLIC",
    #     # 最近游戏的英雄 (用于上一局与与同一召唤师游玩之后显示)
    #     "recentlyChampionName": recentlyChampionName
    # }

    # 适用于 SGP API 返回值
    return {
        "name": summonerName,
        'tagLine': tagLine,
        "icon": icon,
        'championId': championId,
        "level": summoner["level"],
        "rankInfo": rankInfo,
        "gamesInfo": gamesInfo,
        "xpSinceLastLevel": summoner["expPoints"],
        "xpUntilNextLevel": summoner["expToNextLevel"],
        "puuid": puuid,
        "summonerId": summoner['id'],
        "kda": [kill, deaths, assists],
        "cellId": item.get("cellId"),
        "selectedPosition": item.get("selectedPosition"),
        "fateFlag": fateFlag,
        "isPublic": summoner["privacy"] == "PUBLIC",
        # 最近游戏的英雄 (用于上一局与与同一召唤师游玩之后显示)
        "recentlyChampionName": recentlyChampionName
    }


def getTeammatesFromSGPGame(game, puuid):
    json = game['json']
    queueId = json['queueId']

    for player in json['participants']:
        if player['puuid'] == puuid:
            if queueId != 1700:
                tid = player['teamId']
            else:  # 斗魂竞技场
                tid = player['subteamPlacement']

            win = player['win']
            remake = player['teamEarlySurrendered']

            break

    res = {
        'queueId': queueId,
        'win': win,
        'remake': remake,
        'summoners': [],  # 队友召唤师 (由于兼容性, 未修改字段名)
        'enemies': []  # 对面召唤师, 若有多个队伍会全放这里面
    }

    for player in json['participants']:
        if queueId != 1700:
            cmp = player['teamId']
        else:
            cmp = player['subteamPlacement']

        if cmp == tid:
            if player['puuid'] != puuid:
                res['summoners'].append({
                    'summonerId': player['summonerId'],
                    'name': player['summonerName'],
                    'puuid': player['puuid'],
                    'icon': player['profileIcon']
                })
            else:
                # 当前召唤师在该对局使用的英雄, 自定义对局没有该字段
                res["championId"] = player.get('championId', -1)
        else:
            res['enemies'].append({
                'summonerId': player['summonerId'],
                'name': player['summonerName'],
                'puuid': player['puuid'],
                'icon': player['profileIcon']
            })

    return res


async def parseGamesDataFromSGP(game, puuid):
    """
    解析由 SGP 接口得到的具体到某一局的对局记录信息
    """

    game = game['json']

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

    participant = None
    for p in game['participants']:
        if p['puuid'] == puuid:
            participant = p

    championId = participant['championId']
    championIcon = await connector.getChampionIcon(championId)
    spell1Id = participant['spell1Id']
    spell2Id = participant['spell2Id']
    spell1Icon = await connector.getSummonerSpellIcon(spell1Id)
    spell2Icon = await connector.getSummonerSpellIcon(spell2Id)

    champLevel = participant['champLevel']
    kills = participant['kills']
    deaths = participant['deaths']
    assists = participant['assists']

    itemIds = [
        participant['item0'],
        participant['item1'],
        participant['item2'],
        participant['item3'],
        participant['item4'],
        participant['item5'],
        participant['item6'],
    ]

    itemIcons = [await connector.getItemIcon(itemId) for itemId in itemIds]
    runeId = participant['perks']['styles'][0]['selections'][0]['perk']
    runeIcon = await connector.getRuneIcon(runeId)

    cs = participant['totalMinionsKilled'] + \
        participant['neutralMinionsKilled']
    gold = participant['goldEarned']
    remake = participant['gameEndedInEarlySurrender']
    win = participant['win']

    lane = participant['lane']
    role = participant['role']

    position = None
    tt = ToolsTranslator()

    if queueId in [420, 440]:
        if lane == 'TOP':
            position = tt.top
        elif lane == "JUNGLE":
            position = tt.jungle
        elif lane == 'MIDDLE':
            position = tt.middle
        elif role == 'SUPPORT':
            position = tt.support
        elif lane == 'BOTTOM' and role == 'CARRY':
            position = tt.bottom

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


def getNameTagLineFromGame(game, puuid):
    for player in game['json']['participants']:
        if player['puuid'] == puuid:
            return player['riotIdGameName'], player['riotIdTagline']

    return None


class ChampionSelection:
    def __init__(self):
        self.isChampionBanned = False
        self.isChampionPicked = False
        self.isChampionPickedCompleted = False
        self.isSkinPicked = False
        self.opggShowChampionId = None

    def reset(self):
        self.__init__()


async def autoSwap(data, selection: ChampionSelection):
    """
    选用顺序交换请求发生时，自动接受
    """

    if not cfg.get(cfg.autoAcceptCeilSwap):
        return

    for pickOrderSwap in data['pickOrderSwaps']:
        if 'RECEIVED' == pickOrderSwap['state']:
            await connector.acceptTrade(pickOrderSwap['id'])
            selection.isChampionPickedCompleted = False
            return True


async def autoTrade(data, selection):
    """
    英雄交换请求发生时，自动接受
    """
    if not cfg.get(cfg.autoAcceptChampTrade):
        return False

    for trade in data['trades']:
        if 'RECEIVED' == trade['state']:
            await connector.acceptTrade(trade['id'])
            return True

    return False


async def showOpggBuild(data, selection: ChampionSelection):
    cellId = data['localPlayerCellId']

    # 只有在英雄已经选定后才会尝试刷新 OPGG 界面
    for actionGroup in data['actions']:
        for action in actionGroup:
            if action['actorCellId'] == cellId and \
                    (not action['completed'] or action['type'] != 'pick'):
                return False

    # 拿一下位置和英雄 ID
    for player in data['myTeam']:
        if player['cellId'] == cellId:
            position = player.get('assignedPosition')
            championId = player['championId'] or player['championPickIntent']
            break

    # 大乱斗模式下，即使锁定了也可能会换英雄，这里判断一下
    if championId == selection.opggShowChampionId:
        return False

    map = {
        'TOP': "TOP",
        'JUNGLE': "JUNGLE",
        'MIDDLE': "MID",
        'BOTTOM': "ADC",
        'UTILITY': "SUPPORT",
    }

    position = map.get(position, "")

    if championId == 0:
        return False

    # 判断一下是不是大乱斗
    if data.get('benchEnabled'):
        mode = "aram"
    # 不知道怎么判断斗魂竞技场，用这种方式判断一下吧
    elif len(data['myTeam']) == 2:
        mode = 'arena'
    else:
        mode = ""

    selection.opggShowChampionId = championId
    signalBus.toOpggBuildInterface.emit(championId, mode, position)

    return True


async def autoPick(data, selection: ChampionSelection):
    """
    自动选用英雄
    """
    if not cfg.get(cfg.enableAutoSelectChampion) or selection.isChampionPicked:
        return

    localPlayerCellId = data['localPlayerCellId']

    for player in data['myTeam']:
        if player["cellId"] != localPlayerCellId:
            continue

        if bool(player['championId']):
            return

        if bool(player['championPickIntent']):
            return

        break

    bans = itertools.chain(data["bans"]['myTeamBans'],
                           data["bans"]['theirTeamBans'])

    pos = next(filter(lambda x: x['cellId'] ==
               localPlayerCellId, data['myTeam']), None)
    pos = pos.get('assignedPosition')

    if pos == 'top':
        candidates = deepcopy(cfg.get(cfg.autoSelectChampionTop))
    elif pos == 'jungle':
        candidates = deepcopy(cfg.get(cfg.autoSelectChampionJug))
    elif pos == 'middle':
        candidates = deepcopy(cfg.get(cfg.autoSelectChampionMid))
    elif pos == 'bottom':
        candidates = deepcopy(cfg.get(cfg.autoSelectChampionBot))
    elif pos == 'utility':
        candidates = deepcopy(cfg.get(cfg.autoSelectChampionSup))
    else:
        candidates = []

    candidates.extend(cfg.get(cfg.autoSelectChampion))

    candidates = [x for x in candidates if x not in bans]

    if not candidates:
        selection.isChampionPicked = True
        return

    championId = candidates[0]

    for actionGroup in reversed(data['actions']):
        for action in actionGroup:
            if (action["actorCellId"] == localPlayerCellId
                    and action['type'] == "pick"):

                await connector.selectChampion(action['id'], championId)

                selection.isChampionPicked = True
                return True


async def autoComplete(data, selection: ChampionSelection):
    """
    超时自动选定（当前选中英雄）
    """
    isAutoCompleted = cfg.get(cfg.enableAutoSelectTimeoutCompleted)
    if not isAutoCompleted or selection.isChampionPickedCompleted:
        return

    localPlayerCellId = data['localPlayerCellId']
    for actionGroup in reversed(data['actions']):
        for action in actionGroup:
            if (action['actorCellId'] == localPlayerCellId
                    and action['type'] == "pick"
                    and action['isInProgress']
                    and not action['completed']):
                selection.isChampionPickedCompleted = True
                await asyncio.sleep(int(data['timer']['adjustedTimeLeftInPhase'] / 1000) - 1)

                if selection.isChampionPickedCompleted:
                    await connector.selectChampion(action['id'], action['championId'], True)

                return True


async def autoBan(data, selection: ChampionSelection):
    """
    自动禁用英雄
    """
    isAutoBan = cfg.get(cfg.enableAutoBanChampion)
    if not isAutoBan or selection.isChampionBanned:
        return

    selection.isChampionBanned = True

    localPlayerCellId = data['localPlayerCellId']
    for actionGroup in data['actions']:
        for action in actionGroup:
            if (action["actorCellId"] == localPlayerCellId
                    and action['type'] == 'ban'
                    and action["isInProgress"]):

                pos = next(
                    filter(lambda x: x['cellId'] == localPlayerCellId, data['myTeam']), None)
                pos = pos.get('assignedPosition')

                if pos == 'top':
                    candidates = deepcopy(cfg.get(cfg.autoBanChampionTop))
                elif pos == 'jungle':
                    candidates = deepcopy(cfg.get(cfg.autoBanChampionJug))
                elif pos == 'middle':
                    candidates = deepcopy(cfg.get(cfg.autoBanChampionMid))
                elif pos == 'bottom':
                    candidates = deepcopy(cfg.get(cfg.autoBanChampionBot))
                elif pos == 'utility':
                    candidates = deepcopy(cfg.get(cfg.autoBanChampionSup))
                else:
                    candidates = []

                candidates.extend(cfg.get(cfg.autoBanChampion))

                # 给队友一点预选的时间
                await asyncio.sleep(cfg.get(cfg.autoBanDelay))

                isFriendly = cfg.get(cfg.pretentBan)
                if isFriendly:
                    myTeam = (await connector.getChampSelectSession()).get("myTeam")
                    if not myTeam:
                        return
                    intents = [player["championPickIntent"]
                               for player in myTeam]
                    candidates = [x for x in candidates if x not in intents]

                if not candidates:
                    return

                championId = candidates[0]
                await connector.banChampion(action['id'], championId, True)

                return True


async def rollAndSwapBack():
    """
    摇骰子并切换回之前的英雄
    todo: 界面
    """
    championId = await connector.getCurrentChampion()

    await connector.reroll()
    await connector.benchSwap(championId)


async def fixLCUWindowViaExe():
    zoom = await connector.getClientZoom()

    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", "app\\resource\\bin\\fix_lcu_window.exe", f"{zoom}", None, 0)
