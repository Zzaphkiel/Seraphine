import sys

from qasync import asyncSlot, asyncClose
from PyQt5.QtGui import QColor, QPainter, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QStackedWidget, QWidget,
                             QFrame, QVBoxLayout, QSpacerItem, QSizePolicy)


from app.common.icons import Icon
from app.lol.connector import connector
from app.lol.opgg import opgg
from app.common.config import qconfig, cfg
from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import (FramelessWindow, isDarkTheme, BackgroundAnimationWidget,
                                       FluentTitleBar,  ComboBox, BodyLabel, ToolTipFilter,
                                       ToolTipPosition, IndeterminateProgressRing, setTheme,
                                       Theme, setCustomStyleSheet)
from app.components.transparent_button import TransparentToggleButton
from app.components.tier_list_widget import TierListWidget
from app.common.util import getTasklistPath, getLolClientPid


class OpggInterfaceBase(BackgroundAnimationWidget, FramelessWindow):
    def __init__(self, parent=None):
        self._isMicaEnabled = False
        self._lightBackgroundColor = QColor(243, 243, 243)
        self._darkBackgroundColor = QColor(32, 32, 32)

        super().__init__(parent=parent)

        self.setTitleBar(FluentTitleBar(self))
        self.setMicaEffectEnabled(True)
        self.setContentsMargins(0, 36, 0, 0)

        self.titleBar.hBoxLayout.setContentsMargins(14, 0, 0, 0)
        self.titleBar.maxBtn.setVisible(False)

        qconfig.themeChangedFinished.connect(self._onThemeChangedFinished)

    def setCustomBackgroundColor(self, light, dark):
        self._lightBackgroundColor = QColor(light)
        self._darkBackgroundColor = QColor(dark)
        self._updateBackgroundColor()

    def _normalBackgroundColor(self):
        if not self.isMicaEffectEnabled():
            return self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor

        return QColor(0, 0, 0, 0)

    def _onThemeChangedFinished(self):
        if self.isMicaEffectEnabled():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.backgroundColor)
        painter.drawRect(self.rect())

    def setMicaEffectEnabled(self, isEnabled: bool):
        """ set whether the mica effect is enabled, only available on Win11 """
        if sys.platform != 'win32' or sys.getwindowsversion().build < 22000:
            return

        self._isMicaEnabled = isEnabled

        if isEnabled:
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())
        else:
            self.windowEffect.removeBackgroundEffect(self.winId())

        self.setBackgroundColor(self._normalBackgroundColor())

    def isMicaEffectEnabled(self):
        return self._isMicaEnabled


class OpggInterface(OpggInterfaceBase):
    def __init__(self, parent=None):
        super().__init__()

        # setTheme(Theme.LIGHT)
        self.vBoxLayout = QVBoxLayout(self)

        self.filterLayout = QHBoxLayout()
        self.toggleButton = TransparentToggleButton(Icon.APPLIST, Icon.PERSON)
        self.modeComboBox = ComboBox()
        self.regionComboBox = ComboBox()
        self.tierComboBox = ComboBox()
        self.positionComboBox = ComboBox()
        self.versionLabel = BodyLabel()

        self.stackedWidget = QStackedWidget()
        self.tierInterface = TierInterface()
        self.buildInterface = BuildInterface()
        self.waitingInterface = WaitingInterface()

        # 缓存一个召唤师峡谷的梯队数据，切换位置的时候不重新调 opgg 了
        self.cachedTier = None
        self.cachedRegion = None
        self.cachedRankedTierList = None

        self.filterLock = False

        self.__initWindow()
        self.__initLayout()

        # self.test()

    def __initWindow(self):
        self.setMinimumSize(640, 816)
        self.setWindowIcon(QIcon("app/resource/images/opgg.svg"))
        self.setWindowTitle("OP.GG")

        self.toggleButton.setToolTip(self.tr("Show Tier / Build"))
        self.toggleButton.installEventFilter(ToolTipFilter(
            self.toggleButton, 500, ToolTipPosition.TOP))

        self.modeComboBox.addItem(
            self.tr("Ranked"), icon="app/resource/images/sr-victory.png", userData='ranked')
        self.modeComboBox.addItem(
            self.tr("Aram"), icon="app/resource/images/ha-victory.png", userData='aram')
        self.modeComboBox.addItem(
            self.tr("Arena"), icon="app/resource/images/arena-victory.png", userData='arena')
        self.modeComboBox.addItem(
            self.tr("Urf"), icon="app/resource/images/other-victory.png", userData='urf')
        self.modeComboBox.addItem(
            self.tr("Nexus Blitz"), icon="app/resource/images/other-victory.png", userData='nexus_blitz')

        self.regionComboBox.addItem(
            self.tr("All regions"), icon="app/resource/images/global.svg", userData="global")
        self.regionComboBox.addItem(
            self.tr("Korea"), icon="app/resource/images/kr.svg", userData="kr")

        self.tierComboBox.addItem(
            self.tr("All"), icon="app/resource/images/UNRANKED.svg", userData="all")
        self.tierComboBox.addItem(
            self.tr("Gold -"), icon="app/resource/images/GOLD.svg", userData="ibsg")
        self.tierComboBox.addItem(
            self.tr("Gold +"), icon="app/resource/images/GOLD.svg", userData="gold_plus")
        self.tierComboBox.addItem(
            self.tr("Platinum +"), icon="app/resource/images/PLATINUM.svg", userData="platinum_plus")
        self.tierComboBox.addItem(
            self.tr("Emerald +"), icon="app/resource/images/EMERALD.svg", userData="emerald_plus")
        self.tierComboBox.addItem(
            self.tr("Diamond +"), icon="app/resource/images/DIAMOND.svg", userData="diamond_plus")
        self.tierComboBox.addItem(
            self.tr("Master"), icon="app/resource/images/MASTER.svg", userData="master")
        self.tierComboBox.addItem(self.tr(
            "Master +"), icon="app/resource/images/MASTER.svg", userData="master_plus")
        self.tierComboBox.addItem(
            self.tr("Grandmaster"), icon="app/resource/images/GRANDMASTER.svg", userData="grandmaster")
        self.tierComboBox.addItem(self.tr(
            "Challenger"), icon="app/resource/images/CHALLENGER.svg", userData="challenger")

        self.positionComboBox.addItem(
            self.tr("Top"), "app/resource/images/icon-position-top.svg", "TOP")
        self.positionComboBox.addItem(
            self.tr("Jungle"), "app/resource/images/icon-position-jng.svg", "JUNGLE")
        self.positionComboBox.addItem(
            self.tr("Mid"), "app/resource/images/icon-position-mid.svg", "MID")
        self.positionComboBox.addItem(
            self.tr("Bottom"), "app/resource/images/icon-position-bot.svg", "ADC")
        self.positionComboBox.addItem(
            self.tr("Support"), "app/resource/images/icon-position-sup.svg", "SUPPORT")

        self.modeComboBox.currentIndexChanged.connect(
            self.__onFilterTextChanged)
        self.regionComboBox.currentIndexChanged.connect(
            self.__onFilterTextChanged)
        self.tierComboBox.currentIndexChanged.connect(
            self.__onFilterTextChanged)
        self.positionComboBox.currentIndexChanged.connect(
            self.__onFilterTextChanged)

        self.toggleButton.changed.connect(self.__onToggleButtonClicked)

    def __initLayout(self):
        self.filterLayout.addWidget(self.toggleButton)
        self.filterLayout.addWidget(self.modeComboBox)
        self.filterLayout.addWidget(self.regionComboBox)
        self.filterLayout.addWidget(self.tierComboBox)
        self.filterLayout.addWidget(self.positionComboBox)
        self.filterLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding,  QSizePolicy.Fixed))
        self.filterLayout.addWidget(self.versionLabel)
        self.filterLayout.addSpacing(4)

        self.stackedWidget.addWidget(self.tierInterface)
        self.stackedWidget.addWidget(self.buildInterface)
        self.stackedWidget.addWidget(self.waitingInterface)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addLayout(self.filterLayout)
        self.vBoxLayout.addWidget(self.stackedWidget)

    # def __onToggleButtonClicked(self, index):
    #     self.stackedWidget.setCurrentIndex(index)

    @asyncSlot(int)
    async def __onToggleButtonClicked(self, index):
        await opgg.start()
        await connector.autoStart()

        print("init")

    def setWaitingInterfaceEnabled(self, enabled, back):
        self.toggleButton.setEnabled(not enabled)
        self.modeComboBox.setEnabled(not enabled)
        self.regionComboBox.setEnabled(not enabled)
        self.tierComboBox.setEnabled(not enabled)
        self.positionComboBox.setEnabled(not enabled)

        self.stackedWidget.setCurrentIndex(2 if enabled else back)

    @asyncSlot(int)
    async def __onFilterTextChanged(self, _):
        # TODO:
        # 请求异常时显示空白画面并提示，而不是报错

        if self.filterLock:
            return

        self.filterLock = True
        currentIndex = self.stackedWidget.currentIndex()
        self.setWaitingInterfaceEnabled(True, currentIndex)
        if currentIndex == 0:
            await self.__updateTierInterface()

        self.setWaitingInterfaceEnabled(False, currentIndex)
        self.filterLock = False

    async def __updateTierInterface(self):
        mode = self.modeComboBox.currentData()
        region = self.regionComboBox.currentData()
        tier = self.tierComboBox.currentData()
        position = self.positionComboBox.currentData()

        cfg.set(cfg.opggRegion, region)
        cfg.set(cfg.opggTier, tier)

        # 只有在排位模式下，可以选择对应的分路
        if mode != 'ranked':
            position = 'none'
            self.positionComboBox.setVisible(False)
        else:
            self.positionComboBox.setVisible(True)

        # 斗魂竞技场的段位选择只能是 "all"
        if mode == 'arena':
            tier = 'all'
            self.tierComboBox.setVisible(False)
        else:
            self.tierComboBox.setVisible(True)

        if mode == 'ranked':
            if tier == self.cachedTier and \
                    region == self.cachedRegion and \
                    self.cachedRankedTierList != None:
                res = self.cachedRankedTierList['data'][position]
                data = self.cachedRankedTierList
            else:
                data = await opgg.getTierList(region, mode, tier)
                self.cachedTier = tier
                self.cachedRegion = region
                self.cachedRankedTierList = data

                res = data['data'][position]
        else:
            data = await opgg.getTierList(region, mode, tier)
            res = data['data']

        version = data['version']
        self.versionLabel.setText(self.tr("Version: ") + version)
        self.tierInterface.tierList.updateList(res)

    @asyncClose
    async def closeEvent(self, e):
        await connector.close()
        await opgg.close()

        return super().closeEvent(e)


class TierInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.tierList = TierListWidget()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.addWidget(self.tierList)


class BuildInterface(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        pass

    def __initLayout(self):
        pass


class WaitingInterface(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.processRing = IndeterminateProgressRing()

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        StyleSheet.WAITING_INTERFACE.apply(self)

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.processRing, alignment=Qt.AlignCenter)
