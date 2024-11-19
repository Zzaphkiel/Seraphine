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
        self.setStyleSheet(f"ColorLabel {{color: {c1.name()}}}")


class DeathsLabel(ColorLabel):
    def __init__(self, text: str = None, parent=None):
        super().__init__(text=text, type='lose', parent=parent)

    def setColor(self, c1: QColor, c2, c3, c4):
        r, g, b, a = c1.getRgb()

        if isDarkTheme():
            r = int(min(255, (r+50)*1.4))
            g = int(min(255, (g+50)*1.4))
            b = int(min(255, (b+50)*1.4))
        else:
            r = int(min(255, r*0.9))
            g = int(min(255, g*0.9))
            b = int(min(255, b*0.9))

        self.setStyleSheet(f"ColorLabel {{color: rgb({r}, {g}, {b});}}")
