import subprocess
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QWidget, QVBoxLayout,
                             QSpacerItem, QSizePolicy)

from qfluentwidgets import (InfoBar, InfoBarPosition, PushButton, ScrollArea,
                            IndeterminateProgressBar)

from ..common.config import cfg
from ..common.style_sheet import StyleSheet


class StartInterface(ScrollArea):

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.processBar = IndeterminateProgressBar(self)
        self.label1 = QLabel(self.tr("Connecting to LOL Client"), self)
        self.label2 = QLabel(self.tr("Please start LOL Client"), self)
        self.label3 = QLabel(
            self.
            tr("If LOL client is already open, please try opening Seraphine with administrator privileges"
               ), self)
        self.pushButton = PushButton(self.tr("Start LOL Client"), self)

        self.pushButtonLayout = QHBoxLayout()

        self.vBoxLayout = QVBoxLayout(self)

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.pushButtonLayout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.pushButtonLayout.addWidget(self.pushButton)
        self.pushButtonLayout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.label1.setAlignment(Qt.AlignCenter)
        self.label2.setAlignment(Qt.AlignCenter)
        self.label3.setAlignment(Qt.AlignCenter)

        self.vBoxLayout.addWidget(self.processBar)
        self.vBoxLayout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.vBoxLayout.addWidget(self.label1)
        self.vBoxLayout.addWidget(self.label2)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.pushButtonLayout)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.label3)
        self.vBoxLayout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def __initWidget(self):
        self.label1.setObjectName('label1')
        self.label2.setObjectName('label2')
        self.label3.setObjectName('label3')

        StyleSheet.START_INTERFACE.apply(self)
        self.__connectSignalToSlot()

    def __connectSignalToSlot(self):
        self.pushButton.clicked.connect(self.__onPushButtonClicked)

    def __onPushButtonClicked(self):
        path = f'{cfg.get(cfg.lolFolder)}/client.exe'
        if os.path.exists(path):
            subprocess.Popen(f'"{path}"')
            self.__showStartLolSuccessInfo()
        else:
            self.__showLolClientPathErrorInfo()

    def __showStartLolSuccessInfo(self):
        InfoBar.success(title=self.tr('Start LOL successfully'),
                        orient=Qt.Vertical,
                        content="",
                        isClosable=True,
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        duration=5000,
                        parent=self)

    def __showLolClientPathErrorInfo(self):
        InfoBar.error(
            title=self.tr('Invalid path'),
            content=self.
            tr('Please set the correct directory of the LOL client in the setting page'
               ),
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=5000,
            parent=self)