# coding:utf-8
import os
from typing import Union

from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard, PushSettingCard,
    ExpandLayout, Theme, CustomColorSettingCard, InfoBar, setTheme,
    setThemeColor, SmoothScrollArea, SettingCard, FluentIconBase, SpinBox,
    PushButton, PrimaryPushSettingCard, HyperlinkCard, FlyoutView, Flyout,
    FlyoutAnimationType, TeachingTip, TeachingTipTailPosition, TeachingTipView, FluentIcon, InfoBarPosition)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog, QPushButton, QHBoxLayout

from ..common.icons import Icon
from ..common.config import (
    cfg, YEAR, AUTHOR, VERSION, FEEDBACK_URL, GITHUB_URL, isWin11)
from ..common.style_sheet import StyleSheet
from ..components.loose_switch_setting_card import LooseSwitchSettingCard


class LineEditSettingCard(SettingCard):

    def __init__(self, configItem, text, title, step,
                 icon: Union[str, QIcon, FluentIconBase],
                 content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.lineEdit = SpinBox(self)
        self.lineEdit.setRange(1, 999)
        self.lineEdit.setValue(cfg.get(self.configItem))
        self.lineEdit.setSingleStep(step)
        self.pushButton = PushButton(text, self)
        self.pushButton.setMinimumWidth(100)
        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)
        self.pushButton.clicked.connect(self.__onValueChanged)

    def __onValueChanged(self):
        value = self.lineEdit.value()
        cfg.set(self.configItem, value)


class SettingInterface(SmoothScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.functionGroup = SettingCardGroup(self.tr("Functions"),
                                              self.scrollWidget)

        self.teamGamesNumberCard = LineEditSettingCard(
            cfg.teamGamesNumber, self.tr("Apply"),
            self.tr("Pre-team threshold"), 1, Icon.TEAM,
            self.tr("Pre-team threshold for common game rounds"), self.functionGroup)

        self.careerGamesCount = LineEditSettingCard(
            cfg.careerGamesNumber, self.tr("Apply"),
            self.tr("Default games number"), 10, Icon.SLIDESEARCH,
            self.
            tr("Setting the maximum number of games shows in the career interface"
               ), self.functionGroup)
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
        # self.enableStartWithComputer = SwitchSettingCard(
        #     Icon.DESKTOPRIGHT,
        #     self.tr("Auto-start on boot"),
        #     self.
        #     tr("Start Seraphine on boot automatically. Enabling this option may affect the boot speed"
        #        ),
        #     configItem=cfg.enableStartWithComputer,
        #     parent=self.generalGroup)
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
        self.functionGroup.addSettingCard(self.teamGamesNumberCard)
        self.functionGroup.addSettingCard(self.gameInfoShowTierCard)

        self.generalGroup.addSettingCard(self.lolFolderCard)
        # self.generalGroup.addSettingCard(self.enableStartWithComputer)
        self.generalGroup.addSettingCard(self.enableStartLolWithApp)
        self.generalGroup.addSettingCard(self.deleteResourceCard)
        self.generalGroup.addSettingCard(self.enableCloseToTray)

        self.personalizationGroup.addSettingCard(self.micaCard)
        self.personalizationGroup.addSettingCard(self.themeCard)
        self.personalizationGroup.addSettingCard(self.themeColorCard)
        self.personalizationGroup.addSettingCard(self.zoomCard)
        self.personalizationGroup.addSettingCard(self.languageCard)

        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(30)
        self.expandLayout.setContentsMargins(36, 0, 36, 0)
        self.expandLayout.addWidget(self.functionGroup)
        self.expandLayout.addWidget(self.generalGroup)
        self.expandLayout.addWidget(self.personalizationGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __connectSignalToSlot(self):
        self.lolFolderCard.clicked.connect(self.__onLolFolderCardClicked)

        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(setThemeColor)

        cfg.appRestartSig.connect(self.__showRestartToolTip)
        self.teamGamesNumberCard.pushButton.clicked.connect(
            self.__showUpdatedSuccessfullyToolTip)
        self.careerGamesCount.pushButton.clicked.connect(
            self.__showRestartToolTip)
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
        print(cfg.get(cfg.careerGamesNumber))

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
