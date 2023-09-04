import os
import sys
import traceback

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QImage
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (NavigationItemPosition, InfoBar, InfoBarPosition,
                            FluentWindow, SplashScreen, MessageBox)
from qfluentwidgets import FluentIcon as FIF
import pyperclip

from .start_interface import StartInterface
from .setting_interface import SettingInterface
from .career_interface import CareerInterface
from .search_interface import SearchInterface
from .game_info_interface import GameInfoInterface
from .auxiliary_interface import AuxiliaryInterface
from ..components.avatar_widget import NavigationAvatarWidget
from ..common.icons import Icon
from ..common.config import cfg
from ..lol.entries import Summoner
from ..lol.listener import (LolProcessExistenceListener, LolClientEventListener,
                            getLolProcessPid)
from ..lol.connector import connector
from ..lol.tools import (processGameData, translateTier, getRecentChampions,
                         processRankInfo)

import threading


class MainWindow(FluentWindow):
    nameOrIconChanged = pyqtSignal(str, str)
    lolInstallFolderChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.__initWindow()

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

        self.__initInterface()

        # add items to navigation interface
        self.__initNavigation()

        self.__initListener()

        self.splashScreen.finish()

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

        self.careerInterface.searchButton.clicked.connect(
            self.__onCareerInterfaceHistoryButtonClicked)
        self.careerInterface.backToMeButton.clicked.connect(
            self.__onCareerInterfaceBackToMeButtonClicked)
        self.careerInterface.summonerNameClicked.connect(
            self.__onTeammateFlyoutSummonerNameClicked)
        self.careerInterface.gameInfoBarClicked.connect(
            self.__onCareerInterfaceGameInfoBarClicked)
        self.searchInterface.careerButton.clicked.connect(
            self.__onSearchInterfaceCareerButtonClicked)
        self.searchInterface.gamesView.gameDetailView.summonerNameClicked.connect(
            self.__onSearchInterfaceSummonerNameClicked)
        self.gameInfoInterface.summonerViewClicked.connect(
            self.__onSearchInterfaceSummonerNameClicked)
        self.gameInfoInterface.summonerGamesClicked.connect(
            self.__onGameInfoInterfaceGamesSummonerNameClicked)
        self.settingInterface.micaCard.checkedChanged.connect(
            self.setMicaEffectEnabled)
        widget = self.navigationInterface.widget(
            self.careerInterface.objectName())
        widget.clicked.connect(self.careerInterface.setTableStyle)

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
                self.startInterface.pushButton.click()

        self.oldHook = sys.excepthook
        sys.excepthook = self.exceptHook

    def __initListener(self):
        self.processListener.lolClientStarted.connect(
            self.__onLolClientStarted)
        self.processListener.lolClientEnded.connect(self.__onLolClientEnded)

        self.eventListener.currentSummonerProfileChanged.connect(
            self.__onCurrentSummonerProfileChanged)

        self.eventListener.gameStatusChanged.connect(
            self.__onGameStatusChanged)

        self.nameOrIconChanged.connect(self.__onNameOrIconChanged)
        self.lolInstallFolderChanged.connect(self.__onLolInstallFolderChanged)

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

        self.rankInfo = connector.getRankedStatsByPuuid(
            self.currentSummoner.puuid)
        gamesInfo = connector.getSummonerGamesByPuuid(
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
            info = processGameData(game)
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

        champions = getRecentChampions(self.games['games'])

        self.careerInterface.careerInfoChanged.emit(
            {'name': name,
             'icon': icon,
             'level': level,
             'xpSinceLastLevel': xpSinceLastLevel,
             'xpUntilNextLevel': xpUntilNextLevel,
             'puuid': self.currentSummoner.puuid,
             'rankInfo': self.rankInfo,
             'games': self.games,
             'champions': champions,
             'triggerByUser': True, }
        )
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

            status = connector.getGameStatus()
            self.eventListener.gameStatusChanged.emit(status)

        threading.Thread(target=_).start()
        self.checkAndSwitchTo(self.careerInterface)
        self.__unlockInterface()

    def __onLolClientEnded(self):
        def _():
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
            self.careerInterface.careerInfoChanged.emit(
                {'name': name,
                 'icon': icon,
                 'level': level,
                 'xpSinceLastLevel': xpSinceLastLevel,
                 'xpUntilNextLevel': xpUntilNextLevel,
                 'puuid': self.currentSummoner.puuid,
                 'rankInfo': self.rankInfo,
                 'games': self.games,
                 'triggerByUser': False, }
            )

        threading.Thread(target=_).start()

    def __onAvatarWidgetClicked(self):
        if not self.isClientProcessRunning:
            path = f"{cfg.get(cfg.lolFolder)}/client.exe"
            if os.path.exists(path):
                os.Popen(f'"{path}"')
                self.__showStartLolSuccessInfo()
            else:
                self.__showLolClientPathErrorInfo()
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
        self.processListener.terminate()
        self.eventListener.terminate()

        return super().closeEvent(a0)

    def __onCareerInterfaceHistoryButtonClicked(self):
        summonerName = self.careerInterface.name.text()

        self.searchInterface.searchLineEdit.setText(summonerName)
        self.searchInterface.searchButton.clicked.emit()

        self.checkAndSwitchTo(self.searchInterface)

    def __onGameInfoInterfaceGamesSummonerNameClicked(self, name):
        self.searchInterface.searchLineEdit.setText(name)
        self.searchInterface.searchButton.clicked.emit()

        self.checkAndSwitchTo(self.searchInterface)

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
            gamesInfo = connector.getSummonerGamesByPuuid(
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
            gamesInfo = connector.getSummonerGamesByPuuid(
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

    def __onSearchInterfaceSummonerNameClicked(self, puuid):
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
            gamesInfo = connector.getSummonerGamesByPuuid(
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
        self.checkAndSwitchTo(self.careerInterface)

    def __onGameStatusChanged(self, status):
        title = None

        if status == 'None':
            title = self.tr("Home")
            self.__onGameEnd()
        elif status == 'ChampSelect':
            title = self.tr("Selecting Champions")
            self.__onChampionSelectBegin()
        elif status == 'GameStart':
            title = self.tr("Gaming")
            self.__onGameStart()
        elif status == 'WaitingForStatus':
            title = self.tr("Waiting for status")
        elif status == 'EndOfGame':
            title = self.tr("End of game")

            # 到房间内才会清除上一局的玩家信息
            # self.__onGameEnd()
        elif status == 'Lobby':
            title = self.tr("Lobby")
            self.__onGameEnd()
        elif status == 'ReadyCheck':
            title = self.tr("Ready check")
            self.__onMatchMade()
        elif status == 'Matchmaking':
            title = self.tr("Match making")

        if title != None:
            self.setWindowTitle("Seraphine - " + title)

    def __onMatchMade(self):
        if cfg.get(cfg.enableAutoAcceptMatching):
            threading.Thread(
                target=lambda: connector.acceptMatchMaking()).start()

    # 英雄选择界面触发事件
    def __onChampionSelectBegin(self):

        def updateGameInfoInterface():
            summoners = []
            data = connector.getChampSelectSession()

            for item in data["myTeam"]:
                summonerId = item["summonerId"]

                if summonerId == 0:
                    continue

                summoner = connector.getSummonerById(summonerId)

                iconId = summoner["profileIconId"]
                icon = connector.getProfileIcon(iconId)

                puuid = summoner["puuid"]

                origRankInfo = connector.getRankedStatsByPuuid(puuid)
                rankInfo = processRankInfo(origRankInfo)

                origGamesInfo = connector.getSummonerGamesByPuuid(
                    puuid, 0, 10)

                gamesInfo = [processGameData(game)
                             for game in origGamesInfo["games"]]

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

            self.gameInfoInterface.allySummonersInfoReady.emit(
                {'summoners': summoners})

        threading.Thread(target=updateGameInfoInterface).start()

        def selectChampion():
            champion = cfg.get(cfg.autoSelectChampion)
            championId = connector.manager.getChampionIdByName(
                champion)
            connector.selectChampion(championId)

        if cfg.get(cfg.enableAutoSelectChampion):
            threading.Thread(target=selectChampion).start()

    def __onGameStart(self):
        def _():
            session = connector.getGameflowSession()
            data = session['gameData']
            queueId = data['queue']['id']
            # 特判一下斗魂竞技场

            if queueId == 1700:
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

                if puuid == '00000000-0000-0000-0000-000000000000':
                    continue

                summoner = connector.getSummonerByPuuid(puuid)

                iconId = summoner["profileIconId"]
                icon = connector.getProfileIcon(iconId)

                origRankInfo = connector.getRankedStatsByPuuid(puuid)
                rankInfo = processRankInfo(origRankInfo)

                origGamesInfo = connector.getSummonerGamesByPuuid(
                    puuid, 0, 10)

                gamesInfo = [processGameData(game)
                             for game in origGamesInfo["games"]]

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

            self.gameInfoInterface.enemySummonerInfoReady.emit(
                {'summoners': summoners, 'queueId': queueId})

            # if cfg.get(cfg.enableCopyPlayersInfo):
            #     msg = self.gameInfoInterface.getPlayersInfoSummary()
            #     pyperclip.copy(msg)

        threading.Thread(target=_).start()

    def __onGameEnd(self):
        threading.Thread(
            target=lambda: self.gameInfoInterface.gameEnd.emit()).start()

    def __onCareerInterfaceGameInfoBarClicked(self, gameId):
        name = self.careerInterface.name.text()
        self.searchInterface.searchLineEdit.setText(name)
        self.searchInterface.gamesView.gamesTab.triggerByButton = False
        self.searchInterface.gamesView.gamesTab.updatePuuid(
            self.careerInterface.puuid)
        self.searchInterface.gamesView.gamesTab.tabClicked.emit(gameId)

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
