import subprocess

import logging
import asyncio
import willump
from PyQt5.QtCore import QThread, pyqtSignal


def getTasklistPath():
    for path in ['tasklist',
                 'C:/Windows/System32/tasklist.exe',
                 'app/bin/tasklist.exe']:
        try:
            _ = subprocess.check_output(path, shell=True)
            return path
        except:
            pass

    return None


def getLolProcessPid(path):

    processes = subprocess.check_output(
        f'{path} /FI "imagename eq LeagueClientUx.exe" /NH', shell=True)

    if b'LeagueClientUx.exe' in processes:
        arr = processes.split()
        try:
            pos = arr.index(b"LeagueClientUx.exe")
            return int(arr[pos+1])
        except ValueError:
            raise ValueError(f"Subprocess return exception: {processes}")
    else:
        return 0


def isLolGameProcessExist(path):
    processes = subprocess.check_output(
        f'{path} /FI "imagename eq League of Legends.exe" /NH', shell=True)

    return b'League of Legends.exe' in processes


class LolProcessExistenceListener(QThread):
    lolClientStarted = pyqtSignal(int)
    lolClientEnded = pyqtSignal()

    def __init__(self, tasklistPath, parent):
        self.tasklistPath = tasklistPath
        self.isClientRunning = False

        super().__init__(parent)

    def run(self):
        while True:
            pid = getLolProcessPid(self.tasklistPath)
            if pid != 0:
                if not self.isClientRunning:
                    self.isClientRunning = True
                    self.lolClientStarted.emit(pid)
            else:
                if self.isClientRunning and not isLolGameProcessExist():
                    self.isClientRunning = False
                    self.lolClientEnded.emit()

            self.msleep(2000)


class LolClientEventListener(QThread):
    currentSummonerProfileChanged = pyqtSignal(dict)
    gameStatusChanged = pyqtSignal(str)
    champSelectChanged = pyqtSignal(dict)
    goingSwap = pyqtSignal(dict)

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

        async def onGoingSwap(info):
            self.goingSwap.emit(info)

        async def defaultHandler(data):
            print(data)
            # uri = data.get("uri")
            # if uri:
            #     print(uri)

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

            # 订阅选择英雄阶段的交换位置消息
            wllp.subscription_filter_endpoint(
                allEventSubscription, '/lol-champ-select/v1/ongoing-swap', onGoingSwap)

            # print("[INFO] Event listener initialized.")
            while True:
                await asyncio.sleep(10)

        try:
            asyncio.run(main())
        except:
            return


class StoppableThread(QThread):
    def __init__(self, target, parent) -> None:
        self.target = target
        super().__init__(parent)

    def run(self):
        self.target()
