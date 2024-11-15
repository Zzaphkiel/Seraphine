import asyncio
import copy
import os
import sys
import threading
import time
import traceback
from pathlib import Path

import pyperclip
import win32api
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QImage
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from aiohttp.client_exceptions import ClientConnectorError
from qasync import asyncClose, asyncSlot

from app.common.config import cfg, VERSION, BETA
from app.common.icons import Icon
from app.common.logger import logger
from app.common.qfluentwidgets import (NavigationItemPosition, InfoBar, InfoBarPosition, Action,
                                       FluentWindow, SplashScreen, MessageBox, SmoothScrollArea,
                                       ToolTipFilter, FluentIcon, ToolTipPosition)
from app.common.signals import signalBus
from app.common.util import (github, getLolClientPid, getTasklistPath,
                             getLolClientPidSlowly, getLoLPathByRegistry)
from app.components.avatar_widget import NavigationAvatarWidget
from app.components.message_box import (UpdateMessageBox, NoticeMessageBox,
                                        WaitingForLolMessageBox, ExceptionMessageBox,
                                        ChangeDpiMessageBox)
from app.components.temp_system_tray_menu import TmpSystemTrayMenu
from app.lol.aram import AramBuff
from app.lol.champions import ChampionAlias
from app.lol.connector import connector
from app.lol.exceptions import (SummonerGamesNotFound, RetryMaximumAttempts,
                                SummonerNotFound, SummonerNotInGame, SummonerRankInfoNotFound)
from app.lol.listener import (LolProcessExistenceListener, StoppableThread)
from app.lol.opgg import opgg
from app.lol.phase import Planning, Selection
from app.lol.tools import (parseAllyGameInfo, parseGameInfoByGameflowSession,
                           getAllyOrderByGameRole, getTeamColor, ChampionSelection,
                           SERVERS_NAME, SERVERS_SUBSET)
from app.view.auxiliary_interface import AuxiliaryInterface
from app.view.career_interface import CareerInterface
from app.view.game_info_interface import GameInfoInterface
from app.view.opgg_window import OpggWindow
from app.view.search_interface import SearchInterface
from app.view.setting_interface import SettingInterface
from app.view.start_interface import StartInterface

TAG = "MainWindow"


class MainWindow(FluentWindow):
    mainWindowHide = pyqtSignal(bool)
    showUpdateMessageBox = pyqtSignal(dict)
    showNoticeMessageBox = pyqtSignal(str)
    checkUpdateFailed = pyqtSignal()
    fetchNoticeFailed = pyqtSignal()

    def __init__(self):
        super().__init__()

        logger.critical(f"Seraphine started, version: {BETA or VERSION}", TAG)

        self.__initConfig()
        self.__initWindow()
        self.__checkWindowSize()
        self.__initSystemTray()

        # create sub interface
        self.startInterface = StartInterface(self)
        self.careerInterface = CareerInterface(self)
        self.searchInterface = SearchInterface(self)
        self.gameInfoInterface = GameInfoInterface(self)
        self.auxiliaryFuncInterface = AuxiliaryInterface(self)
        self.settingInterface = SettingInterface(self)

        logger.critical("Seraphine interfaces initialized", TAG)

        # create listener
        self.isClientProcessRunning = False
        self.processListener = LolProcessExistenceListener(self)
        self.checkUpdateThread = StoppableThread(
            target=self.checkUpdate, parent=self)
        self.checkNoticeThread = StoppableThread(
            target=lambda: self.checkNotice(False), parent=self)

        logger.critical("Seraphine listerners started", TAG)

        self.currentSummoner = None

        self.isGaming = False
        self.isTrayExit = False
        self.tasklistEnabled = True
        self.championSelection = ChampionSelection()

        self.lastTipsTime = time.time()
        self.lastTipsType = None

        self.__initInterface()
        self.__initNavigation()
        self.__initListener()
        self.__conncetSignalToSlot()
        self.__autoStartLolClient()

        self.splashScreen.finish()

        self.opggWindow = OpggWindow()

        logger.critical("Seraphine initialized", TAG)

    def __initConfig(self):
        folder = cfg.get(cfg.lolFolder)

        isEmptyList = folder == []
        isEmptyStr = folder == str(Path("").absolute()).replace(
            "\\", "/") or folder == ""

        if isEmptyList or isEmptyStr:
            path = getLoLPathByRegistry()

            if not path:
                return

            cfg.set(cfg.lolFolder, [path])
            return

        if type(folder) is str:
            cfg.set(cfg.lolFolder, [folder])

    def __initInterface(self):
        self.__lockInterface()

        self.startInterface.setObjectName("startInterface")
        self.careerInterface.setObjectName("careerInterface")
        self.searchInterface.setObjectName("searchInterface")
        self.gameInfoInterface.setObjectName("gameInfoInterface")
        self.auxiliaryFuncInterface.setObjectName("auxiliaryFuncInterface")
        self.settingInterface.setObjectName("settingInterface")

    def __initNavigation(self):
        pos = NavigationItemPosition.SCROLL

        self.navigationInterface.addSeparator(NavigationItemPosition.TOP)

        self.addSubInterface(
            self.startInterface, Icon.HOME, self.tr("Start"), pos)
        self.addSubInterface(
            self.careerInterface, Icon.PERSON, self.tr("Career"), pos)
        self.addSubInterface(
            self.searchInterface, Icon.SEARCH, self.tr("Search 👀"), pos)
        self.addSubInterface(
            self.gameInfoInterface, Icon.GAME, self.tr("Game Information"), pos)
        self.addSubInterface(
            self.auxiliaryFuncInterface, Icon.WRENCH,
            self.tr("Auxiliary Functions"), pos)

        pos = NavigationItemPosition.BOTTOM

        self.navigationInterface.addItem(
            routeKey='Opgg',
            icon=QIcon("app/resource/images/opgg.svg"),
            text="OP.GG",
            onClick=self.showOpggWindow,
            selectable=False,
            position=pos,
            tooltip="OP.GG"
        )

        self.navigationInterface.addItem(
            routeKey='Fix',
            icon=Icon.ARROWCIRCLE,
            text=self.tr("Back to Lobby"),
            onClick=self.__onFixLCUButtonClicked,
            selectable=False,
            position=pos,
            tooltip=self.tr("Back to Lobby"),
        )

        self.navigationInterface.addItem(
            routeKey='Notice',
            icon=Icon.ALERT,
            text=self.tr("Notice"),
            onClick=lambda: threading.Thread(
                target=lambda: self.checkNotice(True)).start(),
            selectable=False,
            position=pos,
            tooltip=self.tr("Notice"),
        )

        self.navigationInterface.insertSeparator(
            3, NavigationItemPosition.BOTTOM)

        self.avatarWidget = NavigationAvatarWidget(
            avatar="app/resource/images/game.png", name=self.tr("Start LOL"))
        self.navigationInterface.addWidget(
            routeKey="avatar",
            widget=self.avatarWidget,
            onClick=self.__onAvatarWidgetClicked,
            position=pos,
        )

        self.addSubInterface(
            self.settingInterface, FluentIcon.SETTING,
            self.tr("Settings"), pos,
        )

        # set the maximum width
        self.navigationInterface.setExpandWidth(250)
        self.navigationInterface.setMinimumExpandWidth(1321)

    def __conncetSignalToSlot(self):
        # From listener:
        signalBus.tasklistNotFound.connect(self.__showWaitingMessageBox)
        signalBus.lolClientStarted.connect(self.__onLolClientStarted)
        signalBus.lolClientEnded.connect(self.__onLolClientEnded)
        signalBus.lolClientChanged.connect(self.__onLolClientChanged)
        signalBus.terminateListeners.connect(self.__terminateListeners)

        # From connector
        signalBus.currentSummonerProfileChanged.connect(
            self.__onCurrentSummonerProfileChanged)
        signalBus.gameStatusChanged.connect(
            self.__onGameStatusChanged)
        signalBus.champSelectChanged.connect(
            self.__onChampSelectChanged)
        signalBus.lcuApiExceptionRaised.connect(
            self.__onShowLcuConnectError)
        signalBus.getCmdlineError.connect(
            self.__showNeedAdminMessageBox)

        # From career_interface
        signalBus.careerGameBarClicked.connect(self.__onCareerGameClicked)

        # From search_interface and gameinfo_interface
        signalBus.toSearchInterface.connect(self.__switchToSearchInterface)
        signalBus.toCareerInterface.connect(self.__switchToCareerInterface)

        # From setting_interface
        self.settingInterface.careerGamesCount.pushButton.clicked.connect(
            self.__refreshCareerInterface)
        self.settingInterface.micaCard.checkedChanged.connect(
            self.__cascadeSetMicaEffect)

        # From main_window
        self.showUpdateMessageBox.connect(self.__onShowUpdateMessageBox)
        self.showNoticeMessageBox.connect(self.__onShowNoticeMessageBox)
        self.checkUpdateFailed.connect(self.__onCheckUpdateFailed)
        self.fetchNoticeFailed.connect(self.__onFetchNoticeFailed)
        self.stackedWidget.currentChanged.connect(
            self.__onCurrentStackedChanged)
        self.mainWindowHide.connect(self.__onWindowHide)

    def __initWindow(self):
        self.resize(1134, 826)
        self.setMinimumSize(1134, 826)
        self.setWindowIcon(QIcon("app/resource/images/logo.png"))
        self.setWindowTitle("Seraphine")

        self.titleBar.titleLabel.setStyleSheet(
            "QLabel {font: 13px 'Segoe UI', 'Microsoft YaHei';}")
        self.titleBar.hBoxLayout.insertSpacing(0, 10)

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

        self.oldHook = sys.excepthook
        sys.excepthook = self.exceptHook

    @asyncSlot(str, BaseException)
    async def __onShowLcuConnectError(self, api, obj):
        # 同类错误限制弹出频率(1.5秒每次)
        if time.time() - self.lastTipsTime < 1.5 and self.lastTipsType is type(obj):
            return
        else:
            self.lastTipsTime = time.time()
            self.lastTipsType = type(obj)

        if type(obj) in [SummonerGamesNotFound, SummonerRankInfoNotFound]:
            msg = self.tr(
                "The server returned abnormal content, which may be under maintenance.")
        elif type(obj) is RetryMaximumAttempts:
            msg = self.tr("Exceeded maximum retry attempts.")
        elif type(obj) in [SummonerNotFound, SummonerNotInGame]:
            return
        else:
            msg = repr(obj)

        InfoBar.error(
            self.tr("LCU request error"),
            self.tr(f"Connect API") + f" {api}: {msg}",
            duration=5000,
            orient=Qt.Vertical,
            parent=self,
            position=InfoBarPosition.BOTTOM_RIGHT
        )

    def __onWindowHide(self, hide):
        """

        @param hide: True -> 隐藏, False -> 显示
        @return:
        """
        if hide:
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def checkUpdate(self):
        if not cfg.get(cfg.enableCheckUpdate):
            return

        try:
            releasesInfo = github.checkUpdate()
        except:
            self.checkUpdateFailed.emit()
            return

        if releasesInfo:
            self.showUpdateMessageBox.emit(releasesInfo)

    def checkNotice(self, triggerByUser):
        try:
            noticeInfo = github.getNotice()
            sha = noticeInfo['sha']
            content = noticeInfo['content']
        except:
            self.fetchNoticeFailed.emit()
            return

        # 如果是开启软件时，并且该公告曾经已经展示过，就直接 return 了
        if not triggerByUser and sha == cfg.get(cfg.lastNoticeSha):
            return

        cfg.set(cfg.lastNoticeSha, sha)
        self.showNoticeMessageBox.emit(content)

    def __onCheckUpdateFailed(self):
        InfoBar.warning(
            self.tr("Check Update Failed"),
            self.tr(
                "Failed to check for updates, possibly unable to connect to Github."),
            duration=5000,
            orient=Qt.Vertical,
            parent=self,
            position=InfoBarPosition.BOTTOM_RIGHT
        )

    def __onFetchNoticeFailed(self):
        InfoBar.warning(
            self.tr("Fetch notice Failed"),
            self.tr(
                "Failed to fetch notice, possibly unable to connect to Github."),
            duration=5000,
            orient=Qt.Vertical,
            parent=self,
            position=InfoBarPosition.BOTTOM_RIGHT
        )

    def __onShowUpdateMessageBox(self, info):
        msgBox = UpdateMessageBox(info, self.window())
        msgBox.exec()

    def __onShowNoticeMessageBox(self, msg):
        msgBox = NoticeMessageBox(msg, self.window())
        msgBox.exec()

    def __showWaitingMessageBox(self):
        self.tasklistEnabled = False

        msgBox = WaitingForLolMessageBox(self.window())

        if not msgBox.exec():
            signalBus.terminateListeners.emit()
            sys.exit()

    def __showNeedAdminMessageBox(self):
        msgBox = MessageBox(self.tr("Get cmdline error"), self.tr(
            "Try running Seraphine as an administrator"), self.window())
        msgBox.cancelButton.setVisible(False)
        msgBox.exec()

        signalBus.terminateListeners.emit()
        sys.exit()

    def __initSystemTray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setToolTip("Seraphine")
        self.trayIcon.installEventFilter(ToolTipFilter(self.trayIcon))

        self.trayIcon.setIcon(QIcon("app/resource/images/logo.png"))

        careerAction = Action(Icon.PERSON, self.tr("Career"), self)
        searchAction = Action(Icon.SEARCH, self.tr("Search 👀"), self)
        gameInfoAction = Action(Icon.GAME, self.tr("Game Information"), self)
        settingsAction = Action(Icon.SETTING, self.tr("Settings"), self)
        quitAction = Action(Icon.EXIT, self.tr('Quit'), self)

        def showAndSwitch(interface):
            self.show()
            self.checkAndSwitchTo(interface)

        def quit():
            self.isTrayExit = True
            self.close()

        careerAction.triggered.connect(
            lambda: showAndSwitch(self.careerInterface))
        searchAction.triggered.connect(
            lambda: showAndSwitch(self.searchInterface))
        gameInfoAction.triggered.connect(
            lambda: showAndSwitch(self.gameInfoInterface))
        settingsAction.triggered.connect(
            lambda: showAndSwitch(self.settingInterface))
        quitAction.triggered.connect(quit)

        self.trayMenu = TmpSystemTrayMenu(self)

        self.trayMenu.addAction(careerAction)
        self.trayMenu.addAction(searchAction)
        self.trayMenu.addAction(gameInfoAction)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction(settingsAction)
        self.trayMenu.addAction(quitAction)

        self.trayIcon.setContextMenu(self.trayMenu)
        # 双击事件
        self.trayIcon.activated.connect(lambda reason: self.show(
        ) if reason == QSystemTrayIcon.DoubleClick else None)
        self.trayIcon.show()

    def show(self):
        self.activateWindow()
        self.setWindowState(self.windowState() & ~
        Qt.WindowMinimized | Qt.WindowActive)
        self.showNormal()

    def __initListener(self):
        self.processListener.start()
        self.checkUpdateThread.start()
        self.checkNoticeThread.start()
        # self.minimizeThread.start()  # 该功能不再支持 -- By Hpero4

    async def __changeCareerToCurrentSummoner(self):
        summoner = await connector.getCurrentSummoner()
        self.currentSummoner = summoner
        name = summoner.get("gameName") or summoner['displayName']
        self.careerInterface.setLoginSummonerPuuid(summoner['puuid'])

        asyncio.create_task(self.careerInterface.updateInterface(
            summoner=summoner))

    @asyncSlot(int)
    async def __onLolClientStarted(self, pid):
        logger.info(f"League of Legends client started: {pid}", TAG)
        res = await self.__startConnector(pid)
        if not res:
            return

        await opgg.start()
        self.checkAndSwitchTo(self.careerInterface)
        self.isClientProcessRunning = True

        await self.__changeCareerToCurrentSummoner()
        await self.__updateAvatarIconName()

        self.startInterface.hideLoadingPage()

        folder, status = await asyncio.gather(connector.getInstallFolder(),
                                              connector.getGameStatus())

        self.__setLolInstallFolder(folder)

        asyncio.create_task(self.auxiliaryFuncInterface.initChampionList())

        self.auxiliaryFuncInterface.lockConfigCard.loadNowMode()

        # 加载大乱斗buff -- By Hpero4
        aramInitT = asyncio.create_task(AramBuff.checkAndUpdate())
        championsInit = asyncio.create_task(ChampionAlias.checkAndUpdate())

        asyncio.create_task(self.opggWindow.initWindow())
        self.opggWindow.setHomeInterfaceEnabled(False)

        # ---- 240413 ---- By Hpero4
        # 如果你希望 self.__onGameStatusChanged(status) 和 self.__unlockInterface() 并行执行, 可以这样使用:
        #     t = self.__onGameStatusChanged(status)
        #     self.__unlockInterface()
        #     await t
        #
        # 如果你希望等待 self.__onGameStatusChanged(status) 返回之后再执行 self.__unlockInterface() 可以这样使用:
        #     await self.__onGameStatusChanged(status)
        #     self.__unlockInterface()
        #
        # 而不是直接调用:
        #     self.__onGameStatusChanged(status)
        #     self.__unlockInterface()
        #
        # 此外 self.__onGameStatusChanged(status) 本身不是一个常规的异步函数, 它是使用 asyncSlot 装饰的槽函数,
        #   内部封装了task的新建过程, 并且会被立即加入到 QEventLoop 等待执行, 并返回一个Task实例;
        #
        # 如果 func a 是一个常规异步函数, func b 是一个常规的同步函数, 你应该这样使用它:
        #     t = asyncio.create_task(a())
        #     b()
        #     await t
        #
        # 项目中还有其他异步函数使用了await进行了额外的等待, 亦或是直接调用异步函数而没有使用await保证竞态的情况,
        # 这可能导致性能或是其他不可预期的问题, 这是只是一个例子;
        # ---- 240413 ---- By Hpero4

        self.__unlockInterface()
        await asyncio.gather(championsInit, aramInitT)
        await self.__onGameStatusChanged(status)

        # Note 如果你希望测试大乱斗的数据弹框, 参考这个 -- By Hpero4
        # self.careerInterface.icon.aramInfo = AramBuff.getInfoByChampionId(75)

    async def __startConnector(self, pid):
        try:
            await connector.start(pid)
            return True
        except RetryMaximumAttempts:
            # 若超出最大尝试次数, 则认为 lcu 未就绪 (如大区排队中),
            # 捕获到该异常时不抛出, 等待下一个 emit
            await connector.close()

            if self.processListener.isRunning():
                self.processListener.runningPid = 0
            else:
                signalBus.tasklistNotFound.emit()

            return False

    @asyncSlot(int)
    async def __onLolClientChanged(self, pid):
        logger.critical(f"League of Legends client changed: {pid}", TAG)
        await self.__onLolClientEnded()
        self.processListener.runningPid = pid
        await self.__onLolClientStarted(pid)

    @asyncSlot()
    async def __onLolClientEnded(self):
        logger.critical("League of Legends client ended", TAG)

        if self.searchInterface.gameLoadingTask:
            self.searchInterface.puuid = 0
            self.searchInterface.gameLoadingTask = None

        await connector.close()
        await opgg.close()

        self.isClientProcessRunning = False
        self.currentSummoner = None
        self.careerInterface.setLoginSummonerPuuid(None)

        await self.__updateAvatarIconName()

        self.startInterface.showLoadingPage()
        self.careerInterface.setLoadingPageEnabled(True)
        self.opggWindow.setHomeInterfaceEnabled(True)

        self.setWindowTitle("Seraphine")

        self.checkAndSwitchTo(self.startInterface)
        self.__lockInterface()

    async def __updateAvatarIconName(self):
        if self.currentSummoner:
            try:
                iconId = self.currentSummoner['profileIconId']
                icon = await connector.getProfileIcon(iconId)
                name = (self.currentSummoner.get("gameName")
                        or self.currentSummoner['displayName'])

                server = SERVERS_NAME.get(connector.server) or connector.server
                name += self.tr(" (") + server + self.tr(")")

                subset = SERVERS_SUBSET.get(connector.server)

                if subset and not self.avatarWidget.toolTip():
                    tooltip = self.tr(", ").join(subset)
                    self.avatarWidget.setToolTip(tooltip)
                    self.avatarWidget.installEventFilter(
                        ToolTipFilter(self.avatarWidget, 0,
                                      ToolTipPosition.TOP)
                    )

            except:
                icon = "app/resource/images/game.png"
                name = self.tr("Start LOL")
                self.avatarWidget.setToolTip("")
        else:
            icon = "app/resource/images/game.png"
            name = self.tr("Start LOL")
            self.avatarWidget.setToolTip("")

        self.avatarWidget.avatar = QImage(icon).scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatarWidget.name = name

        self.avatarWidget.repaint()

    def __setLolInstallFolder(self, folder: str):
        folder = folder.replace("\\", "/")
        folder = folder.replace("LeagueClient", "TCLS")
        folder = f"{folder[:1].upper()}{folder[1:]}"

        current: list = cfg.get(cfg.lolFolder)

        if folder.lower() not in [item.lower() for item in current]:
            new = copy.deepcopy(current)
            new.append(folder)
            cfg.set(cfg.lolFolder, new)

    @asyncSlot(dict)
    async def __onCurrentSummonerProfileChanged(self, data: dict):
        self.currentSummoner = data

        await asyncio.gather(self.__updateAvatarIconName(),
                             self.careerInterface.updateNameIconExp(data))

        logger.debug(f"Update Summoner Info : {data}", TAG)

    def __autoStartLolClient(self):
        if self.isClientProcessRunning:
            return

        if not cfg.get(cfg.enableStartLolWithApp):
            return

        if self.tasklistEnabled:
            path = getTasklistPath()
            pid = getLolClientPid(path)
        else:
            pid = getLolClientPidSlowly()

        if pid == 0:
            self.__startLolClient()

    def __startLolClient(self):
        for clientName in ("client.exe", "LeagueClient.exe"):
            path = f'{cfg.get(cfg.lolFolder)[0]}/{clientName}'
            if os.path.exists(path):
                os.popen(f'"{path}"')
                self.__showStartLolSuccessInfo()
                break
        else:
            self.__showLolClientPathErrorInfo()

    def __onAvatarWidgetClicked(self):
        if not self.isClientProcessRunning:
            self.__startLolClient()
        else:
            self.careerInterface.backToMeButton.clicked.emit()
            self.checkAndSwitchTo(self.careerInterface)

    def __showStartLolSuccessInfo(self):
        InfoBar.success(
            title=self.tr("Start LOL successfully"),
            orient=Qt.Vertical,
            content="",
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=self,
        )

    def __showLolClientPathErrorInfo(self):
        InfoBar.error(
            title=self.tr("Invalid path"),
            content=self.tr(
                "Please set the correct directory of the LOL client in the setting page"),
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=self,
        )

    def checkAndSwitchTo(self, interface):
        index = self.stackedWidget.indexOf(interface)

        if not self.stackedWidget.currentIndex() == index:
            self.navigationInterface.widget(interface.objectName()).click()

    def __unlockInterface(self):
        self.searchInterface.setEnabled(True)
        self.auxiliaryFuncInterface.setEnabled(True)
        # pass

    def __lockInterface(self):
        self.searchInterface.setEnabled(False)
        self.auxiliaryFuncInterface.setEnabled(False)

    def __terminateListeners(self):
        self.processListener.terminate()
        self.checkUpdateThread.terminate()
        self.checkNoticeThread.terminate()

    @asyncClose
    async def closeEvent(self, a0) -> None:
        # 首次点击 关闭 按钮
        if cfg.get(cfg.enableCloseToTray) is None:
            msgBox = MessageBox(
                self.tr("Do you wish to exit?"),
                self.tr(
                    "Choose action for close button (you can modify it at any time in the settings page)"),
                self
            )

            msgBox.yesButton.setText(self.tr('Minimize'))
            msgBox.cancelButton.setText(self.tr('Exit'))
            self.update()

            cfg.set(cfg.enableCloseToTray, msgBox.exec())

        if not cfg.get(cfg.enableCloseToTray) or self.isTrayExit:
            self.__terminateListeners()
            self.opggWindow.close()

            return super().closeEvent(a0)
        else:
            a0.ignore()
            self.hide()

    @asyncSlot(str)
    async def __switchToSearchInterface(self, name):
        self.searchInterface.searchLineEdit.setText(name)
        self.checkAndSwitchTo(self.searchInterface)

        await self.searchInterface.onSearchButtonClicked()

    @asyncSlot(str)
    async def __switchToCareerInterface(self, puuid):
        if puuid == '00000000-0000-0000-0000-000000000000':
            return

        try:
            self.careerInterface.w.close()
        except:
            pass

        self.checkAndSwitchTo(self.careerInterface)
        await self.careerInterface.updateInterface(puuid=puuid)

    @asyncSlot(str)
    async def __onGameStatusChanged(self, status):
        title = None
        isGaming = False

        if status == 'None':
            title = self.tr("Home")
            await self.__onGameEnd()
        elif status == 'ChampSelect':
            title = self.tr("Selecting Champions")

            # 在标题添加所处队伍
            side = await connector.getMapSide()
            if side:
                if side == 'blue':
                    mapSide = self.tr("Blue Team")
                else:
                    mapSide = self.tr("Red Team")

                title = title + " - " + mapSide

            await self.__onChampionSelectBegin()
        elif status == 'GameStart':
            title = self.tr("Gaming")
            await self.__onGameStart()
            isGaming = True
        elif status == 'InProgress':
            title = self.tr("Gaming")

            # 重连或正常进入游戏 (走 GameStart), 不需要更新数据
            if not self.isGaming:
                await self.__onGameStart()
            isGaming = True
        elif status == 'WaitingForStatus':
            title = self.tr("Waiting for status")
        elif status == 'EndOfGame':
            title = self.tr("End of game")
        elif status == 'Lobby':
            title = self.tr("Lobby")
            await self.__onGameEnd()
            await self.careerInterface.refresh()

            if self.stackedWidget.currentWidget() is self.gameInfoInterface:
                self.switchTo(self.careerInterface)

        elif status == 'ReadyCheck':
            title = self.tr("Ready check")
            await self.__onMatchMade()
        elif status == 'Matchmaking':
            title = self.tr("Match making")
            await self.__onGameEnd()
        elif status == "Reconnect":  # 等待重连
            title = self.tr("Waiting reconnect")
            await self.__onReconnect()

        self.isGaming = isGaming

        if title != None:
            self.setWindowTitle("Seraphine - " + title)

    async def __onMatchMade(self):
        if not cfg.get(cfg.enableAutoAcceptMatching):
            return

        async def accept():
            timeDelay = cfg.get(cfg.autoAcceptMatchingDelay)
            await asyncio.sleep(timeDelay)
            status = await connector.getReadyCheckStatus()

            if status.get("errorCode"):
                return

            if not status['playerResponse'] == 'Declined':
                await connector.acceptMatchMaking()

        asyncio.create_task(accept())

    async def __onReconnect(self):
        if not cfg.get(cfg.enableAutoReconnect):
            return

        async def reconnect():
            while await connector.getGameStatus() == "Reconnect":
                # 掉线立刻重连会无效
                await asyncio.sleep(.3)
                await connector.reconnect()

        asyncio.create_task(reconnect())

    # 进入英雄选择界面时触发
    async def __onChampionSelectBegin(self):
        self.selection = Selection()
        self.championSelection.reset()
        session = await connector.getChampSelectSession()
        await self.selection.act(session)

        if cfg.get(cfg.autoShowOpgg):
            self.opggWindow.show()

        currentSummonerId = self.currentSummoner['summonerId']
        info = await parseAllyGameInfo(session, currentSummonerId, useSGP=True)
        self.gameInfoInterface.updateAllySummoners(info)

        self.checkAndSwitchTo(self.gameInfoInterface)

    # 英雄选择时，英雄改变 / 楼层改变时触发
    @asyncSlot(dict)
    async def __onChampSelectChanged(self, data):
        data = data['data']
        await self.selection.act(data)

        # 更新头像
        await self.gameInfoInterface.updateAllyIcon(data['myTeam'])

        # 更新楼层顺序
        self.gameInfoInterface.updateAllySummonersOrder(data['myTeam'])

    # 进入游戏后触发
    async def __onGameStart(self):
        session = await connector.getGameflowSession()
        currentSummonerId = self.currentSummoner['summonerId']

        queueId = session['gameData']['queue']['id']
        if queueId in (1700, 1090, 1100, 1110, 1130, 1160):  # 斗魂 云顶匹配 (排位)
            return

        # 如果是进游戏后开的软件，需要先把友方信息更新上去
        async def paintAllySummonersInfo():
            # TODO 自定义时, 若队伍成员<5, 会触发重新加载导致性能浪费
            if self.gameInfoInterface.allyChampions and len(self.gameInfoInterface.allyChampions) >= 5:
                return

            info = await parseGameInfoByGameflowSession(
                session, currentSummonerId, "ally", useSGP=True)

            self.gameInfoInterface.allyChampions = {}
            self.gameInfoInterface.allyOrder = []

            self.gameInfoInterface.summonersView.ally.clear()
            self.gameInfoInterface.allyGamesView.clear()

            self.gameInfoInterface.updateAllySummoners(info)

        # 将敌方的召唤师基本信息绘制上去
        async def paintEnemySummonersInfo():
            info = await parseGameInfoByGameflowSession(
                session, currentSummonerId, 'enemy', useSGP=True)

            # 这个 info 是已经按照游戏位置排序过的了（若排位）
            self.gameInfoInterface.updateEnemySummoners(info)

        # 更新己方召唤师楼层顺序至角色顺序
        async def sortAllySummonersByGameRole():
            order = getAllyOrderByGameRole(session, currentSummonerId)
            if order == None:
                return

            interface = self.gameInfoInterface

            if order == interface.allyOrder or len(order) != len(interface.allyOrder):
                return

            interface.summonersView.ally.updateSummonersOrder(order)
            interface.allyGamesView.updateOrder(order)
            interface.allyOrder = order

        # 绘制提示组队的颜色
        async def paintTeamColor():
            ally, enemy = getTeamColor(session, currentSummonerId)
            self.gameInfoInterface.updateTeamColor(ally, enemy)

        await paintAllySummonersInfo()
        await asyncio.gather(paintEnemySummonersInfo(),
                             sortAllySummonersByGameRole())
        await paintTeamColor()

        self.checkAndSwitchTo(self.gameInfoInterface)

    async def __onGameEnd(self):
        if not cfg.get(cfg.enableReserveGameinfo):
            self.gameInfoInterface.clear()

    def __checkWindowSize(self):
        if (dpi := self.devicePixelRatioF()) == 1.0:
            return

        w, h = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
        size: QSize = self.size() * dpi

        if size.width() < w and size.height() < h:
            return

        for scale in [2.0, 1.75, 1.5, 1.25, 1]:
            if scale * self.width() < w and scale * self.height() < h:
                cfg.set(cfg.dpiScale, scale)
                break

        self.splashScreen.finish()
        msg = ChangeDpiMessageBox(self.window())
        msg.exec()

    @asyncSlot(str)
    async def __onCareerGameClicked(self, gameId):
        name = self.careerInterface.getSummonerName()
        self.searchInterface.searchLineEdit.setText(name)

        # 从生涯页跳过来默认将筛选条件设置为全部 -- By Hpero4
        self.searchInterface.filterComboBox.setCurrentIndex(0)

        # 先加载完再切换, 避免加载过程中换搜索目标导致puuid出错 -- By Hpero4
        await self.searchInterface.searchAndShowFirstPage(self.careerInterface.puuid)
        self.checkAndSwitchTo(self.searchInterface)
        self.searchInterface.loadingGameId = gameId

        # 先画框再加载对局 否则快速切换(如筛选或换人)会导致找不到widget -- By Hpero4
        self.searchInterface.waitingForDrawSelect(gameId)
        await self.searchInterface.updateGameDetailView(gameId, self.careerInterface.puuid)

    def showOpggWindow(self):
        self.opggWindow.show()
        self.opggWindow.raise_()

    @asyncSlot()
    async def __refreshCareerInterface(self):
        if self.isClientProcessRunning:
            self.careerInterface.refreshButton.click()

    @asyncSlot()
    async def __cascadeSetMicaEffect(self):
        isMicaEnabled = cfg.get(cfg.micaEnabled)
        self.setMicaEffectEnabled(isMicaEnabled)
        self.opggWindow.setMicaEffectEnabled(isMicaEnabled)

    @asyncSlot()
    async def __onFixLCUButtonClicked(self):
        if self.isClientProcessRunning:
            await connector.playAgain()

    def exceptHook(self, ty, value, tb):
        tracebackFormat = traceback.format_exception(ty, value, tb)
        title = self.tr('Exception occurred 😥')
        content = "".join(tracebackFormat)

        if ty in [ConnectionRefusedError, ClientConnectorError]:
            return

        logger.error(f"Exception occurred:\n{content}", "Crash")

        for call in connector.callStack:
            logger.error(call, "Crash")

        logger.error(str(self.searchInterface), "Crash")
        logger.error(str(self.gameInfoInterface), "Crash")
        logger.error(str(self.careerInterface), "Crash")
        logger.error(str(self.auxiliaryFuncInterface), "Crash")
        logger.error(str(self.settingInterface), "Crash")

        content = f"Seraphine ver.{BETA or VERSION}\n{'-' * 5}\n{content}"

        w = ExceptionMessageBox(title, content, self.window())

        if w.exec():
            pyperclip.copy(content)

        self.oldHook(ty, value, tb)
        signalBus.terminateListeners.emit()
        logger.error("Abnormal exit", "Crash")
        sys.exit()

    def __onCurrentStackedChanged(self, index):
        widget: SmoothScrollArea = self.stackedWidget.view.currentWidget()
        widget.delegate.vScrollBar.resetValue(0)
