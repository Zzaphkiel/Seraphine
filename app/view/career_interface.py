import pyperclip
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QTableWidgetItem, QHeaderView,
                             QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import (ScrollArea, TableWidget, Theme, PushButton,
                            ComboBox, SmoothScrollArea, ToolTipFilter,
                            ToolTipPosition, ToolButton, IndeterminateProgressRing)

from ..components.profile_icon_widget import RoundAvatar
from ..components.game_infobar_widget import GameInfoBar
from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..common.icons import Icon
from ..lol.entries import Summoner
from ..lol.tools import translateTier


class CareerInterface(ScrollArea):
    careerInfoChanged = pyqtSignal(str, str, int, int, int, dict, dict, bool)
    showLoadingPage = pyqtSignal()
    hideLoadingPage = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.summoner: Summoner = None
        self.currentSummonerName: Summoner = None

        self.vBoxLayout = QVBoxLayout(self)
        self.IconNameHBoxLayout = QHBoxLayout()
        self.nameLevelVLayout = QVBoxLayout()
        self.icon = RoundAvatar('app/resource/images/champion-0.png',
                                0,
                                1,
                                parent=self)
        self.name = QLabel(self.tr("Connecting..."))
        self.copyButton = ToolButton(Icon.COPY)
        self.nameButtonLayout = QHBoxLayout()
        self.level = QLabel("Lv. None")

        self.buttonsLayout = QVBoxLayout()
        self.backToMeButton = PushButton(self.tr("Back to me"))
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
        self.copyButton.setFixedSize(26, 26)
        self.copyButton.setEnabled(False)
        self.copyButton.setToolTip(self.tr("Copy summoner name to ClipBoard"))
        self.copyButton.installEventFilter(
            ToolTipFilter(self.copyButton, 500, ToolTipPosition.TOP))

        self.name.setObjectName("name")
        self.level.setObjectName("level")
        self.nameLevelVLayout.setObjectName("nameLevelVLayout")

        self.recent20GamesLabel.setObjectName('rencent20GamesLabel')
        self.winsLabel.setObjectName('winsLabel')
        self.lossesLabel.setObjectName('lossesLabel')
        self.kdaLabel.setObjectName('kdaLabel')
        self.recentInfoHLayout.setObjectName("recentInfoHLayout")
        self.gameInfoArea.setObjectName('gameInfoArea')
        self.gameInfoWidget.setObjectName("gameInfoWidget")

        self.backToMeButton.setEnabled(False)

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
        self.setTableStyle(cfg.theme)

    def __initLayout(self):
        self.nameButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.nameButtonLayout.addWidget(self.name)
        self.nameButtonLayout.addSpacing(5)
        self.nameButtonLayout.addWidget(self.copyButton)

        self.nameLevelVLayout.addSpacerItem(
            QSpacerItem(1, 25, QSizePolicy.Minimum, QSizePolicy.Fixed))
        self.nameLevelVLayout.addLayout(self.nameButtonLayout)
        self.nameLevelVLayout.addWidget(self.level, alignment=Qt.AlignCenter)
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
        self.recentInfoHLayout.addWidget(self.filterComboBox,
                                         alignment=Qt.AlignCenter)

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

        self.__showLoadingPage()

    def __showLoadingPage(self):
        self.icon.setVisible(False)
        self.name.setVisible(False)
        self.copyButton.setVisible(False)
        self.level.setVisible(False)
        self.backToMeButton.setVisible(False)
        self.searchButton.setVisible(False)
        self.rankTable.setVisible(False)
        self.recent20GamesLabel.setVisible(False)
        self.filterComboBox.setVisible(False)
        self.winsLabel.setVisible(False)
        self.lossesLabel.setVisible(False)
        self.kdaLabel.setVisible(False)
        self.winsLabel.setVisible(False)
        self.lossesLabel.setVisible(False)
        self.gameInfoArea.setVisible(False)

        self.progressRing.setVisible(True)

    def __hideLoadingPage(self):
        self.icon.setVisible(True)
        self.name.setVisible(True)
        self.copyButton.setVisible(True)
        self.level.setVisible(True)
        self.backToMeButton.setVisible(True)
        self.searchButton.setVisible(True)
        self.rankTable.setVisible(True)
        self.recent20GamesLabel.setVisible(True)
        self.filterComboBox.setVisible(True)
        self.winsLabel.setVisible(True)
        self.lossesLabel.setVisible(True)
        self.kdaLabel.setVisible(True)
        self.winsLabel.setVisible(True)
        self.lossesLabel.setVisible(True)
        self.gameInfoArea.setVisible(True)

        self.progressRing.setVisible(False)

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

    def setTableStyle(self, theme=None):
        if cfg.theme == Theme.LIGHT:
            borderColor = "rgba(0, 0, 0, 0.095)"
            backgroundColor = "rgba(255, 255, 255, 0.667)"
        else:
            borderColor = "rgb(35, 35, 35)"
            backgroundColor = "rgba(255, 255, 255, 0.051)"

        qss = self.rankTable.styleSheet()
        qss += f'''
        QHeaderView::section:horizontal {{
            border: none;
            border-bottom: 1px solid {borderColor};
        }}

        QTableView {{
            border: 1px solid {borderColor}; 
            border-radius: 6px;
            background: {backgroundColor};
        }}'''
        self.rankTable.setStyleSheet(qss)

    def __connectSignalToSlot(self):
        cfg.themeChanged.connect(self.setTableStyle)
        self.careerInfoChanged.connect(self.__onCareerInfoChanged)
        self.filterComboBox.currentIndexChanged.connect(
            self.__onfilterComboBoxChanged)
        self.copyButton.clicked.connect(
            lambda: pyperclip.copy(self.name.text()))

        self.hideLoadingPage.connect(self.__hideLoadingPage)
        self.showLoadingPage.connect(self.__showLoadingPage)

    def __onCareerInfoChanged(self,
                              name,
                              icon,
                              level,
                              xpSinceLastLevel,
                              xpUntilNextLevel,
                              rankInfo=None,
                              games=None,
                              triggerByUser=True):

        if not triggerByUser and not self.isCurrentSummoner():
            return

        self.icon.updateIcon(icon, xpSinceLastLevel, xpUntilNextLevel)
        self.name.setText(name)

        levelStr = str(level) if level != -1 else "None"
        self.level.setText(f'Lv. {levelStr}')

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
                f"{self.tr('Recent matches')} {self.tr('(Last')} {games['gameCount']} {self.tr('games)')}"
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
            self.winsLabel.setText(f"{self.tr('Wins:')} None")
            self.lossesLabel.setText(f"{self.tr('Losses:')} None")
            self.kdaLabel.setText(f"{self.tr('KDA:')} None / None / None")
        self.games = games

        self.__updateGameInfo()

        self.backToMeButton.setEnabled(not self.isCurrentSummoner())

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

        count, kills, deaths, assists, wins, losses = 0, 0, 0, 0, 0, 0

        for game in self.games['games']:
            if index == 0 or game['queueId'] == targetId:
                bar = GameInfoBar(game)
                bar.setMaximumHeight(86)
                self.gameInfoLayout.addWidget(bar)
                self.gameInfoLayout.addSpacing(5)
                count += 1

                if not game['remake']:
                    kills += game['kills']
                    deaths += game['deaths']
                    assists += game['assists']

                    if game['win']:
                        wins += 1
                    else:
                        losses += 1

        self.recent20GamesLabel.setText(
            f"{self.tr('Recent matches')} {self.tr('(Last')} {count} {self.tr('games)')}"
        )
        self.winsLabel.setText(f"{self.tr('Wins:')} {wins}")
        self.lossesLabel.setText(f"{self.tr('Losses:')} {losses}")
        self.kdaLabel.setText(
            f"{self.tr('KDA:')} {kills} / {deaths} / {assists}")

        self.gameInfoLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def setCurrentSummonerName(self, name):
        self.currentSummonerName = name

    def isCurrentSummoner(self):

        return self.currentSummonerName == None or self.currentSummonerName == self.name.text()
