from typing import Dict

from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QRect
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QFrame, QVBoxLayout,
                             QSpacerItem, QSizePolicy, QStackedWidget,
                             QGridLayout, QSplitter, QApplication)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPalette, QImage

from qfluentwidgets import (SmoothScrollArea, TransparentTogglePushButton,
                            ToolTipFilter, ToolTipPosition)

from ..common.icons import Icon
from ..common.style_sheet import StyleSheet
from ..components.profile_icon_widget import RoundAvatar
from ..components.champion_icon_widget import RoundIcon
from ..components.profile_level_icon_widget import RoundLevelAvatar
from ..components.summoner_name_button import SummonerName
from ..lol.tools import parseGames


class GameInfoInterface(SmoothScrollArea):
    allyOrderUpdate = pyqtSignal(tuple)
    allySummonersInfoReady = pyqtSignal(dict)
    enemySummonerInfoReady = pyqtSignal(dict)
    summonerViewClicked = pyqtSignal(str)
    summonerGamesClicked = pyqtSignal(str)
    pageSwitchSignal = pyqtSignal()
    gameEnd = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.allySummonersInfo = {}
        self.swapBuffer = {}

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
        self.allyOrderUpdate.connect(self.__onAllyOrderUpdate)

        self.gameEnd.connect(self.__onGameEnd)

    def __onAllyOrderUpdate(self, order: tuple):
        """
        更新队友页排序

        @param order: (summonerId,)
        @return:
        """
        if self.allySummonersInfo:
            self.allySummonersInfo["summoners"] = sorted(
                self.allySummonersInfo["summoners"], key=lambda x: order.index(x) if x in order else 5
            )
            self.__onAllySummonerInfoReady(self.allySummonersInfo)


    def __onAllySummonerInfoReady(self, info):
        self.allySummonersInfo = info
        self.summonersView.allySummoners.updateSummoners(info['summoners'])
        self.allySummonerGamesView.updateSummoners(info['summoners'])

        self.summonersView.allyButton.setVisible(True)
        self.summonersView.enemyButton.setVisible(True)
        self.summonersView.allyButton.setEnabled(True)

    def __onEnemiesSummonerInfoReady(self, info):
        self.queueId = info['queueId']

        self.summonersView.enemySummoners.updateSummoners(info['summoners'])
        self.enemySummonerGamesView.updateSummoners(info['summoners'])

        self.summonersView.allyButton.setVisible(True)
        self.summonersView.enemyButton.setVisible(True)
        self.summonersView.enemyButton.setEnabled(True)

    def __onGameEnd(self):
        self.allySummonersInfo = {}
        self.swapBuffer = {}

        self.summonersView.allySummoners.clear()
        self.summonersView.enemySummoners.clear()
        self.allySummonerGamesView.clear()
        self.enemySummonerGamesView.clear()

        self.summonersView.allyButton.click()
        self.summonersView.allyButton.setVisible(False)
        self.summonersView.enemyButton.setVisible(False)
        self.summonersView.allyButton.setEnabled(False)
        self.summonersView.enemyButton.setEnabled(False)

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
        self.allyButton.setEnabled(False)
        self.enemyButton.setEnabled(False)

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

        self.items: Dict[int, SummonerInfoView] = {}
        self.vBoxLayout = QVBoxLayout(self)

        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # self.vBoxLayout.setSpacing(0)

    def updateSummoners(self, summoners):
        self.clear()

        for summoner in summoners:
            summonerView = SummonerInfoView(summoner)
            # 用 summonerId 避免空字符串
            self.items[summoner["summonerId"]] = summonerView
            self.vBoxLayout.addWidget(summonerView, stretch=1)

        if len(summoners) < 5:
            self.vBoxLayout.addStretch(5 - len(summoners))

    def clear(self):
        for i in reversed(range(self.vBoxLayout.count())):
            item = self.vBoxLayout.itemAt(i)
            self.vBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()
        self.items = {}


class SummonerInfoView(QFrame):

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.nowIconId = ''
        self.icon = RoundLevelAvatar(info['icon'],
                                     info['xpSinceLastLevel'],
                                     info['xpUntilNextLevel'],
                                     70, info["level"])

        if info["teammatesMarker"] and info["teamId"]:
            self.setToolTip(
                '\n'.join([t['name'] for t in info["teammatesMarker"]]))
            self.installEventFilter(
                ToolTipFilter(self, 0, ToolTipPosition.TOP))

        self.infoVBoxLayout = QVBoxLayout()
        self.summonerName = SummonerName(info['name'])
        self.summonerName.clicked.connect(lambda: self.parent().parent(
        ).parent().parent().summonerViewClicked.emit(info['puuid']))

        self.gridHBoxLayout = QHBoxLayout()
        self.kdaHBoxLayout = QHBoxLayout()

        self.gridLayout = QGridLayout()

        soloRank = info['rankInfo']['solo']
        self.rankSolo = QLabel(f"{soloRank['tier']} {soloRank['division']}")

        self.kdaLabel = QLabel(f"KDA: ")
        self.kdaLabel.setObjectName("kdaLabel")

        k, d, a = info['kda']
        if d:
            kda = ((k + a) / d)
            self.kdaValLabel = QLabel(f"{kda:.1f}")
            pe = QPalette()
            if 3 <= kda < 4:
                pe.setColor(QPalette.WindowText, QColor(0, 163, 80))
            elif 4 <= kda < 5:
                pe.setColor(QPalette.WindowText, QColor(0, 147, 255))
            elif 5 < kda:
                pe.setColor(QPalette.WindowText, QColor(240, 111, 0))
            self.kdaValLabel.setPalette(pe)
        else:
            self.kdaValLabel = QLabel(f"Perfect")
            pe = QPalette()
            pe.setColor(QPalette.WindowText, QColor(240, 111, 0))
            self.kdaValLabel.setPalette(pe)

        self.kdaValLabel.setAlignment(Qt.AlignCenter)
        self.kdaValLabel.setObjectName("kdaValLabel")

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
        self.kdaHBoxLayout.addWidget(QSplitter())
        self.kdaHBoxLayout.addWidget(self.kdaLabel)
        self.kdaHBoxLayout.addWidget(self.kdaValLabel)
        self.infoVBoxLayout.addLayout(self.kdaHBoxLayout)
        self.kdaHBoxLayout.addWidget(QSplitter())
        # self.infoVBoxLayout.addWidget(self.kdaValLabel)
        self.infoVBoxLayout.addSpacing(3)
        self.infoVBoxLayout.addLayout(self.gridHBoxLayout)
        self.infoVBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.hBoxLayout.setContentsMargins(9, 0, 9, 0)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addLayout(self.infoVBoxLayout)

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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            (self.parent().parent().parent().parent().parent().parent()
             .parent().gameInfoInterface.pageSwitchSignal.emit())

    def enterEvent(self, event):
        QApplication.setOverrideCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def updateIcon(self, iconPath: str):
        self.nowIconId = iconPath.split("/")[-1][:-4]
        self.icon.updateIcon(iconPath)


class SummonersGamesView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.summoners = []

        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

    def updateSummoners(self, summoners):
        self.clear()
        self.summoners = summoners

        for i, summoner in enumerate(summoners):
            games = Games(summoner)
            self.hBoxLayout.addWidget(games, stretch=1)

            if i == 0:
                games.setProperty("isFirst", True)
            elif i == len(summoners) - 1:
                games.setProperty("isLast", True)

        if len(summoners) < 5:
            self.hBoxLayout.addStretch(5 - len(summoners))

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
        # self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self.summonerName = SummonerName(summoner['name'])
        self.summonerName.setObjectName("summonerName")
        self.summonerName.clicked.connect(lambda: self.parent().parent(
        ).parent().summonerGamesClicked.emit(self.summonerName.text()))

        # self.vBoxLayout.setContentsMargins(4, 4, 4, 4)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.summonerName, alignment=Qt.AlignCenter)
        self.vBoxLayout.addSpacing(10)

        games = summoner['gamesInfo']

        for game in games:
            tab = GameTab(game)
            self.vBoxLayout.addWidget(tab)

        if len(games) < 11:
            self.vBoxLayout.addSpacerItem(QSpacerItem(
                1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))


class GameTab(QFrame):

    def __init__(self, game=None, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(54)
        # self.setFixedWidth(129)

        self.hBoxLayout = QHBoxLayout(self)
        self.nameTimeKdaLayout = QVBoxLayout()

        self.gameId = game['gameId']
        self.championIcon = RoundIcon(game['championIcon'], 30, 2, 2)

        self.modeName = QLabel(game['name'].replace("排位赛 ", ""))

        self.time = QLabel(
            f"{game['shortTime']}  {game['kills']}-{game['deaths']}-{game['assists']}"
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
        self.hBoxLayout.setContentsMargins(7, 9, 7, 9)

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
