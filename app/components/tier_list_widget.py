import sys
from typing import Union

from PyQt5.QtGui import QColor, QPainter, QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QStackedLayout, QWidget, QApplication, QStackedWidget,
                             QFrame, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel)


from app.common.icons import Icon
from app.common.config import qconfig
from app.common.qfluentwidgets import (FramelessWindow, isDarkTheme, BackgroundAnimationWidget,
                                       FluentIconBase, FluentStyleSheet, NavigationItemPosition,
                                       qrouter, StackedWidget, FluentTitleBar,  ComboBox,
                                       TransparentToolButton, BodyLabel, ToolTipFilter,
                                       ToolTipPosition, TransparentPushButton, SmoothScrollArea)
from app.components.toggle_button import ToggleButton
from app.components.champion_icon_widget import RoundIcon
from app.common.style_sheet import StyleSheet


class TierListWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        # TODO: 和下方的内容对齐
        self.titleBar = ListTitleBar()

        # TODO: 组件支持点击以及背景动画
        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QFrame()
        self.scrollLayout = QVBoxLayout()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.scrollArea.setObjectName("scrollArea")
        self.scrollWidget.setObjectName("scrollWidget")

        StyleSheet.TIER_LIST_WIDGET.apply(self)

    def __initLayout(self):
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setViewportMargins(0, 0, 14, 0)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addWidget(self.titleBar)
        self.vBoxLayout.addWidget(self.scrollArea)

    def updateList(self, data):
        for x in data:
            item = ListItem(x)
            self.scrollLayout.addWidget(item)


class ListTitleBar(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.counterLabel = BodyLabel("#")
        self.championLabel = BodyLabel(self.tr("Champion"))
        self.tierLabel = TransparentPushButton(self.tr("Tier"))
        self.winRateLabel = TransparentPushButton(self.tr("Win Rate"))
        self.pickRateLabel = TransparentPushButton(self.tr("Pick Rate"))
        self.banRateLabel = TransparentPushButton(self.tr("Ban Rate"))
        self.countersLabel = BodyLabel(self.tr("Counters"))

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(0, 6, 14, 6)

        self.hBoxLayout.addWidget(self.counterLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.championLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.tierLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pickRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.banRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.countersLabel, alignment=Qt.AlignCenter)

    def __initWidget(self):
        pass


class ListItem(QFrame):
    def __init__(self, info, parent: QWidget = None):
        super().__init__(parent)

        # self.setStyleSheet("border: 1px solid black;")

        self.championId = info['championId']
        tierIcon = f"app/resource/images/icon-tier-{info['tier']}.svg"

        self.hBoxLayout = QHBoxLayout(self)

        self.numberLabel = BodyLabel(str(info.get("rank")))
        self.nameLabel = BodyLabel(info.get("name"))
        self.championIcon = RoundIcon(info.get("icon"), 28, 2, 2)
        self.tierLabel = QLabel()
        self.tierLabel.setPixmap(QPixmap(tierIcon))
        self.winRateLabel = BodyLabel(f"{info['winRate']*100:.2f}%")
        self.pickRateLabel = BodyLabel(f"{info['pickRate']*100:.2f}%")
        self.banRateLabel = BodyLabel(f"{info['banRate']*100:.2f}%")
        self.countersLabel = QWidget()
        self.countersLayout = QHBoxLayout(self.countersLabel)

        self.countersLayout.setAlignment(Qt.AlignCenter)
        for c in info.get("counters"):
            icon = RoundIcon(c['icon'], 22, 2, 2)
            self.countersLayout.addWidget(icon)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.numberLabel.setFixedWidth(30)
        self.numberLabel.setAlignment(Qt.AlignCenter)
        self.winRateLabel.setAlignment(Qt.AlignCenter)
        self.pickRateLabel.setAlignment(Qt.AlignCenter)
        self.banRateLabel.setAlignment(Qt.AlignCenter)

        self.winRateLabel.setFixedWidth(60)
        self.pickRateLabel.setFixedWidth(60)
        self.banRateLabel.setFixedWidth(60)
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
        self.hBoxLayout.addSpacing(12)
        self.hBoxLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pickRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.banRateLabel, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.countersLabel, alignment=Qt.AlignCenter)
