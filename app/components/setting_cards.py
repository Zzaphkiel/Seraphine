# coding:utf-8
from typing import Union

from app.common.qfluentwidgets import (
    FluentIconBase, ExpandGroupSettingCard, ConfigItem, qconfig, PushButton, SpinBox,
    ColorDialog, LineEdit, SwitchButton,  IndicatorPosition, setCustomStyleSheet,
    SwitchSettingCard, TransparentToolButton, FluentIcon)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QGridLayout, QFrame, QPushButton,
                             QVBoxLayout)

from app.common.icons import Icon
from app.common.config import cfg
from app.common.signals import signalBus
from app.components.animation_frame import ColorAnimationFrame


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


class GameTabColorSettingCard(ExpandGroupSettingCard):
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

        self.winSettingButton = ColorAnimationFrame(type='win')
        self.loseSettingButton = ColorAnimationFrame(type='lose')
        self.remakeSettingButton = ColorAnimationFrame(type='remake')

        self.resetWidget = QWidget()
        self.resetLayout = QHBoxLayout(self.resetWidget)
        self.resetButton = PushButton(self.tr("Reset"))

        self.defaultWinColor = QColor(winConfigItem.defaultValue)
        self.defaultLoseColor = QColor(loseConfigItem.defaultValue)
        self.defaultRemakeColor = QColor(remakeConfigItem.defaultValue)

        self.winConfigItem = winConfigItem
        self.loseConfigItem = loseConfigItem
        self.remakeConfigItem = remakeConfigItem

        self.__initWidget()
        self.__initLayout()

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
        self.winSettingButton.setFixedSize(100, 32)
        self.loseSettingButton.setFixedSize(100, 32)
        self.remakeSettingButton.setFixedSize(100, 32)

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

    def __setStatusLabel(self):
        if (qconfig.get(self.winConfigItem) == self.defaultWinColor and
                qconfig.get(self.loseConfigItem) == self.defaultLoseColor and
                qconfig.get(self.remakeConfigItem) == self.defaultRemakeColor):
            self.statusLabel.setText(self.tr("Default color"))
            self.resetButton.setEnabled(False)
        else:
            self.statusLabel.setText(self.tr("Custom color"))
            self.resetButton.setEnabled(True)

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

        signalBus.customColorChanged.emit(name)

    def __reset(self):
        self.setValue(self.defaultWinColor, self.defaultLoseColor,
                      self.defaultRemakeColor)

        signalBus.customColorChanged.emit('win')
        signalBus.customColorChanged.emit('lose')
        signalBus.customColorChanged.emit('remake')


class ProxySettingCard(ExpandGroupSettingCard):
    def __init__(self, title, content, enableConfigItem: ConfigItem = None,
                 addrConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.PLANE, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.secondsLabel = QLabel(self.tr("HTTP proxy:"))
        self.lineEdit = LineEdit()

        self.switchButtonWidget = QWidget(self.view)
        self.switchButtonLayout = QHBoxLayout(self.switchButtonWidget)

        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.enableConfigItem = enableConfigItem
        self.addrConfigItem = addrConfigItem

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(self.secondsLabel, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(self.lineEdit, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.switchButtonLayout.setContentsMargins(48, 18, 44, 18)
        self.switchButtonLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
        self.switchButtonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.switchButtonWidget)

    def __initWidget(self):
        self.lineEdit.setText(cfg.get(self.addrConfigItem))
        self.lineEdit.setMinimumWidth(250)
        self.lineEdit.setPlaceholderText("127.0.0.1:10809")

        self.switchButton.setChecked(cfg.get(self.enableConfigItem))

        self.lineEdit.textChanged.connect(self.__onLineEditValueChanged)
        self.switchButton.checkedChanged.connect(
            self.__onSwitchButtonCheckedChanged)

        value, isChecked = self.lineEdit.text(), self.switchButton.isChecked()
        self.__setStatusLableText(value, isChecked)
        self.lineEdit.setEnabled(not isChecked)

    def setValue(self, addr: int, isChecked: bool):
        qconfig.set(self.addrConfigItem, addr)
        qconfig.set(self.enableConfigItem, isChecked)

        self.__setStatusLableText(addr, isChecked)

    def __onSwitchButtonCheckedChanged(self, isChecked: bool):
        self.setValue(self.lineEdit.text(), isChecked)
        self.lineEdit.setEnabled(not isChecked)

    def __onLineEditValueChanged(self, value):
        self.setValue(value, self.switchButton.isChecked())

    def __setStatusLableText(self, addr, isChecked):
        if isChecked:
            self.statusLabel.setText(self.tr("Enabled, proxy: ") + str(addr))
        else:
            self.statusLabel.setText(self.tr("Disabled"))


class LooseSwitchSettingCard(SwitchSettingCard):
    """ 允许bool以外的值来初始化的SwitchSettingCard控件 """

    def __init__(self, icon, title, content=None, configItem: ConfigItem = None, parent=None):
        super().__init__(icon, title, content, configItem, parent)

        self.switchButton.setOnText(self.tr("On"))
        self.switchButton.setOffText(self.tr("Off"))

    def setValue(self, isChecked):
        """
        为适应 config 中对应字段为任意值时初始化控件;

        若传入 bool 以外的值, 前端将会看到False

        需要设置值, 有以下途径:
        1. 代码层调用 setValue 时, 以bool传入
        2. 用户通过前端拨动 SwitchButton

        @param isChecked:
        @return:
        """
        if isinstance(isChecked, bool):
            super().setValue(isChecked)
        else:
            self.switchButton.setChecked(False)
