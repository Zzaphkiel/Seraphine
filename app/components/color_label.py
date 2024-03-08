from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel, QFrame

from app.common.style_sheet import ColorChangeable


class ColorLabel(QLabel, ColorChangeable):
    '''
    该标签颜色会跟随对应 `type` 颜色的改变而自动改变
    '''

    def __init__(self, text: str = None, type: str = None, parent=None):
        QLabel.__init__(self, text=text, parent=parent)
        ColorChangeable.__init__(self, type)

    def setColor(self, c1, c2, c3, c4):
        self.setStyleSheet(f"ColorLabel {{color: {c1.name()}}}")
