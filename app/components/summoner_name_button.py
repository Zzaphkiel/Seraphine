from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt


class SummonerName(QPushButton):

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(text)
