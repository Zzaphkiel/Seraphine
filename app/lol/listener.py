import subprocess

import logging
import asyncio
import willump
from PyQt5.QtCore import QObject, QThread, pyqtSignal


def isLolProcessExists():
    processes = subprocess.check_output("tasklist")
    return b'LeagueClientUx.exe' in processes


class LolProcessExistenceListener(QThread):
    lolClientStarted = pyqtSignal()
    lolClientEnded = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

    def run(self):
        isRunning = False

        while True:
            if isLolProcessExists():
                if not isRunning:
                    isRunning = True
                    self.lolClientStarted.emit()
            else:
                if isRunning:
                    isRunning = False
                    self.lolClientEnded.emit()

            self.msleep(2000)


class LolClientEventListener(QThread):
    currentSummonerProfileChanged = pyqtSignal(dict)
    matchMade = pyqtSignal()
    championSelectBegin = pyqtSignal(dict)

    def __init__(self, parent) -> None:
        super().__init__(parent)
        logging.getLogger().setLevel(level=logging.CRITICAL)

    def run(self):

        async def onCurrentSummonerProfileChanged(data):
            self.currentSummonerProfileChanged.emit(data['data'])

        async def onMatchMade(data):
            print(data)
            if data['data']['playerResponse'] == 'None':
                print('hello1')
                self.matchMade.emit()

        async def onChampionSelectBegin(data):
            if data['eventType'] == 'Create':
                self.championSelectBegin.emit(data)

        async def main():
            wllp = await willump.start()
            allEventSubscription = await wllp.subscribe('OnJsonApiEvent')

            # 订阅改头像 / 改名字消息
            wllp.subscription_filter_endpoint(
                allEventSubscription,
                f'/lol-summoner/v1/summoners/{self.parent().currentSummoner.summonerId}',
                onCurrentSummonerProfileChanged)

            # 订阅对局已匹配消息
            wllp.subscription_filter_endpoint(
                allEventSubscription, '/lol-matchmaking/v1/ready-check',
                onMatchMade)

            wllp.subscription_filter_endpoint(allEventSubscription,
                                              '/lol-champ-select/v1/session',
                                              onChampionSelectBegin)

            while True:
                await asyncio.sleep(10)

        try:
            asyncio.run(main())
        except:
            return
