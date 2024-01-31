import subprocess
import logging
import json

import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import aiohttp

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

    def start(self, port, token):
        self.ws = WSListener(port, token)
        super().start()

    def run(self):
        @self.ws.subscribe(event='OnJsonApiEvent_lol-summoner_v1_current-summoner', 
                           uri='/lol-summoner/v1/current-summoner')
        async def onCurrentSummonerProfileChanged(event):
            self.currentSummonerProfileChanged.emit(event['data'])

        @self.ws.subscribe(event='OnJsonApiEvent_lol-gameflow_v1_gameflow-phase',
                           uri='/lol-gameflow/v1/gameflow-phase')
        async def onGameFlowPhaseChanged(event):
            self.gameStatusChanged.emit(event['data'])

        @self.ws.subscribe(event='OnJsonApiEvent_lol-champ-select_v1_session',
                           uri='/lol-champ-select/v1/session')
        async def onChampSelectChanged(event):
            self.champSelectChanged.emit(event['data'])

        @self.ws.subscribe(event="OnJsonApiEvent_lol-champ-select_v1_ongoing-swap",
                           uri='/lol-champ-select/v1/ongoing-swap')
        async def onGoingSwap(event):
            self.goingSwap.emit(event)
            
        self.ws.start()

class WSListener():
    def __init__(self, port=None, token=None):
        self.port = port
        self.token = token

        self.events = []
        self.subscribes = []

    async def run_ws(self):
        local_session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth('riot', self.token),
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json'
            }
        )
        ws_address = f'https://127.0.0.1:{self.port}'
        ws = await local_session.ws_connect(ws_address, ssl=False)

        for event in self.events:
            await ws.send_json([5, event])

        while True:
            msg = await ws.receive()

            if msg.type == aiohttp.WSMsgType.TEXT and msg.data != '':
                data = json.loads(msg.data)[2]
                self.match_uri(data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                logger.info("WebSocket closed", TAG)
                break

        await ws.close()
        await local_session.close()

    def match_uri(self, data):
        for s in self.subscribes:
            if data.get('uri') == s['uri']:
                logger.info(s['uri'], TAG)
                logger.debug(data, TAG)
                asyncio.create_task(s['callable'](data))
                return

    def start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_ws())

    def subscribe(self, event: str, uri: str):
        def subscribe_wrapper(func):
            self.events.append(event)
            self.subscribes.append({
                'uri': uri,
                'callable': func
            })
            return func
        return subscribe_wrapper

class StoppableThread(QThread):
    def __init__(self, target, parent) -> None:
        self.target = target
        super().__init__(parent)

    def run(self):
        self.target()
