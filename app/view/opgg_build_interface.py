
from PyQt5.QtWidgets import (QHBoxLayout, QWidget, QFrame, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QLabel, QHBoxLayout, QWidget, QLabel, QFrame,
                             QVBoxLayout, QSpacerItem, QSizePolicy, QLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QEasingCurve
from PyQt5.QtGui import QPixmap, QColor
from qasync import asyncSlot

from app.lol.tools import ToolsTranslator
from app.components.animation_frame import ColorAnimationFrame
from app.components.transparent_button import TransparentButton
from app.components.champion_icon_widget import RoundIcon, RoundedLabel
from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import BodyLabel, SmoothScrollArea, FlowLayout, IconWidget
from app.common.icons import Icon


class BuildInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()

        self.titleBar = ChampionTitleBar()
        self.summonerSpells = SummonerSpellsWidget()
        self.championSkills = ChampionSkillsWidget()
        self.championItems = ChampionItemWidget()

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
        self.scrollArea.setViewportMargins(10, 10, 17, 10)
        self.scrollWidget.setContentsMargins(0, 0, 0, 0)

        self.scrollLayout.addWidget(self.titleBar)
        self.scrollLayout.addWidget(self.summonerSpells)
        self.scrollLayout.addWidget(self.championSkills)
        self.scrollLayout.addWidget(self.championItems)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.scrollArea)

    def setCurrentChampionId(self, id):
        self.championId = id

    def getCurrentChampionId(self):
        return self.championId

    def updateInterface(self, data):
        self.titleBar.updateWidget(data['summary'])
        self.summonerSpells.updateWidget(data['summonerSpells'])
        self.championSkills.updateWidget(data['championSkills'])
        self.championItems.updateWidget(data['items'])


class ChampionTitleBar(ColorAnimationFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(type="default", parent=parent)
        self._pressedBackgroundColor = self._hoverBackgroundColor

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setAlignment(Qt.AlignLeft)

        self.nameLayout = QVBoxLayout()
        self.icon = RoundIcon('app/resource/images/champion-0.png', 54, 3, 3)
        self.name = QLabel()
        self.position = QLabel()

        self.winRateLayout = QVBoxLayout()
        self.winRateTextLabel = QLabel(self.tr("Win Rate"))
        self.winRateLabel = QLabel()

        self.pickRateLabel = QLabel()
        self.pickRateLayout = QVBoxLayout()
        self.pickRateTextLabel = QLabel(self.tr("Pick Rate"))

        self.banRateLabel = QLabel()
        self.banRateLayout = QVBoxLayout()
        self.banRateTextLabel = QLabel(self.tr("Ban Rate"))

        self.line1 = QFrame()
        self.line2 = QFrame()

        self.tierLabel = QLabel()

        self.__initWidget()
        self.__initLayout()

        self.setVisible(False)

    def updateWidget(self, data):
        ts = ToolsTranslator()
        self.setType(f"tier{data['tier']}")

        self.icon.setIcon(data['icon'])

        self.name.setText(data['name'])
        self.position.setText(ts.positionMap[data['position']])

        self.winRateLabel.setText(f"{data['winRate']*100:.2f}%")
        self.pickRateLabel.setText(f"{data['pickRate']*100:.2f}%")
        self.banRateLabel.setText(f"{data['banRate']*100:.2f}%")

        _, _, _, color = self.getColors()
        self.line1.setStyleSheet(f"color: {color.name(QColor.HexArgb)};")
        self.line2.setStyleSheet(f"color: {color.name(QColor.HexArgb)};")

        tierIcon = f"app/resource/images/icon-tier-{data['tier']}.svg"
        self.tierLabel.setPixmap(QPixmap(tierIcon))

        self.setVisible(True)

    def __initWidget(self):
        self.name.setObjectName("titleLabel")
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

        self.vLine = QFrame()

        self.__initWidget()
        self.__initLayout()

        self.setVisible(False)

    def __initWidget(self):
        self.vLine.setFrameShape(QFrame.Shape.VLine)
        self.vLine.setLineWidth(1)
        self.vLine.setObjectName("separatorLine")

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(11, 9, 11, 9)
        self.hBoxLayout.addWidget(self.spell1)
        self.hBoxLayout.addSpacing(4)
        self.hBoxLayout.addWidget(self.vLine)
        self.hBoxLayout.addSpacing(4)
        self.hBoxLayout.addWidget(self.spell2)

    def updateWidget(self, data):
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

        self.setVisible(False)

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
    def __init__(self, data, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.iconsLayout = QHBoxLayout()

        self.iconSize = 32

        self.winRateLayout = QVBoxLayout()
        self.winRateLabel = QLabel()
        self.gamesLabel = QLabel()

        self.pickRateLabel = QLabel()

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
        for i in data['icons']:
            icon = RoundedLabel()
            icon.setPicture(i)
            icon.setFixedSize(self.iconSize, self.iconSize)
            self.iconsLayout.addWidget(icon)

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

        self.vLine = QFrame()
        self.hLine1 = QFrame()
        self.hLine2 = QFrame()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.vLine.setFrameShape(QFrame.Shape.VLine)
        self.vLine.setLineWidth(1)
        self.vLine.setObjectName("separatorLine")
        self.hLine1.setFrameShape(QFrame.Shape.HLine)
        self.hLine1.setLineWidth(1)
        self.hLine1.setObjectName("separatorLine")
        self.hLine2.setFrameShape(QFrame.Shape.HLine)
        self.hLine2.setLineWidth(1)
        self.hLine2.setObjectName("separatorLine")

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

    def __updateClass(self, layout: QLayout, data: list):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)

            if widget := item.widget():
                widget.deleteLater()

        if not layout is self.lastItems:
            for i in data:
                items = ItemsWidget(i)
                layout.addWidget(items)
        else:
            for icon in data:
                label = RoundedLabel(icon)
                label.setFixedSize(32, 32)
                layout.addWidget(label)

    def updateWidget(self, data):
        self.__updateClass(self.startItems, data['startItems'])
        self.__updateClass(self.boots, data['boots'])
        self.__updateClass(self.coreItems, data['coreItems'])
        self.__updateClass(self.lastItems, data['lastItems'])
