import sys

from qasync import asyncSlot, asyncClose
from PyQt5.QtGui import QColor, QPainter, QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QStackedWidget, QWidget, QLabel,
                             QFrame, QVBoxLayout, QSpacerItem, QSizePolicy)


from app.common.icons import Icon
from app.lol.connector import connector
from app.lol.opgg import opgg
from app.lol.champions import ChampionAlias
from app.common.logger import logger
from app.common.config import qconfig, cfg
from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import (FramelessWindow, isDarkTheme, BackgroundAnimationWidget,
                                       FluentTitleBar,  ComboBox, BodyLabel, ToolTipFilter,
                                       ToolTipPosition, IndeterminateProgressRing, setTheme,
                                       Theme, setCustomStyleSheet, SubtitleLabel, TitleLabel,
                                       DisplayLabel, PushButton, SearchLineEdit, ToolButton,
                                       FlyoutViewBase, Flyout, TeachingTip, TeachingTipView,
                                       TeachingTipTailPosition)
from app.components.transparent_button import TransparentToggleButton
from app.components.tier_list_widget import TierListWidget
from app.common.util import getTasklistPath, getLolClientPid

TAG = 'OpggInterface'


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

        setTheme(Theme.LIGHT)
        self.vBoxLayout = QVBoxLayout(self)

        self.filterLayout = QHBoxLayout()
        self.searchButton = ToolButton(Icon.SEARCH)
        self.toggleButton = TransparentToggleButton(Icon.APPLIST, Icon.PERSON)
        self.modeComboBox = ComboBox()
        self.regionComboBox = ComboBox()
        self.tierComboBox = ComboBox()
        self.positionComboBox = ComboBox()

        self.debugButton = PushButton()
        self.debugButton.setFixedSize(33, 33)
        self.debugButton.clicked.connect(self.__onDebugButtonClicked)

        self.versionLabel = BodyLabel()

        self.stackedWidget = QStackedWidget()
        self.tierInterface = TierInterface()
        self.buildInterface = BuildInterface()
        self.waitingInterface = WaitingInterface()
        self.errorInterface = ErrorInterface()

        # 缓存一个召唤师峡谷的梯队数据，切换位置的时候不重新调 opgg 了
        self.cachedTier = None
        self.cachedRegion = None
        self.cachedRankedTierList = None

        self.filterLock = False

        self.__initWindow()
        self.__initLayout()

    def __initWindow(self):
        self.setFixedSize(640, 821)
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
        self.searchButton.clicked.connect(self.__onSearchButtonClicked)

    def __initLayout(self):
        self.filterLayout.addWidget(self.toggleButton)
        self.filterLayout.addWidget(self.searchButton)
        self.filterLayout.addWidget(self.modeComboBox)
        self.filterLayout.addWidget(self.regionComboBox)
        self.filterLayout.addWidget(self.tierComboBox)
        self.filterLayout.addWidget(self.positionComboBox)
        self.filterLayout.addWidget(self.debugButton)
        self.filterLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding,  QSizePolicy.Fixed))
        self.filterLayout.addWidget(self.versionLabel)
        self.filterLayout.addSpacing(4)

        self.stackedWidget.addWidget(self.tierInterface)
        self.stackedWidget.addWidget(self.buildInterface)
        self.stackedWidget.addWidget(self.waitingInterface)
        self.stackedWidget.addWidget(self.errorInterface)

        # self.stackedWidget.setCurrentIndex(3)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addLayout(self.filterLayout)
        self.vBoxLayout.addWidget(self.stackedWidget)

    def __onToggleButtonClicked(self, index):
        self.stackedWidget.setCurrentIndex(index)

    def __onSearchButtonClicked(self):
        # 如果当前界面在梯队列表界面，则显示一个普通的搜索框用来筛选下方的英雄
        if self.stackedWidget.currentWidget() is self.tierInterface:
            # 点击之后弹出的搜索框是空白的，让下方的所有英雄重新显示出来比较符合直觉
            self.tierInterface.tierList.showAllChampions()

            view = SearchLineEditFlyout()
            Flyout.make(view, self.searchButton, self, isDeleteOnClose=True)
            view.textChanged.connect(self.__onSearchLineTextChanged)
            view.searchLineEdit.setFocus()

    def __onSearchLineTextChanged(self, text):
        if text == '':
            self.tierInterface.tierList.showAllChampions()
            return

        if ChampionAlias.isAvailable():
            ids = ChampionAlias.getChampionIdsByAliasFuzzily(text)
            self.tierInterface.tierList.filterChampions('championId', ids)
        else:
            self.tierInterface.tierList.filterChampions('name', text)

    @asyncSlot(bool)
    async def __onDebugButtonClicked(self, _):
        await opgg.start()
        await connector.autoStart()
        await ChampionAlias.checkAndUpdate()

        print("init")

    def setComboBoxesEnabled(self, enabled):
        self.toggleButton.setEnabled(enabled)
        self.searchButton.setEnabled(enabled)
        self.modeComboBox.setEnabled(enabled)
        self.regionComboBox.setEnabled(enabled)
        self.tierComboBox.setEnabled(enabled)
        self.positionComboBox.setEnabled(enabled)

    def setCurrentInterface(self, widget: QWidget):
        self.setComboBoxesEnabled(widget is not self.waitingInterface)
        self.stackedWidget.setCurrentWidget(widget)

    @ asyncSlot(int)
    async def __onFilterTextChanged(self, _):
        # 给函数加个互斥锁，防止在该函数内修改了 combo box 的值，导致无限递归
        if self.filterLock:
            return

        self.filterLock = True

        # 判断一下是刷新梯队列表还是 build 界面
        current = self.stackedWidget.currentWidget()

        # 显示转圈圈界面，并且锁住上方的 combo box
        self.setCurrentInterface(self.waitingInterface)

        # 如果是在出错的界面请求的更新，则需要知道是因为刷新了啥才进入到的出错界面
        if current is self.errorInterface:
            current = self.errorInterface.getFromInterface()

        try:
            # 尝试刷新当前的界面
            await self.__updateInterface(current)

            # 让转圈消失，显示界面
            self.setCurrentInterface(current)
        except Exception as e:
            logger.error(f"Get OPGG tier list failed, {e}", TAG)

            # 记录一下是由哪里进入到的出错的界面
            self.errorInterface.setFromInterface(current)

            # 显示出错的界面
            self.setCurrentInterface(self.errorInterface)

        self.filterLock = False

    async def __updateInterface(self, interface: QWidget):
        if interface is self.tierInterface:
            await self.__updateTierInterface()

    async def __updateTierInterface(self):
        mode = self.modeComboBox.currentData()
        region = self.regionComboBox.currentData()
        tier = self.tierComboBox.currentData()
        position = self.positionComboBox.currentData()

        cfg.set(cfg.opggRegion, region)
        cfg.set(cfg.opggTier, tier)

        logger.info(
            f"Get tier list: {mode}, {region}, {tier}, {position}", TAG)

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
            # rank 模式下，如果是切换了位置选项，会命中 cache，不用重新请求了
            if tier == self.cachedTier and \
                    region == self.cachedRegion and \
                    self.cachedRankedTierList != None:
                res = self.cachedRankedTierList['data'][position]
                data = self.cachedRankedTierList
            # 否则是第一次请求 rank 模式数据，记录一下 cache
            else:
                data = await opgg.getTierList(region, mode, tier)
                self.cachedTier = tier
                self.cachedRegion = region
                self.cachedRankedTierList = data

                res = data['data'][position]
        else:
            # 除了 rank 意外的其他模式，该咋整咋整吧
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

        StyleSheet.WAITING_INTERFACE.apply(self)

    def __initWidget(self):
        pass

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.processRing, alignment=Qt.AlignCenter)


class ErrorInterface(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.title = QLabel(self.tr("Fetch data failed 😭"))
        self.content = QLabel(self.tr("Please wait and try again"))

        self.fromInterface: QWidget = None

        self.__initWidget()
        self.__initLayout()

        StyleSheet.ERROR_INTERFACE.apply(self)

    def setFromInterface(self, interface: QWidget):
        self.fromInterface = interface

    def getFromInterface(self):
        return self.fromInterface

    def __initWidget(self):
        self.title.setObjectName("titleLabel")
        self.content.setObjectName("contentLabel")

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.title, alignment=Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.content, alignment=Qt.AlignCenter)


class SearchLineEditFlyout(FlyoutViewBase):
    textChanged = pyqtSignal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.searchLineEdit = SearchLineEdit()
        self.vBoxLayout.addWidget(self.searchLineEdit)

        self.searchLineEdit.textChanged.connect(self.textChanged)
        self.searchLineEdit.setPlaceholderText(self.tr("Search champions"))
        self.searchLineEdit.setMinimumWidth(200)
