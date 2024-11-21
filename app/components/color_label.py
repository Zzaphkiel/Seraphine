from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QColor
from app.common.style_sheet import ColorChangeable
from app.common.qfluentwidgets import isDarkTheme


class ColorLabel(QLabel, ColorChangeable):
    '''
    该标签颜色会跟随对应 `type` 颜色的改变而自动改变
    '''

    def __init__(self, text: str = None, type: str = None, parent=None):
        QLabel.__init__(self, text=text, parent=parent)
        ColorChangeable.__init__(self, type)

    def setColor(self, c1, c2, c3, c4):
        self.setStyleSheet(f"ColorLabel {{color: {c1.name()};}}")


class DeathsLabel(ColorLabel):
    def __init__(self, text: str = None, parent=None):
        super().__init__(text=text, type='deaths', parent=parent)

    def setColor(self, c1: QColor, c2, c3, c4):
        self.setStyleSheet(f"DeathsLabel {{color: {c1.name()};}}")
