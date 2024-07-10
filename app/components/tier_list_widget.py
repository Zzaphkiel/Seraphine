import sys
from typing import Union

from qasync import asyncSlot
from PyQt5.QtGui import QColor, QPainter, QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QStackedLayout, QWidget, QApplication, QStackedWidget,
                             QFrame, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel)


from app.common.icons import Icon
from app.common.config import qconfig
from app.common.qfluentwidgets import (FramelessWindow, isDarkTheme, BackgroundAnimationWidget,
                                       FluentIconBase, FluentStyleSheet, NavigationItemPosition,
                                       qrouter, StackedWidget, FluentTitleBar,  ComboBox,
                                       TransparentToolButton, BodyLabel, ToolTipFilter,
                                       ToolTipPosition, TransparentPushButton, SmoothScrollArea,
                                       setCustomStyleSheet, FlowLayout)
from app.components.champion_icon_widget import RoundIcon
from app.components.transparent_button import TransparentButton
from app.components.animation_frame import ColorAnimationFrame
from app.common.style_sheet import StyleSheet


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
        self.scrollLayout = QVBoxLayout()

        self.data: list = None

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.scrollArea.setObjectName("scrollArea")
        self.scrollWidget.setObjectName("scrollWidget")

        self.titleBar.sortRequested.connect(self.__onSortRequested)

        StyleSheet.TIER_LIST_WIDGET.apply(self)

    def __initLayout(self):
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setSpacing(3)
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
        self.data = data
        self.__update(data)

    def clear(self):
        for i in reversed(range(self.scrollLayout.count())):
            item = self.scrollLayout.itemAt(i)
            self.scrollLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

    def __update(self, data: list):
        self.clear()

        for i, x in enumerate(data, start=1):
            item = ListItem(i, x)
            self.scrollLayout.addWidget(item)

    @asyncSlot(str)
    async def __onSortRequested(self, key: str):
        if self.data[0][key] == None:
            return

        if key == 'rank':
            def fun(x): return x[key]
        else:
            def fun(x): return -x[key]

        data = sorted(self.data, key=fun)
        self.__update(data)


class ListTitleBar(QFrame):
    sortRequested = pyqtSignal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.counterLabel = BodyLabel("#")
        self.championLabel = BodyLabel(self.tr("Champion"))
        self.tierLabel = TransparentPushButton(self.tr("Tier"))
        self.winRateLabel = TransparentButton(self.tr("Win Rate"))
        self.pickRateLabel = TransparentButton(self.tr("Pick Rate"))
        self.banRateLabel = TransparentButton(self.tr("Ban Rate"))
        self.countersLabel = BodyLabel(self.tr("Counters"))

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(16, 6, 27, 6)

        self.hBoxLayout.addWidget(self.counterLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(6)
        self.hBoxLayout.addWidget(self.championLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addWidget(self.tierLabel, alignment=Qt.AlignCenter)
        # self.hBoxLayout.addSpacing(1)
        self.hBoxLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pickRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.banRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.countersLabel, alignment=Qt.AlignCenter)

    def __initWidget(self):
        self.counterLabel.setFixedWidth(30)
        self.counterLabel.setAlignment(Qt.AlignCenter)
        self.countersLabel.setAlignment(Qt.AlignCenter)

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
        super().__init__(type='default', parent=parent)

        # self.setStyleSheet("border: 1px solid black")

        self.championId = info['championId']
        tierIcon = f"app/resource/images/icon-tier-{info['tier']}.svg"

        self.hBoxLayout = QHBoxLayout(self)

        self.numberLabel = BodyLabel(str(number))
        self.nameLabel = BodyLabel(info.get("name"))
        self.championIcon = RoundIcon(info.get("icon"), 28, 2, 2)
        self.tierLabel = QLabel()
        self.tierLabel.setPixmap(QPixmap(tierIcon))

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
        self.tierLabel.setAlignment(Qt.AlignCenter)

        width = 70

        self.tierLabel.setFixedWidth(50)
        self.winRateLabel.setFixedWidth(width)
        self.pickRateLabel.setFixedWidth(width)
        self.banRateLabel.setFixedWidth(width)
        self.countersLabel.setFixedWidth(80)

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
        self.hBoxLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pickRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.banRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.countersLabel, alignment=Qt.AlignCenter)
