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
    gameStart = pyqtSignal()
    gameEnd = pyqtSignal()

    def __init__(self, parent) -> None:
        super().__init__(parent)
        logging.getLogger().setLevel(level=logging.CRITICAL)

    def run(self):

        async def onCurrentSummonerProfileChanged(data):
            self.currentSummonerProfileChanged.emit(data['data'])

        async def onChampionSelectBegin(data):
            if data['eventType'] == 'Create':
                self.championSelectBegin.emit(data['data'])

        async def onGameFlowPhaseChanged(data):
            # {'data': 'Lobby'，'eventType ': 'Update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'None', 'eventType': 'Update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'Lobby'，'eventType': 'update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'ChampSelect'，'eventType': 'update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'GameStart', 'eventType': 'Update','uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'InProgress'，'eventType': 'update', 'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'waitingForStats'，'eventType': 'Uupdate'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # {'data': 'TerminatedInError'，'eventType': 'update'，'uri': '/lol-gameflow/vi/gameflow-phase'}
            # {'data': 'None ', 'eventType': 'Update'，'uri': '/lol-gameflow/v1/gameflow-phase'}
            # print(data, '\n')

            phase = data['data']

            if phase == 'ReadyCheck':
                self.matchMade.emit()
            elif phase == 'GameStart':
                self.gameStart.emit()
            elif phase == 'EndOfGame':
                self.gameEnd.emit()

        async def main():
            wllp = await willump.start()
            allEventSubscription = await wllp.subscribe('OnJsonApiEvent')

            # 订阅改头像 / 改名字消息
            wllp.subscription_filter_endpoint(
                allEventSubscription,
                f'/lol-summoner/v1/summoners/{self.parent().currentSummoner.summonerId}',
                onCurrentSummonerProfileChanged)

            # 订阅开始英雄选择消息
            wllp.subscription_filter_endpoint(allEventSubscription,
                                              '/lol-champ-select/v1/session',
                                              onChampionSelectBegin)

            # 订阅进入游戏 / 游戏结束消息
            wllp.subscription_filter_endpoint(
                allEventSubscription, '/lol-gameflow/v1/gameflow-phase', onGameFlowPhaseChanged)

            print("hi")
            while True:
                await asyncio.sleep(10)

        try:
            asyncio.run(main())
        except:
            return
