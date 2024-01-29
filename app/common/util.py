import requests
import base64

from app.common.config import cfg, VERSION


class Github:
    def __init__(self, user="Zzaphkiel", repositories="Seraphine"):
        self.githubApi = "http://api.github.com"
        self.giteeApi = "http://gitee.com/api"

        self.user = user
        self.repositories = repositories
        self.sess = requests.session()

    def getReleasesInfo(self):
        url = f"{self.githubApi}/repos/{self.user}/{self.repositories}/releases/latest"

        if cfg.get(cfg.enableProxy):
            proxy = {'https': cfg.get(cfg.proxyAddr)}
        else:
            proxy = None

        return self.sess.get(url, proxies=proxy).json()

    def checkUpdate(self):
        """
        检查版本更新
        @return: 有更新 -> info, 无更新 -> None
        """
        info = self.getReleasesInfo()

        if info.get("tag_name")[1:] != VERSION:
            return info
        return None
    
    def getNotice(self):
        url = f'{self.githubApi}/repos/{self.user}/{self.repositories}/contents/document/notice.md'

        if cfg.get(cfg.enableProxy):
            proxy = {'https': cfg.get(cfg.proxyAddr)}
        else:
            proxy = None
        
        res = self.sess.get(url, proxies=proxy).json()

        content = str(base64.b64decode(res['content']), encoding='utf-8')

        return {
            'sha': res['sha'],
            'content': content,
        }
        



github = Github()
