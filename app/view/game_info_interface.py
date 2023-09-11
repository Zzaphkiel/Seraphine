from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QFrame, QVBoxLayout,
                             QSpacerItem, QSizePolicy, QStackedWidget,
                             QGridLayout)
from PyQt5.QtGui import QPixmap

from qfluentwidgets import (SmoothScrollArea, TransparentTogglePushButton,
                            ToolTipFilter, ToolTipPosition)

from ..common.icons import Icon
from ..common.style_sheet import StyleSheet
from ..components.profile_icon_widget import RoundAvatar
from ..components.champion_icon_widget import RoundIcon
from ..components.summoner_name_button import SummonerName


class GameInfoInterface(SmoothScrollArea):
    allySummonersInfoReady = pyqtSignal(dict)
    enemySummonerInfoReady = pyqtSignal(dict)
    summonerViewClicked = pyqtSignal(str)
    summonerGamesClicked = pyqtSignal(str)
    gameEnd = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)

        self.summonersView = SummonersView()
        self.summonersGamesView = QStackedWidget()

        self.allySummonerGamesView = SummonersGamesView()
        self.enemySummonerGamesView = SummonersGamesView()

        self.queueId = 0

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

        StyleSheet.GAME_INFO_INTERFACE.apply(self)

    def __initWidget(self):
        self.summonersGamesView.setObjectName("summonersGamesView")

        self.summonersGamesView.addWidget(self.allySummonerGamesView)
        self.summonersGamesView.addWidget(self.enemySummonerGamesView)

        self.summonersGamesView.setCurrentIndex(0)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(30, 32, 30, 30)

        self.hBoxLayout.addWidget(self.summonersView)
        self.hBoxLayout.addWidget(self.summonersGamesView)

    def __connectSignalToSlot(self):
        self.summonersView.currentTeamChanged.connect(
            self.__onCurrentTeamChanged)
        self.allySummonersInfoReady.connect(self.__onAllySummonerInfoReady)
        self.enemySummonerInfoReady.connect(self.__onEnemiesSummonerInfoReady)

        self.gameEnd.connect(self.__onGameEnd)

    def __onAllySummonerInfoReady(self, info):
        self.summonersView.allySummoners.updateSummoners(info['summoners'])
        self.allySummonerGamesView.updateSummoners(info['summoners'])

        self.summonersView.allyButton.setVisible(True)
        self.summonersView.enemyButton.setVisible(True)

    def __onEnemiesSummonerInfoReady(self, info):
        self.queueId = info['queueId']

        self.summonersView.enemySummoners.updateSummoners(info['summoners'])
        self.enemySummonerGamesView.updateSummoners(info['summoners'])

    def __onGameEnd(self):
        self.summonersView.allySummoners.clear()
        self.summonersView.enemySummoners.clear()
        self.allySummonerGamesView.clear()
        self.enemySummonerGamesView.clear()

        self.summonersView.allyButton.setVisible(False)
        self.summonersView.enemyButton.setVisible(False)

    def __onCurrentTeamChanged(self, ally: bool):
        index = 0 if ally else 1

        self.summonersView.stackedWidget.setCurrentIndex(index)
        self.summonersGamesView.setCurrentIndex(index)

    def getPlayersInfoSummary(self):
        allyWins, allyLosses = 0, 0
        for summoner in self.allySummonerGamesView.summoners:
            for game in summoner['gamesInfo']:
                if game['queueId'] != self.queueId:
                    continue

                if game['remake']:
                    continue

                if game['win']:
                    allyWins += 1
                else:
                    allyLosses += 1

        enemyWins, enemyLosses = 0, 0
        for summoner in self.enemySummonerGamesView.summoners:
            for game in summoner['gamesInfo']:
                if game['queueId'] != self.queueId:
                    continue

                if game['remake']:
                    continue

                if game['win']:
                    enemyWins += 1
                else:
                    enemyLosses += 1

        return


class SummonersView(QFrame):
    # true => 己方, false => 对方
    currentTeamChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.stackedWidget = QStackedWidget()
        self.buttonsLayout = QHBoxLayout()

        self.allySummoners = TeamSummoners()
        self.enemySummoners = TeamSummoners()

        self.allyButton = TransparentTogglePushButton(self.tr("Ally"))
        self.enemyButton = TransparentTogglePushButton(self.tr("Enemy"))

        self.allyButton.setChecked(True)
        self.allyButton.clicked.connect(self.__onAllyButtonClicked)
        self.enemyButton.clicked.connect(self.__onEnemyButtonClicked)

        self.setFixedWidth(235)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.allyButton.setVisible(False)
        self.enemyButton.setVisible(False)

        self.stackedWidget.addWidget(self.allySummoners)
        self.stackedWidget.addWidget(self.enemySummoners)
        self.stackedWidget.setCurrentIndex(0)

    def __initLayout(self):
        self.buttonsLayout.addWidget(self.allyButton)
        self.buttonsLayout.addWidget(self.enemyButton)

        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.buttonsLayout)

    def __onAllyButtonClicked(self):
        if self.allyButton.isChecked():
            self.enemyButton.setChecked(False)
            self.currentTeamChanged.emit(True)
        else:
            self.allyButton.setChecked(True)

    def __onEnemyButtonClicked(self):
        if self.enemyButton.isChecked():
            self.allyButton.setChecked(False)
            self.currentTeamChanged.emit(False)
        else:
            self.enemyButton.setChecked(True)


class TeamSummoners(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

    def updateSummoners(self, summoners):
        self.clear()

        for summoner in summoners:
            summonerView = SummonerInfoView(summoner)
            self.vBoxLayout.addWidget(summonerView)

        if len(summoners) < 5:
            self.vBoxLayout.addSpacerItem(
                QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def clear(self):
        for i in reversed(range(self.vBoxLayout.count())):
            item = self.vBoxLayout.itemAt(i)
            self.vBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()


class SummonerInfoView(QFrame):

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()
        self.icon = RoundAvatar(info['icon'],
                                info['xpSinceLastLevel'],
                                info['xpUntilNextLevel'],
                                diameter=70,
                                sep=20)

        # self.teammateIcon = None
        if info["teammatesMarker"] and info["teamId"]:
            # self.teammateIcon = QLabel()
            # self.teammateIcon.setPixmap(
            #     QPixmap(Icon.TEAM.path()).scaled(
            #         24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation
            #     )
            # )
            # self.teammateIcon.setFixedSize(24, 24)
            # self.teammateIcon.scroll(0, 4)
            # self.teammateIcon.setAlignment(Qt.AlignCenter)
            self.setToolTip(
                '\n'.join([t['name'] for t in info["teammatesMarker"]]))
            self.installEventFilter(
                ToolTipFilter(self.teammateIcon, 0, ToolTipPosition.TOP))

        self.infoVBoxLayout = QVBoxLayout()
        self.summonerName = SummonerName(info['name'])
        self.summonerName.clicked.connect(lambda: self.parent().parent(
        ).parent().parent().summonerViewClicked.emit(info['puuid']))

        self.gridHBoxLayout = QHBoxLayout()

        self.gridLayout = QGridLayout()

        soloRank = info['rankInfo']['solo']
        self.rankSolo = QLabel(f"{soloRank['tier']} {soloRank['division']}")

        self.levelLabel = QLabel(f"Lv. {info['level']}")
        self.levelLabel.setAlignment(Qt.AlignCenter)
        self.levelLabel.setObjectName("levelLabel")

        self.rankSoloIcon = QLabel()

        if soloRank['tier'] not in ["Unranked", '未定级']:
            sacle, scroll, lp = 24, 4, str(soloRank['lp'])
        else:
            sacle, scroll, lp = 15, -2, '--'

        self.rankSoloIcon.setPixmap(
            QPixmap(soloRank['icon']).scaled(sacle, sacle, Qt.KeepAspectRatio,
                                             Qt.SmoothTransformation))
        self.rankSoloIcon.setFixedSize(24, 24)
        self.rankSoloIcon.scroll(0, scroll)
        self.rankSoloIcon.setAlignment(Qt.AlignCenter)
        self.rankSoloLp = QLabel(lp)

        flexRank = info['rankInfo']['flex']
        self.rankFlex = QLabel(f"{flexRank['tier']} {flexRank['division']}")

        if flexRank['tier'] not in ["Unranked", '未定级']:
            sacle, scroll, lp = 24, 4, str(flexRank['lp'])
        else:
            sacle, scroll, lp = 15, -2, '--'

        self.rankFlexIcon = QLabel()
        sacle, scroll = (24,
                         -10) if flexRank['tier'] not in ["Unranked", '未定级'
                                                          ] else (15, 0)
        self.rankFlexIcon.setPixmap(
            QPixmap(flexRank['icon']).scaled(sacle, sacle, Qt.KeepAspectRatio,
                                             Qt.SmoothTransformation))
        self.rankFlexIcon.setFixedSize(24, 24)
        self.rankFlexIcon.scroll(0, scroll)
        self.rankFlexIcon.setAlignment(Qt.AlignCenter)

        self.rankFlexLp = QLabel(lp)

        self.rankSolo.setToolTip(self.tr("Ranked Solo / Duo"))
        self.rankSolo.installEventFilter(
            ToolTipFilter(self.rankSolo, 0, ToolTipPosition.TOP))
        self.rankSoloIcon.setToolTip(self.tr("Ranked Solo / Duo"))
        self.rankSoloIcon.installEventFilter(
            ToolTipFilter(self.rankSoloIcon, 0, ToolTipPosition.TOP))
        self.rankSoloLp.setToolTip(self.tr("Ranked Solo / Duo"))
        self.rankSoloLp.installEventFilter(
            ToolTipFilter(self.rankSoloLp, 0, ToolTipPosition.TOP))

        self.rankFlex.setToolTip(self.tr("Ranked Flex"))
        self.rankFlex.installEventFilter(
            ToolTipFilter(self.rankFlex, 0, ToolTipPosition.TOP))
        self.rankFlexIcon.setToolTip(self.tr("Ranked Flex"))
        self.rankFlexIcon.installEventFilter(
            ToolTipFilter(self.rankFlexIcon, 0, ToolTipPosition.TOP))
        self.rankFlexLp.setToolTip(self.tr("Ranked Flex"))
        self.rankFlexLp.installEventFilter(
            ToolTipFilter(self.rankFlexLp, 0, ToolTipPosition.TOP))

        if info["teamId"]:
            self.__setColor(info["teamId"])

        self.__initLayout()

    def __initLayout(self):
        self.gridLayout.setContentsMargins(8, 0, 0, 0)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setHorizontalSpacing(5)
        self.gridLayout.addWidget(self.rankSoloIcon, 0, 1, Qt.AlignCenter)
        self.gridLayout.addWidget(self.rankSolo, 0, 2, Qt.AlignCenter)
        self.gridLayout.addWidget(self.rankSoloLp, 0, 3, Qt.AlignCenter)

        self.gridLayout.addWidget(self.rankFlexIcon, 1, 1, Qt.AlignCenter)
        self.gridLayout.addWidget(self.rankFlex, 1, 2, Qt.AlignCenter)
        self.gridLayout.addWidget(self.rankFlexLp, 1, 3, Qt.AlignCenter)

        self.gridHBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.gridHBoxLayout.addLayout(self.gridLayout)
        self.gridHBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.infoVBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.infoVBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.infoVBoxLayout.addSpacing(-6)
        self.infoVBoxLayout.addWidget(self.summonerName,
                                      alignment=Qt.AlignCenter)
        self.infoVBoxLayout.addWidget(self.levelLabel)
        self.infoVBoxLayout.addSpacing(3)
        self.infoVBoxLayout.addLayout(self.gridHBoxLayout)
        self.infoVBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.hBoxLayout.setContentsMargins(5, 0, 5, 0)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addLayout(self.infoVBoxLayout)

        self.vBoxLayout.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        # if self.teammateIcon:
        #     self.vBoxLayout.addWidget(self.teammateIcon)

        # self.setFixedHeight(150)

    def __setColor(self, teamId):
        assert 0 < teamId < 3  # 预组队不会超过2个

        if teamId == 1:
            r, g, b = 255, 176, 27
        elif teamId == 2:
            r, g, b = 255, 51, 153
        else:
            return

        f1, f2 = 1.1, 0.8
        r1, g1, b1 = min(r * f1, 255), min(g * f1, 255), min(b * f1, 255)

        self.setStyleSheet(f""" SummonerInfoView {{
            border-radius: 5px;
            border: 1px solid rgb({r}, {g}, {b});
            background-color: rgba({r}, {g}, {b}, 0.15);
        }}
        SummonerInfoView:hover {{
            border-radius: 5px;
            border: 1px solid rgb({r1}, {g1}, {b1});
            background-color: rgba({r1}, {g1}, {b1}, 0.2);
        }}""")


class SummonersGamesView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.summoners = []

        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setSpacing(0)

    def updateSummoners(self, summoners):
        self.clear()
        self.summoners = summoners

        for summoner in summoners:
            games = Games(summoner)
            self.hBoxLayout.addWidget(games, alignment=Qt.AlignHCenter)

        if len(summoners) < 5:
            self.hBoxLayout.addSpacerItem(QSpacerItem(
                1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

    def clear(self):
        self.summoners.clear()

        for i in reversed(range(self.hBoxLayout.count())):
            item = self.hBoxLayout.itemAt(i)
            self.hBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()


class Games(QFrame):

    def __init__(self, summoner, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(5)

        self.summonerName = SummonerName(summoner['name'])
        self.summonerName.setObjectName("summonerName")
        self.summonerName.clicked.connect(lambda: self.parent().parent(
        ).parent().summonerGamesClicked.emit(self.summonerName.text()))

        # self.vBoxLayout.setContentsMargins(4, 4, 4, 4)
        self.vBoxLayout.addWidget(self.summonerName, alignment=Qt.AlignCenter)
        # self.vBoxLayout.addSpacing(10)

        games = summoner['gamesInfo']

        for game in games:
            tab = GameTab(game)
            self.vBoxLayout.addWidget(tab)

        if len(games) < 11:
            self.vBoxLayout.addSpacerItem(QSpacerItem(
                1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))


class GameTab(QFrame):

    def __init__(self, game=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setFixedWidth(129)

        self.hBoxLayout = QHBoxLayout(self)
        self.nameTimeKdaLayout = QVBoxLayout()

        self.gameId = game['gameId']
        self.championIcon = RoundIcon(game['championIcon'], 30, 2, 2)

        self.modeName = QLabel(game['name'].replace("排位赛 ", ""))

        self.time = QLabel(
            f"{game['shortTime']}  {game['kills']}/{game['deaths']}/{game['assists']}"
        )
        self.resultLabel = QLabel()

        if game['remake']:
            self.resultLabel.setText(self.tr('remake'))
        elif game['win']:
            self.resultLabel.setText(self.tr('win'))
        else:
            self.resultLabel.setText(self.tr('lose'))

        self.__setColor(game['remake'], game['win'])

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.time.setObjectName("time")

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(4, 9, 4, 9)

        self.nameTimeKdaLayout.addWidget(self.modeName)
        self.nameTimeKdaLayout.addWidget(self.time)

        self.hBoxLayout.addWidget(self.championIcon)
        self.hBoxLayout.addSpacing(1)
        self.hBoxLayout.addLayout(self.nameTimeKdaLayout)

        self.hBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

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

        self.setStyleSheet(f""" GameTab {{
            border-radius: 5px;
            border: 1px solid rgb({r}, {g}, {b});
            background-color: rgba({r}, {g}, {b}, 0.15);
        }}
        GameTab:hover {{
            border-radius: 5px;
            border: 1px solid rgb({r1}, {g1}, {b1});
            background-color: rgba({r1}, {g1}, {b1}, 0.2);
        }}
        GameTab[pressed = true] {{
            border-radius: 5px;
            border: 1px solid rgb({r2}, {g2}, {b2});
            background-color: rgba({r2}, {g2}, {b2}, 0.25);
        }}""")
