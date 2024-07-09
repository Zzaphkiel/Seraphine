import sys

from qasync import asyncSlot, asyncClose
from PyQt5.QtGui import QColor, QPainter, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QStackedWidget, QWidget,
                             QFrame, QVBoxLayout, QSpacerItem, QSizePolicy)


from app.common.icons import Icon
from app.lol.connector import connector
from app.lol.opgg import opgg
from app.common.config import qconfig
from app.common.qfluentwidgets import (FramelessWindow, isDarkTheme, BackgroundAnimationWidget,
                                       FluentTitleBar,  ComboBox, BodyLabel, ToolTipFilter,
                                       ToolTipPosition, IndeterminateProgressRing)
from app.components.toggle_button import ToggleButton
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

        self.vBoxLayout = QVBoxLayout(self)

        self.filterLayout = QHBoxLayout()
        self.toggleButton = ToggleButton(Icon.APPLIST, Icon.PERSON)
        self.modeComboBox = ComboBox()
        self.regionComboBox = ComboBox()
        self.tierComboBox = ComboBox()
        self.positionComboBox = ComboBox()
        self.versionLable = BodyLabel()

        self.stackedWidget = QStackedWidget()
        self.tierInterface = TierInterface()
        self.buildInterface = BuildInterface()
        self.waitingInterface = WaitingInterface()

        self.__initWindow()
        self.__initLayout()

        self.test()

    def __initWindow(self):
        self.setMinimumSize(600, 800)
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
            self.tr("All"), "app/resource/images/icon-position-all.svg", "ALL")
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

        self.toggleButton.changed.connect(self.__onToggleButtonClicked)

    def __initLayout(self):
        self.filterLayout.addWidget(self.toggleButton)
        self.filterLayout.addWidget(self.modeComboBox)
        self.filterLayout.addWidget(self.regionComboBox)
        self.filterLayout.addWidget(self.tierComboBox)
        self.filterLayout.addWidget(self.positionComboBox)
        self.filterLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding,  QSizePolicy.Fixed))
        self.filterLayout.addWidget(self.versionLable)

        self.stackedWidget.addWidget(self.tierInterface)
        self.stackedWidget.addWidget(self.buildInterface)
        self.stackedWidget.addWidget(self.waitingInterface)
        self.stackedWidget.setCurrentIndex(0)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.addLayout(self.filterLayout)
        self.vBoxLayout.addWidget(self.stackedWidget)

    def __onToggleButtonClicked(self, index):
        self.stackedWidget.setCurrentIndex(index)

    def test(self):
        # await connector.autoStart()
        # await opgg.start()

        # res = await opgg.getTierList("kr", "ranked", "emerald_plus", "14.13")
        res = [{'championId': 145, 'name': '虚空之女', 'icon': 'app/resource/game/champion icons/145.png', 'winRate': 0.513415, 'pickRate': 0.443289, 'banRate': 0.174565, 'kda': 2.772181, 'tier': 1, 'rank': 1, 'position': 'ADC', 'counters': [{'championId': 895, 'icon': 'app/resource/game/champion icons/895.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}]}, {'championId': 22, 'name': '寒冰射手', 'icon': 'app/resource/game/champion icons/22.png', 'winRate': 0.513519, 'pickRate': 0.134393, 'banRate': 0.298265, 'kda': 2.644017, 'tier': 1, 'rank': 2, 'position': 'ADC', 'counters': [{'championId': 29, 'icon': 'app/resource/game/champion icons/29.png'}]}, {'championId': 81, 'name': '探险家', 'icon': 'app/resource/game/champion icons/81.png', 'winRate': 0.499005, 'pickRate': 0.335979, 'banRate': 0.27095, 'kda': 2.681386, 'tier': 2, 'rank': 3, 'position': 'ADC', 'counters': [{'championId': 15, 'icon': 'app/resource/game/champion icons/15.png'}, {'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 29, 'icon': 'app/resource/game/champion icons/29.png'}]}, {'championId': 21, 'name': '赏金猎人', 'icon': 'app/resource/game/champion icons/21.png', 'winRate': 0.507612, 'pickRate': 0.111888, 'banRate': 0.0603609, 'kda': 2.553821, 'tier': 2, 'rank': 4, 'position': 'ADC', 'counters': [{'championId': 115, 'icon': 'app/resource/game/champion icons/115.png'}, {'championId': 119, 'icon': 'app/resource/game/champion icons/119.png'}, {'championId': 22, 'icon': 'app/resource/game/champion icons/22.png'}]}, {'championId': 96, 'name': '深渊巨口', 'icon': 'app/resource/game/champion icons/96.png', 'winRate': 0.524784, 'pickRate': 0.0165673, 'banRate': 0.00308373, 'kda': 2.334625, 'tier': 2, 'rank': 5, 'position': 'ADC', 'counters': [{'championId': 115, 'icon': 'app/resource/game/champion icons/115.png'}, {'championId': 21, 'icon': 'app/resource/game/champion icons/21.png'}, {'championId': 81, 'icon': 'app/resource/game/champion icons/81.png'}]}, {'championId': 222, 'name': '暴走萝莉', 'icon': 'app/resource/game/champion icons/222.png', 'winRate': 0.507693, 'pickRate': 0.0830959, 'banRate': 0.0249029, 'kda': 2.675101, 'tier': 2, 'rank': 6, 'position': 'ADC', 'counters': [{'championId': 115, 'icon': 'app/resource/game/champion icons/115.png'}, {'championId': 42, 'icon': 'app/resource/game/champion icons/42.png'}, {'championId': 29, 'icon': 'app/resource/game/champion icons/29.png'}]}, {'championId': 221, 'name': '祖安花火', 'icon': 'app/resource/game/champion icons/221.png', 'winRate': 0.495851, 'pickRate': 0.189893, 'banRate': 0.0862426, 'kda': 2.573191, 'tier': 2, 'rank': 7, 'position': 'ADC', 'counters': [{'championId': 895, 'icon': 'app/resource/game/champion icons/895.png'}, {'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}]}, {'championId': 202, 'name': '戏命师', 'icon': 'app/resource/game/champion icons/202.png', 'winRate': 0.500374, 'pickRate': 0.127509, 'banRate': 0.010266, 'kda': 3.130994, 'tier': 2, 'rank': 8, 'position': 'ADC', 'counters': [{'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 15, 'icon': 'app/resource/game/champion icons/15.png'}, {'championId': 29, 'icon': 'app/resource/game/champion icons/29.png'}]}, {'championId': 18, 'name': '麦林炮手', 'icon': 'app/resource/game/champion icons/18.png', 'winRate': 0.515868, 'pickRate': 0.01603, 'banRate': 0.0313651, 'kda': 2.635611, 'tier': 2, 'rank': 9, 'position': 'ADC', 'counters': [{'championId': 15, 'icon': 'app/resource/game/champion icons/15.png'}, {'championId': 119, 'icon': 'app/resource/game/champion icons/119.png'}, {'championId': 115, 'icon': 'app/resource/game/champion icons/115.png'}]}, {'championId': 498, 'name': '逆羽', 'icon': 'app/resource/game/champion icons/498.png', 'winRate': 0.500938, 'pickRate': 0.0599187, 'banRate': 0.00664675, 'kda': 2.637435, 'tier': 3, 'rank': 10, 'position': 'ADC', 'counters': [{'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 222, 'icon': 'app/resource/game/champion icons/222.png'}, {'championId': 22, 'icon': 'app/resource/game/champion icons/22.png'}]}, {'championId': 236, 'name': '圣枪游侠', 'icon': 'app/resource/game/champion icons/236.png', 'winRate': 0.495484, 'pickRate': 0.0826938, 'banRate': 0.0323981, 'kda': 2.522069, 'tier': 3, 'rank': 11, 'position': 'ADC', 'counters': [{'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 22, 'icon': 'app/resource/game/champion icons/22.png'}, {'championId': 895, 'icon': 'app/resource/game/champion icons/895.png'}]}, {'championId': 119, 'name': '荣耀行刑官', 'icon': 'app/resource/game/champion icons/119.png', 'winRate': 0.503839, 'pickRate': 0.0352344, 'banRate': 0.112423, 'kda': 2.354947, 'tier': 3, 'rank': 12, 'position': 'ADC', 'counters': [{'championId': 360, 'icon': 'app/resource/game/champion icons/360.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 67, 'icon': 'app/resource/game/champion icons/67.png'}]}, {'championId': 895,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           'name': '不羁之悦', 'icon': 'app/resource/game/champion icons/895.png', 'winRate': 0.518439, 'pickRate': 0.0079569, 'banRate': 0.00700253, 'kda': 2.376208, 'tier': 3, 'rank': 13, 'position': 'ADC', 'counters': [{'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 222, 'icon': 'app/resource/game/champion icons/222.png'}, {'championId': 110, 'icon': 'app/resource/game/champion icons/110.png'}]}, {'championId': 15, 'name': '战争女神', 'icon': 'app/resource/game/champion icons/15.png', 'winRate': 0.50252, 'pickRate': 0.0272242, 'banRate': 0.00549556, 'kda': 2.642289, 'tier': 3, 'rank': 14, 'position': 'ADC', 'counters': [{'championId': 29, 'icon': 'app/resource/game/champion icons/29.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 895, 'icon': 'app/resource/game/champion icons/895.png'}]}, {'championId': 29, 'name': '瘟疫之源', 'icon': 'app/resource/game/champion icons/29.png', 'winRate': 0.508942, 'pickRate': 0.0129986, 'banRate': 0.00380224, 'kda': 2.529564, 'tier': 3, 'rank': 15, 'position': 'ADC', 'counters': [{'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 429, 'icon': 'app/resource/game/champion icons/429.png'}, {'championId': 119, 'icon': 'app/resource/game/champion icons/119.png'}]}, {'championId': 901, 'name': '炽炎雏龙', 'icon': 'app/resource/game/champion icons/901.png', 'winRate': 0.493104, 'pickRate': 0.0303947, 'banRate': 0.00357548, 'kda': 2.553529, 'tier': 4, 'rank': 16, 'position': 'ADC', 'counters': [{'championId': 119, 'icon': 'app/resource/game/champion icons/119.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 202, 'icon': 'app/resource/game/champion icons/202.png'}]}, {'championId': 115, 'name': '爆破鬼才', 'icon': 'app/resource/game/champion icons/115.png', 'winRate': 0.504783, 'pickRate': 0.00936117, 'banRate': 0.000940471, 'kda': 2.541237, 'tier': 4, 'rank': 17, 'position': 'ADC', 'counters': [{'championId': 221, 'icon': 'app/resource/game/champion icons/221.png'}, {'championId': 360, 'icon': 'app/resource/game/champion icons/360.png'}, {'championId': 901, 'icon': 'app/resource/game/champion icons/901.png'}]}, {'championId': 51, 'name': '皮城女警', 'icon': 'app/resource/game/champion icons/51.png', 'winRate': 0.482405, 'pickRate': 0.0702821, 'banRate': 0.0329083, 'kda': 2.345821, 'tier': 4, 'rank': 18, 'position': 'ADC', 'counters': [{'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 119, 'icon': 'app/resource/game/champion icons/119.png'}, {'championId': 29, 'icon': 'app/resource/game/champion icons/29.png'}]}, {'championId': 360, 'name': '沙漠玫瑰', 'icon': 'app/resource/game/champion icons/360.png', 'winRate': 0.486994, 'pickRate': 0.0425568, 'banRate': 0.0676244, 'kda': 2.323828, 'tier': 4, 'rank': 19, 'position': 'ADC', 'counters': [{'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 895, 'icon': 'app/resource/game/champion icons/895.png'}]}, {'championId': 67, 'name': '暗夜猎手', 'icon': 'app/resource/game/champion icons/67.png', 'winRate': 0.488737, 'pickRate': 0.0200466, 'banRate': 0.0296018, 'kda': 2.207755, 'tier': 4, 'rank': 20, 'position': 'ADC', 'counters': [{'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 498, 'icon': 'app/resource/game/champion icons/498.png'}, {'championId': 51, 'icon': 'app/resource/game/champion icons/51.png'}]}, {'championId': 429, 'name': '复仇之矛', 'icon': 'app/resource/game/champion icons/429.png', 'winRate': 0.484617, 'pickRate': 0.0162263, 'banRate': 0.00823172, 'kda': 2.279167, 'tier': 5, 'rank': 21, 'position': 'ADC', 'counters': [{'championId': 21, 'icon': 'app/resource/game/champion icons/21.png'}, {'championId': 67, 'icon': 'app/resource/game/champion icons/67.png'}, {'championId': 145, 'icon': 'app/resource/game/champion icons/145.png'}]}, {'championId': 110, 'name': '惩戒之箭', 'icon': 'app/resource/game/champion icons/110.png', 'winRate': 0.466964, 'pickRate': 0.0299336, 'banRate': 0.00595512, 'kda': 2.325087, 'tier': 5, 'rank': 22, 'position': 'ADC', 'counters': [{'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 67, 'icon': 'app/resource/game/champion icons/67.png'}, {'championId': 222, 'icon': 'app/resource/game/champion icons/222.png'}]}, {'championId': 42, 'name': '英勇投弹手', 'icon': 'app/resource/game/champion icons/42.png', 'winRate': 0.479015, 'pickRate': 0.00812648, 'banRate': 0.00235333, 'kda': 2.563865, 'tier': 5, 'rank': 23, 'position': 'ADC', 'counters': [{'championId': 15, 'icon': 'app/resource/game/champion icons/15.png'}, {'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 119, 'icon': 'app/resource/game/champion icons/119.png'}]}, {'championId': 523, 'name': '残月之肃', 'icon': 'app/resource/game/champion icons/523.png', 'winRate': 0.4554, 'pickRate': 0.0372961, 'banRate': 0.00288858, 'kda': 2.040353, 'tier': 5, 'rank': 24, 'position': 'ADC', 'counters': [{'championId': 18, 'icon': 'app/resource/game/champion icons/18.png'}, {'championId': 96, 'icon': 'app/resource/game/champion icons/96.png'}, {'championId': 895, 'icon': 'app/resource/game/champion icons/895.png'}]}]
        self.tierInterface.tierList.updateList(res)

    @asyncClose
    async def closeEvent(self, e):
        # await connector.close()
        # await opgg.close()

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
        pass

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.processRing, alignment=Qt.AlignCenter)
