import copy
from typing import Dict

from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QRect
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QFrame, QVBoxLayout,
                             QSpacerItem, QSizePolicy, QStackedWidget,
                             QGridLayout, QSplitter, QApplication, QWidget)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPalette, QImage, QFontMetrics

from ..common.qfluentwidgets import (SmoothScrollArea, TransparentTogglePushButton,
                                     ToolTipFilter, ToolTipPosition, setCustomStyleSheet)

from app.common.icons import Icon
from app.common.style_sheet import StyleSheet
from app.common.signals import signalBus
from app.common.config import cfg
from app.components.champion_icon_widget import RoundIcon
from app.components.profile_level_icon_widget import RoundLevelAvatar
from app.components.summoner_name_button import SummonerName
from app.components.animation_frame import CardWidget, ColorAnimationFrame
from app.lol.tools import parseSummonerOrder
from app.lol.connector import connector
from ..components.seraphine_interface import SeraphineInterface


class GameInfoInterface(SeraphineInterface):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.summonersView = SummonersView()
        self.summonersGamesView = QStackedWidget()

        self.allyGamesView = SummonersGamesView()
        self.enemyGamesView = SummonersGamesView()

        # 保存召唤师的英雄信息
        # {summonerId: championId}
        self.allyChampions = {}

        # 保存召唤师楼层的顺序，列表中为 summonerId
        self.allyOrder = []

        self.queueId = 0

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

        StyleSheet.GAME_INFO_INTERFACE.apply(self)

    def __initWidget(self):
        self.summonersGamesView.setObjectName("summonersGamesView")

        self.summonersGamesView.addWidget(self.allyGamesView)
        self.summonersGamesView.addWidget(self.enemyGamesView)

        self.summonersGamesView.setCurrentIndex(0)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(30, 32, 30, 30)

        self.hBoxLayout.addWidget(self.summonersView, stretch=2)
        self.hBoxLayout.addWidget(self.summonersGamesView, stretch=7)

    def __connectSignalToSlot(self):
        self.summonersView.currentTeamChanged.connect(
            self.__onCurrentTeamChanged)

    def updateAllySummonersOrder(self, team: list):
        if len(self.allyOrder) == 0:
            return

        order = parseSummonerOrder(team)

        if order != self.allyOrder and len(order) == len(self.allyOrder):
            self.summonersView.ally.updateSummonersOrder(order)
            self.allyGamesView.updateOrder(order)
            self.allyOrder = order

    def updateAllySummoners(self, info):
        if not info or len(info['summoners']) > 5:
            return

        self.allyChampions = info['champions']
        self.allyOrder = info['order']

        # 概览栏 (左侧)
        self.summonersView.ally.updateSummoners(info['summoners'])
        # 战绩栏 (右侧)
        self.allyGamesView.updateSummoners(info['summoners'])

        self.summonersView.allyButton.setVisible(True)
        self.summonersView.enemyButton.setVisible(True)
        self.summonersView.allyButton.setEnabled(True)

    def updateEnemySummoners(self, info):
        if not info or len(info['summoners']) > 5:
            return

        self.summonersView.enemy.updateSummoners(info['summoners'])
        self.enemyGamesView.updateSummoners(info['summoners'])

        self.summonersView.allyButton.setVisible(True)
        self.summonersView.enemyButton.setVisible(True)
        self.summonersView.enemyButton.setEnabled(True)

    async def updateAllyIcon(self, team):
        for new in team:
            if not new['championId'] or not new['summonerId']:
                continue

            summonerId = new['summonerId']
            view = self.summonersView.ally.items.get(summonerId)
            orig = self.allyChampions.get(summonerId)

            if not view or orig == None:
                continue

            newChampionId = new['championId']

            if orig != newChampionId and newChampionId:  # 若新头像是 0, 那就也不更新
                icon = await connector.getChampionIcon(newChampionId)
                self.allyChampions[summonerId] = newChampionId
                view.updateIcon(icon)

    async def clear(self):
        self.allyChampions = {}
        self.allyOrder = []

        self.summonersView.ally.clear()
        self.summonersView.enemy.clear()
        self.allyGamesView.clear()
        self.enemyGamesView.clear()

        self.summonersView.allyButton.click()
        self.summonersView.allyButton.setVisible(False)
        self.summonersView.enemyButton.setVisible(False)
        self.summonersView.allyButton.setEnabled(False)
        self.summonersView.enemyButton.setEnabled(False)

    def __onCurrentTeamChanged(self, ally: bool):
        index = 0 if ally else 1

        self.summonersView.stackedWidget.setCurrentIndex(index)
        self.summonersGamesView.setCurrentIndex(index)

    # 进入游戏时标记预组队颜色
    def updateTeamColor(self, allyColor, enemyColor):
        self.summonersView.ally.updateColor(allyColor)
        self.summonersView.enemy.updateColor(enemyColor)


class SummonersView(QFrame):
    # true => 己方, false => 对方
    currentTeamChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.stackedWidget = QStackedWidget()
        self.buttonsLayout = QHBoxLayout()

        self.ally = TeamSummoners()
        self.enemy = TeamSummoners()

        self.allyButton = TransparentTogglePushButton(self.tr("Ally"))
        self.enemyButton = TransparentTogglePushButton(self.tr("Enemy"))

        self.allyButton.setChecked(True)
        self.allyButton.clicked.connect(self.__onAllyButtonClicked)
        self.enemyButton.clicked.connect(self.__onEnemyButtonClicked)

        # self.setFixedWidth(235)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.allyButton.setEnabled(False)
        self.enemyButton.setEnabled(False)

        self.allyButton.setVisible(False)
        self.enemyButton.setVisible(False)

        self.stackedWidget.addWidget(self.ally)
        self.stackedWidget.addWidget(self.enemy)
        self.stackedWidget.setCurrentIndex(0)

        self.__setStyleSheet()

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

    def __setStyleSheet(self):
        light = '''
            TransparentTogglePushButton,
            TransparentTogglePushButton:hover {
            border: 1px solid rgba(0, 0, 0, 0.073);
        }'''

        dark = '''
            TransparentTogglePushButton,
            TransparentTogglePushButton:hover {
            border: 1px solid rgba(255, 255, 255, 0.053);
        }'''

        setCustomStyleSheet(self.allyButton, light, dark)
        setCustomStyleSheet(self.enemyButton, light, dark)


class TeamSummoners(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.items: Dict[int, SummonerInfoView] = {}
        self.vBoxLayout = QVBoxLayout(self)

        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

    def updateSummonersOrder(self, order: list):
        for i in reversed(range(self.vBoxLayout.count())):
            item = self.vBoxLayout.itemAt(i)
            self.vBoxLayout.removeItem(item)

        for summonerId in order:
            view = self.items[summonerId]
            self.vBoxLayout.addWidget(view)

        if len(order) < 5:
            self.vBoxLayout.addSpacing(self.vBoxLayout.spacing())
            self.vBoxLayout.addStretch(5 - len(order))

    def updateSummoners(self, summoners):
        self.clear()

        for summoner in summoners:
            if not summoner:
                continue

            summonerView = SummonerInfoView(summoner, self)

            # 用 summonerId 避免空字符串
            self.items[summoner["summonerId"]] = summonerView
            self.vBoxLayout.addWidget(summonerView, stretch=1)

        if len(summoners) < 5:
            self.vBoxLayout.addSpacing(self.vBoxLayout.spacing())
            self.vBoxLayout.addStretch(5 - len(summoners))

    def updateColor(self, colors):
        for summonerId, color in colors.items():
            view = self.items.get(summonerId)

            if not view:
                continue

            view.updateTeamColor(color)

    def clear(self):
        for i in reversed(range(self.vBoxLayout.count())):
            item = self.vBoxLayout.itemAt(i)
            self.vBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

        self.items = {}


class SummonerInfoView(ColorAnimationFrame):
    """
    对局信息页单个召唤师概览 item

    Layout 中页面位于左侧, 多个控件自上而下呈纵向堆叠

    显示了 KDA, 召唤师名称, 经验, 头像 等信息
    """

    def __init__(self, info: dict, parent=None):
        super().__init__(type='default', parent=parent)
        self._pressedBackgroundColor = self._hoverBackgroundColor
        self.hBoxLayout = QHBoxLayout(self)
        self.icon = RoundLevelAvatar(info['icon'],
                                     info['xpSinceLastLevel'],
                                     info['xpUntilNextLevel'],
                                     70, info["level"])

        self.infoVBoxLayout = QVBoxLayout()

        name = info['name']
        fateFlag = info["fateFlag"]
        nameColor = None
        if fateFlag:
            nameColor = "#bf242a" if fateFlag == "enemy" else "#057748"
        self.summonerName = SummonerName(
            name, isPublic=info["isPublic"], color=nameColor, tagLine=info['tagLine'], tips=info["recentlyChampionName"])
        self.summonerName.clicked.connect(
            lambda: signalBus.toCareerInterface.emit(info['puuid']))

        self.gridHBoxLayout = QHBoxLayout()
        self.kdaHBoxLayout = QHBoxLayout()

        self.gridLayout = QGridLayout()

        soloRank = info['rankInfo']['solo']
        self.rankSolo = QLabel(f"{soloRank['tier']} {soloRank['division']}")

        self.kdaLabel = QLabel(f"KDA: ")
        self.kdaLabel.setObjectName("kdaLabel")

        k, d, a = info['kda']
        if d == 0:
            d = 1

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

        # self.setFixedHeight(150)

    def updateTeamColor(self, team):
        if team in [0, 1]:
            self.setType(f"team{team+1}")

    def updateIcon(self, iconPath: str):
        self.icon.updateIcon(iconPath)


class SummonersGamesView(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.items: Dict[int, Games] = {}

        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

    def updateOrder(self, order):
        for i in reversed(range(self.hBoxLayout.count())):
            item = self.hBoxLayout.itemAt(i)
            self.hBoxLayout.removeItem(item)

        for i, summonerId in enumerate(order):
            view = self.items[summonerId]
            self.hBoxLayout.addWidget(view)

            view.setProperty("isFirst", False)
            view.setProperty("isLast", False)

            if i == 0:
                view.setProperty("isFirst", True)
            elif i == 4:
                view.setProperty("isLast", True)

            view.style().polish(view)

        if len(order) < 5:
            self.hBoxLayout.addSpacing(self.hBoxLayout.spacing())
            self.hBoxLayout.addStretch(5 - len(order))

    def updateSummoners(self, summoners):
        self.clear()

        for i, summoner in enumerate(summoners):
            if not summoner:
                continue

            games = Games(summoner)
            self.items[summoner["summonerId"]] = games

            self.hBoxLayout.addWidget(games, stretch=1)

            if i == 0:
                games.setProperty("isFirst", True)
            elif i == 4:
                games.setProperty("isLast", True)

        if len(summoners) < 5:
            self.hBoxLayout.addStretch(5 - len(summoners))

    def clear(self):
        for i in reversed(range(self.hBoxLayout.count())):
            item = self.hBoxLayout.itemAt(i)
            self.hBoxLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

        self.items = {}


class Games(QFrame):

    def __init__(self, summoner, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(5)

        self.vBoxLayout.setContentsMargins(11, 5, 11, 11)

        self.gamesLayout = QVBoxLayout()

        # self.setSizePolicy(QSizePolicy.Policy.Expanding,
        #                    QSizePolicy.Policy.Fixed)

        name: str = summoner['name']
        fateFlag = summoner["fateFlag"]
        nameColor = None
        if fateFlag:
            nameColor = "#bf242a" if fateFlag == "enemy" else "#057748"
        self.summonerName = SummonerName(
            name, isPublic=summoner["isPublic"], color=nameColor, tagLine=summoner['tagLine'], tips=summoner["recentlyChampionName"])
        self.summonerName.setObjectName("summonerName")

        self.summonerName.clicked.connect(
            lambda: signalBus.toSearchInterface.emit(self.summonerName.text()))

        self.summonerName.setFixedHeight(60)

        # self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.summonerName, alignment=Qt.AlignCenter)
        # self.vBoxLayout.addSpacing(11)

        self.vBoxLayout.addLayout(self.gamesLayout)
        self.gamesLayout.setContentsMargins(0, 0, 0, 0)

        games = summoner['gamesInfo']

        for game in games:
            tab = GameTab(game)
            self.gamesLayout.addWidget(tab, stretch=1)

        if len(games) < 11:
            self.gamesLayout.addStretch(11-len(games))
            self.gamesLayout.addSpacing(5)


class GameTab(ColorAnimationFrame):

    def __init__(self, game=None, parent=None):
        if game['remake']:
            type = 'remake'
        elif game['win']:
            type = 'win'
        else:
            type = 'lose'

        super().__init__(type=type, parent=parent)
        self._pressedBackgroundColor = self._hoverBackgroundColor

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

        self.remake = game['remake']
        self.win = game['win']

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.time.setObjectName("time")

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(7, 7, 7, 7)

        self.nameTimeKdaLayout.setSpacing(0)
        self.nameTimeKdaLayout.addWidget(self.modeName)
        self.nameTimeKdaLayout.addWidget(self.time)

        self.hBoxLayout.addWidget(self.championIcon)
        self.hBoxLayout.addSpacing(1)
        self.hBoxLayout.addLayout(self.nameTimeKdaLayout)

        self.hBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
