from PyQt5.QtCore import pyqtSignal

from app.common.qfluentwidgets import TransparentToolButton, ToolButton


class ToggleButton(ToolButton):
    changed = pyqtSignal(int)

    def __init__(self, icon1, icon2, parent=None):
        super().__init__(parent=parent)

        self.icons = [icon1, icon2]
        self.currentIcon = 0

        self.setIcon(icon1)

        self.clicked.connect(self.__onButtonClicked)

    def __onButtonClicked(self):
        new = 1 - self.currentIcon
        self.currentIcon = new
        self.setIcon(self.icons[new])

        self.changed.emit(new)
