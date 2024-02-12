import subprocess
import logging
import json

import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import aiohttp

from app.common.logger import logger
from app.common.signals import signalBus
from app.common.util import getLolProcessPid, isLolGameProcessExist

TAG = "Listener"


class LolProcessExistenceListener(QThread):
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
                    signalBus.lolClientStarted.emit(pid)
            else:
                if self.isClientRunning and not isLolGameProcessExist(self.tasklistPath):
                    self.isClientRunning = False
                    signalBus.lolClientEnded.emit()

            self.msleep(2000)


class StoppableThread(QThread):
    def __init__(self, target, parent) -> None:
        self.target = target
        super().__init__(parent)

    def run(self):
        self.target()
