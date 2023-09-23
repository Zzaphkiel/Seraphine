import requests

from app.common.config import cfg, VERSION


class Github:
    def __init__(self, user="Zzaphkiel", repositories="Seraphine"):
        self.API = "http://api.github.com"

        self.user = user
        self.repositories = repositories
        self.sess = requests.session()

    def getReleasesInfo(self):
        url = f"{self.API}/repos/{self.user}/{self.repositories}/releases/latest"
        return self.sess.get(url, verify=False).json()

    def checkUpdate(self):
        """
        检查版本更新
        @return: 有更新 -> info, 无更新 -> None
        """
        info = self.getReleasesInfo()
        if info.get("tag_name")[1:] != VERSION:
            return info
        return None


github = Github()
