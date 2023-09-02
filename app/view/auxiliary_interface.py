import threading
import os

from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, ExpandLayout,
                            SmoothScrollArea, SettingCard, LineEdit,
                            PushButton, ComboBox, SwitchButton, ConfigItem, qconfig,
                            IndicatorPosition)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QCompleter

from ..common.icons import Icon
from ..common.config import cfg
from ..common.style_sheet import StyleSheet
from ..lol.connector import LolClientConnector, connector


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
            self.tr("Password will NOT be set if line edit is empty"),
            self.gameGroup)
        # 自动接受对局
        self.autoAcceptMatchingCard = SwitchSettingCard(
            Icon.CIRCLEMARK, self.tr("Auto accept"),
            self.tr("Accept match making automatically"),
            cfg.enableAutoAcceptMatching, self.gameGroup)
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

        self.autoSelectChampionCard.lineEdit.setEnabled(a0)

        self.removeTokensCard.pushButton.setEnabled(a0)

        if a0 and cfg.get(cfg.enableAutoSelectChampion):
            self.autoSelectChampionCard.switchButton.setEnabled(True)

        self.lockConfigCard.setEnabled(a0)

        return super().setEnabled(a0)

    def __connectSignalToSlot(self):
        self.onlineStatusCard.pushButton.clicked.connect(
            self.__onSetStatusButtonClicked)
        self.profileBackgroundCard.pushButton.clicked.connect(
            self.__onSetProfileBackgroundButtonClicked)

    def __onSetStatusButtonClicked(self):
        msg = self.onlineStatusCard.lineEdit.text()
        threading.Thread(
            target=lambda: connector.setOnlineStatus(msg)).start()

    def __onSetProfileBackgroundButtonClicked(self):
        champion = self.profileBackgroundCard.championEdit.text()
        skin = self.profileBackgroundCard.skinComboBox.currentText()

        def _():
            skinId = connector.manager.getSkinIdByChampionAndSkinName(
                champion, skin)
            connector.setProfileBackground(skinId)

        threading.Thread(target=_).start()


class OnlineStatusCard(SettingCard):

    def __init__(self, title, content, parent=None):

        super().__init__(Icon.COMMENT, title, content, parent)
        self.lineEdit = LineEdit(self)
        self.lineEdit.setMinimumWidth(422)
        self.lineEdit.setPlaceholderText(self.tr("Please input your status"))
        self.pushButton = PushButton(self.tr("Apply"), self)
        self.pushButton.setMinimumWidth(100)
        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

    def clear(self):
        self.lineEdit.clear()


class ProfileBackgroundCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.VIDEO_PERSON, title, content, parent)
        self.championEdit = LineEdit(self)
        self.championEdit.setPlaceholderText(
            self.tr("Place input champion name"))
        self.championEdit.setMinimumWidth(140)
        self.championEdit.setClearButtonEnabled(True)

        self.pushButton = PushButton(self.tr("Apply"), self)
        self.pushButton.setMinimumWidth(100)
        self.pushButton.setEnabled(False)
        self.skinComboBox = ComboBox()
        self.skinComboBox.setEnabled(False)
        self.skinComboBox.setMinimumWidth(250)
        self.skinComboBox.setPlaceholderText(self.tr("Place select skin"))

        self.completer = None

        self.hBoxLayout.addWidget(self.championEdit)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.skinComboBox)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

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


class ProfileTierCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.CERTIFICATE, title, content, parent)
        self.rankModeBox = ComboBox()
        self.tierBox = ComboBox()
        self.divisionBox = ComboBox()
        self.pushButton = PushButton(self.tr("Apply"))

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

        self.rankModeBox.setPlaceholderText(self.tr("Game mode"))
        self.tierBox.setPlaceholderText(self.tr("Tier"))
        self.divisionBox.setPlaceholderText(self.tr("Division"))

        self.pushButton.setEnabled(False)

        self.rankModeBox.setMinimumWidth(130)
        self.tierBox.setMinimumWidth(130)
        self.divisionBox.setMinimumWidth(130)
        self.pushButton.setMinimumWidth(100)

        self.hBoxLayout.addWidget(self.rankModeBox)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.tierBox)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.divisionBox)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

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


class OnlineAvailabilityCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.PERSONAVAILABLE, title, content, parent)
        self.comboBox = ComboBox()
        self.pushButton = PushButton(self.tr("Apply"))

        self.comboBox.setMinimumWidth(130)
        self.pushButton.setMinimumWidth(100)

        self.comboBox.addItems(
            [self.tr("chat"),
             self.tr("away"),
             self.tr("offline")])
        self.comboBox.setPlaceholderText(self.tr("Availability"))
        self.pushButton.setEnabled(False)

        self.hBoxLayout.addWidget(self.comboBox)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

        self.comboBox.currentTextChanged.connect(self.__onComboBoxTextChanged)
        self.pushButton.clicked.connect(self.__onPushButttonClicked)

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


class CreatePracticeLobbyCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.TEXTEDIT, title, content, parent)
        self.nameLineEdit = LineEdit()
        self.nameLineEdit.setMinimumWidth(216)
        self.nameLineEdit.setClearButtonEnabled(True)
        self.nameLineEdit.setPlaceholderText(self.tr("Lobby name"))

        self.passwordLineEdit = LineEdit()
        self.passwordLineEdit.setMinimumWidth(190)
        self.passwordLineEdit.setClearButtonEnabled(True)
        self.passwordLineEdit.setPlaceholderText(self.tr("Lobby password"))

        self.pushButton = PushButton(self.tr("Create"))
        self.pushButton.setMinimumWidth(100)
        self.pushButton.setEnabled(False)

        self.hBoxLayout.addWidget(self.nameLineEdit)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.passwordLineEdit)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

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


class SpectateCard(SettingCard):
    def __init__(self, title, content=None, parent=None):
        super().__init__(Icon.EYES, title, content, parent)

        self.lineEdit = LineEdit()
        self.lineEdit.setPlaceholderText(
            self.tr("Summoner's name"))
        self.lineEdit.setMinimumWidth(190)
        self.lineEdit.setClearButtonEnabled(True)

        self.button = PushButton(self.tr("Spectate"))
        self.button.setMinimumWidth(100)
        self.button.setEnabled(False)

        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.button)
        self.hBoxLayout.addSpacing(16)

        self.lineEdit.textChanged.connect(self.__onLineEditTextChanged)
        self.button.clicked.connect(self.__onButtonClicked)

    def __onLineEditTextChanged(self):
        enable = self.lineEdit.text() != ""
        self.button.setEnabled(enable)

    def __onButtonClicked(self):
        connector.spectate(self.lineEdit.text())


# 自动选择英雄卡片
class AutoSelectChampionCard(SettingCard):
    def __init__(self, title, content=None, enableConfigItem: ConfigItem = None,
                 championConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.CHECK, title, content, parent)

        self.enableConfigItem = enableConfigItem
        self.championConfigItem = championConfigItem

        self.lineEdit = LineEdit()
        self.lineEdit.setPlaceholderText(
            self.tr("Champion name"))
        self.lineEdit.setMinimumWidth(190)
        self.lineEdit.setClearButtonEnabled(True)

        self.completer = None
        self.champions = []

        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)
        self.switchButton.setEnabled(False)

        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.addSpacing(46)
        self.hBoxLayout.addWidget(self.switchButton)
        self.hBoxLayout.addSpacing(16)

        self.setValue(qconfig.get(championConfigItem),
                      qconfig.get(enableConfigItem))

        self.lineEdit.textChanged.connect(self.__onLineEditTextChanged)
        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

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

    def validate(self):
        text = self.lineEdit.text()

        if text not in self.champions and self.switchButton.checked:
            self.setValue("", False)

        self.__onLineEditTextChanged()

    def __onLineEditTextChanged(self):
        enable = self.lineEdit.text() in self.champions

        self.switchButton.setEnabled(enable)

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

        # self.pushButton.clicked.connect(lambda: print(f"{1/0}"))


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
