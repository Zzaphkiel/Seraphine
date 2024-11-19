from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPixmap, QPen, QPainter, QColor

from app.common.qfluentwidgets import isDarkTheme, Theme
from app.common.signals import signalBus
from app.common.config import cfg
from app.components.champion_icon_widget import RoundIcon, RoundedLabel
from app.components.color_label import ColorLabel, DeathsLabel
from app.components.animation_frame import CardWidget, ColorAnimationFrame


class RoundLevel(QFrame):
    def __init__(self, level, diameter, parent=None):
        super().__init__(parent)
        self.level = str(level)
        self.setFixedSize(diameter, diameter)
        self.setStyleSheet("RoundLevel{border: 1px solid black}")
        self.setStyleSheet("RoundLevel {font: bold 11px 'Segoe UI'}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.TextAntialiasing | QPainter.Antialiasing)
        if isDarkTheme():
            painter.setPen(QPen(QColor(120, 90, 40), 1, Qt.SolidLine))
            painter.setBrush(QColor(1, 10, 19))
            painter.drawEllipse(0, 0, self.width(), self.height())

            painter.setPen(QColor(153, 148, 135))
            painter.drawText(QRect(0, -1, 22, 22), Qt.AlignCenter, self.level)
        else:
            painter.setPen(QPen(QColor(120, 90, 40), 1, Qt.SolidLine))
            painter.setBrush(QColor(249, 249, 249))
            painter.drawEllipse(0, 0, self.width(), self.height())

            painter.setPen(QColor(1, 10, 19))
            painter.drawText(QRect(0, -1, 22, 22), Qt.AlignCenter, self.level)


class RoundIconWithLevel(QWidget):
    def __init__(self, icon, level, parent=None):
        super().__init__(parent)
        self.icon = RoundIcon(icon, 58, 6, 4, parent=self)
        self.level = RoundLevel(level, 22, self)
        self.level.move(42, 36)

        self.setFixedSize(64, 58)


class ResultModeSpell(QFrame):
    def __init__(self, remake, win, mode, spell1, spell2, rune, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.spellsLayout = QHBoxLayout()
        self.resultLabel = ColorLabel()

        if remake:
            self.resultLabel.setText(self.tr("Remake"))
            self.resultLabel.setType('remake')

        elif win:
            self.resultLabel = ColorLabel(self.tr("Win"), 'win')
        else:
            self.resultLabel = ColorLabel(self.tr("Lose"), 'lose')

        self.modeLabel = QLabel(mode)
        self.modeLabel.setStyleSheet("QLabel {font: 12px;}")

        self.spell1 = RoundedLabel(spell1, 0, 2)
        self.spell2 = RoundedLabel(spell2, 0, 2)
        self.spell1.setFixedSize(22, 22)
        self.spell2.setFixedSize(22, 22)

        self.rune = RoundedLabel(rune, 0, 0)
        self.rune.setFixedSize(24, 24)

        self.__initLayout()
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # self.setStyleSheet("ResultModeSpell {border: 1px solid black;}")

    def __initLayout(self):
        self.setMinimumWidth(100)

        self.spellsLayout.setSpacing(0)
        self.spellsLayout.addWidget(self.spell1)
        self.spellsLayout.addWidget(self.spell2)
        self.spellsLayout.addSpacing(5)
        self.spellsLayout.addWidget(self.rune)
        self.spellsLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.resultLabel)
        self.vBoxLayout.addWidget(self.modeLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addLayout(self.spellsLayout)


class ItemsKdaCsGold(QFrame):
    def __init__(self, items, kills, deaths, assists, cs, gold, parent=None):
        super().__init__(parent)
        self.setFixedSize(550, 67)

        self.vBoxLayout = QHBoxLayout(self)
        self.itemsLayout = QHBoxLayout()

        self.kills = QLabel(f"{kills}")
        self.slash1 = QLabel("/")
        self.deaths = DeathsLabel(f"{deaths}")
        self.slash2 = QLabel("/")
        self.assists = QLabel(f"{assists}")

        self.csLabel = QLabel(f"{cs}")
        self.goldLabel = QLabel(format(gold, ","))

        self.kills.setAlignment(Qt.AlignCenter)
        self.kills.setContentsMargins(0, 0, 0, 2)
        self.kills.setFixedWidth(23)
        self.kills.setObjectName("kills")
        self.slash1.setAlignment(Qt.AlignCenter)
        self.slash1.setContentsMargins(0, 0, 0, 2)
        self.slash1.setFixedWidth(9)
        self.slash1.setObjectName("slash1")
        self.deaths.setAlignment(Qt.AlignCenter)
        self.deaths.setContentsMargins(0, 0, 0, 2)
        self.deaths.setFixedWidth(23)
        self.deaths.setObjectName("deaths")
        self.slash2.setAlignment(Qt.AlignCenter)
        self.slash2.setContentsMargins(0, 0, 0, 2)
        self.slash2.setFixedWidth(9)
        self.slash2.setObjectName("slash2")
        self.assists.setAlignment(Qt.AlignCenter)
        self.assists.setContentsMargins(0, 0, 0, 2)
        self.assists.setFixedWidth(23)
        self.assists.setObjectName("assists")

        # self.kills.setStyleSheet("border: 1px solid black;")
        # self.slash1.setStyleSheet("border: 1px solid black;")
        # self.deaths.setStyleSheet("border: 1px solid black;")
        # self.slash2.setStyleSheet("border: 1px solid black;")
        # self.assists.setStyleSheet("border: 1px solid black;")

        self.csLabel.setAlignment(Qt.AlignCenter)
        self.csLabel.setContentsMargins(0, 0, 0, 2)
        self.goldLabel.setAlignment(Qt.AlignCenter)
        self.goldLabel.setContentsMargins(0, 0, 0, 2)
        self.goldLabel.setFixedWidth(55)

        self.csIcon = RoundedLabel(borderWidth=0, radius=0)
        color = "white" if isDarkTheme() else "black"
        self.csIcon.setPicture(f"app/resource/images/Minions_{color}.png")
        self.csIcon.setFixedSize(16, 16)
        self.csIcon.setAlignment(Qt.AlignCenter)

        self.goldIcon = RoundedLabel(borderWidth=0, radius=0)
        self.goldIcon.setPicture(f"app/resource/images/Gold_{color}.png")
        self.goldIcon.setFixedSize(16, 16)
        self.goldIcon.setAlignment(Qt.AlignCenter)

        # self.csLabel.setStyleSheet("QLabel {border: 1px solid black;}")
        # self.goldLabel.setStyleSheet("QLabel {border: 1px solid black;}")

        self.__initLayout(items)
        #  self.setStyleSheet("ItemsKdaCsGold {border: 1px solid black;}")
        cfg.themeChanged.connect(self.__updateIconColor)

    def __initLayout(self, items):
        self.itemsLayout.setSpacing(0)

        for item in items:
            image = RoundedLabel(item, 1)
            image.setFixedSize(34, 34)

            self.itemsLayout.addWidget(image)

        self.csLabel.setFixedWidth(40)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.kills)
        self.vBoxLayout.addSpacing(-11)
        self.vBoxLayout.addWidget(self.slash1)
        self.vBoxLayout.addSpacing(-11)
        self.vBoxLayout.addWidget(self.deaths)
        self.vBoxLayout.addSpacing(-11)
        self.vBoxLayout.addWidget(self.slash2)
        self.vBoxLayout.addSpacing(-11)
        self.vBoxLayout.addWidget(self.assists)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.csLabel)
        self.vBoxLayout.addSpacing(-6)
        self.vBoxLayout.addWidget(self.csIcon)
        self.vBoxLayout.addSpacing(15)
        self.vBoxLayout.addLayout(self.itemsLayout)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.goldLabel)
        self.vBoxLayout.addSpacing(-3)
        self.vBoxLayout.addWidget(self.goldIcon)

    def __updateIconColor(self, theme: Theme):
        color = "white" if theme == Theme.DARK else "black"
        self.csIcon.setPicture(f"app/resource/images/Minions_{color}.png")
        self.goldIcon.setPicture(f"app/resource/images/Gold_{color}.png")


class MapTime(QFrame):
    def __init__(self, map, position, time, duration, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)

        self.mapLabel = QLabel(
            f'{map} - {position}' if position != None else f'{map}')
        self.timeLabel = QLabel(f"{duration} · {time}")

        self.__initLayout()

        # self.setStyleSheet("MapTime {border: 1px solid black}")

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 5, 0, 0)
        self.mapLabel.setStyleSheet("QLabel {font: 12px;}")
        self.timeLabel.setStyleSheet("QLabel {font: 12px;}")

        self.vBoxLayout.addWidget(self.mapLabel)
        self.vBoxLayout.addWidget(self.timeLabel)
        self.vBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )


class GameInfoBar(ColorAnimationFrame):
    def __init__(self, game: dict = None, parent: QWidget = None):
        if game['remake']:
            type = 'remake'
        elif game['win']:
            type = 'win'
        else:
            type = 'lose'

        self.gameId = game['gameId']

        super().__init__(type=type, parent=parent)
        self.hBoxLayout = QHBoxLayout(self)

        self.setProperty('pressed', False)

        self.__initWidget(game)
        self.__initLayout()

        self.clicked.connect(
            lambda: signalBus.careerGameBarClicked.emit(str(self.gameId)))

    def __initWidget(self, game):
        self.championIcon = RoundIconWithLevel(
            game["championIcon"], game["champLevel"])
        self.resultModeSpells = ResultModeSpell(
            game["remake"],
            game["win"],
            game["name"],
            game["spell1Icon"],
            game["spell2Icon"],
            game["runeIcon"],
        )
        self.itemsKdaCsGold = ItemsKdaCsGold(
            game["itemIcons"],
            game["kills"],
            game["deaths"],
            game["assists"],
            game["cs"],
            game["gold"],
        )
        self.mapTime = MapTime(
            game["map"], game['position'], game["time"], game["duration"])

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(11, 8, 11, 8)
        self.hBoxLayout.addWidget(self.championIcon)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.resultModeSpells)
        self.hBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.hBoxLayout.addWidget(self.itemsKdaCsGold)
        self.hBoxLayout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.hBoxLayout.addSpacing(15)
        self.hBoxLayout.addWidget(self.mapTime)
