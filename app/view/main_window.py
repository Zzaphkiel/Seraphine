import json
import os
import sys
import traceback
import time
import webbrowser
from collections import Counter

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QAbstractAnimation
from PyQt5.QtGui import QIcon, QImage, QCursor
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from qfluentwidgets import (NavigationItemPosition, InfoBar, InfoBarPosition, Action,
                            FluentWindow, SplashScreen, MessageBox, SmoothScrollArea,
                            ToolTipFilter)
from qfluentwidgets import FluentIcon as FIF
import pyperclip

from .start_interface import StartInterface
from .setting_interface import SettingInterface
from .career_interface import CareerInterface
from .search_interface import SearchInterface
from .game_info_interface import GameInfoInterface
from .auxiliary_interface import AuxiliaryInterface
from ..common.util import Github, github
from ..components.avatar_widget import NavigationAvatarWidget
from ..components.temp_system_tray_menu import TmpSystemTrayMenu
from ..common.icons import Icon
from ..common.config import cfg, VERSION
from ..components.update_message_box import UpdateMessageBox
from ..lol.entries import Summoner
from ..lol.exceptions import SummonerGamesNotFound, RetryMaximumAttempts, SummonerNotFound, SummonerNotInGame
from ..lol.listener import (LolProcessExistenceListener, LolClientEventListener,
                            getLolProcessPid)
from ..lol.connector import connector
from ..lol.tools import (processGameData, translateTier, getRecentChampions,
                         processRankInfo, getTeammates, assignTeamId, parseGames)

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class MainWindow(FluentWindow):
    nameOrIconChanged = pyqtSignal(str, str)
    lolInstallFolderChanged = pyqtSignal(str)
    showUpdateMessageBox = pyqtSignal(dict)
    checkUpdateFailed = pyqtSignal()
    showLcuConnectError = pyqtSignal(str, BaseException)

    def __init__(self):
        super().__init__()

        self.__initWindow()
        self.__initSystemTray()

        # create sub interface
        self.startInterface = StartInterface(self)
        self.careerInterface = CareerInterface(self)
        self.searchInterface = SearchInterface(self)
        self.gameInfoInterface = GameInfoInterface(self)
        self.auxiliaryFuncInterface = AuxiliaryInterface(self)
        self.settingInterface = SettingInterface(self)

        # crate listener

        self.isClientProcessRunning = False
        self.processListener = LolProcessExistenceListener(self)
        self.eventListener = LolClientEventListener(self)

        self.currentSummoner: Summoner = None

        self.isGaming = False
        self.isTrayExit = False
        self.isChampSelected = False

        self.__initInterface()
        self.__initNavigation()
        self.__initListener()
        self.__conncetSignalToSlot()

        self.splashScreen.finish()
        threading.Thread(target=self.checkUpdate).start()
        threading.Thread(target=self.pollingConnectTimeout,
                         daemon=True).start()

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

        self.navigationInterface.addSeparator()

        # add custom widget to bottom
        self.avatarWidget = NavigationAvatarWidget(
            avatar="app/resource/images/game.png", name=self.tr("Start LOL"))
        self.navigationInterface.addWidget(
            routeKey="avatar",
            widget=self.avatarWidget,
            onClick=self.__onAvatarWidgetClicked,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(
            self.settingInterface, FIF.SETTING,
            self.tr("Settings"), NavigationItemPosition.BOTTOM,
        )

        # set the maximum width
        self.navigationInterface.setExpandWidth(250)

    def __conncetSignalToSlot(self):
        self.processListener.lolClientStarted.connect(
            self.__onLolClientStarted)
        self.processListener.lolClientEnded.connect(self.__onLolClientEnded)

        self.eventListener.currentSummonerProfileChanged.connect(
            self.__onCurrentSummonerProfileChanged)

        self.eventListener.gameStatusChanged.connect(
            self.__onGameStatusChanged)

        self.eventListener.champSelectChanged.connect(
            self.__onChampSelectChanged
        )

        self.nameOrIconChanged.connect(self.__onNameOrIconChanged)
        self.lolInstallFolderChanged.connect(self.__onLolInstallFolderChanged)
        self.showUpdateMessageBox.connect(self.__onShowUpdateMessageBox)
        self.checkUpdateFailed.connect(self.__onCheckUpdateFailed)
        self.showLcuConnectError.connect(self.__onShowLcuConnectError)

        self.careerInterface.searchButton.clicked.connect(
            self.__onCareerInterfaceHistoryButtonClicked)
        self.careerInterface.backToMeButton.clicked.connect(
            self.__onCareerInterfaceBackToMeButtonClicked)
        self.careerInterface.summonerNameClicked.connect(
            self.__onTeammateFlyoutSummonerNameClicked)
        self.careerInterface.gameInfoBarClicked.connect(
            self.__onCareerInterfaceGameInfoBarClicked)
        self.careerInterface.refreshButton.clicked.connect(
            self.__onCareerInterfaceRefreshButtonClicked)
        self.searchInterface.careerButton.clicked.connect(
            self.__onSearchInterfaceCareerButtonClicked)
        self.searchInterface.gamesView.gameDetailView.summonerNameClicked.connect(
            self.__onSearchInterfaceSummonerNameClicked)
        self.gameInfoInterface.summonerViewClicked.connect(
            self.__onSearchInterfaceSummonerNameClicked)
        self.gameInfoInterface.summonerGamesClicked.connect(
            self.__onGameInfoInterfaceGamesSummonerNameClicked)
        self.gameInfoInterface.pageSwitchSignal.connect(
            self.__onGameInfoPageSwitch)
        self.settingInterface.careerGamesCount.pushButton.clicked.connect(
            self.__onCareerInterfaceRefreshButtonClicked)
        self.settingInterface.micaCard.checkedChanged.connect(
            self.setMicaEffectEnabled)
        self.stackedWidget.currentChanged.connect(
            self.__onCurrentStackedChanged)

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

        cfg.themeChanged.connect(
            lambda: self.setMicaEffectEnabled(self.isMicaEffectEnabled()))

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

        if cfg.get(cfg.enableStartLolWithApp):
            if getLolProcessPid() == 0:
                self.__startLolClient()

        self.oldHook = sys.excepthook
        sys.excepthook = self.exceptHook

    def __onShowLcuConnectError(self, api, obj):
        if type(obj) is SummonerGamesNotFound:
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

    def checkUpdate(self):
        if cfg.get(cfg.enableCheckUpdate):
            try:
                releasesInfo = github.checkUpdate()
            except:
                self.checkUpdateFailed.emit()
            else:
                if releasesInfo:
                    self.showUpdateMessageBox.emit(releasesInfo)

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

    def __onShowUpdateMessageBox(self, info):
        msgBox = UpdateMessageBox(info, self.window())
        if msgBox.exec():
            webbrowser.open(info.get("zipball_url"))

    def pollingConnectTimeout(self):
        while True:
            if connector.exceptApi:
                self.showLcuConnectError.emit(
                    connector.exceptApi, connector.exceptObj)
                connector.exceptApi = None
                connector.exceptObj = None

            time.sleep(.5)

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

    def __initListener(self):
        self.processListener.start()

    def __changeCareerToCurrentSummoner(self):
        self.careerInterface.showLoadingPage.emit()
        self.currentSummoner = Summoner(connector.getCurrentSummoner())

        iconId = self.currentSummoner.profileIconId
        icon = connector.getProfileIcon(iconId)
        name = self.currentSummoner.name
        level = self.currentSummoner.level
        xpSinceLastLevel = self.currentSummoner.xpSinceLastLevel
        xpUntilNextLevel = self.currentSummoner.xpUntilNextLevel

        self.careerInterface.currentSummonerName = name

        rankInfo = connector.getRankedStatsByPuuid(
            self.currentSummoner.puuid)

        try:
            gamesInfo = connector.getSummonerGamesByPuuid(
                self.currentSummoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)
        except SummonerGamesNotFound:
            champions = []
            games = {}
        else:
            games = {
                "gameCount": gamesInfo["gameCount"],
                "wins": 0,
                "losses": 0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
                "games": [],
            }

            for game in gamesInfo["games"]:
                info = processGameData(game)
                if not info["remake"] and info["queueId"] != 0:
                    games["kills"] += info["kills"]
                    games["deaths"] += info["deaths"]
                    games["assists"] += info["assists"]

                    if info["win"]:
                        games["wins"] += 1
                    else:
                        games["losses"] += 1

                games["games"].append(info)

            champions = getRecentChampions(games['games'])

        self.nameOrIconChanged.emit(icon, name)
        emitInfo = {
            'name': name,
            'icon': icon,
            'level': level,
            'xpSinceLastLevel': xpSinceLastLevel,
            'xpUntilNextLevel': xpUntilNextLevel,
            'puuid': self.currentSummoner.puuid,
            'rankInfo': rankInfo,
            'games': games,
            'champions': champions,
            'triggerByUser': True,
        }
        if champions:
            emitInfo["champions"] = champions

        self.careerInterface.careerInfoChanged.emit(emitInfo)
        self.careerInterface.hideLoadingPage.emit()

    def __onLolClientStarted(self, pid):
        def _():
            connector.start(pid)
            self.isClientProcessRunning = True

            self.__changeCareerToCurrentSummoner()

            self.startInterface.hideLoadingPage.emit(
                connector.port, connector.token)
            self.careerInterface.hideLoadingPage.emit()

            folder = connector.getInstallFolder()

            if folder != cfg.get(cfg.lolFolder):
                self.lolInstallFolderChanged.emit(folder)

            self.eventListener.start()

            self.auxiliaryFuncInterface.profileBackgroundCard.updateCompleter()
            self.auxiliaryFuncInterface.autoSelectChampionCard.updateCompleter()
            self.auxiliaryFuncInterface.lockConfigCard.loadNowMode.emit()

            status = connector.getGameStatus()
            self.eventListener.gameStatusChanged.emit(status)

        threading.Thread(target=_).start()
        self.checkAndSwitchTo(self.careerInterface)
        self.__unlockInterface()

    def __onLolClientEnded(self):
        def _():
            self.searchInterface.loadGamesThreadStop.set()  # 停掉战绩查询加载

            connector.close()
            self.isClientProcessRunning = False

            self.currentSummoner = None
            self.careerInterface.setCurrentSummonerName(None)

            icon = "app/resource/images/game.png"
            name = self.tr("Start LOL")

            self.nameOrIconChanged.emit(icon, name)

            self.startInterface.showLoadingPage.emit()
            self.careerInterface.showLoadingPage.emit()

        self.eventListener.terminate()
        self.setWindowTitle("Seraphine")

        threading.Thread(target=_).start()
        self.checkAndSwitchTo(self.startInterface)
        self.__lockInterface()

    def __onNameOrIconChanged(self, icon: str, name: str):
        self.avatarWidget.avatar = QImage(icon).scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatarWidget.name = name

        self.avatarWidget.repaint()

    def __onLolInstallFolderChanged(self, folder: str):
        folder = folder.replace("\\", "/")
        folder = folder.replace("LeagueClient", "TCLS")
        folder = f"{folder[:1].upper()}{folder[1:]}"

        cfg.set(cfg.lolFolder, folder)

        self.settingInterface.lolFolderCard.setContent(folder)
        self.settingInterface.lolFolderCard.repaint()

    def __onCurrentSummonerProfileChanged(self, data: dict):
        self.currentSummoner = Summoner(data)

        def _():
            name = self.currentSummoner.name

            iconId = self.currentSummoner.profileIconId
            icon = connector.getProfileIcon(iconId)
            level = self.currentSummoner.level
            xpSinceLastLevel = self.currentSummoner.xpSinceLastLevel
            xpUntilNextLevel = self.currentSummoner.xpUntilNextLevel

            self.nameOrIconChanged.emit(icon, name)
            self.careerInterface.IconLevelExpChanged.emit(
                {'name': name,
                 'icon': icon,
                 'level': level,
                 'xpSinceLastLevel': xpSinceLastLevel,
                 'xpUntilNextLevel': xpUntilNextLevel,
                 }
            )

        threading.Thread(target=_).start()

    def __startLolClient(self):
        path = f"{cfg.get(cfg.lolFolder)}/client.exe"
        if os.path.exists(path):
            os.popen(f'"{path}"')
            self.__showStartLolSuccessInfo()
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

    def __showConnectLolSuccessInfo(self):
        InfoBar.success(
            title=self.tr("LOL Client has been connected"),
            content=f"--app-port: {connector.port}\n--remoting-auth-token: {connector.token}",
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
        # pass

    def closeEvent(self, a0) -> None:

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
            self.processListener.terminate()
            self.eventListener.terminate()
            return super().closeEvent(a0)
        else:
            a0.ignore()
            self.hide()

    def __onCareerInterfaceHistoryButtonClicked(self):
        summonerName = self.careerInterface.name.text()

        self.searchInterface.searchLineEdit.setText(summonerName)
        self.searchInterface.searchLineEdit.searchButton.clicked.emit()

        self.checkAndSwitchTo(self.searchInterface)

    def __onGameInfoInterfaceGamesSummonerNameClicked(self, name):
        self.searchInterface.searchLineEdit.setText(name)
        self.searchInterface.searchLineEdit.searchButton.clicked.emit()

        self.checkAndSwitchTo(self.searchInterface)

    def __onGameInfoPageSwitch(self):
        if self.gameInfoInterface.pageState == 1:
            self.gameInfoInterface.pageState = 2
        else:
            self.gameInfoInterface.pageState = 1

    def __onSearchInterfaceCareerButtonClicked(self):
        self.careerInterface.showLoadingPage.emit()
        name = self.searchInterface.currentSummonerName

        def _():
            summoner = Summoner(connector.getSummonerByName(name))
            iconId = summoner.profileIconId

            icon = connector.getProfileIcon(iconId)
            level = summoner.level
            xpSinceLastLevel = summoner.xpSinceLastLevel
            xpUntilNextLevel = summoner.xpUntilNextLevel

            rankInfo = connector.getRankedStatsByPuuid(summoner.puuid)

            try:
                gamesInfo = connector.getSummonerGamesByPuuid(
                    summoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)
            except SummonerGamesNotFound:
                champions = []
                games = {}
            else:
                games = {
                    "gameCount": gamesInfo["gameCount"],
                    "wins": 0,
                    "losses": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "games": [],
                }

                for game in gamesInfo["games"]:
                    info = processGameData(game)

                    if not info["remake"] and info["queueId"] != 0:
                        games["kills"] += info["kills"]
                        games["deaths"] += info["deaths"]
                        games["assists"] += info["assists"]

                        if info["win"]:
                            games["wins"] += 1
                        else:
                            games["losses"] += 1

                    games["games"].append(info)

                champions = getRecentChampions(games['games'])

            emitInfo = {
                'name': name,
                'icon': icon,
                'level': level,
                'xpSinceLastLevel': xpSinceLastLevel,
                'xpUntilNextLevel': xpUntilNextLevel,
                'puuid': summoner.puuid,
                'rankInfo': rankInfo,
                'games': games,
                'triggerByUser': True,
            }
            if champions:
                emitInfo["champions"] = champions

            self.careerInterface.careerInfoChanged.emit(emitInfo)
            self.careerInterface.hideLoadingPage.emit()

        threading.Thread(target=_).start()
        self.checkAndSwitchTo(self.careerInterface)

    def __onTeammateFlyoutSummonerNameClicked(self, name):
        self.careerInterface.w.close()
        self.careerInterface.showLoadingPage.emit()

        def _():
            summoner = Summoner(connector.getSummonerByName(name))
            iconId = summoner.profileIconId

            icon = connector.getProfileIcon(iconId)
            level = summoner.level
            xpSinceLastLevel = summoner.xpSinceLastLevel
            xpUntilNextLevel = summoner.xpUntilNextLevel

            rankInfo = connector.getRankedStatsByPuuid(summoner.puuid)
            try:
                gamesInfo = connector.getSummonerGamesByPuuid(
                    summoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)
            except SummonerGamesNotFound:
                champions = []
                games = {}
            else:
                games = {
                    "gameCount": gamesInfo["gameCount"],
                    "wins": 0,
                    "losses": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "games": [],
                }

                for game in gamesInfo["games"]:
                    info = processGameData(game)

                    if not info["remake"] and info["queueId"] != 0:
                        games["kills"] += info["kills"]
                        games["deaths"] += info["deaths"]
                        games["assists"] += info["assists"]

                        if info["win"]:
                            games["wins"] += 1
                        else:
                            games["losses"] += 1

                    games["games"].append(info)

                champions = getRecentChampions(games['games'])

            self.careerInterface.careerInfoChanged.emit(
                {'name': name,
                 'icon': icon,
                 'level': level,
                 'xpSinceLastLevel': xpSinceLastLevel,
                 'xpUntilNextLevel': xpUntilNextLevel,
                 'puuid': summoner.puuid,
                 'rankInfo': rankInfo,
                 'games': games,
                 'champions': champions,
                 'triggerByUser': True, }
            )
            self.careerInterface.hideLoadingPage.emit()

        threading.Thread(target=_).start()

    def __onCareerInterfaceBackToMeButtonClicked(self):
        threading.Thread(target=self.__changeCareerToCurrentSummoner).start()

    def __onSearchInterfaceSummonerNameClicked(self, puuid, switch=True):
        if puuid == "00000000-0000-0000-0000-000000000000":
            return

        self.careerInterface.showLoadingPage.emit()

        def _():
            try:
                summoner = Summoner(
                    connector.getSummonerByPuuid(puuid))
            except:
                return

            iconId = summoner.profileIconId

            icon = connector.getProfileIcon(iconId)
            level = summoner.level
            xpSinceLastLevel = summoner.xpSinceLastLevel
            xpUntilNextLevel = summoner.xpUntilNextLevel

            rankInfo = connector.getRankedStatsByPuuid(summoner.puuid)
            try:
                gamesInfo = connector.getSummonerGamesByPuuid(
                    summoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)
            except SummonerGamesNotFound:
                champions = []
                games = {}
            else:
                games = {
                    "gameCount": gamesInfo["gameCount"],
                    "wins": 0,
                    "losses": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "games": [],
                }

                for game in gamesInfo["games"]:
                    info = processGameData(game)

                    if not info["remake"] and info["queueId"] != 0:
                        games["kills"] += info["kills"]
                        games["deaths"] += info["deaths"]
                        games["assists"] += info["assists"]

                        if info["win"]:
                            games["wins"] += 1
                        else:
                            games["losses"] += 1

                    games["games"].append(info)

                champions = getRecentChampions(games['games'])

            self.careerInterface.careerInfoChanged.emit(
                {'name': summoner.name,
                 'icon': icon,
                 'level': level,
                 'xpSinceLastLevel': xpSinceLastLevel,
                 'xpUntilNextLevel': xpUntilNextLevel,
                 'puuid': summoner.puuid,
                 'rankInfo': rankInfo,
                 'games': games,
                 'champions': champions,
                 'triggerByUser': True, }
            )
            self.careerInterface.hideLoadingPage.emit()

        threading.Thread(target=_).start()

        if switch:
            self.checkAndSwitchTo(self.careerInterface)

    def __onChampSelectChanged(self, data):
        for t in data["myTeam"]:
            if t['championId']:
                # 控件可能未绘制, 判断一下避免报错
                summonersView = self.gameInfoInterface.summonersView.allySummoners.items.get(
                    t["summonerId"])
                if summonersView:
                    if summonersView.nowIconId != t['championId']:  # 只有切换了才触发更新
                        championIconPath = connector.getChampionIcon(
                            t['championId'])
                        summonersView.updateIcon(championIconPath)

    def __onGameStatusChanged(self, status):
        title = None
        isGaming = False

        if status == 'None':
            title = self.tr("Home")
            self.__onGameEnd()
        elif status == 'ChampSelect':
            title = self.tr("Selecting Champions")

            # 在标题添加所处队伍
            mapSide = connector.getMapSide()
            if mapSide:
                mapSide = self.tr("Blue Team") if mapSide == "blue" else self.tr("Red Team")
                title = title + " - " + mapSide

            self.__onChampionSelectBegin()
            self.isChampSelected = True
        elif status == 'GameStart':
            title = self.tr("Gaming")
            self.__onGameStart()
            isGaming = True
        elif status == 'InProgress':
            title = self.tr("Gaming")
            # 重连或正常进入游戏(走GameStart), 不需要更新数据
            if not self.isGaming:
                self.__onGameStart()
            isGaming = True
        elif status == 'WaitingForStatus':
            title = self.tr("Waiting for status")
        elif status == 'EndOfGame':
            title = self.tr("End of game")
        elif status == 'Lobby':
            title = self.tr("Lobby")
            self.__onGameEnd()
            self.switchTo(self.careerInterface)
        elif status == 'ReadyCheck':
            title = self.tr("Ready check")
            self.__onMatchMade()
        elif status == 'Matchmaking':
            title = self.tr("Match making")
            self.__onGameEnd()
        elif status == "Reconnect":  # 等待重连
            title = self.tr("Waiting reconnect")
            self.__onReconnect()

        if not isGaming and self.isGaming:
            self.__updateCareerGames()

        self.isGaming = isGaming

        if title != None:
            self.setWindowTitle("Seraphine - " + title)

    def __onMatchMade(self):

        if cfg.get(cfg.enableAutoAcceptMatching):
            def _():
                timeDelay = cfg.get(cfg.autoAcceptMatchingDelay)
                time.sleep(timeDelay)

                status = connector.getReadyCheckStatus()

                if not status['playerResponse'] == 'Declined':
                    connector.acceptMatchMaking()

            threading.Thread(target=_).start()

    def __onReconnect(self):
        """
        自动重连
        @return:
        """
        if cfg.get(cfg.enableAutoReconnect):
            def _():
                while connector.getGameStatus() == "Reconnect":
                    time.sleep(.3)  # 掉线立刻重连会无效;
                    connector.reconnect()

            threading.Thread(target=_).start()

    # 英雄选择界面触发事件
    def __onChampionSelectBegin(self):

        def updateGameInfoInterface(callback=None):
            summoners = []
            data = connector.getChampSelectSession()

            isRank = bool(data["myTeam"][0]["assignedPosition"])  # 排位会有预选位

            def process_item(item):
                summonerId = item["summonerId"]

                if summonerId == 0:
                    return None

                summoner = connector.getSummonerById(summonerId)

                iconId = summoner["profileIconId"]
                icon = connector.getProfileIcon(iconId)

                puuid = summoner["puuid"]

                origRankInfo = connector.getRankedStatsByPuuid(puuid)
                rankInfo = processRankInfo(origRankInfo)

                try:
                    origGamesInfo = connector.getSummonerGamesByPuuid(
                        puuid, 0, 14)

                    if cfg.get(cfg.gameInfoFilter) and isRank:
                        origGamesInfo["games"] = [
                            game for game in origGamesInfo["games"] if game["queueId"] in (420, 440)]
                        begIdx = 15
                        while len(origGamesInfo["games"]) < 11:
                            endIdx = begIdx + 5
                            origGamesInfo["games"].extend([
                                game for game in connector.getSummonerGamesByPuuid(puuid, begIdx, endIdx)["games"]
                                if game["queueId"] in (420, 440)
                            ])
                            begIdx = endIdx + 1
                except SummonerGamesNotFound:
                    gamesInfo = []
                else:
                    gamesInfo = [processGameData(game)
                                 for game in origGamesInfo["games"][:11]]

                _, kill, deaths, assists, _, _ = parseGames(gamesInfo)

                teammatesInfo = [
                    getTeammates(
                        connector.getGameDetailByGameId(game["gameId"]),
                        puuid
                    ) for game in gamesInfo
                ]

                # 统计出现次数
                """
                teammatesCount = Counter({
                    (4018313666, '召唤师1'): 6, 
                    (4018314000, '召唤师2'): 3, 
                    (summonersId, name): cnt,
                    ...
                })
                """
                teammatesCount = Counter(
                    (summoner['summonerId'], summoner['name'])
                    for historyInfo in teammatesInfo
                    for summoner in historyInfo['summoners']
                )

                # 取当前游戏队友交集
                """
                teammatesMarker = [
                    {'summonerId': 4018314000, 'cnt': 3, 'name': "召唤师2"}, 
                    {'summonerId': summonerId, 'cnt': cnt, 'name': name}, 
                    ...
                ]
                """
                teammatesMarker = [
                    {'summonerId': sId, 'cnt': cnt, 'name': name}
                    for (sId, name), cnt in teammatesCount.items()
                    if sId in [x['summonerId'] for x in data['myTeam']] and cnt >= cfg.get(cfg.teamGamesNumber)
                ]

                return {
                    "name": summoner["displayName"],
                    "icon": icon,
                    "level": summoner["summonerLevel"],
                    "rankInfo": rankInfo,
                    "gamesInfo": gamesInfo,
                    "xpSinceLastLevel": summoner["xpSinceLastLevel"],
                    "xpUntilNextLevel": summoner["xpUntilNextLevel"],
                    "puuid": puuid,
                    "summonerId": summonerId,
                    "teammatesMarker": teammatesMarker,
                    "kda": [kill, deaths, assists],
                    "cellId": item["cellId"]
                }

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_item, item)
                           for item in data["myTeam"]]

            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    summoners.append(result)

            assignTeamId(summoners)

            sorted(summoners, key=lambda x: x["cellId"])  # 按照选用顺序排序

            self.gameInfoInterface.allySummonersInfoReady.emit(
                {'summoners': summoners})

            if callback:
                callback()

            # if cfg.get(cfg.enableCopyPlayersInfo):
            #     msg = self.gameInfoInterface.getPlayersInfoSummary()
            #     pyperclip.copy(msg)

        threading.Thread(target=updateGameInfoInterface, args=(
            lambda: self.switchTo(self.gameInfoInterface),)).start()

        def selectChampion():
            champion = cfg.get(cfg.autoSelectChampion)
            championId = connector.manager.getChampionIdByName(
                champion)
            connector.selectChampion(championId)

        if cfg.get(cfg.enableAutoSelectChampion):
            threading.Thread(target=selectChampion).start()

    def __onGameStart(self):
        def _(callback=None):
            session = connector.getGameflowSession()
            data = session['gameData']
            queueId = data['queue']['id']
            # 特判一下斗魂竞技场

            if queueId in (1700, 1090, 1100):  # 斗魂 云顶匹配(排位)
                return

            team1 = data['teamOne']
            team2 = data['teamTwo']
            enemies = None
            allys = None

            # 判断哪边是敌方队伍
            for summoner in team1:
                if summoner['puuid'] == self.currentSummoner.puuid:
                    enemies = team2
                    allys = team1
                    break

            if enemies == None:
                enemies = team1
                allys = team2

            summoners = []

            def process_item(item, isAllys=False):
                # 跟 __onChampionSelectBegin 函数里面的处理方法一样，这里使用 puuid
                puuid = item.get("puuid")

                # AI是没有该字段的, 避免报错
                if not puuid:
                    return None

                if puuid == '00000000-0000-0000-0000-000000000000':
                    return None

                summoner = connector.getSummonerByPuuid(puuid)

                # iconId = summoner["profileIconId"]
                # icon = connector.getProfileIcon(iconId)

                championId = item.get("championId")
                championId = championId if championId != None else -1

                icon = connector.getChampionIcon(championId)

                origRankInfo = connector.getRankedStatsByPuuid(puuid)
                rankInfo = processRankInfo(origRankInfo)

                try:
                    origGamesInfo = connector.getSummonerGamesByPuuid(
                        puuid, 0, 14)

                    if cfg.get(cfg.gameInfoFilter) and queueId in (420, 440):
                        origGamesInfo["games"] = [
                            game for game in origGamesInfo["games"] if game["queueId"] in (420, 440)]
                        begIdx = 15
                        while len(origGamesInfo["games"]) < 11:
                            endIdx = begIdx + 5
                            origGamesInfo["games"].extend([
                                game for game in connector.getSummonerGamesByPuuid(puuid, begIdx, endIdx)["games"]
                                if game["queueId"] in (420, 440)
                            ])
                            begIdx = endIdx + 1
                except SummonerGamesNotFound:
                    gamesInfo = []
                else:
                    gamesInfo = [processGameData(game)
                                 for game in origGamesInfo["games"][0:11]]

                _, kill, deaths, assists, _, _ = parseGames(gamesInfo)

                teammatesInfo = [
                    getTeammates(
                        connector.getGameDetailByGameId(game["gameId"]),
                        puuid
                    ) for game in gamesInfo
                ]

                # 统计出现次数
                """
                teammatesCount = Counter({
                    (4018313666, '召唤师1'): 6, 
                    (4018314000, '召唤师2'): 3, 
                    (123456, '召唤师2'): 1, 
                    (summonersId, name): cnt,
                    ...
                })
                """
                teammatesCount = Counter(
                    (summoner['summonerId'], summoner['name'])
                    for historyInfo in teammatesInfo
                    for summoner in historyInfo['summoners']
                )

                # 取当前游戏队友交集
                """
                teammatesMarker = [
                    {'summonerId': 4018314000, 'cnt': 3, 'name': "召唤师2"}, 
                    {'summonerId': summonerId, 'cnt': cnt, 'name': name}, 
                    ...
                ]
                """
                teamMember = allys if isAllys else enemies
                teammatesMarker = [
                    {'summonerId': sId, 'cnt': cnt, 'name': name}
                    for (sId, name), cnt in teammatesCount.items()
                    if sId in [x.get('summonerId') for x in teamMember] and cnt >= cfg.get(cfg.teamGamesNumber)
                ]

                # FIXME 非排位模式中, selectedPosition 值为 "NONE"
                return {
                    "name": summoner["displayName"],
                    "icon": icon,
                    "level": summoner["summonerLevel"],
                    "rankInfo": rankInfo,
                    "gamesInfo": gamesInfo,
                    "xpSinceLastLevel": summoner["xpSinceLastLevel"],
                    "xpUntilNextLevel": summoner["xpUntilNextLevel"],
                    "puuid": puuid,
                    "summonerId": summoner["summonerId"],
                    "teammatesMarker": teammatesMarker,
                    "kda": [kill, deaths, assists],
                    "order": ("TOP", "JUNGLE", "MIDDLE", "UTILITY", "BOTTOM").index(item['selectedPosition'])  # 上野中辅下
                }

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_item, item)
                           for item in enemies]

            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    summoners.append(result)

            assignTeamId(summoners)

            sorted(summoners, key=lambda x: x["order"])  # 按照 上野中辅下 排序

            if not self.isChampSelected:
                allySummoners = []
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(process_item, item, True)
                               for item in allys]

                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        allySummoners.append(result)

                assignTeamId(allySummoners)

                sorted(allySummoners, key=lambda x: x["order"])  # 按照 上野中辅下 排序

                self.gameInfoInterface.allySummonersInfoReady.emit(
                    {'summoners': allySummoners})
            else:
                res = {
                    item["summonerId"]: ("TOP", "JUNGLE", "MIDDLE", "UTILITY", "BOTTOM").index(item['selectedPosition'])
                    for item in allys
                }
                # TODO
                #  给队友页发信号重新绘制排序后的页面
                #  信号: dict[SummonerId,order]
                #  槽函数接收到信号后重新绘制页面
                #  该信号槽与BP阶段交换位置所触发的事件共用
                #

            self.gameInfoInterface.enemySummonerInfoReady.emit(
                {'summoners': summoners, 'queueId': queueId})

            if callback:
                callback()

            # if cfg.get(cfg.enableCopyPlayersInfo):
            #     msg = self.gameInfoInterface.getPlayersInfoSummary()
            #     pyperclip.copy(msg)

        threading.Thread(target=_, args=(
            lambda: self.switchTo(self.gameInfoInterface),)).start()

    def __onGameEnd(self):
        threading.Thread(
            target=lambda: self.gameInfoInterface.gameEnd.emit()).start()

    def __updateCareerGames(self):
        if not self.careerInterface.isCurrentSummoner():
            return

        def _():
            # 游戏刚出来可能接口返回的信息没刷新，手动让它睡个几秒
            time.sleep(7)
            self.__changeCareerToCurrentSummoner()

        threading.Thread(target=_).start()

    def __onCareerInterfaceGameInfoBarClicked(self, gameId):
        name = self.careerInterface.name.text()
        self.searchInterface.searchLineEdit.setText(name)
        self.searchInterface.gamesView.gamesTab.triggerGameId = gameId
        self.searchInterface.searchLineEdit.searchButton.click()

    def __onCareerInterfaceRefreshButtonClicked(self):
        self.__onSearchInterfaceSummonerNameClicked(
            self.careerInterface.puuid, switch=False)

    def exceptHook(self, ty, value, tb):
        tracebackFormat = traceback.format_exception(ty, value, tb)
        title = self.tr('Exception occurred 😥')
        content = "".join(tracebackFormat)

        w = MessageBox(title, content, self.window())

        w.yesButton.setText(self.tr('Copy to clipboard'))
        w.cancelButton.setText(self.tr('Cancel'))

        if w.exec():
            pyperclip.copy(content)

        self.oldHook(ty, value, tb)

    def __onCurrentStackedChanged(self, index):
        # if index == self.stackedWidget.indexOf(self.careerInterface):
        #     self.careerInterface.setTableStyle()

        widget: SmoothScrollArea = self.stackedWidget.view.currentWidget()
        widget.delegate.vScrollBar.resetValue(0)
