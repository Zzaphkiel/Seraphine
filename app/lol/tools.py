import time

from ..common.config import cfg, Language
from ..lol.connector import LolClientConnector


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
    timeArray = time.localtime(stamp / 1000)
    return time.strftime("%Y/%m/%d %H:%M", timeArray)


def timeStampToShortStr(stamp):
    timeArray = time.localtime(stamp / 1000)
    return time.strftime("%m/%d", timeArray)


def secsToStr(secs):
    return time.strftime("%M:%S", time.gmtime(secs))


def processGameData(game, connector: LolClientConnector):
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
    cs = stats['totalMinionsKilled']
    gold = stats['goldEarned']
    remake = stats['gameEndedInEarlySurrender']
    win = stats['win']

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
    }


def processGameDetailData(puuid, game, connector: LolClientConnector):
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
        summonerName = participant['player']['summonerName']
        summonerPuuid = participant['player']['puuid']
        isCurrent = (summonerPuuid == puuid)

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

                if getRankInfo:
                    rank = connector.getRankedStatsByPuuid(
                        summonerPuuid)['queueMap']
                    rankInfo = rank[
                        'RANKED_FLEX_SR'] if queueId == 440 else rank[
                            'RANKED_SOLO_5x5']

                    tier: str = rankInfo['tier']
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
                    tier, division, lp, rankIcon = None, None, None, None

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
                    'cs': stats['totalMinionsKilled'],
                    'gold': gold,
                    'runeIcon': runeIcon,
                    'champLevel': stats['champLevel'],
                    'demage': stats['totalDamageDealtToChampions'],
                    'subteamPlacement': subteamPlacement
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
