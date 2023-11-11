from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpacerItem, QSizePolicy

from app.components.champion_icon_widget import RoundIcon


class ChartIconLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.buffer = []

    def updateIcon(self, info):
        """

        @param info: dict[召唤师名: 英雄图标path]
        @return:
        """

        if self.buffer:
            idx = 0
            for name, championIcon in info.items():
                self.buffer[idx].image = QPixmap(championIcon)
                self.buffer[idx].setToolTip(name)
                idx += 1
            return

        for name, championIcon in info.items():
            icon = RoundIcon(championIcon, 32, 0, 5)
            icon.setToolTip(name)
            self.vBoxLayout.addWidget(icon)
            self.buffer.append(icon)

        self.vBoxLayout.setContentsMargins(self.width() * .07, self.height() * 0.168, 0, self.height() * 0.14)

