from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import ToolTipPosition, ToolTipFilter


class SummonerName(QLabel):
    clicked = pyqtSignal(bool)

    def __init__(self, text, isPublic=True, color=None, tagLine=None, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(text if isPublic else f"{text}🫣")

        self.setAlignment(Qt.AlignCenter)

        self.setWordWrap(True)
        self.setProperty('pressed', False)
        if color:
            self.setStyleSheet(f"color: {color}")

            if color == "#bf242a":
                self.setToolTip(self.tr("Former enemy"))
            else:
                self.setToolTip(self.tr("Former ally"))

            self.installEventFilter(
                ToolTipFilter(self, 0, ToolTipPosition.BOTTOM))

        self.tagLine = tagLine

    def text(self) -> str:
        name = super().text().replace("🫣", "")

        if len(self.tagLine):
            name += f'#{self.tagLine}'

        return name

    def mousePressEvent(self, ev) -> None:
        self.setProperty('pressed', True)
        self.style().polish(self)

        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, a0) -> None:
        self.setProperty("pressed", False)
        self.style().polish(self)

        self.clicked.emit(True)

        return super().mouseReleaseEvent(a0)
