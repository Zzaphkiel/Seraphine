
from PyQt5.QtWidgets import (QHBoxLayout, QWidget, QFrame, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QLabel, QHBoxLayout, QWidget, QLabel, QFrame,
                             QVBoxLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QEasingCurve
from PyQt5.QtGui import QPixmap
from qasync import asyncSlot

from app.components.animation_frame import ColorAnimationFrame
from app.components.transparent_button import TransparentButton
from app.components.champion_icon_widget import RoundIcon
from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import BodyLabel, SmoothScrollArea, FlowLayout


class BuildInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.__initWidget()
        self.__initLayout()

        StyleSheet.OPGG_BUILD_INTERFACE.apply(self)

    def __initWidget(self):
        pass

    def __initLayout(self):
        pass
