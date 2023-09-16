import subprocess

import logging
import asyncio
import willump
from PyQt5.QtCore import QObject, QThread, pyqtSignal


def getLolProcessPid():
    processes = subprocess.check_output(
        'tasklist /FI "imagename eq LeagueClientUx.exe" /NH', shell=True)

    if b'LeagueClientUx.exe' in processes:
        arr = processes.split()
        return int(arr[1])
    else:
        return 0


def isLolGameProcessExist():
    processes = subprocess.check_output(
        'tasklist /FI "imagename eq League of Legends.exe" /NH', shell=True)

    return b'League of Legends.exe' in processes


class LolProcessExistenceListener(QThread):
    lolClientStarted = pyqtSignal(int)
    lolClientEnded = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

    def run(self):
        isRunning = False

        while True:
            pid = getLolProcessPid()
            if pid != 0:
                if not isRunning:
                    isRunning = True
                    self.lolClientStarted.emit(pid)
            else:
                if isRunning and not isLolGameProcessExist():
                    isRunning = False
                    self.lolClientEnded.emit()

            self.msleep(2000)


class LolClientEventListener(QThread):
    currentSummonerProfileChanged = pyqtSignal(dict)
    gameStatusChanged = pyqtSignal(str)
    champSelectChanged = pyqtSignal(dict)

    def __init__(self, parent) -> None:
        super().__init__(parent)
        logging.getLogger().setLevel(level=logging.CRITICAL)

    def run(self):

        async def onCurrentSummonerProfileChanged(data):
            self.currentSummonerProfileChanged.emit(data['data'])

        async def onGameFlowPhaseChanged(data):
            self.gameStatusChanged.emit(data["data"])

        async def onChampSelectChanged(data):
            self.champSelectChanged.emit(data["data"])

        async def defaultHandler(data):
            print(data)

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

            # 订阅英雄选择消息
            wllp.subscription_filter_endpoint(
                allEventSubscription, '/lol-champ-select/v1/session', onChampSelectChanged)

            # print("[INFO] Event listener initialized.")
            while True:
                await asyncio.sleep(10)

        try:
            asyncio.run(main())
        except:
            return
