import subprocess

import logging
import asyncio
import willump
from PyQt5.QtCore import QObject, QThread, pyqtSignal


def isLolProcessExists():
    processes = subprocess.check_output("tasklist", shell=True)
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
    gameStatusChanged = pyqtSignal(str)

    def __init__(self, parent) -> None:
        super().__init__(parent)
        logging.getLogger().setLevel(level=logging.CRITICAL)

    def run(self):

        async def onCurrentSummonerProfileChanged(data):
            self.currentSummonerProfileChanged.emit(data['data'])

        async def onGameFlowPhaseChanged(data):
            # {'data': 'None', 'eventType': 'Update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'Lobby'，'eventType': 'update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'ChampSelect'，'eventType': 'update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'GameStart', 'eventType': 'Update','uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'InProgress'，'eventType': 'update', 'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'waitingForStats'，'eventType': 'Uupdate'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'TerminatedInError'，'eventType': 'update'，'uri': '/lol-gameflow/vi/gameflow-phase'}
            # {'data': 'None ', 'eventType': 'Update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            self.gameStatusChanged.emit(data["data"])

        async def main():
            wllp = await willump.start()
            allEventSubscription = await wllp.subscribe('OnJsonApiEvent')

            res = await wllp.request("get", "/lol-summoner/v1/current-summoner")
            res = await res.json()

            # 订阅改头像 / 改名字消息
            wllp.subscription_filter_endpoint(
                allEventSubscription,
                f'/lol-summoner/v1/summoners/{res["summonerId"]}',
                onCurrentSummonerProfileChanged)

            # 订阅游戏状态改变消息
            wllp.subscription_filter_endpoint(
                allEventSubscription, '/lol-gameflow/v1/gameflow-phase', onGameFlowPhaseChanged)

            # print("[INFO] Event listener initialized.")
            while True:
                await asyncio.sleep(10)

        try:
            asyncio.run(main())
        except:
            return
