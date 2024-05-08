# coding:utf-8
import os

from ..common.qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard, PushSettingCard,
    ExpandLayout, CustomColorSettingCard, InfoBar, setTheme, setThemeColor,
    SmoothScrollArea, PrimaryPushSettingCard,
    HyperlinkCard, TeachingTip, TeachingTipTailPosition, TeachingTipView,
    ExpandGroupSettingCard, ConfigItem, setCustomStyleSheet, SwitchButton,
    qconfig, LineEdit, PushButton, IndicatorPosition, FluentIcon)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout

from ..common.icons import Icon
from ..common.config import (
    cfg, YEAR, AUTHOR, VERSION, FEEDBACK_URL, GITHUB_URL, isWin11)
from ..common.style_sheet import StyleSheet
from ..components.seraphine_interface import SeraphineInterface
from ..components.setting_cards import (LineEditSettingCard, GameTabColorSettingCard,
                                        LooseSwitchSettingCard, ProxySettingCard)


class SettingInterface(SeraphineInterface):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.functionGroup = SettingCardGroup(self.tr("Functions"),
                                              self.scrollWidget)

        self.apiConcurrencyCount = LineEditSettingCard(
            cfg.apiConcurrencyNumber,
            self.tr("LCU API concurrency number"),
            self.tr("Number of concurrency:"),
            1, 1, 5,
            Icon.APPLIST,
            self.tr("Setting the maximum number of API concurrency."),
            self.functionGroup)

        self.careerGamesCount = LineEditSettingCard(
            cfg.careerGamesNumber,
            self.tr("Default games number"),
            self.tr("Number of games:"),
            10, 10, 100,
            Icon.SLIDESEARCH,
            self.tr("Setting the maximum number of games shows in the career interface"), self.functionGroup)

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
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor, Icon.PALETTE, self.tr("Theme color"),
            self.tr("Change the theme color of Seraphine"),
            self.personalizationGroup)
        self.gameTabColorSettingCard = GameTabColorSettingCard(
            self.tr("Game tabs color"),
            self.tr("Change the color of game tabs"),
            cfg.winCardColor, cfg.loseCardColor, cfg.remakeCardColor,
            self.personalizationGroup
        )
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

        self.updateGroup = SettingCardGroup(
            self.tr("Update"), self.scrollWidget)
        self.checkUpdateCard = SwitchSettingCard(
            Icon.UPDATE, self.tr("Check for updates"),
            self.tr(
                "Automatically check for updates when software starts"),
            cfg.enableCheckUpdate
        )
        self.httpProxyCard = ProxySettingCard(
            self.tr("HTTP proxy"), self.tr(
                "Using a proxy when connecting to GitHub"),
            cfg.enableProxy, cfg.proxyAddr, self.updateGroup)

        self.aboutGroup = SettingCardGroup(self.tr("About"), self.scrollWidget)
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'), Icon.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve Seraphine by providing feedback'),
            self.aboutGroup)
        self.viewLogBtn = PushButton(FluentIcon.LINK, "View Log", self.feedbackCard)
        self.viewLogBtn.clicked.connect(lambda: os.system(f'explorer {os.getcwd()}\\log'))
        self.feedbackCard.hBoxLayout.removeWidget(self.feedbackCard.button)  # Note 它在右边会更协调些, 一会儿加回来
        self.feedbackCard.hBoxLayout.addWidget(self.viewLogBtn)
        self.feedbackCard.hBoxLayout.addSpacing(16)
        self.feedbackCard.hBoxLayout.addWidget(self.feedbackCard.button)
        self.feedbackCard.hBoxLayout.addSpacing(16)
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
        self.functionGroup.addSettingCard(self.apiConcurrencyCount)
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
        self.personalizationGroup.addSettingCard(self.gameTabColorSettingCard)
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

        self.themeCard.comboBox.currentIndexChanged.connect(
            lambda: setTheme(cfg.get(cfg.themeMode)))
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
        self.window().startInterface.label2.setText(folder)

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
