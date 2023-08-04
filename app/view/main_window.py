import os
import subprocess

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QImage
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, InfoBar, InfoBarPosition, qrouter,
                            )
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow

from .start_interface import StartInterface
from .setting_interface import SettingInterface
from .career_interface import CareerInterface
from .search_interface import SearchInterface
from .game_info_interface import GameInfoInterface
from .auxiliary_interface import AuxiliaryInterface
from ..common.style_sheet import StyleSheet
from ..components.avatar_widget import NavigationAvatarWidget
from ..components.title_bar import CustomTitleBar
from ..components.stacked_widget import StackedWidget
from ..common.icons import Icon
from ..common.config import cfg
from ..lol.entries import Summoner
from ..lol.listener import LolProcessExistenceListener, LolClientEventListener
from ..lol.connector import LolClientConnector
from ..lol.tools import processGameData, translateTier

import threading


class MainWindow(FramelessWindow):
    nameOrIconChanged = pyqtSignal(str, str)
    lolInstallFolderChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setTitleBar(CustomTitleBar(self))
        self.hBoxLayout = QHBoxLayout(self)
        self.widgetLayout = QHBoxLayout()

        self.stackWidget = StackedWidget(self)
        self.navigationInterface = NavigationInterface(self, True, True)

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
        self.rankInfo = {}
        self.games = {}

        self.lolConnector = LolClientConnector()

        # initialize layout
        self.__initLayout()

        # add items to navigation interface
        self.__initNavigation()

        self.__initWindow()

        self.__initListener()

    def __initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addLayout(self.widgetLayout)
        self.hBoxLayout.setStretchFactor(self.widgetLayout, 1)

        self.widgetLayout.addWidget(self.stackWidget)
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(
            self.titleBar.raise_)

    def __initNavigation(self):
        self.navigationInterface.addSeparator()

        self.__addSubInterface(
            self.startInterface, "startInterface", Icon.HOME, True, self.tr("Start"))
        self.__addSubInterface(
            self.careerInterface,
            "profileInterface",
            Icon.PERSON,
            False,
            self.tr("Career"),
        )
        self.__addSubInterface(
            self.searchInterface,
            "searchInterface",
            Icon.SEARCH,
            False,
            self.tr("Search"),
        )
        self.__addSubInterface(
            self.gameInfoInterface,
            "gameinfoInterface",
            Icon.GAME,
            False,
            self.tr("Game Information"),
        )
        self.__addSubInterface(
            self.auxiliaryFuncInterface,
            "auxiliaryFuncInterface",
            Icon.WRENCH,
            False,
            self.tr("Auxiliary Functions"),
        )

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

        self.__addSubInterface(
            self.settingInterface,
            "settingInterface",
            FIF.SETTING,
            True,
            self.tr("Settings"),
            NavigationItemPosition.BOTTOM,
        )

        #!IMPORTANT: don't forget to set the default route key
        qrouter.setDefaultRouteKey(
            self.stackWidget, self.startInterface.objectName())

        # set the maximum width
        # self.navigationInterface.setExpandWidth(300)

        self.stackWidget.currentWidgetChanged.connect(
            self.__onCurrentWidgetChanged)
        self.navigationInterface.setCurrentItem(
            self.startInterface.objectName())
        self.stackWidget.setCurrentIndex(0)

        self.careerInterface.searchButton.clicked.connect(
            self.__onCareerInterfaceHistoryButtonClicked)
        self.careerInterface.backToMeButton.clicked.connect(
            self.__onCareerInterfaceBackToMeButtonClicked)
        self.searchInterface.careerButton.clicked.connect(
            self.__onSearchInterfaceCareerButtonClicked)
        self.searchInterface.gamesView.gameDetailView.summonerNameClicked.connect(
            self.__onSearchInterfaceSummonerNameClicked)
        self.gameInfoInterface.summonerViewClicked.connect(
            self.__onSearchInterfaceSummonerNameClicked)
        self.gameInfoInterface.summonerGamesClicked.connect(
            self.__onGameInfoInterfaceGamesSummonerNameClicked)

    def __initWindow(self):
        self.resize(1134, 826)
        self.setMinimumSize(1134, 826)
        self.setWindowIcon(QIcon("app/resource/images/logo.png"))
        self.setWindowTitle("Seraphine")
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        # self.splashScreen = SplashScreen(self.windowIcon(), self)
        # self.splashScreen.setIconSize(QSize(106, 106))
        # self.splashScreen.raise_()

        StyleSheet.MAIN_WINDOW.apply(self)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        # self.show()
        # QApplication.processEvents()

    def __initListener(self):
        self.processListener.lolClientStarted.connect(
            self.__onLolClientStarted)
        self.processListener.lolClientEnded.connect(self.__onLolClientEnded)

        self.eventListener.currentSummonerProfileChanged.connect(
            self.__onCurrentSummonerProfileChanged)
        self.eventListener.matchMade.connect(self.__onMatchMade)
        self.eventListener.championSelectBegin.connect(
            self.__onChampionSelectBegin)
        self.eventListener.gameStart.connect(self.__onGameStart)
        self.eventListener.gameEnd.connect(self.__onGameEnd)

        self.nameOrIconChanged.connect(self.__onNameOrIconChanged)
        self.lolInstallFolderChanged.connect(self.__onLolInstallFolderChanged)

        self.processListener.start()

    def __changeCareerToCurrentSummoner(self):
        self.currentSummoner = Summoner(self.lolConnector.getCurrentSummoner())

        iconId = self.currentSummoner.profileIconId
        icon = self.lolConnector.getProfileIcon(iconId)
        name = self.currentSummoner.name
        level = self.currentSummoner.level
        xpSinceLastLevel = self.currentSummoner.xpSinceLastLevel
        xpUntilNextLevel = self.currentSummoner.xpUntilNextLevel

        self.rankInfo = self.lolConnector.getRankedStatsByPuuid(
            self.currentSummoner.puuid)
        gamesInfo = self.lolConnector.getSummonerGamesByPuuid(
            self.currentSummoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)

        self.games = {
            "gameCount": gamesInfo["gameCount"],
            "wins": 0,
            "losses": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "games": [],
        }

        for game in gamesInfo["games"]:
            info = processGameData(game, self.lolConnector)
            if not info["remake"] and info["queueId"] != 0:
                self.games["kills"] += info["kills"]
                self.games["deaths"] += info["deaths"]
                self.games["assists"] += info["assists"]
                if info["win"]:
                    self.games["wins"] += 1
                else:
                    self.games["losses"] += 1

            self.games["games"].append(info)

        self.nameOrIconChanged.emit(icon, name)
        self.careerInterface.careerInfoChanged.emit(
            name,
            icon,
            level,
            xpSinceLastLevel,
            xpUntilNextLevel,
            self.rankInfo,
            self.games,
            True,
        )

    def __onLolClientStarted(self):
        def _():
            self.lolConnector.start()
            self.isClientProcessRunning = True

            self.__changeCareerToCurrentSummoner()

            folder = self.lolConnector.getInstallFolder()

            if folder != cfg.get(cfg.lolFolder):
                self.lolInstallFolderChanged.emit(folder)

            self.eventListener.start()
            self.searchInterface.lolConnector = self.lolConnector
            self.searchInterface.gamesView.gamesTab.lolConnector = self.lolConnector
            self.auxiliaryFuncInterface.lolConnector = self.lolConnector
            self.auxiliaryFuncInterface.profileBackgroundCard.lolConnector = self.lolConnector
            self.auxiliaryFuncInterface.profileTierCard.lolConnector = self.lolConnector
            self.auxiliaryFuncInterface.onlineAvailabilityCard.lolConnector = self.lolConnector
            self.auxiliaryFuncInterface.removeTokensCard.lolConnector = self.lolConnector
            self.auxiliaryFuncInterface.createPracticeLobbyCard.lolConnector = self.lolConnector

            self.auxiliaryFuncInterface.profileBackgroundCard.updateCompleter()

        threading.Thread(target=_).start()
        self.__unlockNavigationAndSwitchToCareer()

    def __onLolClientEnded(self):
        def _():
            self.lolConnector.close()
            self.isClientProcessRunning = False

            self.currentSummoner = None
            icon = "app/resource/images/game.png"
            name = self.tr("Start LOL")
            self.nameOrIconChanged.emit(icon, name)
            self.careerInterface.careerInfoChanged.emit(self.tr(
                "Connecting..."), "app/resource/images/champion-0.png", -1, 0, 1, {}, {}, True)
            self.searchInterface.lolConnector = None
            self.searchInterface.gamesView.gamesTab.lolConnector = None
            self.auxiliaryFuncInterface.lolConnector = None
            self.auxiliaryFuncInterface.profileBackgroundCard.lolConnector = None
            self.auxiliaryFuncInterface.profileTierCard.lolConnector = None
            self.auxiliaryFuncInterface.onlineAvailabilityCard.lolConnector = None
            self.auxiliaryFuncInterface.removeTokensCard.lolConnector = None
            self.auxiliaryFuncInterface.createPracticeLobbyCard.lolConnector = None

        self.eventListener.exit()

        threading.Thread(target=_).start()

        self.__lockNavigationAndSwitchToStart()

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
            icon = self.lolConnector.getProfileIcon(iconId)
            level = self.currentSummoner.level
            xpSinceLastLevel = self.currentSummoner.xpSinceLastLevel
            xpUntilNextLevel = self.currentSummoner.xpUntilNextLevel

            self.nameOrIconChanged.emit(icon, name)
            self.careerInterface.careerInfoChanged.emit(
                name,
                icon,
                level,
                xpSinceLastLevel,
                xpUntilNextLevel,
                self.rankInfo,
                self.games,
                False,
            )

        threading.Thread(target=_).start()

    def __onAvatarWidgetClicked(self):
        if not self.isClientProcessRunning:
            path = f"{cfg.get(cfg.lolFolder)}/client.exe"
            if os.path.exists(path):
                subprocess.Popen(f'"{path}"')
                self.__showStartLolSuccessInfo()
            else:
                self.__showLolClientPathErrorInfo()
        else:
            self.careerInterface.backToMeButton.clicked.emit()
            self.__switchTo(self.careerInterface)

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
            content=f"--app-port: {self.lolConnector.port}\n--remoting-auth-token: {self.lolConnector.token}",
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=self,
        )

    def __addSubInterface(
        self,
        interface: QWidget,
        objectName: str,
        icon,
        selectable,
        text: str,
        position=NavigationItemPosition.TOP,
    ):
        """add sub interface"""
        interface.setObjectName(objectName)
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=objectName,
            icon=icon,
            text=text,
            onClick=lambda: self.__switchTo(interface),
            selectable=selectable,
            position=position,
            tooltip=text,
        )

    def __unlockNavigationAndSwitchToCareer(self):
        qrouter.setDefaultRouteKey(
            self.stackWidget, self.careerInterface.objectName())

        for item in self.navigationInterface.panel.items.values():
            if item.routeKey in [self.startInterface.objectName(), "avatar"]:
                item.widget.isSelectable = False
            else:
                item.widget.isSelectable = True

        self.navigationInterface.panel.widget(
            self.startInterface.objectName()).isSelected = False

        self.navigationInterface.repaint()

        self.navigationInterface.setCurrentItem(
            self.careerInterface.objectName())
        self.stackWidget.setCurrentIndex(1)

    def __lockNavigationAndSwitchToStart(self):
        qrouter.setDefaultRouteKey(
            self.stackWidget, self.startInterface.objectName())

        for item in self.navigationInterface.panel.items.values():
            item.widget.isSelected = False

            if item.routeKey in [
                self.startInterface.objectName(),
                self.settingInterface.objectName(),
            ]:
                item.widget.isSelectable = True
            else:
                item.widget.isSelectable = False

        self.navigationInterface.repaint()

        self.navigationInterface.setCurrentItem(
            self.startInterface.objectName())
        self.stackWidget.setCurrentIndex(0)

    def __switchTo(self, widget, triggerByUser=True):
        if self.navigationInterface.panel.widget(widget.objectName()).isSelectable:
            if widget is self.careerInterface:
                self.careerInterface.setTableStyle(cfg.theme)

            self.stackWidget.setCurrentWidget(widget, not triggerByUser)

    def __onCurrentWidgetChanged(self, widget: QWidget):
        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackWidget, widget.objectName())

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width() - 46, self.titleBar.height())

    def closeEvent(self, a0) -> None:
        self.processListener.terminate()

        return super().closeEvent(a0)

    def __onCareerInterfaceHistoryButtonClicked(self):
        summonerName = self.careerInterface.name.text()

        self.searchInterface.searchLineEdit.setText(summonerName)
        self.searchInterface.searchButton.clicked.emit()

        self.__switchTo(self.searchInterface)

    def __onGameInfoInterfaceGamesSummonerNameClicked(self, name):
        self.searchInterface.searchLineEdit.setText(name)
        self.searchInterface.searchButton.clicked.emit()

        self.__switchTo(self.searchInterface)

    def __onSearchInterfaceCareerButtonClicked(self):
        name = self.searchInterface.currentSummonerName

        def _():
            summoner = Summoner(self.lolConnector.getSummonerByName(name))
            iconId = summoner.profileIconId

            icon = self.lolConnector.getProfileIcon(iconId)
            level = summoner.level
            xpSinceLastLevel = summoner.xpSinceLastLevel
            xpUntilNextLevel = summoner.xpUntilNextLevel

            rankInfo = self.lolConnector.getRankedStatsByPuuid(summoner.puuid)
            gamesInfo = self.lolConnector.getSummonerGamesByPuuid(
                summoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)

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
                info = processGameData(game, self.lolConnector)

                if not info["remake"] and info["queueId"] != 0:
                    games["kills"] += info["kills"]
                    games["deaths"] += info["deaths"]
                    games["assists"] += info["assists"]

                    if info["win"]:
                        games["wins"] += 1
                    else:
                        games["losses"] += 1

                games["games"].append(info)

            self.careerInterface.careerInfoChanged.emit(
                name,
                icon,
                level,
                xpSinceLastLevel,
                xpUntilNextLevel,
                rankInfo,
                games,
                True,
            )

        threading.Thread(target=_).start()
        self.__switchTo(self.careerInterface)

    def __onCareerInterfaceBackToMeButtonClicked(self):
        threading.Thread(target=self.__changeCareerToCurrentSummoner).start()

    def __onSearchInterfaceSummonerNameClicked(self, puuid):
        if puuid == "00000000-0000-0000-0000-000000000000":
            return

        def _():
            try:
                summoner = Summoner(
                    self.lolConnector.getSummonerByPuuid(puuid))
            except:
                return

            iconId = summoner.profileIconId

            icon = self.lolConnector.getProfileIcon(iconId)
            level = summoner.level
            xpSinceLastLevel = summoner.xpSinceLastLevel
            xpUntilNextLevel = summoner.xpUntilNextLevel

            rankInfo = self.lolConnector.getRankedStatsByPuuid(summoner.puuid)
            gamesInfo = self.lolConnector.getSummonerGamesByPuuid(
                summoner.puuid, 0, cfg.get(cfg.careerGamesNumber) - 1)

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
                info = processGameData(game, self.lolConnector)

                if not info["remake"] and info["queueId"] != 0:
                    games["kills"] += info["kills"]
                    games["deaths"] += info["deaths"]
                    games["assists"] += info["assists"]

                    if info["win"]:
                        games["wins"] += 1
                    else:
                        games["losses"] += 1

                games["games"].append(info)

            self.careerInterface.careerInfoChanged.emit(
                summoner.name,
                icon,
                level,
                xpSinceLastLevel,
                xpUntilNextLevel,
                rankInfo,
                games,
                True,
            )

        threading.Thread(target=_).start()
        self.__switchTo(self.careerInterface)

    def __onMatchMade(self):
        if cfg.get(cfg.enableAutoAcceptMatching):
            threading.Thread(
                target=lambda: self.lolConnector.acceptMatchMaking()).start()

    def __onChampionSelectBegin(self, data):
        def _():
            summoners = []

            for item in data["myTeam"]:
                summonerId = item["summonerId"]
                summoner = self.lolConnector.getSummonerById(summonerId)

                iconId = summoner["profileIconId"]
                icon = self.lolConnector.getProfileIcon(iconId)

                puuid = summoner["puuid"]

                origRankInfo = self.lolConnector.getRankedStatsByPuuid(puuid)
                soloRankInfo = origRankInfo["queueMap"]["RANKED_SOLO_5x5"]
                flexRankInfo = origRankInfo["queueMap"]["RANKED_FLEX_SR"]

                soloTier = soloRankInfo["tier"]
                soloDivision = soloRankInfo["division"]

                if soloTier == "":
                    soloIcon = "app/resource/images/UNRANKED.svg"
                    soloTier = self.tr("Unranked")
                else:
                    soloIcon = f"app/resource/images/{soloTier}.svg"
                    soloTier = translateTier(soloTier, True)

                if soloDivision == "NA":
                    soloDivision = ""

                flexTier = flexRankInfo["tier"]
                flexDivision = flexRankInfo["division"]

                if flexTier == "":
                    flexIcon = "app/resource/images/UNRANKED.svg"
                    flexTier = self.tr("Unranked")
                else:
                    flexIcon = f"app/resource/images/{flexTier}.svg"
                    flexTier = translateTier(flexTier, True)

                if flexDivision == "NA":
                    flexDivision = ""

                rankInfo = {
                    "solo": {
                        "tier": soloTier,
                        "icon": soloIcon,
                        "division": soloDivision,
                        "lp": soloRankInfo["leaguePoints"],
                    },
                    "flex": {
                        "tier": flexTier,
                        "icon": flexIcon,
                        "division": flexDivision,
                        "lp": flexRankInfo["leaguePoints"],
                    },
                }

                origGamesInfo = self.lolConnector.getSummonerGamesByPuuid(
                    puuid, 0, 10)

                gamesInfo = [processGameData(
                    game, self.lolConnector) for game in origGamesInfo["games"]]

                summoners.append(
                    {
                        "name": summoner["displayName"],
                        "icon": icon,
                        "level": summoner["summonerLevel"],
                        "rankInfo": rankInfo,
                        "gamesInfo": gamesInfo,
                        "xpSinceLastLevel": summoner["xpSinceLastLevel"],
                        "xpUntilNextLevel": summoner["xpUntilNextLevel"],
                        "puuid": puuid,
                    }
                )

            self.gameInfoInterface.allySummonersInfoReady.emit(summoners)

        threading.Thread(target=_).start()

    def __onGameStart(self):
        def _():
            data = self.lolConnector.getGamePlayersInfo()['gameData']

            # 特判一下斗魂竞技场
            if data['queue']['id'] == 1700:
                return

            team1 = data['teamOne']
            team2 = data['teamTwo']
            enemies = None

            # 判断哪边是敌方队伍
            for summoner in team1:
                if summoner['puuid'] == self.currentSummoner.puuid:
                    enemies = team2
                    break

            if enemies == None:
                enemies = team1

            summoners = []

            # 跟 __onChampionSelectBegin 函数里面的处理方法一样，这里使用 puuid
            for item in enemies:
                puuid = item["puuid"]

                summoner = self.lolConnector.getSummonerByPuuid(puuid)

                iconId = summoner["profileIconId"]
                icon = self.lolConnector.getProfileIcon(iconId)

                origRankInfo = self.lolConnector.getRankedStatsByPuuid(puuid)
                soloRankInfo = origRankInfo["queueMap"]["RANKED_SOLO_5x5"]
                flexRankInfo = origRankInfo["queueMap"]["RANKED_FLEX_SR"]

                soloTier = soloRankInfo["tier"]
                soloDivision = soloRankInfo["division"]

                if soloTier == "":
                    soloIcon = "app/resource/images/UNRANKED.svg"
                    soloTier = self.tr("Unranked")
                else:
                    soloIcon = f"app/resource/images/{soloTier}.svg"
                    soloTier = translateTier(soloTier, True)

                if soloDivision == "NA":
                    soloDivision = ""

                flexTier = flexRankInfo["tier"]
                flexDivision = flexRankInfo["division"]

                if flexTier == "":
                    flexIcon = "app/resource/images/UNRANKED.svg"
                    flexTier = self.tr("Unranked")
                else:
                    flexIcon = f"app/resource/images/{flexTier}.svg"
                    flexTier = translateTier(flexTier, True)

                if flexDivision == "NA":
                    flexDivision = ""

                rankInfo = {
                    "solo": {
                        "tier": soloTier,
                        "icon": soloIcon,
                        "division": soloDivision,
                        "lp": soloRankInfo["leaguePoints"],
                    },
                    "flex": {
                        "tier": flexTier,
                        "icon": flexIcon,
                        "division": flexDivision,
                        "lp": flexRankInfo["leaguePoints"],
                    },
                }

                origGamesInfo = self.lolConnector.getSummonerGamesByPuuid(
                    puuid, 0, 10)

                gamesInfo = [processGameData(
                    game, self.lolConnector) for game in origGamesInfo["games"]]

                summoners.append(
                    {
                        "name": summoner["displayName"],
                        "icon": icon,
                        "level": summoner["summonerLevel"],
                        "rankInfo": rankInfo,
                        "gamesInfo": gamesInfo,
                        "xpSinceLastLevel": summoner["xpSinceLastLevel"],
                        "xpUntilNextLevel": summoner["xpUntilNextLevel"],
                        "puuid": puuid,
                    }
                )

            self.gameInfoInterface.enemySummonerInfoReady.emit(summoners)

        threading.Thread(target=_).start()

    def __onGameEnd(self):
        threading.Thread(
            target=lambda: self.gameInfoInterface.gameEnd.emit()).start()
