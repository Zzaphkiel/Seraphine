
from PyQt5.QtWidgets import (QHBoxLayout, QWidget, QFrame, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QLabel, QHBoxLayout, QWidget, QLabel, QFrame,
                             QVBoxLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QEasingCurve
from PyQt5.QtGui import QPixmap
from qasync import asyncSlot

from app.components.animation_frame import ColorAnimationFrame
from app.components.transparent_button import TransparentButton
from app.components.champion_icon_widget import RoundIcon, RoundedLabel
from app.common.signals import signalBus
from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import BodyLabel, SmoothScrollArea, FlowLayout, IconWidget


class TierInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.tierList = TierListWidget()

        self.__initWidget()
        self.__initLayout()

        StyleSheet.OPGG_TIER_INTERFACE.apply(self)

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.tierList)


class TierListWidget(QFrame):
    def __init__(self, parent=None):
        '''
        英雄梯队列表组件

        观前警告：
            为了实现该死的上下对齐，该类实现中含有大量魔法数字
            请自备降压药
        '''

        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.titleBar = ListTitleBar()

        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QFrame()
        self.scrollLayout = FlowLayout(needAni=True, isTight=True)

        self.allChampionShowing = True

        self.items: list[ListItem] = []

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.scrollArea.setObjectName("scrollArea")
        self.scrollWidget.setObjectName("scrollWidget")

        self.titleBar.sortRequested.connect(self.__onSortRequested)

    def __initLayout(self):
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setVerticalSpacing(3)
        self.scrollLayout.setAnimation(450, QEasingCurve.Type.OutQuart)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setViewportMargins(6, 6, 17, 6)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addWidget(self.titleBar)
        self.vBoxLayout.addWidget(self.scrollArea)

    def updateList(self, data: list):
        if len(self.items) != 0:
            self.scrollLayout.takeAllWidgets()

        self.scrollArea.delegate.vScrollBar.resetValue(0)
        self.scrollArea.verticalScrollBar().setSliderPosition(0)

        self.items = [ListItem(0, x) for x in data]
        self.__update()

    def __update(self):
        self.scrollLayout.removeAllWidgets()

        for i, x in enumerate(self.items, start=1):
            x.setCounter(i)
            self.scrollLayout.addWidget(x)

    @asyncSlot(str)
    async def __onSortRequested(self, key: str):
        if self.items[0].info.get(key) == None:
            return

        if key == 'rank':
            def fun(x): return x.info.get(key)
        else:
            def fun(x): return -x.info.get(key)

        self.items.sort(key=fun)
        self.__update()

    def filterChampions(self, type: str, x):
        self.allChampionShowing = False

        '''
        通过两种方式来筛选英雄：
        - `type` 为 `championId` 时，通过判断英雄 id 在不在列表 `x` 中筛选
        - `type` 为 `name` 时，通过判断字符串 `x` 在不在英雄名中筛选
        '''

        if type == 'championId':
            for item in self.items:
                item.setVisible(item.info['championId'] in x)

        else:
            for item in self.items:
                item.setVisible(x in item.info['name'])

    def showAllChampions(self):
        if self.allChampionShowing:
            return

        self.allChampionShowing = True

        for item in self.items:
            item.setVisible(True)


class ListTitleBar(QFrame):
    sortRequested = pyqtSignal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # self.setStyleSheet("border: 1px solid black;")

        self.hBoxLayout = QHBoxLayout(self)

        self.counterLabel = QLabel("#")
        self.championLabel = QLabel(self.tr("Champion"))
        self.tierLabel = TransparentButton(self.tr("Tier"))
        self.winRateLabel = TransparentButton(self.tr("Win Rate"))
        self.pickRateLabel = TransparentButton(self.tr("Pick Rate"))
        self.banRateLabel = TransparentButton(self.tr("Ban Rate"))
        self.countersLabel = QLabel(self.tr("Counters"))

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(16, 6, 27, 6)

        self.hBoxLayout.addWidget(self.counterLabel, alignment=Qt.AlignCenter)
        # self.hBoxLayout.addSpacing()
        self.hBoxLayout.addWidget(self.championLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addWidget(self.tierLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addWidget(self.pickRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.banRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.countersLabel, alignment=Qt.AlignCenter)

    def __initWidget(self):
        self.counterLabel.setFixedWidth(30)
        self.counterLabel.setObjectName("counterLabel")
        self.counterLabel.setAlignment(Qt.AlignCenter)
        self.countersLabel.setAlignment(Qt.AlignCenter)
        self.countersLabel.setObjectName("countersLabel")
        self.championLabel.setAlignment(Qt.AlignCenter)
        self.championLabel.setObjectName("championLabel")

        width = 70

        self.tierLabel.setFixedWidth(50)
        self.winRateLabel.setFixedWidth(width)
        self.pickRateLabel.setFixedWidth(width)
        self.banRateLabel.setFixedWidth(width)
        self.countersLabel.setFixedWidth(80)

        self.tierLabel.clicked.connect(
            lambda: self.sortRequested.emit("rank"))
        self.winRateLabel.clicked.connect(
            lambda: self.sortRequested.emit("winRate"))
        self.pickRateLabel.clicked.connect(
            lambda: self.sortRequested.emit("pickRate"))
        self.banRateLabel.clicked.connect(
            lambda: self.sortRequested.emit("banRate"))


class ListItem(ColorAnimationFrame):
    def __init__(self, number, info, parent: QWidget = None):
        super().__init__(type=f"tier{info['tier']}", parent=parent)
        # super().__init__(type="default", parent=parent)
        self.setFixedWidth(589)

        self.championId = info['championId']
        self.name = info['name']

        self.info = info

        tierIcon = f"app/resource/images/icon-tier-{info['tier']}.svg"

        self.hBoxLayout = QHBoxLayout(self)

        self.numberLabel = BodyLabel(str(number))
        self.nameLabel = BodyLabel(info.get("name"))
        self.championIcon = RoundIcon(info.get("icon"), 28, 2, 2)
        self.tierLabel = RoundedLabel(tierIcon, borderWidth=0, radius=0)

        if info['winRate']:
            self.winRateLabel = BodyLabel(f"{info['winRate']*100:.2f}%")
        else:
            self.winRateLabel = BodyLabel("--")

        if info['pickRate']:
            self.pickRateLabel = BodyLabel(f"{info['pickRate']*100:.2f}%")
        else:
            self.pickRateLabel = BodyLabel("--")

        if info['banRate']:
            self.banRateLabel = BodyLabel(f"{info['banRate']*100:.2f}%")
        else:
            self.banRateLabel = BodyLabel("--")

        self.countersLabel = QWidget()
        self.countersLayout = QHBoxLayout(self.countersLabel)

        self.countersLayout.setAlignment(Qt.AlignCenter)

        counters = info.get("counters")
        if counters:
            for c in counters:
                icon = RoundIcon(c['icon'], 22, 2, 2)
                self.countersLayout.addWidget(icon)
        else:
            icon = BodyLabel("--")
            self.countersLayout.addWidget(icon)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.numberLabel.setFixedWidth(30)
        self.numberLabel.setAlignment(Qt.AlignCenter)
        self.winRateLabel.setAlignment(Qt.AlignCenter)
        self.pickRateLabel.setAlignment(Qt.AlignCenter)
        self.banRateLabel.setAlignment(Qt.AlignCenter)

        width = 70

        # self.tierLabel.setFixedWidth(50)
        self.winRateLabel.setFixedWidth(width)
        self.pickRateLabel.setFixedWidth(width)
        self.banRateLabel.setFixedWidth(width)
        self.countersLabel.setFixedWidth(80)

        self.nameLabel.setContentsMargins(0, 0, 0, 2)
        # self.tierLabel.setContentsMargins(0, 0, 0, 2)
        # self.winRateLabel.setContentsMargins(0, 0, 0, 2)
        # self.pickRateLabel.setContentsMargins(0, 0, 0, 2)
        # self.banRateLabel.setContentsMargins(0, 0, 0, 2)

        self.clicked.connect(self.__onClicked)

    def __initLayout(self):
        self.countersLayout.setContentsMargins(0, 0, 0, 0)
        self.countersLayout.setSpacing(2)

        self.hBoxLayout.addWidget(self.numberLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(6)
        self.hBoxLayout.addWidget(self.championIcon, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(6)
        self.hBoxLayout.addWidget(self.nameLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addWidget(self.tierLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(13)
        self.hBoxLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pickRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.banRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.countersLabel, alignment=Qt.AlignCenter)

    def setCounter(self, x):
        self.numberLabel.setText(str(x))

    def __onClicked(self):
        signalBus.tierChampionClicked.emit(self.championId)
