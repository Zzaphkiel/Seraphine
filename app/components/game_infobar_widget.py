from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QPixmap, QPen, QPainter, QColor
from qfluentwidgets import isDarkTheme, Theme

from ..common.config import cfg
from ..components.champion_icon_widget import RoundIcon


class RoundLevel(QFrame):
    def __init__(self, level, diameter, parent=None):
        super().__init__(parent)
        self.level = str(level)
        self.setFixedSize(diameter, diameter)
        self.setStyleSheet("RoundLevel{border: 1px solid black}")

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

        self.setStyleSheet("RoundLevel {font: bold 11px 'Segoe UI'}")


class RoundIconWithLevel(QWidget):
    def __init__(self, icon, level, parent=None):
        super().__init__(parent)
        self.icon = RoundIcon(icon, 58, 6, 4, self)
        self.level = RoundLevel(level, 22, self)
        self.level.move(42, 36)

        self.setFixedSize(64, 58)


class ResultModeSpell(QFrame):
    def __init__(self, remake, win, mode, spell1, spell2, rune, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.spellsLayout = QHBoxLayout()
        self.resultLabel = QLabel()

        if remake:
            color = "162, 162, 162"
            self.resultLabel.setText(self.tr("Remake"))
        elif win:
            color = "57, 176, 27"
            self.resultLabel.setText(self.tr("Win"))
        else:
            color = "211, 25, 12"
            self.resultLabel.setText(self.tr("Lose"))

        self.resultLabel.setStyleSheet(
            f"QLabel {{color: rgb({color}); font: bold 16px;}}"
        )
        self.modeLabel = QLabel(mode)
        self.modeLabel.setStyleSheet("QLabel {font: 12px;}")

        self.spell1 = QLabel()
        self.spell2 = QLabel()
        self.spell1.setPixmap(
            QPixmap(spell1).scaled(
                22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.spell2.setPixmap(
            QPixmap(spell2).scaled(
                22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

        self.spell1.setFixedSize(22, 22)
        self.spell2.setFixedSize(22, 22)
        self.spell1.setStyleSheet("QLabel {border: 1px solid rgb(70, 55, 20)}")
        self.spell2.setStyleSheet("QLabel {border: 1px solid rgb(70, 55, 20)}")

        self.rune = QLabel()
        self.rune.setPixmap(
            QPixmap(rune).scaled(
                24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
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

        self.kdaLabel = QLabel(f"{kills} / {deaths} / {assists}")
        self.csLabel = QLabel(f"{cs}")
        self.goldLabel = QLabel(format(gold, ","))

        self.kdaLabel.setAlignment(Qt.AlignCenter)
        self.csLabel.setAlignment(Qt.AlignCenter)
        self.goldLabel.setAlignment(Qt.AlignCenter)
        self.goldLabel.setFixedWidth(55)

        self.csIcon = QLabel()
        color = "white" if isDarkTheme() else "black"
        self.csIcon.setPixmap(
            QPixmap(f"app/resource/images/Minions_{color}.png").scaled(
                16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.csIcon.setFixedSize(16, 16)
        self.csIcon.setAlignment(Qt.AlignCenter)

        self.goldIcon = QLabel()
        self.goldIcon.setPixmap(
            QPixmap(f"app/resource/images/Gold_{color}.png").scaled(
                16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.goldIcon.setFixedSize(16, 16)
        self.goldIcon.setAlignment(Qt.AlignCenter)

        # self.kdaLabel.setStyleSheet("QLabel {border: 1px solid black;}")
        # self.csLabel.setStyleSheet("QLabel {border: 1px solid black;}")
        # self.goldLabel.setStyleSheet("QLabel {border: 1px solid black;}")

        self.__initLayout(items)
        #  self.setStyleSheet("ItemsKdaCsGold {border: 1px solid black;}")
        cfg.themeChanged.connect(self.__updateIconColor)

    def __initLayout(self, items):
        self.itemsLayout.setSpacing(0)

        for item in items:
            image = QLabel()
            image.setPixmap(
                QPixmap(item).scaled(
                    34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            image.setFixedSize(34, 34)
            image.setStyleSheet("QLabel {border: 1px solid rgb(70, 55, 20)}")

            self.itemsLayout.addWidget(image)

        self.kdaLabel.setFixedWidth(90)
        self.csLabel.setFixedWidth(30)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.kdaLabel)
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
        self.csIcon.setPixmap(
            QPixmap(f"app/resource/images/Minions_{color}.png").scaled(
                16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.goldIcon.setPixmap(
            QPixmap(f"app/resource/images/Gold_{color}.png").scaled(
                16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )


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


class GameInfoBar(QFrame):
    def __init__(self, game: dict = None, parent: QWidget = None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)

        self.setProperty('pressed', False)
        self.gameId = game['gameId']

        self.__initWidget(game)
        self.__initLayout()

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

        self.__setColor(game["remake"], game["win"])

    def __setColor(self, remake, win):
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
            f""" GameInfoBar {{
            border-radius: 6px;
            border: 1px solid rgb({r}, {g}, {b});
            background-color: rgba({r}, {g}, {b}, 0.15);
        }}
        GameInfoBar:hover {{
            border-radius: 6px;
            border: 1px solid rgb({r1}, {g1}, {b1});
            background-color: rgba({r1}, {g1}, {b1}, 0.2);
        }}
        GameInfoBar[pressed = true] {{
            border-radius: 6px;
            border: 1px solid rgb({r2}, {g2}, {b2});
            background-color: rgba({r2}, {g2}, {b2}, 0.25);
        }}""")

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

    def mousePressEvent(self, a0) -> None:
        self.setProperty("pressed", True)
        self.style().polish(self)
        return super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0) -> None:
        self.setProperty("pressed", False)
        self.style().polish(self)

        self.parent().parent().parent().parent().gameInfoBarClicked.emit(str(self.gameId))
        return super().mouseReleaseEvent(a0)
