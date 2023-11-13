from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal


class SummonerName(QLabel):
    clicked = pyqtSignal(bool)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(text)

        self.setAlignment(Qt.AlignCenter)

        self.setWordWrap(True)
        self.setProperty('pressed', False)

    def mousePressEvent(self, ev) -> None:
        self.setProperty('pressed', True)
        self.style().polish(self)

        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, a0) -> None:
        self.setProperty("pressed", False)
        self.style().polish(self)

        self.clicked.emit(True)

        return super().mouseReleaseEvent(a0)
