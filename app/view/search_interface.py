import threading

import pyperclip
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QFrame,
                             QSpacerItem, QSizePolicy, QLabel, QStackedWidget, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from qfluentwidgets import (
    ScrollArea,
    LineEdit,
    PushButton,
    ToolButton,
    InfoBar,
    InfoBarPosition,
    ToolTipFilter,
    ToolTipPosition,
    Theme,
    isDarkTheme,
    FlyoutViewBase,
    Flyout,
)

from ..common.style_sheet import StyleSheet
from ..common.icons import Icon
from ..common.config import cfg
from ..components.champion_icon_widget import RoundIcon
from ..components.summoner_name_button import SummonerName
from ..lol.connector import LolClientConnector
from ..lol.tools import processGameData, processGameDetailData


class GamesTab(QFrame):
    gamesInfoReady = pyqtSignal(int)
    tabClicked = pyqtSignal(str)
    gameDetailReady = pyqtSignal(dict)

    def __init__(self, parnet=None):
        super().__init__(parnet)
        self.setFixedWidth(160)
        self.vBoxLayout = QVBoxLayout(self)

        self.stackWidget = QStackedWidget()
        self.buttonsLayout = QHBoxLayout()

        self.prevButton = ToolButton(Icon.CHEVRONLEFT)
        self.pageLabel = QLabel(" ")
        self.nextButton = ToolButton(Icon.CHEVRONRIGHT)

        self.currentIndex = 0
        self.gamesNumberPerPage = 10
        self.maxPage = None

        self.lolConnector: LolClientConnector = None
        self.puuid = None
        self.games = []

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.pageLabel.setAlignment(Qt.AlignCenter)
        self.prevButton.setVisible(False)
        self.prevButton.setEnabled(False)
        self.nextButton.setVisible(False)
        self.nextButton.setEnabled(False)

    def __initLayout(self):
        defaultWidget = QWidget()
        layout = QVBoxLayout(defaultWidget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stackWidget.addWidget(defaultWidget)
        self.stackWidget.setCurrentIndex(self.currentIndex)

        self.buttonsLayout.addWidget(self.prevButton)
        self.buttonsLayout.addWidget(self.pageLabel)
        self.buttonsLayout.addWidget(self.nextButton)

        self.vBoxLayout.addWidget(self.stackWidget)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addLayout(self.buttonsLayout)

    def __connectSignalToSlot(self):
        self.prevButton.clicked.connect(self.__onPrevButtonClicked)
        self.nextButton.clicked.connect(self.__onNextButtonClicked)

        self.gamesInfoReady.connect(self.__onGamesInfoReady)
        self.tabClicked.connect(self.__onTabClicked)
        self.gameDetailReady.connect(self.__onGameDetailReady)

    def __onTabClicked(self, gameId):
        def _():
            game = self.lolConnector.getGameDetailByGameId(gameId)
            game = processGameDetailData(self.puuid, game, self.lolConnector)
            self.gameDetailReady.emit(game)

        threading.Thread(target=_).start()

    def __onGameDetailReady(self, game):
        self.parent().gameDetailView.updateGame(game)

    def __onPrevButtonClicked(self):
        self.currentIndex -= 1
        self.stackWidget.setCurrentIndex(self.currentIndex)

        self.nextButton.setEnabled(True)
        self.pageLabel.setText(f"{self.currentIndex}")

        if self.currentIndex == 1:
            self.prevButton.setEnabled(False)

    def __onNextButtonClicked(self):
        self.currentIndex += 1

        if len(self.stackWidget) <= self.currentIndex:
            self.nextButton.setEnabled(False)
            self.prevButton.setEnabled(False)
            self.updateGames(self.currentIndex)
        else:
            self.stackWidget.setCurrentIndex(self.currentIndex)
            self.pageLabel.setText(f"{self.currentIndex}")
            if self.currentIndex == self.maxPage:
                self.nextButton.setEnabled(False)
            self.prevButton.setEnabled(True)

    def backToDefaultPage(self):
        self.currentIndex = 0
        self.maxPage = None
        self.games = []
        self.puuid = None

        for i in reversed(range(len(self.stackWidget))):
            if i != 0:
                widget = self.stackWidget.widget(i)
                self.stackWidget.removeWidget(widget)
                widget.deleteLater()

        self.stackWidget.setCurrentIndex(0)
        self.pageLabel.setText(" ")

        self.prevButton.setEnabled(False)
        self.nextButton.setEnabled(False)
        self.prevButton.setVisible(False)
        self.nextButton.setVisible(False)

    def updatePuuid(self, puuid):
        if self.puuid != None:
            self.backToDefaultPage()

        self.puuid = puuid
        self.prevButton.setVisible(True)
        self.nextButton.setVisible(True)
        self.__onNextButtonClicked()

    def updateTabs(self, begin, n):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        for i in range(begin, begin + n):
            tab = GameTab(self.games[i])
            layout.addWidget(tab)

        if n < self.gamesNumberPerPage:
            layout.addSpacerItem(QSpacerItem(
                1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.stackWidget.addWidget(widget)
        self.stackWidget.setCurrentIndex(self.currentIndex)
        self.pageLabel.setText(f"{self.currentIndex}")

        if self.currentIndex != self.maxPage:
            self.nextButton.setEnabled(True)

        if self.currentIndex != 1:
            self.prevButton.setEnabled(True)

    def updateGames(self, page):
        def _():
            if self.maxPage != None:
                self.gamesInfoReady.emit(page)
                return

            count = 10 * (page + 1) - len(self.games)

            begin = len(self.games)
            end = begin + count - 1

            games = self.lolConnector.getSummonerGamesByPuuid(
                self.puuid, begin, end)

            self.games += [processGameData(game, self.lolConnector)
                           for game in games["games"]]

            if page == 1:
                if len(games["games"]) <= 10:
                    self.maxPage = 1
            else:
                if len(games["games"]) < 10:
                    if len(games["games"]) == 0:
                        self.maxPage = page
                    else:
                        self.maxPage = page + 1

            self.gamesInfoReady.emit(page)

        threading.Thread(target=_).start()

    def __onGamesInfoReady(self, page):
        if len(self.games) == 0:
            self.__showEmptyPage()
            return

        m = self.gamesNumberPerPage
        begin = m * (page - 1)

        n = 10 if self.currentIndex != self.maxPage else min(
            m, (len(self.games) - 1) % m + 1)

        self.updateTabs(begin, n)

    def __showEmptyPage(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(self.tr("Empty"))
        label.setObjectName("emptyLabel")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.stackWidget.addWidget(widget)
        self.stackWidget.setCurrentIndex(self.currentIndex)
        self.pageLabel.setText(f"{self.currentIndex}")
        self.prevButton.setVisible(False)
        self.nextButton.setVisible(False)
        self.pageLabel.setText(" ")


class GameDetailView(QFrame):
    summonerNameClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.titleBar = GameTitleBar()

        self.teamView1 = TeamView()
        self.teamView2 = TeamView()

        self.extraTeamView1 = TeamView()
        self.extraTeamView2 = TeamView()

        self.__initLayout()

    def clear(self):
        for i in reversed(range(self.vBoxLayout.count())):
            item = self.vBoxLayout.itemAt(i)
            self.vBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

        self.titleBar = GameTitleBar()

        self.teamView1 = TeamView()
        self.teamView2 = TeamView()

        self.extraTeamView1 = TeamView()
        self.extraTeamView2 = TeamView()
        self.vBoxLayout.addWidget(self.titleBar)
        self.vBoxLayout.addWidget(self.teamView1)
        self.vBoxLayout.addWidget(self.teamView2)

        self.vBoxLayout.addWidget(self.extraTeamView1)
        self.vBoxLayout.addWidget(self.extraTeamView2)

        self.extraTeamView1.setVisible(False)
        self.extraTeamView2.setVisible(False)

    def __initLayout(self):
        self.vBoxLayout.addWidget(self.titleBar)
        self.vBoxLayout.addWidget(self.teamView1)
        self.vBoxLayout.addWidget(self.teamView2)

        self.vBoxLayout.addWidget(self.extraTeamView1)
        self.vBoxLayout.addWidget(self.extraTeamView2)

        self.extraTeamView1.setVisible(False)
        self.extraTeamView2.setVisible(False)

        # self.vBoxLayout.addSpacerItem(
        #     QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def updateGame(self, game: dict):
        isCherry = game["queueId"] == 1700

        mapIcon = QPixmap(game["mapIcon"]).scaled(
            54, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if game["remake"]:
            result = self.tr("Remake")
            color = "162, 162, 162"
        elif game["win"]:
            result = self.tr("Win")
            color = "57, 176, 27"
        else:
            result = self.tr("Lose")
            color = "211, 25, 12"

        if isCherry:
            cherryResult = game["cherryResult"]
            if cherryResult == 1:
                result = self.tr("1st")
            elif cherryResult == 2:
                result = self.tr("2nd")
            elif cherryResult == 3:
                result = self.tr("3rd")
            else:
                result = self.tr("4th")

        self.titleBar.updateTitleBar(
            mapIcon, result, game["mapName"], game["modeName"], game["gameDuration"], game["gameCreation"], game["gameId"], color
        )

        team1 = game["teams"][100]
        team2 = game["teams"][200]

        self.teamView1.updateTeam(
            team1["win"],
            team1["baronIcon"],
            team1["baronKills"],
            team1["dragonIcon"],
            team1["dragonKills"],
            team1["riftHeraldIcon"],
            team1["riftHeraldKills"],
            team1["inhibitorIcon"],
            team1["inhibitorKills"],
            team1["towerIcon"],
            team1["towerKills"],
            team1["kills"],
            team1["deaths"],
            team1["assists"],
            team1["bans"],
            isCherry,
            self.tr("1st"),
        )
        self.teamView1.updateSummoners(team1["summoners"])

        self.teamView2.updateTeam(
            team2["win"],
            team2["baronIcon"],
            team2["baronKills"],
            team2["dragonIcon"],
            team2["dragonKills"],
            team2["riftHeraldIcon"],
            team2["riftHeraldKills"],
            team2["inhibitorIcon"],
            team2["inhibitorKills"],
            team2["towerIcon"],
            team2["towerKills"],
            team2["kills"],
            team2["deaths"],
            team2["assists"],
            team2["bans"],
            isCherry,
            self.tr("2nd"),
        )
        self.teamView2.updateSummoners(team2["summoners"])

        self.extraTeamView1.setVisible(isCherry)
        self.extraTeamView2.setVisible(isCherry)

        if isCherry:
            team3 = game["teams"][300]
            team4 = game["teams"][400]

            self.extraTeamView1.updateTeam(
                team3["win"],
                team3["baronIcon"],
                team3["baronKills"],
                team3["dragonIcon"],
                team3["dragonKills"],
                team3["riftHeraldIcon"],
                team3["riftHeraldKills"],
                team3["inhibitorIcon"],
                team3["inhibitorKills"],
                team3["towerIcon"],
                team3["towerKills"],
                team3["kills"],
                team3["deaths"],
                team3["assists"],
                team3["bans"],
                isCherry,
                self.tr("3rd"),
            )
            self.extraTeamView1.updateSummoners(team3["summoners"])

            self.extraTeamView2.updateTeam(
                team4["win"],
                team4["baronIcon"],
                team4["baronKills"],
                team4["dragonIcon"],
                team4["dragonKills"],
                team4["riftHeraldIcon"],
                team4["riftHeraldKills"],
                team4["inhibitorIcon"],
                team4["inhibitorKills"],
                team4["towerIcon"],
                team4["towerKills"],
                team4["kills"],
                team4["deaths"],
                team4["assists"],
                team4["bans"],
                isCherry,
                self.tr("4th"),
            )
            self.extraTeamView2.updateSummoners(team4["summoners"])


class TeamView(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.titleBarLayout = QHBoxLayout()
        self.summonersLayout = QVBoxLayout()

        self.teamResultLabel = QLabel()
        self.towerIconLabel = QLabel()
        self.towerKillsLabel = QLabel()
        self.inhibitorIconLabel = QLabel()
        self.inhibitorKillsLabel = QLabel()
        self.baronIconLabel = QLabel()
        self.baronKillsLabel = QLabel()
        self.dragonIconLabel = QLabel()
        self.dragonKillsLabel = QLabel()
        self.riftHeraldIconLabel = QLabel()
        self.riftHeraldKillsLabel = QLabel()

        self.bansButton = PushButton("Bans")
        self.csIconLabel = QLabel()
        self.goldIconLabel = QLabel()
        self.dmgIconLabel = QLabel()
        self.kdaLabel = QLabel()

        self.bansFlyOut = None

        self.__initWidget()
        self.__initLayout()

        cfg.themeChanged.connect(self.__updateIconColor)
        self.bansButton.clicked.connect(lambda: Flyout.make(
            self.bansFlyOut, self.bansButton, self))

    def __initWidget(self):
        self.teamResultLabel.setObjectName("teamResult")

        self.towerIconLabel.setToolTip(self.tr("Tower destroyed"))
        self.towerIconLabel.setAlignment(Qt.AlignCenter)
        self.inhibitorIconLabel.setToolTip(self.tr("Inhibitor destroyed"))
        self.inhibitorIconLabel.setAlignment(Qt.AlignCenter)
        self.baronIconLabel.setToolTip(self.tr("Baron Nashor killed"))
        self.baronIconLabel.setAlignment(Qt.AlignCenter)
        self.dragonIconLabel.setToolTip(self.tr("Dragon killed"))
        self.dragonIconLabel.setAlignment(Qt.AlignCenter)
        self.riftHeraldIconLabel.setToolTip(self.tr("Rift Herald killed"))
        self.riftHeraldIconLabel.setAlignment(Qt.AlignCenter)

        self.towerIconLabel.installEventFilter(ToolTipFilter(
            self.towerIconLabel, 500, ToolTipPosition.TOP))
        self.inhibitorIconLabel.installEventFilter(ToolTipFilter(
            self.inhibitorIconLabel, 500, ToolTipPosition.TOP))
        self.baronIconLabel.installEventFilter(ToolTipFilter(
            self.baronIconLabel, 500, ToolTipPosition.TOP))
        self.dragonIconLabel.installEventFilter(ToolTipFilter(
            self.dragonIconLabel, 500, ToolTipPosition.TOP))
        self.riftHeraldIconLabel.installEventFilter(ToolTipFilter(
            self.riftHeraldIconLabel, 500, ToolTipPosition.TOP))

        self.towerKillsLabel.setToolTip(self.tr("Tower destroyed"))
        self.inhibitorKillsLabel.setToolTip(self.tr("Inhibitor destroyed"))
        self.baronKillsLabel.setToolTip(self.tr("Baron Nashor killed"))
        self.dragonKillsLabel.setToolTip(self.tr("Dragon killed"))
        self.riftHeraldKillsLabel.setToolTip(self.tr("Rift Herald killed"))

        self.towerKillsLabel.installEventFilter(ToolTipFilter(
            self.towerKillsLabel, 500, ToolTipPosition.TOP))
        self.inhibitorKillsLabel.installEventFilter(ToolTipFilter(
            self.inhibitorKillsLabel, 500, ToolTipPosition.TOP))
        self.baronKillsLabel.installEventFilter(ToolTipFilter(
            self.baronKillsLabel, 500, ToolTipPosition.TOP))
        self.dragonKillsLabel.installEventFilter(ToolTipFilter(
            self.dragonKillsLabel, 500, ToolTipPosition.TOP))
        self.riftHeraldKillsLabel.installEventFilter(ToolTipFilter(
            self.riftHeraldKillsLabel, 500, ToolTipPosition.TOP))

        self.towerIconLabel.setFixedWidth(24)
        self.inhibitorIconLabel.setFixedWidth(24)
        self.baronIconLabel.setFixedWidth(24)
        self.dragonIconLabel.setFixedWidth(24)
        self.riftHeraldIconLabel.setFixedWidth(24)

        self.bansButton.setVisible(False)

        self.kdaLabel.setFixedWidth(100)
        self.kdaLabel.setAlignment(Qt.AlignCenter)
        self.csIconLabel.setFixedWidth(50)
        self.csIconLabel.setAlignment(Qt.AlignCenter)
        self.goldIconLabel.setFixedWidth(60)
        self.goldIconLabel.setAlignment(Qt.AlignCenter)
        self.dmgIconLabel.setFixedWidth(70)
        self.dmgIconLabel.setAlignment(Qt.AlignCenter)

        self.csIconLabel.setToolTip(self.tr("Minions killed"))
        self.goldIconLabel.setToolTip(self.tr("Gold earned"))
        self.dmgIconLabel.setToolTip(self.tr("Damage dealed to champions"))

        self.csIconLabel.installEventFilter(ToolTipFilter(
            self.csIconLabel, 500, ToolTipPosition.TOP))
        self.goldIconLabel.installEventFilter(ToolTipFilter(
            self.goldIconLabel, 500, ToolTipPosition.TOP))
        self.dmgIconLabel.installEventFilter(ToolTipFilter(
            self.dmgIconLabel, 500, ToolTipPosition.TOP))

        self.csIconLabel.setVisible(False)
        self.goldIconLabel.setVisible(False)

        self.dmgIconLabel.setObjectName("dmgIconLabel")

    def __initLayout(self):
        self.teamResultLabel.setFixedHeight(43)
        self.teamResultLabel.setFixedWidth(55)

        self.titleBarLayout.setSpacing(0)
        self.titleBarLayout.addWidget(self.teamResultLabel)
        self.titleBarLayout.addSpacing(18)
        self.titleBarLayout.addWidget(self.towerIconLabel)
        self.titleBarLayout.addWidget(self.towerKillsLabel)
        self.titleBarLayout.addSpacing(18)
        self.titleBarLayout.addWidget(self.inhibitorIconLabel)
        self.titleBarLayout.addWidget(self.inhibitorKillsLabel)
        self.titleBarLayout.addSpacing(18)
        self.titleBarLayout.addWidget(self.baronIconLabel)
        self.titleBarLayout.addWidget(self.baronKillsLabel)
        self.titleBarLayout.addSpacing(18)
        self.titleBarLayout.addWidget(self.dragonIconLabel)
        self.titleBarLayout.addWidget(self.dragonKillsLabel)
        self.titleBarLayout.addSpacing(18)
        self.titleBarLayout.addWidget(self.riftHeraldIconLabel)
        self.titleBarLayout.addWidget(self.riftHeraldKillsLabel)
        self.titleBarLayout.addSpacerItem(QSpacerItem(
            1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.titleBarLayout.addWidget(self.bansButton)
        self.titleBarLayout.addSpacing(59)
        self.titleBarLayout.addWidget(self.kdaLabel)
        self.titleBarLayout.addSpacing(6)
        self.titleBarLayout.addWidget(self.csIconLabel)
        self.titleBarLayout.addSpacing(6)
        self.titleBarLayout.addWidget(self.goldIconLabel)
        self.titleBarLayout.addSpacing(6)
        self.titleBarLayout.addWidget(self.dmgIconLabel)
        self.titleBarLayout.addSpacing(7)

        self.summonersLayout.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.setContentsMargins(11, 0, 11, 11)
        self.vBoxLayout.addLayout(self.titleBarLayout)
        self.vBoxLayout.addLayout(self.summonersLayout)
        # self.vBoxLayout.addSpacerItem(
        #     QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def updateTeam(
        self,
        win,
        baronIcon,
        baronKills,
        dragonIcon,
        dragonKills,
        riftHeraldIcon,
        riftHeraldKills,
        inhibitorIcon,
        inhibitorKills,
        towerIcon,
        towerKills,
        kills,
        deaths,
        assists,
        bans,
        isCherry,
        result,
    ):
        if isCherry:
            self.teamResultLabel.setText(result)
        elif win == "Win":
            self.teamResultLabel.setText(self.tr("Winner"))
        else:
            self.teamResultLabel.setText(self.tr("Loser"))

        self.towerKillsLabel.setText(str(towerKills))
        self.inhibitorKillsLabel.setText(str(inhibitorKills))
        self.baronKillsLabel.setText(str(baronKills))
        self.dragonKillsLabel.setText(str(dragonKills))
        self.riftHeraldKillsLabel.setText(str(riftHeraldKills))

        self.towerIconLabel.setPixmap(QPixmap(towerIcon).scaled(
            20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.inhibitorIconLabel.setPixmap(QPixmap(inhibitorIcon).scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.baronIconLabel.setPixmap(QPixmap(baronIcon).scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.dragonIconLabel.setPixmap(QPixmap(dragonIcon).scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.riftHeraldIconLabel.setPixmap(QPixmap(riftHeraldIcon).scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.dmgIconLabel.setText("DMG")

        color = "white" if isDarkTheme() else "black"
        self.goldIconLabel.setPixmap(QPixmap(f"app/resource/images/Gold_{color}.png").scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.csIconLabel.setPixmap(QPixmap(f"app/resource/images/Minions_{color}.png").scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        if len(bans) != 0:
            self.bansButton.setVisible(True)
            self.bansFlyOut = BansFlyoutView(bans)
        else:
            self.bansButton.setVisible(False)

        self.csIconLabel.setVisible(True)
        self.goldIconLabel.setVisible(True)

        self.kdaLabel.setText(f"{kills} / {deaths} / {assists}")

    def updateSummoners(self, summoners):
        for i in reversed(range(self.summonersLayout.count())):
            item = self.summonersLayout.itemAt(i)
            self.summonersLayout.removeItem(item)
            if item.widget():
                item.widget().deleteLater()

        for summoner in summoners:
            infoBar = SummonerInfoBar(summoner)

            self.summonersLayout.addWidget(infoBar)

        if len(summoners) != 5:
            self.summonersLayout.addSpacerItem(QSpacerItem(
                1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def __updateIconColor(self, theme: Theme):
        color = "white" if theme == Theme.DARK else "black"
        self.goldIconLabel.setPixmap(QPixmap(f"app/resource/images/Gold_{color}.png").scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.csIconLabel.setPixmap(QPixmap(f"app/resource/images/Minions_{color}.png").scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class BansFlyoutView(FlyoutViewBase):
    def __init__(self, bans, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)

        for champion in bans:
            icon = RoundIcon(champion, 25, 0, 3)
            self.hBoxLayout.addWidget(icon)


class SummonerInfoBar(QFrame):
    def __init__(self, summoner, parent=None):
        super().__init__(parent)
        self.setFixedHeight(39)

        self.hBoxLayout = QHBoxLayout(self)
        self.runeIcon = QLabel()

        self.spellsLayout = QHBoxLayout()

        self.spell1Icon = QLabel()
        self.spell2Icon = QLabel()

        self.levelLabel = QLabel()
        self.championIconLabel = RoundIcon(summoner["championIcon"], 25, 0, 3)
        self.summonerName = SummonerName(summoner["summonerName"])

        self.rankIcon = QLabel()

        self.itemsLayout = QHBoxLayout()
        self.items = []

        self.kdaLabel = QLabel()
        self.csLabel = QLabel()
        self.goldLabel = QLabel()
        self.demageLabel = QLabel()

        self.__initWidget(summoner)
        self.__initLayout()

        self.summonerName.clicked.connect(lambda: self.parent(
        ).parent().summonerNameClicked.emit(summoner["puuid"]))

    def __initWidget(self, summoner):
        self.isCurrent = summoner["isCurrent"]
        if self.isCurrent:
            self.setObjectName("currentSummonerWidget")

        self.runeIcon.setPixmap(QPixmap(summoner["runeIcon"]).scaled(
            23, 23, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.spell1Icon.setFixedSize(18, 18)
        self.spell1Icon.setPixmap(QPixmap(summoner["spell1Icon"]).scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.spell2Icon.setFixedSize(18, 18)
        self.spell2Icon.setPixmap(QPixmap(summoner["spell2Icon"]).scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.spell1Icon.setStyleSheet(
            "QLabel {border: 1px solid rgb(70, 55, 20)}")
        self.spell2Icon.setStyleSheet(
            "QLabel {border: 1px solid rgb(70, 55, 20)}")

        self.levelLabel.setText(str(summoner["champLevel"]))
        self.levelLabel.setObjectName("levelLabel")
        self.levelLabel.setAlignment(Qt.AlignCenter)
        self.levelLabel.setFixedWidth(20)

        self.items = [QPixmap(icon).scaled(
            21, 21, Qt.KeepAspectRatio, Qt.SmoothTransformation) for icon in summoner["itemIcons"]]

        if summoner["rankInfo"]:
            if summoner['rankIcon'] != None:
                self.rankIcon.setPixmap(QPixmap(summoner["rankIcon"]).scaled(
                    30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.rankIcon.setFixedSize(30, 30)

                tier, divison, lp = summoner["tier"], summoner["division"], summoner["lp"]
                if tier != "":
                    self.rankIcon.setToolTip(f"{tier} {divison} {lp}")
                else:
                    self.rankIcon.setToolTip(self.tr("Unranked"))

                self.rankIcon.installEventFilter(
                    ToolTipFilter(self.rankIcon, 0, ToolTipPosition.TOP))
            else:
                self.rankIcon.setText(str(summoner['lp']))
                self.rankIcon.setFixedWidth(40)

        self.kdaLabel.setText(
            f"{summoner['kills']} / {summoner['deaths']} / {summoner['assists']}")
        self.kdaLabel.setFixedWidth(100)
        self.kdaLabel.setAlignment(Qt.AlignCenter)

        self.csLabel.setText(str(summoner["cs"]))
        self.csLabel.setAlignment(Qt.AlignCenter)
        self.csLabel.setFixedWidth(50)

        self.goldLabel.setText(str(summoner["gold"]))
        self.goldLabel.setAlignment(Qt.AlignCenter)
        self.goldLabel.setFixedWidth(60)

        self.demageLabel.setText(str(summoner["demage"]))
        self.demageLabel.setAlignment(Qt.AlignCenter)
        self.demageLabel.setFixedWidth(70)

    def __initLayout(self):
        self.spellsLayout.setContentsMargins(0, 0, 0, 0)
        self.spellsLayout.setSpacing(0)
        self.spellsLayout.addWidget(self.spell1Icon)
        self.spellsLayout.addWidget(self.spell2Icon)

        self.itemsLayout.setSpacing(0)
        self.spellsLayout.setContentsMargins(0, 0, 0, 0)
        for icon in self.items:
            itemLabel = QLabel()
            itemLabel.setPixmap(icon)
            itemLabel.setStyleSheet(
                "QLabel {border: 1px solid rgb(70, 55, 20)}")
            itemLabel.setFixedSize(23, 23)

            self.itemsLayout.addWidget(itemLabel)

        self.hBoxLayout.setContentsMargins(6, 0, 6, 0)
        self.hBoxLayout.addWidget(self.runeIcon)
        self.hBoxLayout.addLayout(self.spellsLayout)
        self.hBoxLayout.addWidget(self.levelLabel)
        self.hBoxLayout.addWidget(self.championIconLabel)
        self.hBoxLayout.addWidget(self.summonerName)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.rankIcon)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.itemsLayout)

        self.hBoxLayout.addWidget(self.kdaLabel)
        self.hBoxLayout.addWidget(self.csLabel)
        self.hBoxLayout.addWidget(self.goldLabel)
        self.hBoxLayout.addWidget(self.demageLabel)


class GameTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(78)
        self.titleBarLayout = QHBoxLayout(self)
        self.infoLayout = QVBoxLayout()
        self.mapIcon = QLabel()
        self.resultLabel = QLabel()
        self.infoLabel = QLabel()
        self.copyGameIdButton = ToolButton(Icon.COPY)
        self.gameId = None

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.resultLabel.setObjectName("resultLabel")
        self.infoLabel.setObjectName("infoLabel")
        self.copyGameIdButton.setVisible(False)
        self.copyGameIdButton.setFixedSize(36, 36)
        self.copyGameIdButton.setToolTip(self.tr("Copy game ID"))
        self.copyGameIdButton.installEventFilter(ToolTipFilter(
            self.copyGameIdButton, 500, ToolTipPosition.LEFT))

    def __initLayout(self):
        self.infoLayout.setSpacing(0)
        self.infoLayout.setContentsMargins(0, 4, 0, 6)
        self.infoLayout.addSpacing(-5)
        self.infoLayout.addWidget(self.resultLabel)
        self.infoLayout.addWidget(self.infoLabel)

        self.titleBarLayout.addWidget(self.mapIcon)
        self.titleBarLayout.addSpacing(5)
        self.titleBarLayout.addLayout(self.infoLayout)
        self.titleBarLayout.addSpacerItem(QSpacerItem(
            1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.titleBarLayout.addWidget(self.copyGameIdButton)
        self.titleBarLayout.addSpacing(10)

    def updateTitleBar(self, mapIcon, result, mapName, modeName, duration, creation, gameId, color):
        self.gameId = gameId
        self.mapIcon.setPixmap(mapIcon)
        self.resultLabel.setText(result)
        self.infoLabel.setText(
            f"{mapName}  ·  {modeName}  ·  {duration}  ·  {creation}  ·  " + self.tr("Game ID: ") + f"{gameId}")
        self.copyGameIdButton.setVisible(True)

        self.setStyleSheet(
            f""" GameTitleBar {{
            border: 1px solid rgb({color});
            border-radius: 5px;
            background-color: rgba({color}, 0.05);
        }}"""
        )

    def __connectSignalToSlot(self):
        self.copyGameIdButton.clicked.connect(
            lambda: pyperclip.copy(self.gameId))


class GamesView(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.gamesTab = GamesTab()
        self.gameDetailView = GameDetailView()

        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)

        self.hBoxLayout.addWidget(self.gamesTab)
        self.hBoxLayout.addWidget(self.gameDetailView)


class GameTab(QFrame):
    def __init__(self, game=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setFixedWidth(141)
        self.setProperty("press", False)

        self.vBoxLayout = QHBoxLayout(self)
        self.nameTimeKdaLayout = QVBoxLayout()

        self.gameId = game["gameId"]
        self.championIcon = RoundIcon(game["championIcon"], 32, 2, 2)

        self.modeName = QLabel(game["name"].replace("排位赛 ", ""))

        self.time = QLabel(
            f"{game['shortTime']}  {game['kills']}/{game['deaths']}/{game['assists']}")
        self.resultLabel = QLabel()

        if game["remake"]:
            self.resultLabel.setText(self.tr("remake"))
        elif game["win"]:
            self.resultLabel.setText(self.tr("win"))
        else:
            self.resultLabel.setText(self.tr("lose"))

        self.__setColor(game["remake"], game["win"])

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.time.setObjectName("time")

    def __initLayout(self):
        self.nameTimeKdaLayout.addWidget(self.modeName)
        self.nameTimeKdaLayout.addWidget(self.time)

        self.vBoxLayout.addWidget(self.championIcon)
        self.vBoxLayout.addSpacing(2)
        self.vBoxLayout.addLayout(self.nameTimeKdaLayout)

        self.vBoxLayout.addSpacerItem(QSpacerItem(
            1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

    def __setColor(self, remake=True, win=True):
        if remake:
            r, g, b = 162, 162, 162
        elif win:
            r, g, b = 57, 176, 27
        else:
            r, g, b = 211, 25, 12

        f1, f2 = 1.1, 0.8
        r1, g1, b1 = min(r * f1, 255), min(g * f1, 255), min(b * f1, 255)
        r2, g2, b2 = min(r * f2, 255), min(g * f2, 255), min(b * f2, 255)

        self.setStyleSheet(
            f""" GameTab {{
            border-radius: 5px;
            border: 1px solid rgb({r}, {g}, {b});
            background-color: rgba({r}, {g}, {b}, 0.05);
        }}
        GameTab:hover {{
            border-radius: 5px;
            border: 1px solid rgb({r1}, {g1}, {b1});
            background-color: rgba({r1}, {g1}, {b1}, 0.15);
        }}
        GameTab[pressed = true] {{
            border-radius: 5px;
            border: 1px solid rgb({r2}, {g2}, {b2});
            background-color: rgba({r2}, {g2}, {b2}, 0.1);
        }}"""
        )

    def mousePressEvent(self, a0) -> None:
        self.setProperty("pressed", True)
        self.style().polish(self)
        return super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0) -> None:
        self.setProperty("pressed", False)
        self.style().polish(self)

        self.parent().parent().parent().tabClicked.emit(str(self.gameId))
        return super().mouseReleaseEvent(a0)


class SearchInterface(ScrollArea):
    summonerPuuidGetted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lolConnector: LolClientConnector = None
        self.vBoxLayout = QVBoxLayout(self)

        self.searchLayout = QHBoxLayout()
        self.searchLineEdit = LineEdit()
        self.searchButton = PushButton(self.tr("Search 🔍"))
        self.careerButton = PushButton(self.tr("Career"))

        self.gamesView = GamesView()
        self.currentSummonerName = None

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.searchLineEdit.setAlignment(Qt.AlignCenter)
        self.searchLineEdit.setClearButtonEnabled(True)
        self.searchLineEdit.setPlaceholderText(
            self.tr("Please input summoner name"))
        self.careerButton.setEnabled(False)

        self.searchButton.setShortcut("Return")

        StyleSheet.SEARCH_INTERFACE.apply(self)

    def __initLayout(self):
        self.searchLayout.addWidget(self.searchLineEdit)
        self.searchLayout.addSpacing(5)
        self.searchLayout.addWidget(self.searchButton)
        self.searchLayout.addWidget(self.careerButton)

        self.vBoxLayout.addLayout(self.searchLayout)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.gamesView)
        self.vBoxLayout.setContentsMargins(30, 32, 30, 30)

    def __onSearchButtonClicked(self):
        targetName = self.searchLineEdit.text()
        if targetName == "":
            return

        def _():
            try:
                summoner = self.lolConnector.getSummonerByName(targetName)
                puuid = summoner["puuid"]
                self.currentSummonerName = targetName
            except:
                puuid = "-1"

            self.summonerPuuidGetted.emit(puuid)

        threading.Thread(target=_).start()

    def __onSummonerPuuidGetted(self, puuid):
        if puuid != "-1":
            self.careerButton.setEnabled(True)
            self.gamesView.gameDetailView.clear()
            self.gamesView.gamesTab.updatePuuid(puuid)
        else:
            self.__showSummonerNotFoundMessage()

    def __connectSignalToSlot(self):
        self.searchButton.clicked.connect(self.__onSearchButtonClicked)
        self.summonerPuuidGetted.connect(self.__onSummonerPuuidGetted)

    def __showSummonerNotFoundMessage(self):
        InfoBar.error(
            title=self.tr("Summoner not found"),
            content=self.tr("Please check the summoner name and retry"),
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=self,
        )

    def setEnabled(self, a0: bool) -> None:
        self.gamesView.gamesTab.backToDefaultPage()
        self.gamesView.gameDetailView.clear()
        self.searchLineEdit.clear()

        self.searchLineEdit.setEnabled(a0)
        self.searchButton.setEnabled(a0)

        return super().setEnabled(a0)

    # def clear(self):
