from typing import List

from PyQt5.QtWidgets import (QHBoxLayout, QWidget, QFrame, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QLabel, QHBoxLayout, QWidget, QLabel, QFrame,
                             QVBoxLayout, QSpacerItem, QSizePolicy, QLayout, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QEasingCurve
from PyQt5.QtGui import QPixmap, QColor, QCursor
from qasync import asyncSlot

from app.lol.tools import ToolsTranslator
from app.components.animation_frame import (ColorAnimationFrame,
                                            NoBorderColorAnimationFrame, CardWidget)
from app.components.transparent_button import PrimaryButton
from app.components.champion_icon_widget import RoundIcon, RoundedLabel
from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import (SmoothScrollArea, IconWidget, isDarkTheme,
                                       ToolTipFilter, ToolTipPosition, PushButton,
                                       PrimaryToolButton, FluentIcon, PillToolButton,
                                       TransparentToolButton, ThemeColor)
from app.common.icons import Icon
from app.common.config import qconfig, cfg
from app.common.signals import signalBus
from app.lol.connector import connector


class BuildInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.championId = None
        self.vBoxLayout = QVBoxLayout(self)

        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()

        self.titleBar = ChampionTitleBar()
        self.summonerSpells = SummonerSpellsWidget()
        self.championSkills = ChampionSkillsWidget()
        self.championItems = ChampionItemWidget()
        self.championCounters = ChampionCountersWidget()
        self.championPerks = ChampionPerksWidget()
        self.championAugments = ChampionAugmentsWidget()
        self.championSynergies = ChampionSynergiesWidget()

        self.__initWidget()
        self.__initLayout()

        StyleSheet.OPGG_BUILD_INTERFACE.apply(self)

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.scrollArea.setObjectName("scrollArea")
        self.scrollWidget.setObjectName("scrollWidget")

        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        # self.scrollArea.setVerticalScrollBarPolicy(
        #     Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.scrollArea.setViewportMargins(10, 10, 17, 10)
        self.scrollArea.setViewportMargins(0, 0, 15, 0)
        self.scrollWidget.setContentsMargins(0, 0, 0, 0)

        self.scrollLayout.addWidget(self.titleBar)
        self.scrollLayout.addWidget(self.summonerSpells)
        self.scrollLayout.addWidget(self.championPerks)
        self.scrollLayout.addWidget(self.championSkills)
        self.scrollLayout.addWidget(self.championItems)
        self.scrollLayout.addWidget(self.championCounters)
        self.scrollLayout.addWidget(self.championAugments)
        self.scrollLayout.addWidget(self.championSynergies)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.scrollArea)

    def setCurrentChampionId(self, id):
        self.championId = id

    def getCurrentChampionId(self):
        return self.championId

    def updateInterface(self, data: dict):
        summary = data.get('summary')

        self.titleBar.updateWidget(summary)
        self.summonerSpells.updateWidget(data.get('summonerSpells'))
        self.championPerks.updateWidget(data.get('perks'), summary)
        self.championSkills.updateWidget(data.get('championSkills'))
        self.championItems.updateWidget(data.get('items'))
        self.championCounters.updateWidget(data.get('counters'), summary)
        self.championAugments.updateWidget(data.get('augments'))
        self.championSynergies.updateWidget(data.get('synergies'))

        self.scrollArea.delegate.vScrollBar.resetValue(0)
        self.scrollArea.verticalScrollBar().setSliderPosition(0)


class ChampionTitleBar(ColorAnimationFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(type="default", parent=parent)
        self._pressedBackgroundColor = self._hoverBackgroundColor

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setAlignment(Qt.AlignLeft)

        self.nameLayout = QVBoxLayout()
        self.icon = RoundIcon('app/resource/images/champion-0.png', 54, 2, 3)
        self.name = QLabel()
        self.position = QLabel()

        self.winRateLayout = QVBoxLayout()
        self.winRateTextLabel = QLabel()
        self.winRateLabel = QLabel()

        self.pickRateLabel = QLabel()
        self.pickRateLayout = QVBoxLayout()
        self.pickRateTextLabel = QLabel()

        self.banRateLabel = QLabel()
        self.banRateLayout = QVBoxLayout()
        self.banRateTextLabel = QLabel()

        self.line1 = QFrame()
        self.line2 = QFrame()

        self.tierLabel = IconWidget()

        self.__initWidget()
        self.__initLayout()

        self.setVisible(False)

    def updateWidget(self, data):
        ts = ToolsTranslator()
        self.setType(f"tier{data['tier']}")

        self.icon.setIcon(data['icon'])
        self.name.setText(data['name'])

        if data['position'] != 'none':
            self.position.setText(ts.positionMap[data['position']])
            self.position.setVisible(True)
        else:
            self.position.setVisible(False)

        self.banRateTextLabel.setVisible(True)
        self.banRateLabel.setVisible(True)
        self.line2.setVisible(True)

        if firstRate := data.get('firstRate'):
            self.winRateTextLabel.setText(self.tr("First Rate"))
            self.winRateLabel.setText(f"{firstRate*100:.2f}%")

            self.pickRateTextLabel.setText(self.tr("Average Place"))
            self.pickRateLabel.setText(f"{data['averagePlace']:.2f}")

            self.banRateTextLabel.setText(self.tr("Pick Rate"))
            self.banRateLabel.setText(f"{data['pickRate']*100:.2f}%")
        else:
            self.winRateTextLabel.setText(self.tr("Win Rate"))
            self.winRateLabel.setText(f"{data['winRate']*100:.2f}%")

            self.pickRateTextLabel.setText(self.tr("Pick Rate"))
            self.pickRateLabel.setText(f"{data['pickRate']*100:.2f}%")

            if banRate := data['banRate']:
                self.banRateTextLabel.setText(self.tr("Ban Rate"))
                self.banRateLabel.setText(f"{banRate*100:.2f}%")
            else:
                self.banRateTextLabel.setVisible(False)
                self.banRateLabel.setVisible(False)
                self.line2.setVisible(False)

        _, _, _, color = self.getColors()
        self.line1.setStyleSheet(f"color: {color.name(QColor.HexArgb)};")
        self.line2.setStyleSheet(f"color: {color.name(QColor.HexArgb)};")

        tierIcon = f"app/resource/images/icon-tier-{data['tier']}.svg"
        self.tierLabel.setIcon(tierIcon)

        self.setVisible(True)

    def __initWidget(self):
        self.name.setObjectName("titleLabel")
        self.name.setContentsMargins(0, 0, 0, 4)
        self.position.setObjectName("bodyLabel")
        self.winRateTextLabel.setObjectName("subtitleLabel")
        self.winRateLabel.setObjectName("bodyLabel")
        self.pickRateTextLabel.setObjectName("subtitleLabel")
        self.pickRateLabel.setObjectName("bodyLabel")
        self.banRateTextLabel.setObjectName("subtitleLabel")
        self.banRateLabel.setObjectName("bodyLabel")

        self.line1.setFrameShape(QFrame.Shape.VLine)
        self.line1.setLineWidth(1)
        self.line2.setFrameShape(QFrame.Shape.VLine)
        self.line2.setLineWidth(1)

        self.tierLabel.setFixedSize(30, 30)

    def __initLayout(self):
        self.nameLayout.setAlignment(Qt.AlignCenter)
        self.nameLayout.setContentsMargins(0, 0, 0, 0)
        self.nameLayout.setSpacing(0)
        self.nameLayout.addWidget(self.name)
        self.nameLayout.addWidget(self.position)

        self.winRateLayout.setAlignment(Qt.AlignCenter)
        self.winRateLayout.setSpacing(0)
        self.winRateLayout.setContentsMargins(0, 0, 0, 0)
        self.winRateLayout.addWidget(
            self.winRateTextLabel, alignment=Qt.AlignCenter)
        self.winRateLayout.addWidget(
            self.winRateLabel, alignment=Qt.AlignCenter)

        self.pickRateLayout.setAlignment(Qt.AlignCenter)
        self.pickRateLayout.setSpacing(0)
        self.pickRateLayout.setContentsMargins(0, 0, 0, 0)
        self.pickRateLayout.addWidget(
            self.pickRateTextLabel, alignment=Qt.AlignCenter)
        self.pickRateLayout.addWidget(
            self.pickRateLabel, alignment=Qt.AlignCenter)

        self.banRateLayout.setAlignment(Qt.AlignCenter)
        self.banRateLayout.setSpacing(0)
        self.banRateLayout.setContentsMargins(0, 0, 0, 0)
        self.banRateLayout.addWidget(
            self.banRateTextLabel, alignment=Qt.AlignCenter)
        self.banRateLayout.addWidget(
            self.banRateLabel, alignment=Qt.AlignCenter)

        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addLayout(self.nameLayout)

        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.hBoxLayout.addLayout(self.winRateLayout)
        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addWidget(self.line1)
        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addLayout(self.pickRateLayout)
        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addWidget(self.line2)
        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addLayout(self.banRateLayout)
        self.hBoxLayout.addSpacing(15)
        self.hBoxLayout.addWidget(self.tierLabel)
        self.hBoxLayout.addSpacing(6)


class BuildWidgetBase(ColorAnimationFrame):
    def __init__(self, parent=None):
        super().__init__(type='default', parent=parent)
        self._pressedBackgroundColor = self._hoverBackgroundColor
        self.setVisible(False)


class SeparatorLine(QFrame):
    def __init__(self, shape, parent=None):
        super().__init__(parent)
        self.setFrameShape(shape)
        self.setLineWidth(1)
        self.setObjectName("separatorLine")


class Spell(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.iconSize = 32
        self.iconsLayout = QHBoxLayout()
        self.icon1 = RoundedLabel()
        self.icon2 = RoundedLabel()

        self.winRateLayout = QVBoxLayout()
        self.winRateLabel = QLabel()
        self.gamesLabel = QLabel()

        self.pickRateLabel = QLabel()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.icon1.setFixedSize(self.iconSize, self.iconSize)
        self.icon2.setFixedSize(self.iconSize, self.iconSize)

        self.winRateLabel.setObjectName("bodyLabel")
        self.gamesLabel.setObjectName("grayBodyLabel")
        self.pickRateLabel.setObjectName("boldBodyLabel")

        self.gamesLabel.setFixedWidth(81)
        self.gamesLabel.setAlignment(Qt.AlignCenter)
        self.pickRateLabel.setFixedWidth(43)
        self.pickRateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __initLayout(self):
        self.winRateLayout.setAlignment(Qt.AlignCenter)
        self.winRateLayout.setContentsMargins(0, 0, 0, 0)
        self.winRateLayout.setSpacing(0)

        self.winRateLayout.addWidget(
            self.winRateLabel, alignment=Qt.AlignCenter)
        self.winRateLayout.addWidget(
            self.gamesLabel, alignment=Qt.AlignCenter)

        self.iconsLayout.setContentsMargins(0, 0, 0, 0)
        self.iconsLayout.setAlignment(Qt.AlignLeft)
        self.iconsLayout.setSpacing(3)
        self.iconsLayout.addWidget(self.icon1)
        self.iconsLayout.addWidget(self.icon2)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addLayout(self.iconsLayout)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addLayout(self.winRateLayout)
        self.hBoxLayout.addSpacing(22)
        self.hBoxLayout.addWidget(self.pickRateLabel)

    def updateSpell(self, data):
        self.icon1.setPicture(data['icons'][0])
        self.icon2.setPicture(data['icons'][1])

        self.winRateLabel.setText(f"{data['win']/data['play']*100:.2f}%")
        self.pickRateLabel.setText(f"{data['pickRate']*100:.2f}%")
        self.gamesLabel.setText(f"{data['play']:,} " + self.tr("Games"))


class SummonerSpellsWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.spell1 = Spell()
        self.spell2 = Spell()

        self.vLine = SeparatorLine(QFrame.Shape.VLine)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(11, 9, 11, 9)
        self.hBoxLayout.addWidget(self.spell1)
        self.hBoxLayout.addSpacing(4)
        self.hBoxLayout.addWidget(self.vLine)
        self.hBoxLayout.addSpacing(4)
        self.hBoxLayout.addWidget(self.spell2)

    def updateWidget(self, data):
        if not data:
            self.setVisible(False)
            return

        self.spell1.updateSpell(data[0])
        self.spell2.updateSpell(data[1])

        self.setVisible(True)


class SkillIcon(QLabel):
    def __init__(self, text: str, type: str, parent=None):
        super().__init__(text, parent=parent)
        self.setProperty("name", text)
        self.setProperty("type", type)
        self.setAlignment(Qt.AlignCenter)

        if type == "main":
            self.setContentsMargins(0, 0, 0, 4)
            size = 32
        else:
            self.setContentsMargins(0, 0, 0, 0)
            size = 22

        self.setFixedSize(size, size)


class ChampionSkillsWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.skillsLayout = QVBoxLayout()
        self.mainSkillLayout = QHBoxLayout()
        self.skillOrderLayout = QHBoxLayout()

        self.gamesLayout = QVBoxLayout()
        self.winRateLabel = QLabel()
        self.gamesLabel = QLabel()

        self.pickRateLabel = QLabel()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.pickRateLabel.setObjectName("boldBodyLabel")
        self.winRateLabel.setObjectName("bodyLabel")
        self.gamesLabel.setObjectName("grayBodyLabel")

        self.gamesLabel.setFixedWidth(81)
        self.gamesLabel.setAlignment(Qt.AlignCenter)
        self.pickRateLabel.setFixedWidth(43)
        self.pickRateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __initLayout(self):
        self.mainSkillLayout.setContentsMargins(0, 0, 0, 0)
        self.mainSkillLayout.setAlignment(Qt.AlignLeft)
        self.skillOrderLayout.setContentsMargins(0, 0, 0, 0)
        self.skillOrderLayout.setAlignment(Qt.AlignLeft)
        self.skillOrderLayout.setSpacing(3)
        self.skillsLayout.setContentsMargins(0, 0, 0, 0)
        self.skillsLayout.setAlignment(Qt.AlignLeft)

        self.skillsLayout.addLayout(self.mainSkillLayout)
        self.skillsLayout.addLayout(self.skillOrderLayout)

        self.gamesLayout.setContentsMargins(0, 0, 0, 0)
        self.gamesLayout.setAlignment(Qt.AlignCenter)
        self.gamesLayout.setSpacing(0)
        self.gamesLayout.addWidget(self.winRateLabel, alignment=Qt.AlignCenter)
        self.gamesLayout.addWidget(self.gamesLabel, alignment=Qt.AlignCenter)

        self.hBoxLayout.addLayout(self.skillsLayout)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addLayout(self.gamesLayout)
        self.hBoxLayout.addSpacing(22)
        self.hBoxLayout.addWidget(self.pickRateLabel)
        self.hBoxLayout.addSpacing(2)

    def __clearLayout(self, layout: QLayout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)

            if widget := item.widget():
                widget.deleteLater()

    def updateWidget(self, data):
        self.__clearLayout(self.mainSkillLayout)
        self.__clearLayout(self.skillOrderLayout)

        for i, skill in enumerate(data['masteries']):
            icon = SkillIcon(skill, 'main')
            self.mainSkillLayout.addWidget(icon)

            if i != len(data['masteries']) - 1:
                arrow = IconWidget(Icon.GRAYCHEVRONRIGHT)
                arrow.setFixedSize(20, 20)

                self.mainSkillLayout.addWidget(arrow)

        for skill in data['order']:
            icon = SkillIcon(skill, 'order')
            self.skillOrderLayout.addWidget(icon)

        self.gamesLabel.setText(f"{data['play']:,} " + self.tr("Games"))
        self.winRateLabel.setText(f"{data['win'] / data['play'] * 100:.2f}%")
        self.pickRateLabel.setText(f"{data['pickRate']*100:.2f}%")

        self.setVisible(True)


class ItemsWidget(QFrame):
    def __init__(self, data, useSeparator=False, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.iconsLayout = QHBoxLayout()

        self.iconSize = 32

        self.winRateLayout = QVBoxLayout()
        self.winRateLabel = QLabel()
        self.gamesLabel = QLabel()

        self.pickRateLabel = QLabel()

        self.useSeparator = useSeparator

        self.__initWidget()
        self.__initLayout()

        self.updateItems(data)

    def __initWidget(self):
        self.winRateLabel.setObjectName("bodyLabel")
        self.gamesLabel.setObjectName("grayBodyLabel")
        self.pickRateLabel.setObjectName("boldBodyLabel")

        self.gamesLabel.setFixedWidth(81)
        self.gamesLabel.setAlignment(Qt.AlignCenter)
        self.pickRateLabel.setFixedWidth(43)
        self.pickRateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __initLayout(self):
        self.iconsLayout.setContentsMargins(0, 0, 0, 0)
        self.iconsLayout.setAlignment(Qt.AlignLeft)
        self.iconsLayout.setSpacing(3)

        self.winRateLayout.setAlignment(Qt.AlignCenter)
        self.winRateLayout.setContentsMargins(0, 0, 0, 0)
        self.winRateLayout.setSpacing(0)

        self.winRateLayout.addWidget(
            self.winRateLabel, alignment=Qt.AlignCenter)
        self.winRateLayout.addWidget(
            self.gamesLabel, alignment=Qt.AlignCenter)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addLayout(self.iconsLayout)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addLayout(self.winRateLayout)
        self.hBoxLayout.addSpacing(22)
        self.hBoxLayout.addWidget(self.pickRateLabel)

    def updateItems(self, data):
        for x, i in enumerate(data['icons']):
            icon = RoundedLabel()
            icon.setPicture(i)
            icon.setFixedSize(self.iconSize, self.iconSize)
            self.iconsLayout.addWidget(icon)

            if x != len(data['icons']) - 1 and self.useSeparator:
                arrow = IconWidget(Icon.GRAYCHEVRONRIGHT)
                arrow.setFixedSize(20, 20)

                self.iconsLayout.addSpacing(6)
                self.iconsLayout.addWidget(arrow)
                self.iconsLayout.addSpacing(6)

        self.winRateLabel.setText(f"{data['win']/data['play']*100:.2f}%")
        self.pickRateLabel.setText(f"{data['pickRate']*100:.2f}%")
        self.gamesLabel.setText(f"{data['play']:,} " + self.tr("Games"))


class ChampionItemWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.bootsAndStartLayout = QHBoxLayout()

        self.startItems = QVBoxLayout()
        self.boots = QVBoxLayout()
        self.coreItems = QVBoxLayout()
        self.lastItems = QHBoxLayout()

        self.vLine = SeparatorLine(QFrame.Shape.VLine)
        self.hLine1 = SeparatorLine(QFrame.Shape.HLine)
        self.hLine2 = SeparatorLine(QFrame.Shape.HLine)

        self.__initLayout()

    def __initLayout(self):
        self.bootsAndStartLayout.setContentsMargins(0, 0, 0, 0)
        self.bootsAndStartLayout.addLayout(self.startItems)
        self.bootsAndStartLayout.addSpacing(4)
        self.bootsAndStartLayout.addWidget(self.vLine)
        self.bootsAndStartLayout.addSpacing(4)
        self.bootsAndStartLayout.addLayout(self.boots)

        self.lastItems.setAlignment(Qt.AlignLeft)
        self.lastItems.setSpacing(3)
        self.startItems.setContentsMargins(0, 0, 0, 0)
        self.boots.setContentsMargins(0, 0, 0, 0)
        self.coreItems.setContentsMargins(0, 0, 0, 0)
        self.lastItems.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.setContentsMargins(13, 11, 13, 11)
        self.vBoxLayout.addLayout(self.bootsAndStartLayout)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.hLine1)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addLayout(self.lastItems)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.hLine2)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addLayout(self.coreItems)

    def __updateLayout(self, layout: QLayout, data: list):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)

            if widget := item.widget():
                widget.deleteLater()

        useSeparator = layout is self.coreItems

        if not layout is self.lastItems:
            for i, x in enumerate(data):
                items = ItemsWidget(x, useSeparator)
                layout.addWidget(items)
        else:
            for icon in data:
                label = RoundedLabel(icon)
                label.setFixedSize(32, 32)
                layout.addWidget(label)

    def updateWidget(self, data):
        self.__updateLayout(self.startItems, data['startItems'])
        self.__updateLayout(self.boots, data['boots'])
        self.__updateLayout(self.coreItems, data['coreItems'])
        self.__updateLayout(self.lastItems, data['lastItems'])

        self.setVisible(True)


class CounterChampionWidget(QFrame):
    def __init__(self, data, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.winRate = data['winRate']
        self.champion = ChampionWidget(data)
        self.winRateLabel = QLabel(f"{self.winRate*100:.2f}%")
        self.playsLabel = QLabel(f"{data['play']:,} " + self.tr("Games"))

        if self.winRate > 0.5:
            self.color = min(255 * (data['winRate'] - 0.5)*16 + 40, 255)
        else:
            self.color = min(255 * (0.5 - data['winRate'])*12 + 40, 200)

        self.__initWidget()
        self.__initLayout()

        self.setFixedHeight(32)

    def __initWidget(self):
        self.winRateLabel.setObjectName("boldBodyLabel")
        self.winRateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.winRateLabel.setFixedWidth(43)
        self.winRateLabel.setContentsMargins(0, 0, 0, 2)

        self.playsLabel.setObjectName("grayBodyLabel")
        self.playsLabel.setAlignment(Qt.AlignCenter)
        self.playsLabel.setFixedWidth(81)
        self.playsLabel.setContentsMargins(0, 0, 0, 2)

        self.__setColor()
        qconfig.themeChanged.connect(self.__setColor)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.champion)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addWidget(self.playsLabel)
        self.hBoxLayout.addSpacing(14)
        self.hBoxLayout.addWidget(self.winRateLabel)

    def __setColor(self):
        if self.winRate > 0.5:
            if not isDarkTheme():
                color = f"color: rgb({self.color}, 0, 0)"
            else:
                color = f"color: rgb(255, {255 - self.color}, {255 - self.color})"
        else:
            if not isDarkTheme():
                color = f"color: rgb(0, {self.color}, 0)"
            else:
                color = f"color: rgb({255 - self.color}, 255, {255 - self.color})"

        self.winRateLabel.setStyleSheet(color)


class ChampionWidget(QFrame):
    def __init__(self, data: dict, d=26, o=4, w=2, s=2, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.icon = RoundIcon(data['icon'], d, o, w)
        self.nameLabel = QLabel(data['name'])
        self.championId = data.get('championId')

        self.space = s

        self.__initWidget()
        self.__initLayout()

        cfg.themeChanged.connect(self.__setDefaultLabelColor)

    def __initWidget(self):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nameLabel.setObjectName("bodyLabel")
        self.nameLabel.setContentsMargins(0, 0, 0, 1)

    def __initLayout(self):
        self.hBoxLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.hBoxLayout.addWidget(self.icon, alignment=Qt.AlignCenter)
        self.hBoxLayout.addSpacing(self.space)
        self.hBoxLayout.addWidget(self.nameLabel, alignment=Qt.AlignCenter)

    # Q: 为什么这堆东西不写到 qss 里面？
    # A: 因为不会 ^^_
    #    qss 写不了类似 ChampionWidget:hover>#bodyLabel 一类的玩意
    def __setDefaultLabelColor(self):
        color = 'white' if isDarkTheme() else 'black'
        self.nameLabel.setStyleSheet(f"QLabel {{color: {color};}}")

    def __setHoverLabelColor(self):
        color = ThemeColor.DARK_1.color()
        self.nameLabel.setStyleSheet(f"QLabel {{color: {color.name()};}}")

    def __setPressedLabelColor(self):
        color = ThemeColor.LIGHT_1.color()
        self.nameLabel.setStyleSheet(f"QLabel {{color: {color.name()};}}")

    def enterEvent(self, e):
        self.__setHoverLabelColor()
        return super().enterEvent(e)

    def leaveEvent(self, a0):
        self.__setDefaultLabelColor()
        return super().leaveEvent(a0)

    def mousePressEvent(self, a0):
        self.__setPressedLabelColor()
        return super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0):
        self.__setHoverLabelColor()
        self.__onMouseClicked()

        return super().mouseReleaseEvent(a0)

    def __onMouseClicked(self):
        if not self.championId:
            return

        signalBus.toOpggBuildInterface.emit(self.championId, "", "")


class ChampionCountersWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.strongAgainstWidget = QWidget()
        self.strongAgainstLayout = QVBoxLayout(self.strongAgainstWidget)
        self.separatorLine = SeparatorLine(QFrame.Shape.VLine)

        self.weakAgainstWidget = QWidget()
        self.weakAgainstLayout = QVBoxLayout(self.weakAgainstWidget)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.strongAgainstLayout.setAlignment(Qt.AlignTop)
        self.strongAgainstLayout.setContentsMargins(0, 0, 0, 0)
        self.strongAgainstLayout.setSpacing(6)
        self.weakAgainstLayout.setAlignment(Qt.AlignTop)
        self.weakAgainstLayout.setContentsMargins(0, 0, 0, 0)
        self.weakAgainstLayout.setSpacing(6)

        self.hBoxLayout.setContentsMargins(13, 11, 13, 11)
        self.hBoxLayout.addWidget(self.strongAgainstWidget)
        self.hBoxLayout.addSpacing(4)
        self.hBoxLayout.addWidget(self.separatorLine)
        self.hBoxLayout.addSpacing(4)
        self.hBoxLayout.addWidget(self.weakAgainstWidget)

    def __updateLayout(self, layout: QLayout, data: list):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)

            if widget := item.widget():
                widget.deleteLater()

        for x in data:
            item = CounterChampionWidget(x)
            layout.addWidget(item)

    def updateWidget(self, data, summary: dict):
        if not data:
            self.setVisible(False)
            return

        strong = data['strongAgainst']
        weak = data['weakAgainst']

        if len(strong) == 0 and len(weak) == 0:
            self.setVisible(False)
            return

        self.__updateLayout(self.strongAgainstLayout, strong)
        self.__updateLayout(self.weakAgainstLayout, weak)

        tooltip = self.tr(f"<b>{summary.get('name')}</b>" +
                          self.tr("'s strong against"))
        self.strongAgainstWidget.setToolTip(tooltip)
        self.strongAgainstWidget.installEventFilter(
            ToolTipFilter(self.strongAgainstWidget, 300))

        tooltip = self.tr(f"<b>{summary.get('name')}</b>" +
                          self.tr("'s weak against"))
        self.weakAgainstWidget.setToolTip(tooltip)
        self.weakAgainstWidget.installEventFilter(
            ToolTipFilter(self.weakAgainstWidget))

        self.setVisible(True)


class ChampionPerksWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.perkShowLayout = QVBoxLayout()
        self.setRuneButton = PrimaryButton(self.tr("Set Rune Page"))
        self.perksView = PerksWidget()

        self.vLine = SeparatorLine(QFrame.Shape.VLine)

        self.perkSelectLayout = QVBoxLayout()
        self.summaryWidgets = [PerksSummaryWidget(),
                               PerksSummaryWidget(),
                               PerksSummaryWidget()]

        self.data = None
        self.selectedIndex = 0

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        for i, widget in enumerate(self.summaryWidgets):
            widget.clicked.connect(
                lambda index=i: self.__onSummaryWidgetClicked(index))

        self.setRuneButton.clicked.connect(self.__onSetRunePageButtonClicked)

    def __initLayout(self):
        self.perkShowLayout.setContentsMargins(0, 0, 0, 0)
        self.perkShowLayout.addWidget(self.perksView)

        self.perkSelectLayout.setContentsMargins(0, 0, 0, 0)
        self.perkSelectLayout.setSpacing(4)
        for widget in self.summaryWidgets:
            self.perkSelectLayout.addWidget(widget)

        self.perkSelectLayout.addWidget(self.setRuneButton)

        self.hBoxLayout.setAlignment(Qt.AlignLeft)
        self.hBoxLayout.setContentsMargins(7, 7, 4, 7)
        self.hBoxLayout.addLayout(self.perkShowLayout)
        self.hBoxLayout.addWidget(self.vLine)
        self.hBoxLayout.addLayout(self.perkSelectLayout)

    def updateWidget(self, data: list, summary: dict):
        if not data:
            self.setVisible(False)
            return

        self.data = data
        self.summary = summary
        self.selectedIndex = 0

        self.perksView.setCurrentPerks(
            data[0]['primaryId'], data[0]['secondaryId'], data[0]['perks'])

        for i, (d, widget) in enumerate(zip(data, self.summaryWidgets)):
            widget.updateSummary(d)
            widget.setProperty('selected', i == 0)
            widget.style().polish(widget)

        self.setVisible(True)

    def __onSummaryWidgetClicked(self, index):
        last = self.summaryWidgets[self.selectedIndex]
        last.setProperty("selected", False)
        last.style().polish(last)

        new: PerksSummaryWidget = self.summaryWidgets[index]
        new.setProperty("selected", True)
        new.style().polish(new)

        self.selectedIndex = index
        data = self.data[index]
        self.perksView.setCurrentPerks(
            data['primaryId'], data['secondaryId'], data['perks'])

    @asyncSlot(bool)
    async def __onSetRunePageButtonClicked(self, _):
        data = self.data[self.selectedIndex]
        name = "Seraphine" + self.tr(": ") + self.summary['name']

        await connector.deleteCurrentRunePage()
        await connector.createRunePage(
            name, data['primaryId'], data['secondaryId'], data['perks'])


class PerksSummaryWidget(NoBorderColorAnimationFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(type='default', parent=parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()
        self.runeIcon = RoundIcon(diameter=32, borderWidth=0)

        self.playsLayout = QVBoxLayout()
        self.winRateLabel = QLabel()
        self.playsLabel = QLabel()
        self.pickRateLabel = QLabel()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.winRateLabel.setObjectName("bodyLabel")
        self.winRateLabel.setAlignment(Qt.AlignCenter)
        self.playsLabel.setObjectName("grayBodyLabel")
        self.playsLabel.setAlignment(Qt.AlignCenter)
        self.playsLabel.setFixedWidth(81)
        self.pickRateLabel.setObjectName("boldBodyLabel")
        self.pickRateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pickRateLabel.setFixedWidth(43)

    def __initLayout(self):
        self.playsLayout.setAlignment(Qt.AlignCenter)
        self.playsLayout.setContentsMargins(0, 0, 0, 0)
        self.playsLayout.setSpacing(0)
        self.playsLayout.addWidget(self.winRateLabel)
        self.playsLayout.addWidget(self.playsLabel)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.runeIcon)
        # self.hBoxLayout.addWidget(self.subIcon)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addLayout(self.playsLayout)
        self.hBoxLayout.addSpacing(29)
        self.hBoxLayout.addWidget(self.pickRateLabel)

        self.vBoxLayout.setContentsMargins(5, 5, 8, 5)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addLayout(self.hBoxLayout)

    def updateSummary(self, data):
        self.runeIcon.setIcon(data['icons'][0])
        self.winRateLabel.setText(f"{data['win'] / data['play']*100:.2f}%")
        self.playsLabel.setText(f"{data['play']:,} " + self.tr("Games"))
        self.pickRateLabel.setText(f"{data['pickRate']*100:.2f}%")


class PerksWidget(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # self.setStyleSheet("PerksWidget{border: 1px solid black;}")
        self.gridLayout = QGridLayout(self)

        self.iconSize = 26

        self.mainTitleIcon = RoundIcon(diameter=self.iconSize, borderWidth=0)

        self.primaryPerksLayout = QVBoxLayout()
        self.primaryPerksSlots = [
            QHBoxLayout(),
            QHBoxLayout(),
            QHBoxLayout(),
            QHBoxLayout(),
        ]

        self.secondaryTitleIcon = RoundIcon(
            diameter=self.iconSize, borderWidth=0)

        self.secondaryPerksLayout = QVBoxLayout()
        self.secondaryPerksSlots = [
            QHBoxLayout(),
            QHBoxLayout(),
            QHBoxLayout(),
        ]

        self.shardsPerksLayout = QVBoxLayout()
        self.shardsPerksSlots = [
            QHBoxLayout(),
            QHBoxLayout(),
            QHBoxLayout(),
        ]

        self.perks = {}

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.primaryPerksLayout.setSpacing(8)
        self.primaryPerksLayout.setContentsMargins(0, 0, 0, 0)
        for layout in self.primaryPerksSlots:
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            self.primaryPerksLayout.addLayout(layout)

        self.primaryPerksSlots[0].setSpacing(0)

        self.secondaryPerksLayout.setSpacing(8)
        self.secondaryPerksLayout.setContentsMargins(0, 0, 0, 0)
        for layout in self.secondaryPerksSlots:
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            self.secondaryPerksLayout.addLayout(layout)

        self.shardsPerksLayout.setSpacing(8)
        self.shardsPerksLayout.setContentsMargins(0, 0, 0, 0)
        for layout in self.shardsPerksSlots:
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            self.shardsPerksLayout.addLayout(layout)

        self.gridLayout.setAlignment(Qt.AlignCenter)
        self.gridLayout.setHorizontalSpacing(18)
        self.gridLayout.setContentsMargins(0, 0, 4, 4)
        self.gridLayout.addWidget(
            self.mainTitleIcon, 0, 0, alignment=Qt.AlignCenter)
        self.gridLayout.addWidget(
            self.secondaryTitleIcon, 0, 1, alignment=Qt.AlignCenter)
        self.gridLayout.addLayout(
            self.primaryPerksLayout, 1, 0, alignment=Qt.AlignCenter)
        self.gridLayout.addLayout(
            self.secondaryPerksLayout, 1, 1, alignment=Qt.AlignCenter)
        self.gridLayout.addLayout(
            self.shardsPerksLayout, 1, 2, alignment=Qt.AlignCenter)

    def __clearPerks(self, layouts: List[QLayout]):
        for layout in layouts:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                layout.removeItem(item)

                if widget := item.widget():
                    widget.deleteLater()

    def clear(self):
        self.__clearPerks(self.primaryPerksSlots)
        self.__clearPerks(self.secondaryPerksSlots)
        self.__clearPerks(self.shardsPerksSlots)

        self.perks = {}
        self.shards = {}

    def setPerkStyle(self, main, sub):
        styles = connector.manager.getPerkStyles()

        main = styles[main]
        self.mainTitleIcon.setIcon(main['icon'])
        self.mainTitleIcon.setToolTip(main['name'])
        self.mainTitleIcon.installEventFilter(ToolTipFilter(
            self.mainTitleIcon, 200, ToolTipPosition.TOP))

        for i, slot in enumerate(main['slots'][:4]):
            for perk in slot:
                if i != 0:
                    icon = RoundIcon(
                        perk['icon'], self.iconSize, 0, 2, enabled=False)
                else:
                    icon = RoundIcon(
                        perk['icon'], self.iconSize + 12, 0, 0, enabled=False)

                self.primaryPerksSlots[i].addWidget(icon)
                self.perks[perk['runeId']] = icon

                icon.setToolTip(f"<b>{perk['name']}</b><br><br>{perk['desc']}")
                icon.installEventFilter(ToolTipFilter(
                    icon, 200, ToolTipPosition.TOP))

        sub = styles[sub]
        self.secondaryTitleIcon.setIcon(sub['icon'])
        self.secondaryTitleIcon.setToolTip(sub['name'])
        self.secondaryTitleIcon.installEventFilter(ToolTipFilter(
            self.secondaryTitleIcon, 200, ToolTipPosition.TOP))

        for i, slot in enumerate(sub['slots'][1:4]):
            for perk in slot:
                icon = RoundIcon(
                    perk['icon'], self.iconSize, 0, 2, enabled=False)
                self.secondaryPerksSlots[i].addWidget(icon)
                self.perks[perk['runeId']] = icon

                icon.setToolTip(f"<b>{perk['name']}</b><br><br>{perk['desc']}")
                icon.installEventFilter(ToolTipFilter(
                    icon, 200, ToolTipPosition.TOP))

        for i, slot in enumerate(main['slots'][4:]):
            for perk in slot:
                icon = RoundIcon(perk['icon'], self.iconSize-4,
                                 0, 0, drawBackground=True, enabled=False)
                self.shardsPerksSlots[i].addWidget(icon)

                self.shards[(perk['runeId'], i)] = icon

                icon.setToolTip(f"<b>{perk['name']}</b><br><br>{perk['desc']}")
                icon.installEventFilter(ToolTipFilter(
                    icon, 200, ToolTipPosition.TOP))

    def setPerks(self, perks):
        for id in perks[:-3]:
            if icon := self.perks.get(id):
                icon.setEnabeld(True)

        for (i, id) in enumerate(perks[-3:]):
            if icon := self.shards.get((id, i)):
                icon.setEnabeld(True)

    def setCurrentPerks(self, primaryId, secondaryId, perks):
        self.clear()

        self.setPerkStyle(primaryId, secondaryId)
        self.setPerks(perks)


class ChampionAugmentsWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.augmentsLayouts = [QVBoxLayout() for _ in range(3)]

        self.vLine1 = SeparatorLine(QFrame.Shape.VLine)
        self.vLine2 = SeparatorLine(QFrame.Shape.VLine)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        for layout in self.augmentsLayouts:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignTop)
            layout.setSpacing(12)

        self.hBoxLayout.setSpacing(12)
        self.hBoxLayout.setContentsMargins(13, 11, 13, 11)
        self.hBoxLayout.addLayout(self.augmentsLayouts[0])
        self.hBoxLayout.addWidget(self.vLine1)
        self.hBoxLayout.addLayout(self.augmentsLayouts[1])
        self.hBoxLayout.addWidget(self.vLine2)
        self.hBoxLayout.addLayout(self.augmentsLayouts[2])

    def __clearLayouts(self):
        for layout in self.augmentsLayouts:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                layout.removeItem(item)

                if widget := item.widget():
                    widget.deleteLater()

    def updateWidget(self, data):
        if data == None:
            self.setVisible(False)
            return

        self.__clearLayouts()
        for i, (data, layout) in enumerate(zip(data, self.augmentsLayouts)):
            for augment in data:
                item = AugmentItemBar(augment, i)
                layout.addWidget(item)

        self.setVisible(True)


class AugmentItemBar(QFrame):
    def __init__(self, data, color, parent: QWidget = None):
        super().__init__(parent)

        if color == 0:
            borderColor = QColor(153, 176, 180)
        elif color == 1:
            borderColor = QColor(194, 172, 141)
        else:
            borderColor = QColor(184, 123, 255)

        self.hBoxLayout = QHBoxLayout(self)
        self.icon = RoundedLabel(
            data['icon'], 4, 6, borderColor, True)

        self.nameLayout = QVBoxLayout()
        self.name = QLabel(data['name'])

        self.firstRateLayout = QHBoxLayout()
        self.firstRateText = QLabel(f"{data['play']:,} "+self.tr("Games"))
        self.firstRate = QLabel(
            f"{data['firstPlace'] / data['play'] * 100:.2f}%")

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.icon.setFixedSize(32, 32)
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setObjectName("bodyLabel")

        self.firstRateText.setObjectName("grayBodyLabel")
        self.firstRate.setObjectName("boldBodyLabel")

        self.firstRate.setToolTip(self.tr("First Rate"))
        self.firstRate.installEventFilter(ToolTipFilter(self.firstRate, 100))

    def __initLayout(self):
        self.firstRateLayout.setContentsMargins(0, 0, 0, 0)
        self.firstRateLayout.setAlignment(Qt.AlignLeft)
        self.firstRateLayout.setSpacing(0)
        self.firstRateLayout.addWidget(self.firstRateText)
        self.firstRateLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.firstRateLayout.addWidget(self.firstRate)

        self.nameLayout.setContentsMargins(0, 0, 0, 0)
        self.nameLayout.setSpacing(0)
        self.nameLayout.setAlignment(Qt.AlignCenter)
        self.nameLayout.addWidget(self.name, alignment=Qt.AlignLeft)
        self.nameLayout.addLayout(self.firstRateLayout)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addLayout(self.nameLayout)


class ChampionSynergiesWidget(BuildWidgetBase):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(13, 11, 13, 11)
        self.vBoxLayout.setSpacing(8)

    def __clearLayout(self):
        for i in reversed(range(self.vBoxLayout.count())):
            item = self.vBoxLayout.itemAt(i)
            self.vBoxLayout.removeItem(item)

            if widget := item.widget():
                widget.deleteLater()

    def updateWidget(self, data):
        if not data:
            self.setVisible(False)
            return

        self.__clearLayout()

        for x in data:
            item = SynergyItemWidget(x)
            self.vBoxLayout.addWidget(item)

        self.setVisible(True)


class SynergyItemWidget(QFrame):
    def __init__(self, data, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.champion = ChampionWidget(data, 32, 4, 3, 5)

        self.averagePlaceLayout = QVBoxLayout()
        self.averagePlaceTextLabel = QLabel(self.tr("Average Place"))
        self.averagePlaceLabel = QLabel(
            f"{data['totalPlace'] / data['play']:.2f}")

        self.firstRateLayout = QVBoxLayout()
        self.firstRateTextLabel = QLabel(self.tr("First Rate"))
        self.firstRateLabel = QLabel(
            f"{data['firstPlace'] / data['play'] * 100:.2f}%")

        self.winRateLayout = QVBoxLayout()
        self.winRateLabel = QLabel(
            f"{data['win'] / data['play'] * 100:.2f}%")
        self.playLabel = QLabel(f"{data['play']:,} " + self.tr("Games"))

        self.pickRateLabel = QLabel(f"{data['pickRate']*100:.2f}%")

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.averagePlaceLabel.setObjectName("bodyLabel")
        self.averagePlaceTextLabel.setObjectName("grayBodyLabel")
        self.averagePlaceTextLabel.setFixedWidth(81)
        self.averagePlaceTextLabel.setAlignment(Qt.AlignCenter)

        self.firstRateLabel.setObjectName("bodyLabel")
        self.firstRateTextLabel.setObjectName("grayBodyLabel")
        self.firstRateTextLabel.setFixedWidth(81)
        self.firstRateTextLabel.setAlignment(Qt.AlignCenter)

        self.winRateLabel.setObjectName("bodyLabel")
        self.playLabel.setObjectName("grayBodyLabel")
        self.playLabel.setFixedWidth(81)
        self.playLabel.setAlignment(Qt.AlignCenter)

        self.pickRateLabel.setObjectName("boldBodyLabel")
        self.pickRateLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pickRateLabel.setFixedWidth(43)

    def __initLayout(self):
        self.averagePlaceLayout.setContentsMargins(0, 0, 0, 0)
        self.averagePlaceLayout.setSpacing(0)
        self.averagePlaceLayout.setAlignment(Qt.AlignCenter)
        self.averagePlaceLayout.addWidget(
            self.averagePlaceLabel, alignment=Qt.AlignCenter)
        self.averagePlaceLayout.addWidget(
            self.averagePlaceTextLabel, alignment=Qt.AlignCenter)

        self.firstRateLayout.setContentsMargins(0, 0, 0, 0)
        self.firstRateLayout.setSpacing(0)
        self.firstRateLayout.setAlignment(Qt.AlignCenter)
        self.firstRateLayout.addWidget(
            self.firstRateLabel, alignment=Qt.AlignCenter)
        self.firstRateLayout.addWidget(
            self.firstRateTextLabel, alignment=Qt.AlignCenter)

        self.winRateLayout.setContentsMargins(0, 0, 0, 0)
        self.winRateLayout.setSpacing(0)
        self.winRateLayout.setAlignment(Qt.AlignCenter)
        self.winRateLayout.addWidget(
            self.winRateLabel, alignment=Qt.AlignCenter)
        self.winRateLayout.addWidget(self.playLabel, alignment=Qt.AlignCenter)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.champion)
        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addLayout(self.averagePlaceLayout)
        self.hBoxLayout.addSpacing(2)
        self.hBoxLayout.addLayout(self.firstRateLayout)
        # self.hBoxLayout.addSpacing(22)
        self.hBoxLayout.addLayout(self.winRateLayout)
        self.hBoxLayout.addSpacing(21)
        self.hBoxLayout.addWidget(self.pickRateLabel)
