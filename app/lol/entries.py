class Summoner:

    def __init__(self, data: dict):
        self.summonerId = data['summonerId']
        self.name = data['displayName']
        self.profileIconId = data['profileIconId']
        self.puuid = data['puuid']
        self.level = data['summonerLevel']
        self.xpSinceLastLevel = data['xpSinceLastLevel']
        self.xpUntilNextLevel = data['xpUntilNextLevel']
        self.isPublic = data["privacy"] == "PUBLIC"
