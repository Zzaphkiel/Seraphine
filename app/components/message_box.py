from qasync import asyncSlot
import aiohttp
import os
import shutil
import sys
import webbrowser
import py7zr

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget
from app.common.qfluentwidgets import (MessageBoxBase, SmoothScrollArea,
                                       BodyLabel, TextEdit, TitleLabel,
                                       ProgressBar,
                                       PrimaryPushButton, ComboBox)

from app.common.config import VERSION, cfg, LOCAL_PATH, BETA
from app.common.util import getLolClientPidSlowly
from app.common.signals import signalBus
from app.common.update import runUpdater
from app.lol.connector import connector
from app.components.multi_champion_select import MultiChampionSelectWidget
from app.components.multi_lol_path_setting import PathDraggableWidget


class UpdateMessageBox(MessageBoxBase):
    def __init__(self, info, parent=None):
        super().__init__(parent=parent)
        self.info = info

        self.myYesButton = QPushButton(
            self.tr("Update and Restart"), self.buttonGroup)
        self.myCancelButton = QPushButton(self.tr("Ok"), self.buttonGroup)
        self.manuallyButton = PrimaryPushButton(self.tr("Manually Download"))

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
        self.myYesButton.setObjectName('cancelButton')

        self.buttonLayout.addWidget(self.manuallyButton)
        self.buttonLayout.addWidget(self.myYesButton)
        self.buttonLayout.addWidget(self.myCancelButton)

        self.titleLabel.setText(self.tr('Update detected'))
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        self.content.setText(self.tr("current: v") + (BETA or VERSION) + self.tr(", ")
                             + self.tr("new: v") + self.info.get("tag_name")[1:])
        self.content.setContentsMargins(8, 0, 5, 0)

        self.textEdit.setFixedWidth(int(self.width() * .6))
        self.textEdit.setFixedHeight(int(self.height() * .4))
        self.textEdit.setMarkdown(self.info.get("body"))
        self.textEdit.setReadOnly(True)

        self.infoLabel.setVisible(False)
        self.bar.setVisible(False)

        self.manuallyButton.clicked.connect(self.__onManuallyButtonClicked)
        self.myYesButton.clicked.connect(self.__onYesButtonClicked)
        self.myCancelButton.clicked.connect(self.__onCancelButtonClicked)

        # 简单判断下打开方式
        if not os.path.exists("Seraphine.exe"):
            self.infoLabel.setVisible(True)
            self.infoLabel.setText(
                self.tr("Updating is only available on releases version"))

            self.myYesButton.setEnabled(False)

        # 当前版本被禁用时, 不允许忽略版本
        self.myCancelButton.setEnabled(not self.info["forbidden"])

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content)
        self.viewLayout.addWidget(self.textEdit)
        self.viewLayout.addWidget(self.infoLabel, alignment=Qt.AlignRight)
        self.viewLayout.addWidget(self.bar)

    @asyncSlot()
    async def __onYesButtonClicked(self):
        '''
        该函数负责
        1. 删除 `LOCAL_PATH` 中之前可能下载过的文件
        2. 重新下载新版本压缩包
        3. 解压缩，并删除压缩包
        4. 释放并运行 bat 文件，关闭自己
        5. 删除当前文件夹下的自己，并将解压好的新版本拷贝进来
        6. 重新运行自己
        '''

        # url = f"{github.proxyApi}/{self.info['assets'][0]['browser_download_url']}"

        # 把下载地址换成 Gitee 的
        url: str = self.info['assets'][0]['browser_download_url']
        url = url.replace("github", "gitee")
        url = url.replace("Zzaphkiel/Seraphine", "Zzaphkiel/seraphine")

        self.myYesButton.setEnabled(False)
        self.myCancelButton.setEnabled(False)
        self.manuallyButton.setEnabled(False)

        self.infoLabel.setVisible(True)
        self.bar.setVisible(True)

        zipPath = f'{LOCAL_PATH}/Seraphine.7z'
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

        with py7zr.SevenZipFile(zipPath, mode='r') as z:
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

    def __onManuallyButtonClicked(self):
        url: str = self.info['assets'][0]['browser_download_url']
        url = url.replace("github", "gitee")
        url = url.replace("Zzaphkiel/Seraphine", "Zzaphkiel/seraphine")

        webbrowser.open(url)

        self.reject()
        self.rejected.emit()


class NoticeMessageBox(MessageBoxBase):
    def __init__(self, msg, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(self.tr('Notice'), self)
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        textEdit = TextEdit(self)
        textEdit.setFixedWidth(int(self.width() * 0.6))
        textEdit.setFixedHeight(int(self.height() * 0.4))
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
            summoner = connector.getLoginSummonerByPid(pid)
            item = (summoner.get("gameName") or summoner['displayName']) + \
                self.tr(", ") + self.tr("PID: ") + str(pid)

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


class ExceptionMessageBox(MessageBoxBase):
    def __init__(self, title, content, parent):
        super().__init__(parent=parent)

        self.titleLabel = TitleLabel(title)
        self.textEdit = TextEdit()
        self.textEdit.setText(content)

        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()

        self.__intiWidget()
        self.__initLayout()

    def __intiWidget(self):
        self.yesButton.setText(self.tr('Copy to clipboard and exit'))
        self.cancelButton.setText(self.tr('Exit'))

        self.textEdit.setFixedWidth(int(self.width() * .6))
        self.textEdit.setFixedHeight(int(self.height() * .4))

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.textEdit)


class MultiChampionSelectMsgBox(MessageBoxBase):
    completed = pyqtSignal(list)

    def __init__(self, champions: dict, selected: list, parent=None):
        super().__init__(parent)

        self.myYesButton = PrimaryPushButton(self.tr('OK'), self.buttonGroup)
        self.myCancelButton = QPushButton(self.tr('Cancel'), self.buttonGroup)

        self.titleLabel = TitleLabel(self.tr("Choose Champions"))
        self.championSelectWidget = MultiChampionSelectWidget(
            champions, selected)

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.championSelectWidget)

        self.buttonLayout.addWidget(self.myYesButton)
        self.buttonLayout.addWidget(self.myCancelButton)

    def __initWidget(self):
        self.yesButton.setVisible(False)
        self.cancelButton.setVisible(False)
        self.myCancelButton.setObjectName("cancelButton")

        self.myYesButton.clicked.connect(self.__myOnYesButtonClicked)
        self.myCancelButton.clicked.connect(self.__myOnCancelButtonClicked)

        # 强迫症 TV 之这玩意左边多出来了
        self.titleLabel.setStyleSheet("padding-left: 3px")

    def __myOnYesButtonClicked(self):
        self.completed.emit(
            self.championSelectWidget.getSelectedChampionIds())

        self.accept()
        self.accepted.emit()

    def __myOnCancelButtonClicked(self):
        self.reject()
        self.rejected.emit()


class MultiPathSettingMsgBox(MessageBoxBase):

    def __init__(self, paths: list, parent=None):
        super().__init__(parent)
        self.myYesButton = PrimaryPushButton(self.tr('OK'), self.buttonGroup)
        self.myCancelButton = QPushButton(self.tr('Cancel'), self.buttonGroup)

        self.titleLabel = TitleLabel(self.tr("Set LOL cLient path"))
        self.pathsWidget = PathDraggableWidget(paths)

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.pathsWidget)

        self.buttonLayout.addWidget(self.myYesButton)
        self.buttonLayout.addWidget(self.myCancelButton)

    def __initWidget(self):
        self.yesButton.setVisible(False)
        self.cancelButton.setVisible(False)
        self.myCancelButton.setObjectName("cancelButton")

        self.myYesButton.clicked.connect(self.__myOnYesButtonClicked)
        self.myCancelButton.clicked.connect(self.__myOnCancelButtonClicked)

        # 强迫症 TV 之这玩意左边多出来了
        self.titleLabel.setStyleSheet("padding-left: 1px")

    def __myOnYesButtonClicked(self):
        cfg.set(cfg.lolFolder, self.pathsWidget.getCurrentPaths())

        self.accept()
        self.accepted.emit()

    def __myOnCancelButtonClicked(self):
        self.reject()
        self.rejected.emit()
