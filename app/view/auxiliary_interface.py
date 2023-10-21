import threading
import os
from typing import Union
from PyQt5.QtGui import QIcon

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, ExpandLayout,
                            SmoothScrollArea, SettingCard, LineEdit, setCustomStyleSheet,
                            PushButton, ComboBox, SwitchButton, ConfigItem, qconfig,
                            IndicatorPosition, InfoBar, InfoBarPosition, SpinBox, ExpandGroupSettingCard)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QCompleter, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets.common.icon import FluentIconBase

from ..common.icons import Icon
from ..common.config import cfg
from ..common.style_sheet import StyleSheet
from ..lol.connector import connector
from ..lol.exceptions import *


class AuxiliaryInterface(SmoothScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.titleLabel = QLabel(self.tr("Auxiliary Functions"), self)

        self.profileGroup = SettingCardGroup(self.tr("Profile"),
                                             self.scrollWidget)
        self.gameGroup = SettingCardGroup(self.tr("Game"), self.scrollWidget)

        self.onlineStatusCard = OnlineStatusCard(
            title=self.tr("Online status"),
            content=self.tr("Set your profile online status"),
            parent=self.profileGroup)
        self.profileBackgroundCard = ProfileBackgroundCard(
            self.tr("Profile background"),
            self.tr("Set your profile background skin"), self.profileGroup)
        self.profileTierCard = ProfileTierCard(
            self.tr("Profile tier"),
            self.tr("Set your tier showed in your profile card"),
            self.profileGroup)
        self.onlineAvailabilityCard = OnlineAvailabilityCard(
            self.tr("Online Availability"),
            self.tr("Set your online Availability"), self.profileGroup)
        self.removeTokensCard = RemoveTokensCard(
            self.tr("Remove challenge tokens"),
            self.tr("Remove all challenge tokens from your profile"),
            self.profileGroup)
        # self.dodgeCard = DodgeCard(
        #     self.tr("Dodge"),
        #     self.tr("Dodge from champion select without closing clint"),
        #     self.gameGroup
        # )
        self.lockConfigCard = LockConfigCard(
            self.tr("Lock config"),
            self.tr("Make your game config unchangeable"),
            cfg.lockConfig, self.gameGroup)

        self.createPracticeLobbyCard = CreatePracticeLobbyCard(
            self.tr("Create 5v5 practice lobby"),
            self.tr("Only bots can be added to the lobby"),
            self.gameGroup)
        # 自动接受对局
        self.autoAcceptMatchingCard = AutoAcceptMatchingCard(
            self.tr("Auto accept"),
            self.tr(
                "Accept match making automatically after the number of seconds you set"),
            cfg.enableAutoAcceptMatching, cfg.autoAcceptMatchingDelay,
            self.gameGroup)
        self.autoReconnectCard = SwitchSettingCard(
            Icon.CONNECTION,
            self.tr("Auto reconnect"),
            self.tr("Automatically reconnect when disconnected"),
            cfg.enableAutoReconnect, self.gameGroup)
        self.spectateCard = SpectateCard(
            self.tr("Spectate"),
            self.tr("Spectate live game of summoner in the same environment"),
            self.gameGroup
        )
        self.autoSelectChampionCard = AutoSelectChampionCard(
            self.tr("Auto select champion"),
            self.tr("Auto select champion when blind selection begin"),
            cfg.enableAutoSelectChampion, cfg.autoSelectChampion,
            self.gameGroup)

        # self.copyPlayersInfoCard = SwitchSettingCard(
        #     Icon.COPY, self.tr("Auto copy players' info"),
        #     self.tr("Copy players' infomation to clipboard when game starts"),
        #     cfg.enableCopyPlayersInfo)

        self.__initWidget()
        self.__initLayout()

        self.__connectSignalToSlot()

    def __initWidget(self):
        self.titleLabel.setObjectName("titleLabel")
        self.scrollWidget.setObjectName('scrollWidget')

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 90, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        StyleSheet.AUXILIARY_INTERFACE.apply(self)

    def __initLayout(self):
        self.titleLabel.move(36, 30)

        # 个人主页
        self.profileGroup.addSettingCard(self.onlineStatusCard)
        self.profileGroup.addSettingCard(self.profileBackgroundCard)
        self.profileGroup.addSettingCard(self.profileTierCard)
        self.profileGroup.addSettingCard(self.onlineAvailabilityCard)
        self.profileGroup.addSettingCard(self.removeTokensCard)

        # 游戏
        self.gameGroup.addSettingCard(self.autoAcceptMatchingCard)
        self.gameGroup.addSettingCard(self.autoReconnectCard)
        self.gameGroup.addSettingCard(self.autoSelectChampionCard)
        # self.gameGroup.addSettingCard(self.copyPlayersInfoCard)
        self.gameGroup.addSettingCard(self.createPracticeLobbyCard)
        self.gameGroup.addSettingCard(self.spectateCard)
        # self.gameGroup.addSettingCard(self.dodgeCard)
        self.gameGroup.addSettingCard(self.lockConfigCard)

        self.expandLayout.setSpacing(30)
        self.expandLayout.setContentsMargins(36, 0, 36, 0)
        self.expandLayout.addWidget(self.gameGroup)
        self.expandLayout.addWidget(self.profileGroup)

    def setEnabled(self, a0: bool) -> None:
        self.autoAcceptMatchingCard.switchButton.setEnabled(a0)
        self.autoAcceptMatchingCard.lineEdit.setEnabled(a0)

        self.createPracticeLobbyCard.clear()
        self.createPracticeLobbyCard.nameLineEdit.setEnabled(a0)
        self.createPracticeLobbyCard.passwordLineEdit.setEnabled(a0)

        self.spectateCard.lineEdit.clear()
        self.spectateCard.lineEdit.setEnabled(a0)

        self.onlineStatusCard.clear()
        self.onlineStatusCard.lineEdit.setEnabled(a0)

        self.profileBackgroundCard.clear()
        self.profileBackgroundCard.championEdit.setEnabled(a0)

        self.profileTierCard.clear()
        self.profileTierCard.rankModeBox.setEnabled(a0)
        self.profileTierCard.tierBox.setEnabled(a0)
        self.profileTierCard.divisionBox.setEnabled(a0)

        self.onlineAvailabilityCard.clear()
        self.onlineAvailabilityCard.comboBox.setEnabled(a0)

        if not cfg.get(cfg.enableAutoSelectChampion):
            self.autoSelectChampionCard.lineEdit.setEnabled(a0)
        if a0:
            self.autoSelectChampionCard.validate()

        self.removeTokensCard.pushButton.setEnabled(a0)

        if a0 and cfg.get(cfg.enableAutoSelectChampion):
            self.autoSelectChampionCard.switchButton.setEnabled(True)

        self.lockConfigCard.setEnabled(a0)
        self.autoReconnectCard.setEnabled(a0)

        return super().setEnabled(a0)

    def __connectSignalToSlot(self):
        self.profileBackgroundCard.pushButton.clicked.connect(
            self.__onSetProfileBackgroundButtonClicked)

    def __onSetProfileBackgroundButtonClicked(self):
        champion = self.profileBackgroundCard.championEdit.text()
        skin = self.profileBackgroundCard.skinComboBox.currentText()

        def _():
            skinId = connector.manager.getSkinIdByChampionAndSkinName(
                champion, skin)
            connector.setProfileBackground(skinId)

        threading.Thread(target=_).start()


class OnlineStatusCard(ExpandGroupSettingCard):
    def __init__(self, title, content, parent=None):
        super().__init__(Icon.COMMENT, title, content, parent)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)
        self.statusLabel = QLabel(
            self.tr("Online status you want to change to:"))
        self.lineEdit = LineEdit()

        self.buttonWidget = QWidget()
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.pushButton = PushButton(self.tr("Apply"), self)

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.statusLabel, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(self.lineEdit, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.pushButton, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def __initWidget(self):
        self.lineEdit.setMinimumWidth(250)
        self.lineEdit.setPlaceholderText(self.tr("Please input your status"))

        self.pushButton.setMinimumWidth(100)
        self.pushButton.clicked.connect(self.__onPushButtonClicked)

    def __onPushButtonClicked(self):
        msg = self.lineEdit.text()

        threading.Thread(
            target=lambda: connector.setOnlineStatus(msg)).start()

    def clear(self):
        self.lineEdit.clear()


class ProfileBackgroundCard(ExpandGroupSettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.VIDEO_PERSON, title, content, parent)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.championLabel = QLabel(self.tr("Champion's name:"))
        self.championEdit = LineEdit(self)

        self.skinLabel = QLabel(self.tr("Skin's name:"))
        self.skinComboBox = ComboBox()

        self.buttonWidget = QWidget(self.view)
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.pushButton = PushButton(self.tr("Apply"))

        self.completer = None

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.inputLayout.setVerticalSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.championLabel, 0, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.championEdit, 0, 1, alignment=Qt.AlignRight)

        self.inputLayout.addWidget(
            self.skinLabel, 1, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.skinComboBox, 1, 1, alignment=Qt.AlignRight)

        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.pushButton, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def __initWidget(self):
        self.championEdit.setPlaceholderText(
            self.tr("Place input champion name"))
        self.championEdit.setMinimumWidth(250)
        self.championEdit.setClearButtonEnabled(True)

        self.pushButton.setMinimumWidth(100)
        self.pushButton.setEnabled(False)

        self.skinComboBox.setEnabled(False)
        self.skinComboBox.setMinimumWidth(250)
        self.skinComboBox.setPlaceholderText(self.tr("Place select skin"))

        self.championEdit.textChanged.connect(self.__onLineEditTextChanged)
        self.skinComboBox.currentTextChanged.connect(
            self.__onComboBoxTextChanged)

    def clear(self):
        self.championEdit.clear()
        self.skinComboBox.clear()
        self.completer = None

    def updateCompleter(self):
        champions = connector.manager.getChampionList()
        self.completer = QCompleter(champions)
        self.completer.setFilterMode(Qt.MatchContains)
        self.championEdit.setCompleter(self.completer)

    def __onLineEditTextChanged(self):
        text = self.championEdit.text()
        skins = connector.manager.getSkinListByChampionName(text)

        if len(skins) != 0:
            self.skinComboBox.addItems(skins)
            self.skinComboBox.setEnabled(True)
        else:
            self.skinComboBox.clear()
            self.skinComboBox.setEnabled(False)
            self.skinComboBox.setPlaceholderText(self.tr("Place select skin"))

    def __onComboBoxTextChanged(self):
        enable = self.championEdit.text(
        ) != "" and self.skinComboBox.currentText() != ""
        self.pushButton.setEnabled(enable)


class ProfileTierCard(ExpandGroupSettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.CERTIFICATE, title, content, parent)
        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.rankModeLabel = QLabel(self.tr("Game mode:"))
        self.rankModeBox = ComboBox()
        self.tierLabel = QLabel(self.tr("Tier:"))
        self.tierBox = ComboBox()
        self.divisionLabel = QLabel(self.tr("Division:"))
        self.divisionBox = ComboBox()

        self.buttonWidget = QWidget(self.view)
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.pushButton = PushButton(self.tr("Apply"))

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.inputLayout.setVerticalSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.rankModeLabel, 0, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.rankModeBox, 0, 1, alignment=Qt.AlignRight)

        self.inputLayout.addWidget(
            self.tierLabel, 1, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.tierBox, 1, 1, alignment=Qt.AlignRight)

        self.inputLayout.addWidget(
            self.divisionLabel, 2, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.divisionBox, 2, 1, alignment=Qt.AlignRight)

        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.pushButton, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def __initWidget(self):
        self.rankModeBox.addItems([
            self.tr("Teamfight Tactics"),
            self.tr("Ranked solo"),
            self.tr("Ranked flex")
        ])
        self.tierBox.addItems([
            self.tr('Na'),
            self.tr('Iron'),
            self.tr('Bronze'),
            self.tr('Silver'),
            self.tr('Gold'),
            self.tr('Platinum'),
            self.tr('Emerald'),
            self.tr('Diamond'),
            self.tr('Master'),
            self.tr('Grandmaster'),
            self.tr('Challenger')
        ])
        self.divisionBox.addItems(['I', 'II', 'III', 'IV'])

        self.rankModeBox.setPlaceholderText(self.tr("Please select game mode"))
        self.tierBox.setPlaceholderText(self.tr("Please select Tier"))
        self.divisionBox.setPlaceholderText(self.tr("Please select Division"))

        self.pushButton.setEnabled(False)

        self.rankModeBox.setMinimumWidth(250)
        self.tierBox.setMinimumWidth(250)
        self.divisionBox.setMinimumWidth(250)
        self.pushButton.setMinimumWidth(100)

        self.rankModeBox.currentTextChanged.connect(
            self.__onRankModeTextChanged)
        self.tierBox.currentTextChanged.connect(self.__onTierTextChanged)
        self.divisionBox.currentTextChanged.connect(
            self.__setPushButtonAvailability)
        self.pushButton.clicked.connect(self.__onPushButtonClicked)

    def clear(self):
        self.rankModeBox.setCurrentIndex(0)
        self.tierBox.setCurrentIndex(0)
        self.divisionBox.setCurrentIndex(0)

        self.rankModeBox.setPlaceholderText(self.tr("Game mode"))
        self.tierBox.setPlaceholderText(self.tr("Tier"))
        self.divisionBox.setPlaceholderText(self.tr("Division"))

    def __onRankModeTextChanged(self):
        currentText = self.tierBox.currentText()
        self.tierBox.clear()
        if self.rankModeBox.currentIndex() == 0:
            self.tierBox.addItems([
                self.tr('Na'),
                self.tr('Iron'),
                self.tr('Bronze'),
                self.tr('Silver'),
                self.tr('Gold'),
                self.tr('Platinum'),
                self.tr('Diamond'),
                self.tr('Master'),
                self.tr('Grandmaster'),
                self.tr('Challenger')
            ])

            if currentText != self.tr('Emerald'):
                self.tierBox.setCurrentText(currentText)
            else:
                self.tierBox.setPlaceholderText(self.tr("Tier"))
        else:
            self.tierBox.addItems([
                self.tr('Na'),
                self.tr('Iron'),
                self.tr('Bronze'),
                self.tr('Silver'),
                self.tr('Gold'),
                self.tr('Platinum'),
                self.tr('Emerald'),
                self.tr('Diamond'),
                self.tr('Master'),
                self.tr('Grandmaster'),
                self.tr('Challenger')
            ])

            self.tierBox.setCurrentText(currentText)

        self.__setPushButtonAvailability()

    def __onTierTextChanged(self):
        currentTier = self.tierBox.currentText()
        currentDivision = self.divisionBox.currentText()
        self.divisionBox.clear()
        if currentTier in [
                self.tr("Na"),
                self.tr('Master'),
                self.tr('Grandmaster'),
                self.tr('Challenger')
        ]:
            self.divisionBox.addItems(['--'])
            self.divisionBox.setCurrentText('--')
        else:
            self.divisionBox.addItems(['I', 'II', 'III', 'IV'])
            if currentDivision != '--':
                self.divisionBox.setCurrentText(currentDivision)
            else:
                self.divisionBox.setPlaceholderText("Division")

        self.__setPushButtonAvailability()

    def __setPushButtonAvailability(self):
        rankMode = self.rankModeBox.currentText()
        tier = self.tierBox.currentText()
        division = self.divisionBox.currentText()

        enable = rankMode != '' and tier != '' and division != ''
        self.pushButton.setEnabled(enable)

    def __onPushButtonClicked(self):
        queue = {
            self.tr("Teamfight Tactics"): "RANKED_TFT",
            self.tr("Ranked solo"): "RANKED_SOLO_5x5",
            self.tr("Ranked flex"): 'RANKED_FLEX_SR'
        }[self.rankModeBox.currentText()]

        tier = {
            self.tr('Na'): 'UNRANKED',
            self.tr('Iron'): 'IRON',
            self.tr('Bronze'): 'BRONZE',
            self.tr('Silver'): 'SILVER',
            self.tr('Gold'): 'GOLD',
            self.tr('Platinum'): 'PLATINUM',
            self.tr('Emerald'): 'EMERALD',
            self.tr('Diamond'): 'DIAMOND',
            self.tr('Master'): 'MASTER',
            self.tr('Grandmaster'): 'GRANDMASTER',
            self.tr('Challenger'): 'CHALLENGER'
        }[self.tierBox.currentText()]

        currentDivision = self.divisionBox.currentText()
        division = currentDivision if currentDivision != '--' else "NA"

        threading.Thread(target=lambda: connector.setTierShowed(
            queue, tier, division)).start()


class OnlineAvailabilityCard(ExpandGroupSettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.PERSONAVAILABLE, title, content, parent)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.availabilityLabel = QLabel(
            self.tr("Your online availability will be shown:"))
        self.comboBox = ComboBox()

        self.buttonWidget = QWidget(self.view)
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.pushButton = PushButton(self.tr("Apply"))

        self.__initLayout()
        self.__initWidget()

    def __initWidget(self):
        self.comboBox.setMinimumWidth(130)
        self.pushButton.setMinimumWidth(100)

        self.comboBox.addItems(
            [self.tr("chat"),
             self.tr("away"),
             self.tr("offline")])

        self.comboBox.setPlaceholderText(self.tr("Availability"))
        self.pushButton.setEnabled(False)

        self.comboBox.currentTextChanged.connect(self.__onComboBoxTextChanged)
        self.pushButton.clicked.connect(self.__onPushButttonClicked)

    def __initLayout(self):
        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.availabilityLabel, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(self.comboBox, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.pushButton, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def clear(self):
        self.comboBox.setPlaceholderText(self.tr("Availability"))
        self.comboBox.setCurrentIndex(0)

    def __onPushButttonClicked(self):
        availability = {
            self.tr("chat"): "chat",
            self.tr("away"): "away",
            self.tr("offline"): "offline"
        }[self.comboBox.currentText()]

        threading.Thread(target=lambda: connector.
                         setOnlineAvailability(availability)).start()

    def __onComboBoxTextChanged(self):
        if self.comboBox.currentIndex == -1:
            return

        self.pushButton.setEnabled(True)


class RemoveTokensCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.STAROFF, title, content, parent)
        self.pushButton = PushButton(self.tr("Remove"))
        self.pushButton.setMinimumWidth(100)

        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

        self.pushButton.clicked.connect(lambda: threading.Thread(
            target=lambda: connector.removeTokens()).start())


class CreatePracticeLobbyCard(ExpandGroupSettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.TEXTEDIT, title, content, parent)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QVBoxLayout(self.inputWidget)

        self.nameLayout = QHBoxLayout()
        self.nameLabel = QLabel(self.tr("Lobby's name: (cannot be empty)"))
        self.nameLineEdit = LineEdit()

        self.passwordLayout = QHBoxLayout()
        self.passwordLabel = QLabel(
            self.tr("Password: (password will NOT be set if it's empty)"))
        self.passwordLineEdit = LineEdit()

        self.pushButtonWidget = QWidget(self.view)
        self.pushButtonLayout = QHBoxLayout(self.pushButtonWidget)

        self.pushButton = PushButton(self.tr("Create"))

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.nameLayout.setContentsMargins(0, 0, 0, 0)
        self.nameLayout.addWidget(self.nameLabel, alignment=Qt.AlignLeft)
        self.nameLayout.addWidget(self.nameLineEdit, alignment=Qt.AlignRight)

        self.passwordLayout.setContentsMargins(0, 0, 0, 0)
        self.passwordLayout.addWidget(
            self.passwordLabel, alignment=Qt.AlignLeft)
        self.passwordLayout.addWidget(
            self.passwordLineEdit, alignment=Qt.AlignRight)

        self.inputLayout.addLayout(self.nameLayout)
        self.inputLayout.addLayout(self.passwordLayout)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.pushButtonLayout.setContentsMargins(48, 18, 44, 18)
        self.pushButtonLayout.addWidget(self.pushButton, 0, Qt.AlignRight)
        self.pushButtonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.pushButtonWidget)

    def __initWidget(self):
        self.nameLineEdit.setMinimumWidth(250)
        self.nameLineEdit.setClearButtonEnabled(True)
        self.nameLineEdit.setPlaceholderText(
            self.tr("Please input lobby's name"))

        self.passwordLineEdit.setMinimumWidth(250)
        self.passwordLineEdit.setClearButtonEnabled(True)
        self.passwordLineEdit.setPlaceholderText(
            self.tr("Please input password"))

        self.pushButton.setMinimumWidth(100)
        self.pushButton.setEnabled(False)

        self.nameLineEdit.textChanged.connect(self.__onNameLineEditTextChanged)
        self.pushButton.clicked.connect(self.__onPushButtonClicked)

    def clear(self):
        self.nameLineEdit.clear()
        self.passwordLineEdit.clear()

    def __onNameLineEditTextChanged(self):
        enable = self.nameLineEdit.text() != ""
        self.pushButton.setEnabled(enable)

    def __onPushButtonClicked(self):
        name = self.nameLineEdit.text()
        password = self.passwordLineEdit.text()

        threading.Thread(target=lambda: connector.
                         create5v5PracticeLobby(name, password)).start()


class SpectateCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None, parent=None):
        super().__init__(Icon.EYES, title, content, parent)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.summonerNameLabel = QLabel(
            self.tr("Summoners's name you want to spectate:"))
        self.lineEdit = LineEdit()

        self.buttonWidget = QWidget(self.view)
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.button = PushButton(self.tr("Spectate"))

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.summonerNameLabel, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(self.lineEdit, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def __initWidget(self):
        self.lineEdit.setPlaceholderText(
            self.tr("Please input summoner's name"))
        self.lineEdit.setMinimumWidth(250)
        self.lineEdit.setClearButtonEnabled(True)

        self.button.setMinimumWidth(100)
        self.button.setEnabled(False)

        self.lineEdit.textChanged.connect(self.__onLineEditTextChanged)
        self.button.clicked.connect(self.__onButtonClicked)

    def __onLineEditTextChanged(self):
        enable = self.lineEdit.text() != ""
        self.button.setEnabled(enable)

    def __onButtonClicked(self):
        def info(type, title, content):
            f = InfoBar.error if type == 'error' else InfoBar.success

            f(title=title, content=content, orient=Qt.Vertical, isClosable=True,
              position=InfoBarPosition.TOP_RIGHT, duration=5000,
              parent=self.parent().parent().parent().parent())

        try:
            connector.spectate(self.lineEdit.text())
        except SummonerNotFound:
            info('error', self.tr("Summoner not found"),
                 self.tr("Please check the summoner's name and retry"))
        except SummonerNotInGame:
            info('error', self.tr("Summoner isn't in game"), "")
        else:
            info('success', self.tr("Spectate successfully"),
                 self.tr("Please wait"),)


class AutoAcceptMatchingCard(ExpandGroupSettingCard):
    def __init__(self, title, content, enableConfigItem: ConfigItem = None,
                 delayConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.CIRCLEMARK, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.secondsLabel = QLabel(self.tr("Delay seconds after match made:"))
        self.lineEdit = SpinBox()

        self.switchButtonWidget = QWidget(self.view)
        self.switchButtonLayout = QHBoxLayout(self.switchButtonWidget)

        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.enableConfigItem = enableConfigItem
        self.delayConfigItem = delayConfigItem

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
        self.lineEdit.setRange(0, 11)
        self.lineEdit.setValue(cfg.get(self.delayConfigItem))
        self.lineEdit.setSingleStep(1)
        self.lineEdit.setMinimumWidth(250)

        self.switchButton.setEnabled(False)
        self.switchButton.setChecked(cfg.get(self.enableConfigItem))

        self.lineEdit.valueChanged.connect(self.__onLineEditValueChanged)
        self.switchButton.checkedChanged.connect(
            self.__onSwitchButtonCheckedChanged)

        # 这玩意在 enabled 是 false 的时候边框怪怪的，强行让它不那么怪
        qss = """
            SpinBox:disabled {
                color: rgba(255, 255, 255, 150);
                border: 1px solid rgba(255, 255, 255, 0.0698);
                background-color: rgba(255, 255, 255, 0.0419);
            }
        """
        setCustomStyleSheet(self.lineEdit, "", qss)

        value, isChecked = self.lineEdit.value(), self.switchButton.isChecked()
        self.__setStatusLableText(value, isChecked)

    def setValue(self, delay: int, isChecked: bool):
        qconfig.set(self.delayConfigItem, delay)
        qconfig.set(self.enableConfigItem, isChecked)

        self.__setStatusLableText(delay, isChecked)

    def __onSwitchButtonCheckedChanged(self, isChecked: bool):
        self.setValue(self.lineEdit.value(), isChecked)

    def __onLineEditValueChanged(self, value):
        self.setValue(value, self.switchButton.isChecked())

    def __setStatusLableText(self, delay, isChecked):
        if isChecked:
            self.statusLabel.setText(self.tr("Enabled, delay: ") + str(delay) +
                                     self.tr(" seconds"))
        else:
            self.statusLabel.setText(self.tr("Disabled"))


# 自动选择英雄卡片
class AutoSelectChampionCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None, enableConfigItem: ConfigItem = None,
                 championConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.CHECK, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.championLabel = QLabel(
            self.tr("Champion will be seleted automatically:"))
        self.lineEdit = LineEdit()

        self.switchButtonWidget = QWidget(self.view)
        self.switchButtonLayout = QHBoxLayout(self.switchButtonWidget)
        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.completer = None
        self.champions = []

        self.enableConfigItem = enableConfigItem
        self.championConfigItem = championConfigItem

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(self.championLabel, alignment=Qt.AlignLeft)
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
        self.lineEdit.setPlaceholderText(self.tr("Champion name"))
        self.lineEdit.setMinimumWidth(250)
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setEnabled(False)

        self.switchButton.setEnabled(False)

        self.setValue(qconfig.get(self.championConfigItem),
                      qconfig.get(self.enableConfigItem))

        self.lineEdit.textChanged.connect(self.__onLineEditTextChanged)
        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __setStatusLabelText(self, champion, isChecked):
        if isChecked:
            self.statusLabel.setText(self.tr("Enabled, champion: ") + champion)
        else:
            self.statusLabel.setText(self.tr("Disabled"))

    def updateCompleter(self):
        self.champions = connector.manager.getChampionList()
        self.completer = QCompleter(self.champions)
        self.completer.setFilterMode(Qt.MatchContains)
        self.lineEdit.setCompleter(self.completer)

        self.validate()

    def setValue(self, championName: str, isChecked: bool):
        qconfig.set(self.championConfigItem, championName)
        qconfig.set(self.enableConfigItem, isChecked)

        self.lineEdit.setText(championName)
        self.switchButton.setChecked(isChecked)

        self.__setStatusLabelText(championName, isChecked)

    def validate(self):
        text = self.lineEdit.text()

        if text not in self.champions and self.switchButton.checked:
            self.setValue("", False)

        self.__onLineEditTextChanged(text)

    def __onLineEditTextChanged(self, text):
        enable = text in self.champions

        self.switchButton.setEnabled(enable)

        self.setValue(text, self.switchButton.isChecked())

    def __onCheckedChanged(self, isChecked: bool):
        self.lineEdit.setEnabled(not isChecked)
        self.setValue(self.lineEdit.text(), isChecked)


class DodgeCard(SettingCard):
    def __init__(self, title, content, parent):
        super().__init__(Icon.EXIT, title, content, parent)
        self.pushButton = PushButton(self.tr("Dodge"))
        self.pushButton.setMinimumWidth(100)
        self.pushButton.setEnabled(False)

        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

        self.pushButton.clicked.connect(lambda: threading.Thread(
            target=lambda: connector.dodge()).start())


class LockConfigCard(SettingCard):
    def __init__(self, title, content, configItem: ConfigItem, parent):
        super().__init__(Icon.LOCK, title, content, parent)

        self.configItem = configItem

        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.hBoxLayout.addWidget(self.switchButton)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def setValue(self, isChecked: bool):
        qconfig.set(self.configItem, isChecked)
        self.switchButton.setChecked(isChecked)

    def __onCheckedChanged(self, isChecked: bool):
        self.setValue(isChecked)

        self.setConfigFileReadOnlyEnabled(isChecked)

    def setConfigFileReadOnlyEnabled(self, enable):
        path = f"{cfg.get(cfg.lolFolder)}/../Game/Config/PersistedSettings.json"

        if not os.path.exists(path):
            return

        mode = 0o444 if enable else 0o666
        os.chmod(path, mode)
