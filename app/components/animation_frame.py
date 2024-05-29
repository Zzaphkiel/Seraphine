from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from app.common.qfluentwidgets import BackgroundAnimationWidget, isDarkTheme

from app.common.style_sheet import ColorChangeable


class CardWidget(BackgroundAnimationWidget, QFrame):
    clicked = pyqtSignal()
    pressed = pyqtSignal()

    def __init__(self, parent=None, type=None):
        QFrame.__init__(self, parent=parent)
        if type:
            BackgroundAnimationWidget.__init__(self, type=type)
        else:
            BackgroundAnimationWidget.__init__(self)
        self._isClickEnabled = False
        self._borderRadius = 4

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.pressed.emit()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setClickEnabled(self, isEnabled: bool):
        self._isClickEnabled = isEnabled
        self.update()

    def isClickEnabled(self):
        return self._isClickEnabled

    def _normalBackgroundColor(self):
        return QColor(233, 233, 233, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        return QColor(243, 243, 243, 21 if isDarkTheme() else 127)

    def _pressedBackgroundColor(self):
        return QColor(255, 255, 255, 8 if isDarkTheme() else 64)

    def getBorderRadius(self):
        return self._borderRadius

    def setBorderRadius(self, radius: int):
        self._borderRadius = radius
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        r = self.borderRadius

        # draw background
        painter.setPen(Qt.NoPen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(rect, r, r)

    borderRadius = pyqtProperty(int, getBorderRadius, setBorderRadius)


class ColorAnimationFrame(CardWidget, ColorChangeable):
    def __init__(self, type: str = None, parent=None):
        # `BackgroundAnimationWidget` 的 `__init__` 里调用了 `super().__init__()`
        # 这里不能再 `ColorChangeable.__init__()` 了，不然它会被 `__init__` 两次
        CardWidget.__init__(self, parent=parent, type=type)

    def setColor(self, c1: QColor, c2: QColor, c3: QColor, c4: QColor):
        self.normalBackgroundColor = c1
        self.hoverBackgroundColor = c2
        self.pressedBackgroundColor = c3

        # 只负责颜色，不负责宽度等
        self.setStyleSheet(
            f"ColorAnimationFrame {{border-color: {c4.name(QColor.HexArgb)};}}")

        try:
            # 由于同样原因，这里不 try 就报错咯 ^^_
            self._updateBackgroundColor()
        except:
            return

    def _normalBackgroundColor(self):
        return self.normalBackgroundColor

    def _hoverBackgroundColor(self):
        return self.hoverBackgroundColor

    def _pressedBackgroundColor(self):
        return self.pressedBackgroundColor
