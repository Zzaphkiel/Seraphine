# coding:utf-8
from typing import Union
from copy import deepcopy

from app.common.qfluentwidgets import (FluentIconBase, ExpandGroupSettingCard,
                                       ConfigItem, qconfig, PushButton, SpinBox,
                                       ColorDialog, LineEdit, SwitchButton,
                                       IndicatorPosition, setCustomStyleSheet, SwitchSettingCard, TransparentToolButton, FluentIcon, setThemeColor,
                                       PillPushButton)
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


class DeathsNumberColorSettingCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None, lightConfigItem: ConfigItem = None,
                 darkConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.TEXTCOLOR, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.lightHintLabel = QLabel(self.tr("Color in Light theme:"))
        self.darkHintLabel = QLabel(self.tr("Color in Dark theme:"))

        self.lightSettingButton = ColorAnimationFrame(type='deathsLight')
        self.darkSettingButton = ColorAnimationFrame(type='deathsDark')

        self.resetWidget = QWidget()
        self.resetLayout = QHBoxLayout(self.resetWidget)
        self.resetButton = PushButton(self.tr("Reset"))

        self.defaultLightColor = QColor(lightConfigItem.defaultValue)
        self.defaultDarkColor = QColor(darkConfigItem.defaultValue)

        self.lightConfigItem = lightConfigItem
        self.darkConfigItem = darkConfigItem

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.lightHintLabel, 0, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.darkHintLabel, 1, 0, alignment=Qt.AlignLeft)

        self.inputLayout.addWidget(
            self.lightSettingButton, 0, 1, alignment=Qt.AlignRight)
        self.inputLayout.addWidget(
            self.darkSettingButton, 1, 1, alignment=Qt.AlignRight)

        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.resetLayout.setContentsMargins(48, 18, 44, 18)
        self.resetLayout.addWidget(self.resetButton, 0, Qt.AlignRight)
        self.resetLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.resetWidget)

    def __initWidget(self):
        self.lightSettingButton.setFixedSize(100, 32)
        self.darkSettingButton.setFixedSize(100, 32)

        self.resetButton.setMinimumWidth(100)

        self.setValue(qconfig.get(self.lightConfigItem),
                      qconfig.get(self.darkConfigItem))

        self.lightSettingButton.clicked.connect(
            lambda: self.__onSettingButtonClicked('deathsLight'))
        self.darkSettingButton.clicked.connect(
            lambda: self.__onSettingButtonClicked('deathsDark'))

        self.resetButton.clicked.connect(self.__reset)

    def setValue(self, lightColor: QColor = None, darkColor: QColor = None):
        if lightColor:
            qconfig.set(self.lightConfigItem, lightColor)

        if darkColor:
            qconfig.set(self.darkConfigItem, darkColor)

        self.__setStatusLabel()

    def __setStatusLabel(self):
        if (qconfig.get(self.lightConfigItem) == self.defaultLightColor and
                qconfig.get(self.darkConfigItem) == self.defaultDarkColor):
            self.statusLabel.setText(self.tr("Default color"))
            self.resetButton.setEnabled(False)
        else:
            self.statusLabel.setText(self.tr("Custom color"))
            self.resetButton.setEnabled(True)

    def __onSettingButtonClicked(self, name):
        if name == 'deathsLight':
            configItem = self.lightConfigItem
        elif name == 'deathsDark':
            configItem = self.darkConfigItem

        w = ColorDialog(
            qconfig.get(configItem), self.tr('Choose color'), self.window())
        w.colorChanged.connect(
            lambda color: self.__onColorChanged(color, name))
        w.exec()

    def __onColorChanged(self, color, name):
        if name == 'deathsLight':
            self.setValue(lightColor=color)
        elif name == 'deathsDark':
            self.setValue(darkColor=color)

        signalBus.customColorChanged.emit(name)
        signalBus.customColorChanged.emit("deaths")

    def __reset(self):
        self.setValue(self.defaultLightColor, self.defaultDarkColor)

        signalBus.customColorChanged.emit('deathsLight')
        signalBus.customColorChanged.emit('deathsDark')
        signalBus.customColorChanged.emit("deaths")


class ThemeColorSettingCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None,
                 colorConfigItem: ConfigItem = None,
                 parent=None):
        super().__init__(Icon.PALETTE, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.colorHintLabel = QLabel(self.tr("Theme color:"))

        self.colorSettingButton = ColorAnimationFrame(type='theme')

        self.resetWidget = QWidget()
        self.resetLayout = QHBoxLayout(self.resetWidget)
        self.resetButton = PushButton(self.tr("Reset"))

        self.defaultColor = QColor(colorConfigItem.defaultValue)

        self.colorConfigItem = colorConfigItem

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.colorHintLabel, 0, 0, alignment=Qt.AlignLeft)

        self.inputLayout.addWidget(
            self.colorSettingButton, 0, 1, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.resetLayout.setContentsMargins(48, 18, 44, 18)
        self.resetLayout.addWidget(self.resetButton, 0, Qt.AlignRight)
        self.resetLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.resetWidget)

    def __initWidget(self):
        self.colorSettingButton.setFixedSize(100, 32)
        self.resetButton.setMinimumWidth(100)

        self.setValue(qconfig.get(self.colorConfigItem))

        self.colorSettingButton.clicked.connect(self.__onSettingButtonClicked)
        self.resetButton.clicked.connect(
            lambda: self.__onColorChanged(self.defaultColor))

    def setValue(self, color):
        qconfig.set(self.colorConfigItem, color)

        self.__setStatusLabel()

    def __setStatusLabel(self):
        if qconfig.get(self.colorConfigItem) == self.defaultColor:
            self.statusLabel.setText(self.tr("Default color"))
            self.resetButton.setEnabled(False)
        else:
            self.statusLabel.setText(self.tr("Custom color"))
            self.resetButton.setEnabled(True)

    def __onSettingButtonClicked(self):
        configItem = self.colorConfigItem

        w = ColorDialog(
            qconfig.get(configItem), self.tr('Choose color'), self.window(), False)
        w.colorChanged.connect(self.__onColorChanged)

        w.exec()

    def __onColorChanged(self, color):
        self.setValue(color=color)

        signalBus.customColorChanged.emit('theme')
        setThemeColor(color)


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

        # 之前 lineEdit 有一个 placeholder "127.0.0.1:10809"，本意是提示用户将 proxy 写成这种形式，
        # 但部分用户误以为此 placeholder 是已经填好的数值；
        # 同时，switchButton 可以在 lineEidt 为空的时候设置为 checked，这更让用户误以为启用了代理。
        # 所以这里修改了部分代码逻辑

        enable = self.lineEdit.text() != ""
        self.switchButton.setEnabled(enable)
        self.switchButton.setChecked(cfg.get(self.enableConfigItem) and enable)

        # 防止之前有人在 HttpProxy 为空的时候设置了 enable
        if cfg.get(self.enableConfigItem) and not enable:
            cfg.set(self.enableConfigItem, False)

        self.lineEdit.textChanged.connect(self.__onLineEditValueChanged)
        self.switchButton.checkedChanged.connect(
            self.__onSwitchButtonCheckedChanged)

        value, isChecked = self.lineEdit.text(), self.switchButton.isChecked()
        self.__setStatusLableText(value, isChecked)
        self.lineEdit.setEnabled(not isChecked)

    def __onSwitchButtonCheckedChanged(self, isChecked: bool):
        cfg.set(self.enableConfigItem, isChecked)
        self.lineEdit.setEnabled(not isChecked)
        self.__setStatusLableText(self.lineEdit.text(), isChecked)

    def __onLineEditValueChanged(self, value):
        cfg.set(self.addrConfigItem, value)
        self.switchButton.setEnabled(value != "")

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


class ModeCheckButtonsGroup(QWidget):
    selectedChanged = pyqtSignal(list)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.allButton = PillPushButton(self.tr("Show All"))

        self.normalButton = PillPushButton(self.tr("Normal"))
        self.quickButton = PillPushButton(self.tr("Quickplay"))
        self.soloDuoButton = PillPushButton(self.tr("Ranked Solo / Duo"))
        self.flexButton = PillPushButton(self.tr("Ranked Flex"))
        self.aramButton = PillPushButton(self.tr("A.R.A.M."))

        self.modeButtons = [self.normalButton,
                            self.quickButton,
                            self.soloDuoButton,
                            self.flexButton,
                            self.aramButton]

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.VLine)
        self.separator.setLineWidth(1)

        self.selected = []

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.separator.setObjectName("separator")

        # 只能从未选中变成选中
        self.allButton.clicked.connect(self.__onAllButtonClicked)

        self.normalButton.clicked.connect(
            lambda: self.__onModeButtonClicked(430))
        self.quickButton.clicked.connect(
            lambda: self.__onModeButtonClicked(480))
        self.soloDuoButton.clicked.connect(
            lambda: self.__onModeButtonClicked(420))
        self.flexButton.clicked.connect(
            lambda: self.__onModeButtonClicked(440))
        self.aramButton.clicked.connect(
            lambda: self.__onModeButtonClicked(450))

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(12)

        self.hBoxLayout.addWidget(self.allButton)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.separator)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.normalButton)
        self.hBoxLayout.addWidget(self.quickButton)
        self.hBoxLayout.addWidget(self.soloDuoButton)
        self.hBoxLayout.addWidget(self.flexButton)
        self.hBoxLayout.addWidget(self.aramButton)

    def setSelectedButtons(self, selected: list):
        self.selected = selected

        if len(selected) == 0:
            self.allButton.setChecked(True)

            for button in self.modeButtons:
                button.setChecked(False)
        else:
            self.allButton.setChecked(False)

            for queueId in selected:
                button = self.getButton(queueId)
                button.setChecked(True)

    def getButton(self, queueId) -> PillPushButton:
        return {
            430: self.normalButton,
            420: self.soloDuoButton,
            440: self.flexButton,
            450: self.aramButton,
            480: self.quickButton,
        }[queueId]

    def __onAllButtonClicked(self):
        if self.allButton.isChecked():
            for button in self.modeButtons:
                button.setChecked(False)

            self.selected = []
            self.selectedChanged.emit(self.selected)
        else:
            self.allButton.setChecked(True)

    def __onModeButtonClicked(self, queueId):
        button = self.getButton(queueId)

        if button.isChecked():
            self.selected.append(queueId)
            self.allButton.setChecked(False)
        else:
            self.selected.remove(queueId)

            if all(map(lambda button: not button.isChecked(),
                       self.modeButtons)):
                self.allButton.setChecked(True)

        self.selectedChanged.emit(self.selected)


class QueueFilterCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None,
                 configItem: ConfigItem = None,
                 parent=None):
        super().__init__(Icon.FILTER, title, content, parent)

        self.configItem = configItem

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.normalHintLabel = QLabel(self.tr("Normal:"))
        self.quickHintLabel = QLabel(self.tr("Quickplay:"))
        self.soloDuoHintLabel = QLabel(self.tr("Ranked Solo / Duo:"))
        self.flexHintLabel = QLabel(self.tr("Ranked Flex:"))
        self.aramHintLabel = QLabel(self.tr("A.R.A.M.:"))

        self.normalButtonsGroup = ModeCheckButtonsGroup()
        self.quickButtonsGroup = ModeCheckButtonsGroup()
        self.soloDuoButtonsGroup = ModeCheckButtonsGroup()
        self.flexButtonsGroup = ModeCheckButtonsGroup()
        self.aramButtonsGroup = ModeCheckButtonsGroup()

        self.buttonsWidget = QWidget(self.view)
        self.buttonsLayout = QGridLayout(self.buttonsWidget)
        self.resetButton = PushButton(self.tr("Reset"))

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.resetButton.setMinimumWidth(100)

        selected = deepcopy(qconfig.get(self.configItem))

        self.normalButtonsGroup.setSelectedButtons(selected['430'])
        self.quickButtonsGroup.setSelectedButtons(selected['480'])
        self.soloDuoButtonsGroup.setSelectedButtons(selected['420'])
        self.flexButtonsGroup.setSelectedButtons(selected['440'])
        self.aramButtonsGroup.setSelectedButtons(selected['450'])

        self.normalButtonsGroup.selectedChanged.connect(
            lambda l: self.__onButtonsGroupSelectChanged(l, '430'))
        self.quickButtonsGroup.selectedChanged.connect(
            lambda l: self.__onButtonsGroupSelectChanged(l, '480'))
        self.soloDuoButtonsGroup.selectedChanged.connect(
            lambda l: self.__onButtonsGroupSelectChanged(l, '420'))
        self.flexButtonsGroup.selectedChanged.connect(
            lambda l: self.__onButtonsGroupSelectChanged(l, '440'))
        self.aramButtonsGroup.selectedChanged.connect(
            lambda l: self.__onButtonsGroupSelectChanged(l, '450'))

        self.resetButton.clicked.connect(self.__onResetButtonClicked)

    def __initLayout(self):
        self.inputLayout.setVerticalSpacing(19)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.inputLayout.addWidget(self.normalHintLabel, 0, 0, Qt.AlignLeft)
        self.inputLayout.addWidget(self.quickHintLabel, 1, 0, Qt.AlignLeft)
        self.inputLayout.addWidget(self.soloDuoHintLabel, 2, 0, Qt.AlignLeft)
        self.inputLayout.addWidget(self.flexHintLabel, 3, 0, Qt.AlignLeft)
        self.inputLayout.addWidget(self.aramHintLabel, 4, 0, Qt.AlignLeft)
        self.inputLayout.addWidget(self.normalButtonsGroup, 0, 1, Qt.AlignLeft)
        self.inputLayout.addWidget(self.quickButtonsGroup, 1, 1, Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.soloDuoButtonsGroup, 2, 1, Qt.AlignLeft)
        self.inputLayout.addWidget(self.flexButtonsGroup, 3, 1, Qt.AlignLeft)
        self.inputLayout.addWidget(self.aramButtonsGroup, 4, 1, Qt.AlignLeft)

        self.buttonsLayout.setVerticalSpacing(19)
        self.buttonsLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonsLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        self.buttonsLayout.addWidget(self.resetButton, 0, 1, Qt.AlignRight)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonsWidget)

    def __onButtonsGroupSelectChanged(self, selected, queueId):
        current = deepcopy(qconfig.get(self.configItem))
        current[queueId] = selected
        qconfig.set(self.configItem, current)

    def __onResetButtonClicked(self):
        self.normalButtonsGroup.setSelectedButtons([])
        self.quickButtonsGroup.setSelectedButtons([])
        self.soloDuoButtonsGroup.setSelectedButtons([])
        self.flexButtonsGroup.setSelectedButtons([])
        self.aramButtonsGroup.setSelectedButtons([])

        default = self.configItem.defaultValue
        qconfig.set(self.configItem, default)
