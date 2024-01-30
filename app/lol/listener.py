import subprocess
import logging


import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import lcu_driver

from app.common.logger import logger

TAG = "Listener"

def getTasklistPath():
    for path in ['tasklist',
                 'C:/Windows/System32/tasklist.exe']:
        try:
            cmd = f'{path} /FI "imagename eq LeagueClientUx.exe" /NH'
            _ = subprocess.check_output(cmd, shell=True)
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
                if self.isClientRunning and not isLolGameProcessExist(self.tasklistPath):
                    self.isClientRunning = False
                    self.lolClientEnded.emit()

            self.msleep(2000)


class LolClientEventListener(QThread):
    currentSummonerProfileChanged = pyqtSignal(dict)
    gameStatusChanged = pyqtSignal(str)
    champSelectChanged = pyqtSignal(dict)
    goingSwap = pyqtSignal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        logging.getLogger().setLevel(level=logging.CRITICAL)


    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        co = lcu_driver.Connector()

        @co.ws.register('/lol-summoner/v1/current-summoner', event_types=('UPDATE',))
        async def onCurrentSummonerProfileChanged(connection, event):
            logger.info("/lol-summoner/v1/current-summoner")
            logger.debug(event.data)
            self.currentSummonerProfileChanged.emit(event.data)

        @co.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
        async def onGameFlowPhaseChanged(connection, event):
            logger.info("/lol-gameflow/v1/gameflow-phase")
            logger.debug(event.data)
            self.gameStatusChanged.emit(event.data)

        @co.ws.register('/lol-champ-select/v1/session', event_types=('UPDATE',))
        async def onChampSelectChanged(connection, event):
            logger.info("/lol-champ-select/v1/session")
            logger.debug(event.data)
            self.champSelectChanged.emit(event.data)

        @co.ws.register('/lol-champ-select/v1/ongoing-swap')
        async def onGoingSwap(connection, event):
            logger.info("/lol-champ-select/v1/ongoing-swap")
            logger.debug(event)
            self.goingSwap.emit({'data': event.data, 'eventType': event.type})
            
        co.start()


class StoppableThread(QThread):
    def __init__(self, target, parent) -> None:
        self.target = target
        super().__init__(parent)

    def run(self):
        self.target()
