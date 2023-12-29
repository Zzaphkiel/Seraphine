class Summoner:

    def __init__(self, data: dict):
        self.summonerId = data['summonerId']
        self.name = data.get("gameName") or data['displayName']  # 兼容外服
        self.profileIconId = data['profileIconId']
        self.puuid = data['puuid']
        self.level = data['summonerLevel']
        self.xpSinceLastLevel = data['xpSinceLastLevel']
        self.xpUntilNextLevel = data['xpUntilNextLevel']
        self.isPublic = data["privacy"] == "PUBLIC"
        self.tagLine = data.get("tagLine")
        self.completeName = "#".join(
            (self.name, self.tagLine)) if self.tagLine else self.name  # 兼容外服
