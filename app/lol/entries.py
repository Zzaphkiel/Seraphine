# class Summoner():

#     def __init__(self, summonerId, name, profileIconId, puuid, level,
#                  xpSinceLastLevel, xpUntilNextLevel):
#         self.summonerId = summonerId
#         self.name = name
#         self.profileIconId = profileIconId
#         self.puuid = puuid
#         self.level = level
#         self.xpSinceLastLevel = xpSinceLastLevel
#         self.xpUntilNextLevel = xpUntilNextLevel


class Summoner():

    def __init__(self, data: dict):
        self.summonerId = data['summonerId']
        self.name = data['displayName']
        self.profileIconId = data['profileIconId']
        self.puuid = data['puuid']
        self.level = data['summonerLevel']
        self.xpSinceLastLevel = data['xpSinceLastLevel']
        self.xpUntilNextLevel = data['xpUntilNextLevel']
