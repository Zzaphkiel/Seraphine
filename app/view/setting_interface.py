# coding:utf-8
import os
from typing import Union

from ..common.qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard, PushSettingCard,
    ExpandLayout, CustomColorSettingCard, InfoBar, setTheme, setThemeColor, 
    SmoothScrollArea, FluentIconBase, PrimaryPushSettingCard, 
    HyperlinkCard, TeachingTip, TeachingTipTailPosition, TeachingTipView, 
    ExpandGroupSettingCard, ConfigItem, setCustomStyleSheet, SwitchButton, 
    qconfig, LineEdit, PushButton, IndicatorPosition, SpinBox)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout

from ..common.icons import Icon
from ..common.config import (
    cfg, YEAR, AUTHOR, VERSION, FEEDBACK_URL, GITHUB_URL, isWin11)
from ..common.style_sheet import StyleSheet


class LineEditSettingCard(ExpandGroupSettingCard):

    def __init__(self, configItem, title, hintContent, step,
                 icon: Union[str, QIcon, FluentIconBase],
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
        self.__initWidget(step)

    def __onValueChanged(self):
        value = self.lineEdit.value()
        cfg.set(self.configItem, value)
        self.__setStatusLabelText(value)

    def __initWidget(self, step):
        self.lineEdit.setRange(1, 999)
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


class SettingInterface(SmoothScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.functionGroup = SettingCardGroup(self.tr("Functions"),
                                              self.scrollWidget)

        self.careerGamesCount = LineEditSettingCard(
            cfg.careerGamesNumber,
            self.tr("Default games number"), self.tr(
                "Number of games:"), 10, Icon.SLIDESEARCH,
            self.
            tr("Setting the maximum number of games shows in the career interface"
               ), self.functionGroup)

        self.gameInfoFilterCard = SwitchSettingCard(
            Icon.FILTER, self.tr("Rank filter other mode"),
            self.tr(
                "Filter out other modes on the Game Information interface when ranking"),
            cfg.gameInfoFilter
        )

        self.gameInfoShowTierCard = SwitchSettingCard(
            Icon.TROPHY, self.tr("Show tier in game information"),
            self.
            tr("Show tier icon in game information interface. Enabling this option affects APP's performance"
               ), cfg.showTierInGameInfo)

        self.generalGroup = SettingCardGroup(self.tr("General"),
                                             self.scrollWidget)
        

        self.lolFolderCard = PushSettingCard(self.tr("Choose folder"),
                                             Icon.FOLDER,
                                             self.tr("Client Path"),
                                             cfg.get(cfg.lolFolder),
                                             self.generalGroup)

        self.gameStartMinimizeCard = SwitchSettingCard(
            Icon.PAGE, self.tr("Minimize windows during game activities"),
            self.tr(
                "Reduce CPU usage for rendering UI during gaming"),
            cfg.enableGameStartMinimize
        )

        self.logLevelCard = ComboBoxSettingCard(
            cfg.logLevel,
            Icon.LOG,
            self.tr('Log Level'),
            self.tr('The level of logging for Seraphine (take effect after restart)'),
            texts=["Debug", "Info", "Warning", "Error"],
            parent=self.generalGroup)
        
        self.enableStartLolWithApp = SwitchSettingCard(
            Icon.CIRCLERIGHT,
            self.tr("Auto-start LOL"),
            self.tr("Launch LOL client upon opening Seraphine automatically"),
            configItem=cfg.enableStartLolWithApp,
            parent=self.generalGroup)
        self.deleteResourceCard = PushSettingCard(
            self.tr("Delete"), Icon.DELETE, self.tr("Delete cache"),
            self.
            tr("Delete all game resources (Apply it when game resources update)"
               ), self.generalGroup)
        self.enableCloseToTray = LooseSwitchSettingCard(
            Icon.EXIT,
            self.tr("Minimize to tray on close"),
            self.tr("Minimize to system tray when clicking close"),
            configItem=cfg.enableCloseToTray,
            parent=self.generalGroup)

        self.personalizationGroup = SettingCardGroup(
            self.tr("Personalization"), self.scrollWidget)

        self.micaCard = SwitchSettingCard(
            Icon.BLUR,
            self.tr('Mica effect'),
            self.tr(
                'Apply semi transparent to windows and surfaces (only available on Win11)'),
            cfg.micaEnabled,
            self.personalizationGroup
        )
        self.themeCard = ComboBoxSettingCard(
            cfg.themeMode,
            Icon.BRUSH,
            self.tr("Application theme"),
            self.tr("Change the appearance of Seraphine"),
            texts=[
                self.tr("Light"),
                self.tr("Dark"),
                self.tr("Use system setting")
            ],
            parent=self.personalizationGroup)
        self.themeColorCard = self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor, Icon.PALETTE, self.tr("Theme color"),
            self.tr("Change the theme color of Seraphine"),
            self.personalizationGroup)
        self.zoomCard = ComboBoxSettingCard(
            cfg.dpiScale,
            Icon.ZOOMFIT,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalizationGroup)
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            Icon.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for Seraphine'),
            texts=['简体中文', 'English',
                   self.tr('Use system setting')],
            parent=self.personalizationGroup)
        
        self.updateGroup = SettingCardGroup(self.tr("Update"), self.scrollWidget)
        self.checkUpdateCard = SwitchSettingCard(
            Icon.UPDATE, self.tr("Check for updates"),
            self.tr(
                "Automatically check for updates when software starts"),
            cfg.enableCheckUpdate
        )
        self.httpProxyCard = ProxySettingCard(
            self.tr("Http proxy"), self.tr("Using a proxy when connecting to GitHub"), 
            cfg.enableProxy, cfg.proxyAddr, self.updateGroup)

        self.aboutGroup = SettingCardGroup(self.tr("About"), self.scrollWidget)
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'), Icon.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve Seraphine by providing feedback'),
            self.aboutGroup)
        self.aboutCard = HyperlinkCard(
            GITHUB_URL, self.tr("View GitHub"), Icon.INFO, self.tr('About'),
            self.tr('Copyright') + ' © ' + f"{YEAR}, {AUTHOR}. " +
            self.tr('Version') + f" {VERSION}", self.aboutGroup)
        self.aboutCard.linkButton.setIcon(Icon.GITHUB)

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 90, 0, 20)
        # self.scrollDelagate.vScrollBar.setContentsMargins(0, 50, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.micaCard.switchButton.setEnabled(isWin11())

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.functionGroup.addSettingCard(self.careerGamesCount)
        self.functionGroup.addSettingCard(self.gameInfoFilterCard)
        self.functionGroup.addSettingCard(self.gameInfoShowTierCard)

        self.generalGroup.addSettingCard(self.lolFolderCard)
        # self.generalGroup.addSettingCard(self.enableStartWithComputer)
        self.generalGroup.addSettingCard(self.enableStartLolWithApp)
        self.generalGroup.addSettingCard(self.deleteResourceCard)
        self.generalGroup.addSettingCard(self.enableCloseToTray)
        self.generalGroup.addSettingCard(self.gameStartMinimizeCard)
        self.generalGroup.addSettingCard(self.logLevelCard)

        self.personalizationGroup.addSettingCard(self.micaCard)
        self.personalizationGroup.addSettingCard(self.themeCard)
        self.personalizationGroup.addSettingCard(self.themeColorCard)
        self.personalizationGroup.addSettingCard(self.zoomCard)
        self.personalizationGroup.addSettingCard(self.languageCard)

        self.updateGroup.addSettingCard(self.checkUpdateCard)
        self.updateGroup.addSettingCard(self.httpProxyCard)

        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(30)
        self.expandLayout.setContentsMargins(36, 0, 36, 0)
        self.expandLayout.addWidget(self.functionGroup)
        self.expandLayout.addWidget(self.generalGroup)
        self.expandLayout.addWidget(self.personalizationGroup)
        self.expandLayout.addWidget(self.updateGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __connectSignalToSlot(self):
        self.lolFolderCard.clicked.connect(self.__onLolFolderCardClicked)

        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(setThemeColor)

        cfg.appRestartSig.connect(self.__showRestartToolTip)
        self.careerGamesCount.pushButton.clicked.connect(
            self.__showUpdatedSuccessfullyToolTip)
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
        self.deleteResourceCard.clicked.connect(self.__showFlyout)

    def __onLolFolderCardClicked(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"),
            self.lolFolderCard.contentLabel.text())

        if not folder or cfg.get(cfg.lolFolder) == folder:
            return

        cfg.set(cfg.lolFolder, folder)
        self.lolFolderCard.setContent(folder)

    def __showRestartToolTip(self):
        InfoBar.success(self.tr("Updated successfully"),
                        self.tr("Configuration takes effect after restart"),
                        duration=2000,
                        parent=self)

    def __showUpdatedSuccessfullyToolTip(self):
        InfoBar.success(self.tr("Updated successfully"),
                        self.tr("Settings have been applied"),
                        duration=2000,
                        parent=self)

    def __onDeleteButtonClicked(self):

        folders = [
            'champion icons', 'item icons', 'profile icons', 'rune icons',
            'summoner spell icons'
        ]

        for folder in folders:
            path = f'app/resource/game/{folder}'
            for file in os.listdir(path):
                filePath = f"{path}/{file}"
                os.remove(filePath)

    def __showFlyout(self):
        view = TeachingTipView(
            title=self.tr("Really?"),
            content=self.
            tr("Game resources will be downloaded again\nwhen they are used by Seraphine, which will cost more time"
               ),
            isClosable=True,
            tailPosition=TeachingTipTailPosition.RIGHT)

        applyButton = PushButton(self.tr('Confirm delete'))

        view.widgetLayout.insertSpacing(1, 10)
        view.widgetLayout.addSpacing(10)
        view.addWidget(applyButton, align=Qt.AlignRight)

        t = TeachingTip.make(
            view,
            self.deleteResourceCard.button,
            -1,
            TeachingTipTailPosition.RIGHT,
            self,
        )

        applyButton.clicked.connect(self.__onDeleteButtonClicked)
        view.closed.connect(t.close)


class ProxySettingCard(ExpandGroupSettingCard):
    def __init__(self, title, content, enableConfigItem: ConfigItem = None,
                 addrConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.PLANE, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.secondsLabel = QLabel(self.tr("Http proxy:"))
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

        # 这玩意在 enabled 是 False 的时候边框怪怪的，强行让它不那么怪
        qss = """
            SpinBox:disabled {
                color: rgba(255, 255, 255, 150);
                border: 1px solid rgba(255, 255, 255, 0.0698);
                background-color: rgba(255, 255, 255, 0.0419);
            }
        """
        setCustomStyleSheet(self.lineEdit, "", qss)

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
