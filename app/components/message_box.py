from qasync import asyncSlot
import aiohttp
import os
import zipfile
import shutil
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QTextBrowser, QPushButton
from ..common.qfluentwidgets import (MessageBox, MessageBoxBase, SmoothScrollArea,
                                     SubtitleLabel, BodyLabel, TextEdit, TitleLabel,
                                     CheckBox, setCustomStyleSheet, ProgressBar,
                                     PrimaryPushButton, ComboBox)

from app.common.config import VERSION, cfg, LOCAL_PATH
from app.common.util import (github, getLolClientPidSlowly, getPortTokenServerByPid,
                             getTasklistPath, getLolClientPids, getLolClientPidsSlowly)
from app.common.signals import signalBus
from app.common.update import runUpdater
from app.lol.connector import connector


class UpdateMessageBox(MessageBoxBase):
    def __init__(self, info, parent=None):
        super().__init__(parent=parent)
        self.info = info

        self.myYesButton = PrimaryPushButton(self.tr('OK'), self.buttonGroup)
        self.myCancelButton = QPushButton(self.tr('Cancel'), self.buttonGroup)

        self.titleLabel = TitleLabel()
        self.content = BodyLabel()

        self.textEdit = TextEdit()
        self.infoLabel = BodyLabel()
        self.bar = ProgressBar()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.yesButton.setVisible(False)
        self.cancelButton.setVisible(False)

        self.myCancelButton.setObjectName("cancelButton")
        self.buttonLayout.addWidget(self.myYesButton)
        self.buttonLayout.addWidget(self.myCancelButton)

        self.titleLabel.setText(self.tr('Update detected'))
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        self.content.setText(self.tr("current: v") + VERSION + self.tr(", ")
                             + self.tr("new: v") + self.info.get("tag_name")[1:])
        self.content.setContentsMargins(8, 0, 5, 0)

        self.textEdit.setFixedWidth(int(self.width() * .6))
        self.textEdit.setFixedHeight(int(self.height() * .4))
        self.textEdit.setMarkdown(self.info.get("body"))
        self.textEdit.setReadOnly(True)

        self.infoLabel.setVisible(False)
        self.bar.setVisible(False)

        self.myYesButton.setText(self.tr("Update and Restart"))
        self.myCancelButton.setText(self.tr("Ok"))

        self.myYesButton.clicked.connect(self.__onYesButtonClicked)
        self.myCancelButton.clicked.connect(self.__onCancelButtonClicked)

        # 简单判断下打开方式
        if not os.path.exists("Seraphine.exe"):
            self.infoLabel.setVisible(True)
            self.infoLabel.setText(
                self.tr("Updating is only available on releases version"))

            self.myYesButton.setEnabled(False)

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content)
        self.viewLayout.addWidget(self.textEdit)
        self.viewLayout.addWidget(self.infoLabel, alignment=Qt.AlignRight)
        self.viewLayout.addWidget(self.bar)

    @asyncSlot()
    async def __onYesButtonClicked(self):
        url = f"{github.proxyApi}/{self.info['assets'][0]['browser_download_url']}"
        self.myYesButton.setEnabled(False)
        self.myCancelButton.setEnabled(False)

        self.infoLabel.setVisible(True)
        self.bar.setVisible(True)

        zipPath = f'{LOCAL_PATH}/Seraphine.zip'
        if os.path.exists(zipPath):
            os.remove(zipPath)

        dirPath = f'{LOCAL_PATH}/temp'
        if os.path.exists(dirPath):
            shutil.rmtree(dirPath, ignore_errors=True)

        async with aiohttp.ClientSession() as sess:
            resp = await sess.get(url)
            length = int(resp.headers['content-length'])
            self.bar.setMaximum(length)
            cur = 0

            with open(zipPath, 'wb') as f:
                async for chunk in resp.content.iter_chunked(1024*1024):
                    f.write(chunk)

                    cur += len(chunk)
                    self.bar.setValue(cur)
                    self.infoLabel.setText(
                        f"{cur / (1024*1024):.2f} MB / {length / (1024*1024):.2f} MB ({cur * 100 / length:.2f}%)")

        self.infoLabel.setText(
            self.tr("Downloading finished, decompressing..."))

        with zipfile.ZipFile(zipPath, 'r') as z:
            z.extractall(dirPath)

        os.remove(zipPath)
        self.infoLabel.setText("Waiting for restart...")

        # 覆盖自己
        runUpdater()

        # 关掉 QThread 之后退出
        signalBus.terminateListeners.emit()
        sys.exit()

    def __onCancelButtonClicked(self):
        self.reject()
        self.rejected.emit()


class NoticeMessageBox(MessageBoxBase):
    def __init__(self, msg, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(self.tr('Notice'), self)
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        textEdit = TextEdit(self)
        textEdit.setFixedWidth(int(self.width() * .6))
        textEdit.setMarkdown(msg)
        textEdit.setReadOnly(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(textEdit)

        self.hideCancelButton()

        self.yesButton.setText(self.tr("Ok"))


class WaitingForLolMessageBox(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.myYesButton = PrimaryPushButton(
            self.tr('Connect To Client'), self.buttonGroup)
        self.myCancelButton = QPushButton(
            self.tr('Exit Seraphine'), self.buttonGroup)

        self.titleLabel = TitleLabel()
        self.content = BodyLabel()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.yesButton.setVisible(False)
        self.cancelButton.setVisible(False)

        self.myCancelButton.setObjectName("cancelButton")
        self.buttonLayout.addWidget(self.myYesButton)
        self.buttonLayout.addWidget(self.myCancelButton)

        self.titleLabel.setText(self.tr('Tasklist is not available'))
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        self.content.setText(
            self.tr('Please clicked "Connect To Client" button manually when LOL launched completely'))
        self.content.setContentsMargins(8, 0, 5, 0)

        self.myYesButton.clicked.connect(self.__onYesButtonClicked)
        self.myCancelButton.clicked.connect(self.__onCancelButtonClicked)

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content)

    def __onYesButtonClicked(self):
        pid = getLolClientPidSlowly()

        if pid == -1:
            return

        signalBus.lolClientStarted.emit(pid)
        self.accept()
        self.accepted.emit()

    def __onCancelButtonClicked(self):
        self.reject()
        self.rejected.emit()


class ChangeClientMessageBox(MessageBoxBase):
    def __init__(self, pids, parent=None):
        super().__init__(parent)

        self.myYesButton = PrimaryPushButton(
            self.tr('Reconnect'), self.buttonGroup)
        self.myCancelButton = QPushButton(
            self.tr('Cancel'), self.buttonGroup)

        self.pids = pids

        self.titleLabel = TitleLabel()
        self.content = BodyLabel()

        self.comboBox = ComboBox()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.yesButton.setVisible(False)
        self.cancelButton.setVisible(False)
        self.myYesButton.clicked.connect(self.__onYesButtonClicked)
        self.myCancelButton.clicked.connect(self.__onCancelButtonClicked)

        self.myCancelButton.setObjectName("cancelButton")
        self.buttonLayout.addWidget(self.myYesButton)
        self.buttonLayout.addWidget(self.myCancelButton)

        self.titleLabel.setText(self.tr('Change client'))
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        self.content.setText(
            self.tr('Please select the target LOL client:'))
        self.content.setContentsMargins(8, 0, 5, 0)

        for i, pid in enumerate(self.pids):
            _, _, server = getPortTokenServerByPid(pid)
            item = self.tr("PID: ") + str(pid) + self.tr(", ") + \
                self.tr("server: ") + server

            if pid == connector.pid:
                item += " " + self.tr("(current)")
                currentIdx = i

            self.comboBox.addItem(item)

        self.comboBox.setCurrentIndex(currentIdx)
        self.comboBox.setMinimumWidth(400)

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content)
        self.viewLayout.addWidget(self.comboBox)

    def __onYesButtonClicked(self):
        pid = self.pids[self.comboBox.currentIndex()]
        if connector.pid != pid:
            signalBus.lolClientChanged.emit(pid)

        self.accept()
        self.accepted.emit()

    def __onCancelButtonClicked(self):
        self.reject()
        self.rejected.emit()
