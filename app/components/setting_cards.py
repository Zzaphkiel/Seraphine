# coding:utf-8
from typing import Union

from ..common.qfluentwidgets import (
    FluentIconBase, ExpandGroupSettingCard, ConfigItem, qconfig, PushButton, SpinBox,
    ColorDialog, setCustomStyleSheet)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QGridLayout, QFrame, QPushButton

from ..common.icons import Icon
from ..common.config import cfg
from ..common.signals import signalBus


class LineEditSettingCard(ExpandGroupSettingCard):

    def __init__(self, configItem, title, hintContent, step, min,
                 max, icon: Union[str, QIcon, FluentIconBase],
                 content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.configItem = configItem

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.hintLabel = QLabel(hintContent)
        self.lineEdit = SpinBox(self)

        self.buttonWidget = QWidget(self.view)
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.pushButton = PushButton(self.tr("Apply"))

        self.statusLabel = QLabel(self)

        self.__initLayout()
        self.__initWidget(step, min, max)

    def __onValueChanged(self):
        value = self.lineEdit.value()
        cfg.set(self.configItem, value)
        self.__setStatusLabelText(value)

    def __initWidget(self, step, min, max):
        self.lineEdit.setRange(min, max)
        value = cfg.get(self.configItem)
        self.__setStatusLabelText(value)

        self.lineEdit.setValue(value)
        self.lineEdit.setSingleStep(step)
        self.lineEdit.setMinimumWidth(250)
        self.pushButton.setMinimumWidth(100)
        self.pushButton.clicked.connect(self.__onValueChanged)

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.hintLabel, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(self.lineEdit, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.pushButton, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def __setStatusLabelText(self, value):
        self.statusLabel.setText(self.tr("Now: ") + str(value))


class gameTabColorSettingCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None, winConfigItem: ConfigItem = None,
                 loseConfigItem: ConfigItem = None, remakeConfigItem: ConfigItem = None,
                 parent=None):
        super().__init__(Icon.BACKGROUNDCOLOR, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.winHintLabel = QLabel(self.tr("Color of wins:"))
        self.loseHintLabel = QLabel(self.tr("Color of losses:"))
        self.remakeHintLabel = QLabel(self.tr("Color of remakes:"))

        self.winSettingButton = PushButton()
        self.loseSettingButton = PushButton()
        self.remakeSettingButton = PushButton()

        self.resetWidget = QWidget()
        self.resetLayout = QHBoxLayout(self.resetWidget)
        self.resetButton = PushButton(self.tr("Reset"))

        self.defaultWinColor = QColor(winConfigItem.defaultValue)
        self.defaultLoseColor = QColor(loseConfigItem.defaultValue)
        self.defaultRemakeColor = QColor(remakeConfigItem.defaultValue)

        self.winConfigItem = winConfigItem
        self.loseConfigItem = loseConfigItem
        self.remakeConfigItem = remakeConfigItem

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.winHintLabel, 0, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.loseHintLabel, 1, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.remakeHintLabel, 2, 0, alignment=Qt.AlignLeft)

        self.inputLayout.addWidget(
            self.winSettingButton, 0, 1, alignment=Qt.AlignRight)
        self.inputLayout.addWidget(
            self.loseSettingButton, 1, 1, alignment=Qt.AlignRight)
        self.inputLayout.addWidget(
            self.remakeSettingButton, 2, 1, alignment=Qt.AlignRight)

        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.resetLayout.setContentsMargins(48, 18, 44, 18)
        self.resetLayout.addWidget(self.resetButton, 0, Qt.AlignRight)
        self.resetLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.resetWidget)

    def __initWidget(self):
        self.winSettingButton.setFixedWidth(100)
        self.loseSettingButton.setFixedWidth(100)
        self.remakeSettingButton.setFixedWidth(100)
        self.resetButton.setMinimumWidth(100)

        self.setValue(qconfig.get(self.winConfigItem),
                      qconfig.get(self.loseConfigItem),
                      qconfig.get(self.remakeConfigItem))

        self.winSettingButton.clicked.connect(
            lambda: self.__onSettingButtonClicked('win'))
        self.loseSettingButton.clicked.connect(
            lambda: self.__onSettingButtonClicked('lose'))
        self.remakeSettingButton.clicked.connect(
            lambda: self.__onSettingButtonClicked('remake'))

        self.resetButton.clicked.connect(self.__reset)

    def setValue(self, winColor: QColor = None, loseColor: QColor = None, remakeColor: QColor = None):
        if winColor:
            qconfig.set(self.winConfigItem, winColor)

        if loseColor:
            qconfig.set(self.loseConfigItem, loseColor)

        if remakeColor:
            qconfig.set(self.remakeConfigItem, remakeColor)

        self.__setStatusLabel()
        self.__setButtonsColor()

    def __setStatusLabel(self):
        if (qconfig.get(self.winConfigItem) == self.defaultWinColor and
                qconfig.get(self.loseConfigItem) == self.defaultLoseColor and
                qconfig.get(self.remakeConfigItem) == self.defaultRemakeColor):
            self.statusLabel.setText(self.tr("Default color"))
            self.resetButton.setEnabled(False)
        else:
            self.statusLabel.setText(self.tr("Custom color"))
            self.resetButton.setEnabled(True)

    def __setButtonsColor(self):
        winColor = qconfig.get(self.winConfigItem)
        self.__setColor(self.winSettingButton, winColor)

        loseColor = qconfig.get(self.loseConfigItem)
        self.__setColor(self.loseSettingButton, loseColor)

        remakeColor = qconfig.get(self.remakeConfigItem)
        self.__setColor(self.remakeSettingButton, remakeColor)

    def __setColor(self, widget, color: QColor):
        r, g, b, a = color.getRgb()
        a /= 255

        f1, f2 = 1.1, 0.9
        r1, g1, b1 = min(r * f1, 255), min(g * f1, 255), min(b * f1, 255)
        r2, g2, b2 = min(r * f2, 255), min(g * f2, 255), min(b * f2, 255)

        qss = f"""
            QPushButton {{
                border-radius: 6px;
                border: 1px solid rgb({r}, {g}, {b});
                background-color: rgba({r}, {g}, {b}, {a});
            }}
            QPushButton:hover {{
                border: 1px solid rgb({r1}, {g1}, {b1});
                background-color: rgba({r1}, {g1}, {b1}, {min(a+0.1, 1)});
            }}
            QPushButton:pressed {{
                border: 1px solid rgb({r2}, {g2}, {b2});
                background-color: rgba({r2}, {g2}, {b2}, {min(a+0.2, 1)});
            }}
        """

        setCustomStyleSheet(widget, qss, qss)

    def __onSettingButtonClicked(self, name):
        if name == 'win':
            configItem = self.winConfigItem
        elif name == 'lose':
            configItem = self.loseConfigItem
        else:
            configItem = self.remakeConfigItem

        w = ColorDialog(
            qconfig.get(configItem), self.tr('Choose color'), self.window(), True)
        w.colorChanged.connect(
            lambda color: self.__onColorChanged(color, name))
        w.exec()

    def __onColorChanged(self, color, name):
        if name == 'win':
            self.setValue(winColor=color)
        elif name == 'lose':
            self.setValue(loseColor=color)
        else:
            self.setValue(remakeColor=color)

        signalBus.tabColorChanged.emit()

    def __reset(self):
        self.setValue(self.defaultWinColor, self.defaultLoseColor,
                      self.defaultRemakeColor)
        signalBus.tabColorChanged.emit()
