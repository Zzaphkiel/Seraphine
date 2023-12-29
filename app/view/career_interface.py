import threading
import time
import typing
from PyQt5 import QtCore

import pyperclip
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QTableWidgetItem, QHeaderView,
                             QWidget, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import (ScrollArea, TableWidget, Theme, PushButton, ComboBox,
                            SmoothScrollArea, ToolTipFilter, setCustomStyleSheet,
                            ToolTipPosition, ToolButton, IndeterminateProgressRing,
                            Flyout, FlyoutViewBase, FlyoutAnimationType)

from ..components.profile_icon_widget import RoundAvatar
from ..components.game_infobar_widget import GameInfoBar
from ..components.champion_icon_widget import RoundIcon
from ..components.profile_level_icon_widget import RoundLevelAvatar
from ..components.summoner_name_button import SummonerName
from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..common.icons import Icon
from ..lol.connector import connector
from ..lol.entries import Summoner
from ..lol.tools import translateTier, getTeammates, parseGames


class NameLabel(QLabel):
    def text(self) -> str:
        return super().text().replace("🫣", '')


class TagLineLabel(QLabel):
    def text(self) -> str:
        return super().text().replace(" ", '')


class CareerInterface(SmoothScrollArea):
    careerInfoChanged = pyqtSignal(dict)
    showLoadingPage = pyqtSignal()
    hideLoadingPage = pyqtSignal()
    summonerNameClicked = pyqtSignal(str)
    gameInfoBarClicked = pyqtSignal(str)
    IconLevelExpChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentSummonerName = None
        self.puuid = None
        self.showTagLine = False

        self.vBoxLayout = QVBoxLayout(self)
        self.IconNameHBoxLayout = QHBoxLayout()
        self.nameLevelVLayout = QVBoxLayout()
        self.icon = RoundLevelAvatar('app/resource/images/champion-0.png',
                                     0,
                                     1,
                                     parent=self)
        self.name = NameLabel(self.tr("Connecting..."))
        self.tagLineLabel = TagLineLabel()
        self.copyButton = ToolButton(Icon.COPY)
        self.nameButtonLayout = QHBoxLayout()
        self.nameTagLineLayout = QVBoxLayout()

        self.buttonsLayout = QVBoxLayout()
        self.backToMeButton = PushButton(self.tr("Back to me"))
        self.refreshButton = PushButton(self.tr("Refresh"))
        self.searchButton = PushButton(self.tr("Game history"))

        self.tableLayout = QHBoxLayout()
        self.rankInfo = None
        self.rankTable = TableWidget(self)

        self.recentInfoHLayout = QHBoxLayout()
        self.recent20GamesLabel = QLabel(
            self.tr('Recent matches') + " " + self.tr('(Last') + " None " +
            self.tr('games)'))
        self.winsLabel = QLabel(self.tr("Wins:") + " None")
        self.lossesLabel = QLabel(self.tr("Losses:") + " None")
        self.kdaLabel = QLabel(self.tr("KDA:") + " None / None / None")
        self.championsCard = ChampionsCard()
        self.recentTeamButton = PushButton(self.tr("Recent teammates"))
        self.teammatesFlyout = TeammatesFlyOut()
        self.filterComboBox = ComboBox()

        self.gameInfoAreaLayout = QHBoxLayout()
        self.gameInfoArea = SmoothScrollArea()
        self.gameInfoLayout = QVBoxLayout()
        self.gameInfoWidget = QWidget()

        self.progressRing = IndeterminateProgressRing()

        self.games = []

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.tagLineLabel.setVisible(False)
        self.tagLineLabel.setAlignment(Qt.AlignCenter)

        self.copyButton.setFixedSize(26, 26)
        self.copyButton.setEnabled(False)
        self.copyButton.setToolTip(self.tr("Copy summoner name to ClipBoard"))
        self.copyButton.installEventFilter(
            ToolTipFilter(self.copyButton, 500, ToolTipPosition.TOP))

        self.name.setObjectName("name")
        self.tagLineLabel.setObjectName("tagLineLabel")
        self.nameLevelVLayout.setObjectName("nameLevelVLayout")

        self.recent20GamesLabel.setObjectName('rencent20GamesLabel')
        self.winsLabel.setObjectName('winsLabel')
        self.lossesLabel.setObjectName('lossesLabel')
        self.kdaLabel.setObjectName('kdaLabel')
        self.recentInfoHLayout.setObjectName("recentInfoHLayout")
        self.gameInfoArea.setObjectName('gameInfoArea')
        self.gameInfoWidget.setObjectName("gameInfoWidget")

        self.backToMeButton.setEnabled(False)

        self.recentTeamButton.setEnabled(True)

        self.rankTable.setRowCount(2)
        self.rankTable.setColumnCount(9)
        self.rankTable.verticalHeader().hide()
        self.rankTable.setWordWrap(False)
        self.rankTable.setHorizontalHeaderLabels([
            self.tr('Game Type'),
            self.tr('Total'),
            self.tr('Win Rate'),
            self.tr('Wins'),
            self.tr('Losses'),
            self.tr('Tier'),
            self.tr('LP'),
            self.tr("Highest tier"),
            self.tr("Previous end tier"),
        ])

        self.rankInfo = [[
            self.tr('Ranked Solo'),
        ], [
            self.tr('Ranked Flex'),
        ]]

        self.filterComboBox.addItems([
            self.tr('All'),
            self.tr('Normal'),
            self.tr("A.R.A.M."),
            self.tr("Ranked Solo"),
            self.tr("Ranked Flex")
        ])
        self.filterComboBox.setCurrentIndex(0)
        self.winsLabel.setToolTip(
            self.tr("Remakes or Customs do not count in statistics"))
        self.winsLabel.installEventFilter(
            ToolTipFilter(self.winsLabel, 500, ToolTipPosition.TOP))
        self.lossesLabel.setToolTip(
            self.tr("Remakes or Customs do not count in statistics"))
        self.lossesLabel.installEventFilter(
            ToolTipFilter(self.lossesLabel, 500, ToolTipPosition.TOP))
        self.kdaLabel.setToolTip(
            self.tr("Remakes or Customs do not count in statistics"))
        self.kdaLabel.installEventFilter(
            ToolTipFilter(self.kdaLabel, 500, ToolTipPosition.RIGHT))

        self.__updateTable()

        StyleSheet.CAREER_INTERFACE.apply(self)
        self.initTableStyle()

    def __initLayout(self):
        self.nameTagLineLayout.setContentsMargins(0, 0, 0, 0)
        self.nameTagLineLayout.addWidget(self.name)
        self.nameTagLineLayout.addWidget(self.tagLineLabel)
        self.nameTagLineLayout.setSpacing(0)

        self.nameButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.nameButtonLayout.addLayout(self.nameTagLineLayout)
        self.nameButtonLayout.addSpacing(5)
        self.nameButtonLayout.addWidget(self.copyButton)

        self.nameLevelVLayout.addSpacerItem(
            QSpacerItem(1, 25, QSizePolicy.Minimum, QSizePolicy.Fixed))
        self.nameLevelVLayout.addLayout(self.nameButtonLayout)
        # self.nameLevelVLayout.addWidget(self.level, alignment=Qt.AlignCenter)
        self.nameLevelVLayout.addSpacerItem(
            QSpacerItem(1, 25, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.recentInfoHLayout.setSpacing(20)
        self.recentInfoHLayout.addWidget(self.recent20GamesLabel,
                                         alignment=Qt.AlignCenter)
        self.recentInfoHLayout.addWidget(self.winsLabel,
                                         alignment=Qt.AlignCenter)
        self.recentInfoHLayout.addWidget(self.lossesLabel,
                                         alignment=Qt.AlignCenter)
        self.recentInfoHLayout.addWidget(self.kdaLabel,
                                         alignment=Qt.AlignCenter)
        self.recentInfoHLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.recentInfoHLayout.addWidget(
            self.championsCard, alignment=Qt.AlignCenter)
        self.recentInfoHLayout.addWidget(
            self.recentTeamButton, alignment=Qt.AlignCenter)
        self.recentInfoHLayout.addWidget(self.filterComboBox,
                                         alignment=Qt.AlignCenter)

        # 这俩玩意的高度居然不一样，看着难受，手动让它俩一样
        # 33 == self.filterComboBox.height()
        self.recentTeamButton.setFixedHeight(33)

        self.IconNameHBoxLayout.addSpacing(
            self.backToMeButton.sizeHint().width())
        self.IconNameHBoxLayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.IconNameHBoxLayout.addWidget(self.icon)
        self.IconNameHBoxLayout.addSpacing(20)
        self.IconNameHBoxLayout.addLayout(self.nameLevelVLayout)
        self.IconNameHBoxLayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.buttonsLayout.addWidget(self.backToMeButton)
        self.buttonsLayout.addWidget(self.refreshButton)
        self.buttonsLayout.addWidget(self.searchButton)
        self.IconNameHBoxLayout.addLayout(self.buttonsLayout)

        self.gameInfoWidget.setLayout(self.gameInfoLayout)
        self.gameInfoArea.setWidget(self.gameInfoWidget)
        self.gameInfoArea.setWidgetResizable(True)
        self.gameInfoArea.setViewportMargins(0, 0, 5, 0)

        self.vBoxLayout.addWidget(self.progressRing, alignment=Qt.AlignCenter)

        self.vBoxLayout.addLayout(self.IconNameHBoxLayout)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.rankTable)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addLayout(self.recentInfoHLayout)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.gameInfoArea)
        self.vBoxLayout.addSpacing(10)

        self.vBoxLayout.setContentsMargins(30, 32, 30, 20)

        self.__setLoadingPageEnabled(True)

    def __setLoadingPageEnabled(self, enable):
        self.gameInfoArea.delegate.vScrollBar.resetValue(0)
        self.gameInfoArea.verticalScrollBar().setSliderPosition(0)

        self.icon.setVisible(not enable)
        self.name.setVisible(not enable)
        self.copyButton.setVisible(not enable)
        self.refreshButton.setVisible(not enable)
        self.backToMeButton.setVisible(not enable)
        self.searchButton.setVisible(not enable)
        self.rankTable.setVisible(not enable)
        self.recent20GamesLabel.setVisible(not enable)
        self.filterComboBox.setVisible(not enable)
        self.championsCard.setVisible(not enable)
        self.recentTeamButton.setVisible(not enable)
        self.winsLabel.setVisible(not enable)
        self.lossesLabel.setVisible(not enable)
        self.kdaLabel.setVisible(not enable)
        self.winsLabel.setVisible(not enable)
        self.lossesLabel.setVisible(not enable)
        self.gameInfoArea.setVisible(not enable)
        self.tagLineLabel.setVisible(not enable and self.showTagLine)

        self.progressRing.setVisible(enable)

    def __updateTable(self):
        for i, line in enumerate(self.rankInfo):
            for j, data in enumerate(line):
                item = QTableWidgetItem(data)
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.rankTable.setItem(i, j, item)

        self.rankTable.resizeColumnsToContents()
        self.rankTable.resizeRowsToContents()
        # self.table.setFixedWidth(self.table.viewportSizeHint().width())
        self.rankTable.setFixedHeight(
            self.rankTable.viewportSizeHint().height() + 4)
        self.rankTable.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)

    def initTableStyle(self):
        light = '''
            QHeaderView::section:horizontal {
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.095);
            }

            QTableView {
                border: 1px solid rgba(0, 0, 0, 0.095); 
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.667);
            }
        '''

        dark = '''
            QHeaderView::section:horizontal {
                border: none;
                border-bottom: 1px solid rgb(35, 35, 35);
            }

            QTableView {
                border: 1px solid rgb(35, 35, 35); 
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.051);
            }
        '''

        setCustomStyleSheet(self.rankTable, light, dark)

    def __connectSignalToSlot(self):
        self.careerInfoChanged.connect(self.__onCareerInfoChanged)
        self.IconLevelExpChanged.connect(self.__onChangeIconLevelAndExp)
        self.filterComboBox.currentIndexChanged.connect(
            self.__onfilterComboBoxChanged)
        self.copyButton.clicked.connect(
            lambda: pyperclip.copy(self.getSummonerName()))

        self.hideLoadingPage.connect(
            lambda: self.__setLoadingPageEnabled(False))
        self.showLoadingPage.connect(
            lambda: self.__setLoadingPageEnabled(True))

        self.recentTeamButton.clicked.connect(
            self.__onRecentTeammatesButtonClicked)

    def __onChangeIconLevelAndExp(self, info):
        if not self.isCurrentSummoner():
            return

        name = info['name'] if info['isPublic'] else f"{info['name']}🫣"
        icon = info['icon']
        level = info['level']
        xpSinceLastLevel = info['xpSinceLastLevel']
        xpUntilNextLevel = info['xpUntilNextLevel']

        self.name.setText(name)
        levelStr = str(level) if level != -1 else "None"
        self.icon.updateIcon(icon, xpSinceLastLevel,
                             xpUntilNextLevel, levelStr)

    def __onCareerInfoChanged(self, info: dict):
        if not info['triggerByUser'] and not self.isCurrentSummoner():
            return

        name = info['name'] if info['isPublic'] else f"{info['name']}🫣"
        icon = info['icon']
        level = info['level']
        xpSinceLastLevel = info['xpSinceLastLevel']
        xpUntilNextLevel = info['xpUntilNextLevel']
        puuid = info['puuid']
        rankInfo = info['rankInfo']
        games = info['games']

        if info['tagLine'] != None:
            self.showTagLine = True
            self.tagLineLabel.setText(f"# {info['tagLine']}")

        levelStr = str(level) if level != -1 else "None"
        self.icon.updateIcon(icon, xpSinceLastLevel,
                             xpUntilNextLevel, levelStr)
        self.name.setText(name)

        self.puuid = puuid

        if 'queueMap' in rankInfo:
            soloRankInfo = rankInfo['queueMap']['RANKED_SOLO_5x5']
            soloTier = translateTier(soloRankInfo['tier'])
            soloDivision = soloRankInfo['division']
            if soloTier == '--' or soloDivision == 'NA':
                soloDivision = ""

            soloHighestTier = translateTier(soloRankInfo['highestTier'])
            soloHighestDivision = soloRankInfo['highestDivision']
            if soloHighestTier == '--' or soloHighestDivision == 'NA':
                soloHighestDivision = ""

            solxPreviousSeasonEndTier = translateTier(
                soloRankInfo['previousSeasonEndTier'])
            soloPreviousSeasonDivision = soloRankInfo[
                'previousSeasonEndDivision']
            if solxPreviousSeasonEndTier == '--' or soloPreviousSeasonDivision == 'NA':
                soloPreviousSeasonDivision = ""

            soloWins = soloRankInfo['wins']
            soloLosses = soloRankInfo['losses']
            soloTotal = soloWins + soloLosses
            soloWinRate = soloWins * 100 // soloTotal if soloTotal != 0 else 0
            soloLp = soloRankInfo['leaguePoints']

            flexRankInfo = rankInfo['queueMap']['RANKED_FLEX_SR']
            flexTier = translateTier(flexRankInfo['tier'])
            flexDivision = flexRankInfo['division']
            if flexTier == '--' or flexDivision == 'NA':
                flexDivision = ""

            flexHighestTier = translateTier(flexRankInfo['highestTier'])
            flexHighestDivision = flexRankInfo['highestDivision']
            if flexHighestTier == '--' or flexHighestDivision == 'NA':
                flexHighestDivision = ""

            flexPreviousSeasonEndTier = translateTier(
                flexRankInfo['previousSeasonEndTier'])
            flexPreviousSeasonEndDivision = flexRankInfo[
                'previousSeasonEndDivision']
            if flexPreviousSeasonEndTier == '--' or flexPreviousSeasonEndDivision == 'NA':
                flexPreviousSeasonEndDivision = ""

            flexWins = flexRankInfo['wins']
            flexLosses = flexRankInfo['losses']
            flexTotal = flexWins + flexLosses
            flexWinRate = flexWins * 100 // flexTotal if flexTotal != 0 else 0
            flexLp = flexRankInfo['leaguePoints']

            self.rankInfo = [
                [
                    self.tr('Ranked Solo'),
                    str(soloTotal),
                    str(soloWinRate) + ' %' if soloTotal != 0 else '--',
                    str(soloWins),
                    str(soloLosses),
                    f'{soloTier} {soloDivision}',
                    str(soloLp),
                    f'{soloHighestTier} {soloHighestDivision}',
                    f'{solxPreviousSeasonEndTier} {soloPreviousSeasonDivision}',
                ],
                [
                    self.tr('Ranked Flex'),
                    str(flexTotal),
                    str(flexWinRate) + ' %' if flexTotal != 0 else '--',
                    str(flexWins),
                    str(flexLosses),
                    f'{flexTier} {flexDivision}',
                    str(flexLp),
                    f'{flexHighestTier} {flexHighestDivision}',
                    f'{flexPreviousSeasonEndTier} {flexPreviousSeasonEndDivision}',
                ],
            ]

            self.copyButton.setEnabled(True)
        else:
            self.rankInfo = [[
                self.tr('Ranked Solo'),
            ], [
                self.tr('Ranked Flex'),
            ]]
            self.copyButton.setEnabled(False)

        if not self.isCurrentSummoner():
            for i in range(0, 2):
                for j in [1, 2, 4]:
                    self.rankInfo[i][j] = '--'

        self.__updateTable()

        if 'gameCount' in games:
            self.recent20GamesLabel.setText(
                f"{self.tr('Recent matches')} {self.tr('(Last')} {len(games['games'])} {self.tr('games)')}"
            )
            self.winsLabel.setText(f"{self.tr('Wins:')} {games['wins']}")
            self.lossesLabel.setText(f"{self.tr('Losses:')} {games['losses']}")
            self.kdaLabel.setText(
                f"{self.tr('KDA:')} {games['kills']} / {games['deaths']} / {games['assists']}"
            )
        else:
            self.recent20GamesLabel.setText(
                f"{self.tr('Recent matches')} {self.tr('(Last')} None {self.tr('games)')}"
            )
            self.winsLabel.setText(f"{self.tr('Wins:')} 0")
            self.lossesLabel.setText(f"{self.tr('Losses:')} 0")
            self.kdaLabel.setText(f"{self.tr('KDA:')} 0 / 0 / 0")
        self.games = games

        self.__updateGameInfo()

        self.backToMeButton.setEnabled(not self.isCurrentSummoner())

        self.teammatesFlyout.updatePuuid(puuid)

        if self.games:
            self.updateRecentTeammates()

        if 'champions' in info:
            self.championsCard.updateChampions(info['champions'])

    def __updateGameInfo(self):
        for i in reversed(range(self.gameInfoLayout.count())):
            item = self.gameInfoLayout.itemAt(i)
            self.gameInfoLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

        if 'gameCount' in self.games:

            for bar in [GameInfoBar(game) for game in self.games['games']]:
                bar.setMaximumHeight(86)
                self.gameInfoLayout.addWidget(bar)
                self.gameInfoLayout.addSpacing(5)

            self.gameInfoLayout.addSpacerItem(
                QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def __onfilterComboBoxChanged(self, index):
        items = list(range(self.gameInfoLayout.count()))
        items.reverse()

        for i in items:
            item = self.gameInfoLayout.itemAt(i)
            self.gameInfoLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

        if index == 1:
            targetId = 430
        elif index == 2:
            targetId = 450
        elif index == 3:
            targetId = 420
        elif index == 4:
            targetId = 440
        else:
            targetId = 0

        hitGames, kills, deaths, assists, wins, losses = parseGames(
            self.games["games"], targetId)

        for game in hitGames:
            bar = GameInfoBar(game)
            bar.setMaximumHeight(86)
            self.gameInfoLayout.addWidget(bar)
            self.gameInfoLayout.addSpacing(5)

        self.recent20GamesLabel.setText(
            f"{self.tr('Recent matches')} {self.tr('(Last')} {len(hitGames)} {self.tr('games)')}"
        )
        self.winsLabel.setText(f"{self.tr('Wins:')} {wins}")
        self.lossesLabel.setText(f"{self.tr('Losses:')} {losses}")
        self.kdaLabel.setText(
            f"{self.tr('KDA:')} {kills} / {deaths} / {assists}")

        self.gameInfoLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def setCurrentSummonerName(self, name):
        self.currentSummonerName = name

    def getSummonerName(self):
        return self.name.text() if not self.showTagLine else f'{self.name.text()}{self.tagLineLabel.text()}'

    def isCurrentSummoner(self):

        return self.currentSummonerName == None or self.currentSummonerName == self.name.text()

    def __onRecentTeammatesButtonClicked(self):
        self.w = Flyout.make(
            self.teammatesFlyout, self.recentTeamButton, self,
            aniType=FlyoutAnimationType.DROP_DOWN, isDeleteOnClose=False)

    def updateRecentTeammates(self):
        self.teammatesFlyout.showLoadingPage.emit()

        def _():
            summoners = {}
            puuid = self.puuid

            for game in self.games['games']:
                gameId = game['gameId']
                game = connector.getGameDetailByGameId(gameId)

                teammates = getTeammates(game, puuid)
                for p in teammates['summoners']:
                    if p['puuid'] not in summoners:
                        summonerIcon = connector.getProfileIcon(p['icon'])
                        summoners[p['puuid']] = {
                            "name": p['name'], 'icon': summonerIcon,
                            "total": 0, "wins": 0, "losses": 0, "puuid": p["puuid"]}

                    summoners[p['puuid']]['total'] += 1

                    if not teammates['remake']:
                        if teammates['win']:
                            summoners[p['puuid']]['wins'] += 1
                        else:
                            summoners[p['puuid']]['losses'] += 1

            ret = {"puuid": self.puuid, "summoners": [
                item for item in summoners.values()]}

            ret['summoners'] = sorted(ret['summoners'],
                                      key=lambda x: x['total'], reverse=True)[:5]

            self.teammatesFlyout.hideLoadingPage.emit()
            self.teammatesFlyout.summonersInfoReady.emit(ret)

        threading.Thread(target=_).start()


class TeammatesFlyOut(FlyoutViewBase):
    summonersInfoReady = pyqtSignal(dict)
    showLoadingPage = pyqtSignal()
    hideLoadingPage = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.stackedWidget = QStackedWidget()

        self.loadingPageWidget = QWidget()
        self.infoPageWidget = QWidget()

        self.loadingVBoxLayout = QVBoxLayout(self.loadingPageWidget)
        self.infopageVBoxLayout = QVBoxLayout(self.infoPageWidget)

        self.processRing = IndeterminateProgressRing()

        self.__initLayout()
        self.__connectSignalToSlot()

    def __connectSignalToSlot(self):
        self.summonersInfoReady.connect(self.__summonersInfoReady)
        self.showLoadingPage.connect(
            lambda: self.__setLoadingPageEnabled(True))
        self.hideLoadingPage.connect(
            lambda: self.__setLoadingPageEnabled(False))

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.loadingVBoxLayout.addWidget(
            self.processRing, alignment=Qt.AlignCenter)

        self.vBoxLayout.addWidget(self.stackedWidget)

        self.stackedWidget.addWidget(self.loadingPageWidget)
        self.stackedWidget.addWidget(self.infoPageWidget)

        self.stackedWidget.setFixedHeight(352)
        self.stackedWidget.setFixedWidth(490)

    def updatePuuid(self, puuid):
        self.puuid = puuid

    def clear(self):
        for i in reversed(range(self.infopageVBoxLayout.count())):
            item = self.infopageVBoxLayout.itemAt(i)
            self.infopageVBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

    def __summonersInfoReady(self, info):
        if self.puuid != info['puuid']:
            return

        self.clear()

        for summoner in info['summoners']:
            infoBar = TeammateInfoBar(summoner)
            self.infopageVBoxLayout.addWidget(infoBar)

    def __setLoadingPageEnabled(self, enable):
        index = 0 if enable else 1
        self.stackedWidget.setCurrentIndex(index)


class TeammateInfoBar(QFrame):
    # closed = pyqtSignal()

    def __init__(self, summoner, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.icon = RoundIcon(summoner['icon'], 40, 4, 4)
        self.name = SummonerName(summoner['name'])

        self.totalTitle = QLabel(self.tr("Total: "))
        self.totalLabel = QLabel(str(summoner["total"]))
        self.winsTitle = QLabel(self.tr("Wins: "))
        self.winsLabel = QLabel(str(summoner['wins']))
        self.lossesTitle = QLabel(self.tr("Losses: "))
        self.lossesLabel = QLabel(str(summoner['losses']))

        self.__initWidget()
        self.__initLayout()

        self.setFixedHeight(62)

        self.name.clicked.connect(
            lambda: self.parent().parent().parent().parent()
            .parent().summonerNameClicked.emit(summoner['puuid']))

    def __initWidget(self):
        self.name.setFixedWidth(180)
        self.totalLabel.setFixedWidth(40)
        self.winsLabel.setFixedWidth(40)
        self.lossesLabel.setFixedWidth(40)

        self.totalLabel.setObjectName('totalLabel')
        self.winsLabel.setObjectName("winsLabel")
        self.lossesLabel.setObjectName("lossesLabel")

        self.totalTitle.setAlignment(Qt.AlignCenter)
        self.totalLabel.setAlignment(Qt.AlignCenter)
        self.winsTitle.setAlignment(Qt.AlignCenter)
        self.winsLabel.setAlignment(Qt.AlignCenter)
        self.lossesTitle.setAlignment(Qt.AlignCenter)
        self.lossesLabel.setAlignment(Qt.AlignCenter)

    def __initLayout(self):
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addWidget(self.name)
        self.hBoxLayout.addWidget(self.totalTitle)
        self.hBoxLayout.addWidget(self.totalLabel)
        self.hBoxLayout.addWidget(self.winsTitle)
        self.hBoxLayout.addWidget(self.winsLabel)
        self.hBoxLayout.addWidget(self.lossesTitle)
        self.hBoxLayout.addWidget(self.lossesLabel)


class ChampionsCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.setFixedHeight(33)

    def updateChampions(self, champions):
        self.clear()

        for champion in champions:
            icon = RoundIcon(champion['icon'], 28, 2, 2)

            toolTip = self.tr("Total: ") + str(champion['total']) + "   "
            toolTip += self.tr("Wins: ") + str(champion['wins']) + "   "
            toolTip += self.tr("Losses: ") + str(champion['losses']) + "   "
            toolTip += self.tr("Win Rate: ")
            toolTip += ("100" if champion['losses'] == 0 else "{:.2f}".format(
                champion['wins'] * 100 / (champion['wins'] + champion['losses']))) + "%"
            icon.setToolTip(toolTip)
            icon.installEventFilter(
                ToolTipFilter(icon, 0, ToolTipPosition.TOP))

            self.hBoxLayout.addWidget(icon, alignment=Qt.AlignCenter)

    def clear(self):
        for i in reversed(range(self.hBoxLayout.count())):
            item = self.hBoxLayout.itemAt(i)
            self.hBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()
