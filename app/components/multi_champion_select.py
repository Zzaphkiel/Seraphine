from qasync import asyncSlot
from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QEasingCurve)
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget)
from PyQt5.QtGui import QFont
from app.common.qfluentwidgets import (TransparentToolButton, FluentIcon, SearchLineEdit,
                                       FlowLayout, SmoothScrollArea, FlyoutViewBase,
                                       PipsScrollButtonDisplayMode, HorizontalPipsPager,
                                       PrimaryPushButton, PushButton)


from app.common.style_sheet import StyleSheet
from app.components.champion_icon_widget import RoundIcon, RoundIconButton
from app.components.draggable_widget import DraggableItem, ItemsDraggableWidget
from app.components.champion_icon_widget import TopRoundedLabel

from app.lol.connector import connector
from app.lol.champions import ChampionAlias


class ChampionTabItem(DraggableItem):
    closeRequested = pyqtSignal()

    def __init__(self, icon, name, championId, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.icon = RoundIcon(icon, 26, 2, 2)
        self.name = QLabel(name)
        self.championId = championId

        self.closeButton = TransparentToolButton(FluentIcon.CLOSE)

        self.__initWidgets()
        self.__initLayout()

    def __initWidgets(self):
        self.setFixedSize(141, 44)
        self.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)

        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setFixedSize(QSize(26, 26))
        self.closeButton.clicked.connect(self.closeRequested)

        self.setMinimumWidth(200)
        self.name.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(10, 8, 4, 8)
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.name)
        self.hBoxLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)

    def sizeHint(self):
        return QSize(141, 44)


class ChampionDraggableWidget(ItemsDraggableWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(318)
        self.setFixedWidth(224)

    def addItem(self, icon, name, championId):
        item = ChampionTabItem(icon, name, championId)
        item.closeRequested.connect(lambda i=item: self._removeItem(i))

        self._addItem(item)

    def getCurrentChampionIds(self):
        return [item.championId for item in self.items]


class ChampionsSelectWidget(QWidget):
    championClicked = pyqtSignal(int)

    def __init__(self, champions: dict, parent: QWidget = None):
        super().__init__(parent=parent)

        self.champions = champions
        self.items: list[RoundIconButton] = []

        self.searchLineEdit = SearchLineEdit()

        self.vBoxLayout = QVBoxLayout(self)
        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QWidget()
        self.championsShowLayout = FlowLayout(needAni=True, isTight=True)

        self.__initWidget()
        self.__initLayout()

        StyleSheet.CHAMPIONS_SELECT_WIDGET.apply(self)

    def __initWidget(self):
        self.scrollArea.setObjectName("scrollArea")
        self.scrollWidget.setObjectName("scrollWidget")

        for i, [name, icon] in self.champions.items():
            button = RoundIconButton(icon, 38, 4, 2, name, i)
            self.items.append(button)
            button.clicked.connect(self.championClicked)

            self.championsShowLayout.addWidget(button)

        self.searchLineEdit.textChanged.connect(self.__onSearchLineTextChanged)

    def __initLayout(self):
        self.championsShowLayout.setHorizontalSpacing(7)
        self.championsShowLayout.setVerticalSpacing(7)
        self.championsShowLayout.setContentsMargins(5, 5, 5, 5)
        self.championsShowLayout.setAnimation(
            450, QEasingCurve.Type.OutQuart)

        self.scrollWidget.setLayout(self.championsShowLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setViewportMargins(1, 1, 5, 1)

        self.scrollArea.setFixedSize(330, 279)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.searchLineEdit)
        self.vBoxLayout.addWidget(self.scrollArea)

    def __onSearchLineTextChanged(self, text: str):
        if text == "":
            self.__showAllChampions()
            return

        if ChampionAlias.isAvailable():
            ids = ChampionAlias.getChampionIdsByAliasFuzzily(text)
            for icon in self.items:
                icon.setVisible(icon.championId in ids)
        else:
            for icon in self.items:
                icon.setVisible(text in icon.championName)

        self.scrollWidget.repaint()

    def __getChampionIdsByAlias(self, alias):
        if ChampionAlias.isAvailable():
            return ChampionAlias.getChampionIdsByAliasFuzzily(alias)
        else:
            return [id for id, [name, _] in self.champions.items()
                    if alias in name]

    def __showAllChampions(self):
        for icon in self.items:
            icon.setVisible(True)


class MultiChampionSelectWidget(QWidget):
    def __init__(self, champions: dict, selected: list, parent=None):
        super().__init__(parent=parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.itemsDraggableWidget = ChampionDraggableWidget()
        self.championsSelectWidget = ChampionsSelectWidget(champions)
        self.champions: dict = champions
        self.selected = selected

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        for id in self.selected:
            name = connector.manager.getChampionNameById(id)
            icon = self.champions[id][1]

            self.itemsDraggableWidget.addItem(icon, name, id)

        self.championsSelectWidget.championClicked.connect(
            self.__onChampionIconClicked)

    def __initLayout(self):
        self.hBoxLayout.addWidget(self.itemsDraggableWidget)
        self.hBoxLayout.addWidget(self.championsSelectWidget)

    def __onChampionIconClicked(self, championId):
        if self.itemsDraggableWidget.count() == 6:
            return

        if championId in self.itemsDraggableWidget.getCurrentChampionIds():
            return

        champion = self.champions[championId]
        self.itemsDraggableWidget.addItem(champion[1], champion[0], championId)

    def getSelectedChampionIds(self) -> list:
        return self.itemsDraggableWidget.getCurrentChampionIds()


class ChampionSelectFlyout(FlyoutViewBase):
    championSelected = pyqtSignal(int)

    def __init__(self, champions: dict, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.selectWidget = ChampionsSelectWidget(champions)
        self.selectWidget.championClicked.connect(self.championSelected)

        self.vBoxLayout.addWidget(self.selectWidget)


class SplashesSelectWidget(QWidget):
    selectedChanged = pyqtSignal(int, str)

    def __init__(self, skinList, skinId, parent=None):
        super().__init__(parent)

        self.skinList = skinList
        self.skinId = skinId

        self.vBoxLayout = QVBoxLayout(self)

        self.viewWidget = QWidget()
        self.viewLayout = QVBoxLayout(self.viewWidget)

        self.buttonsGroup = QWidget()
        self.buttonsLayout = QVBoxLayout()

        self.splashesImg = TopRoundedLabel(radius=8.0, parent=self)
        self.splashesNameLabel = QLabel()
        self.pager = HorizontalPipsPager()

        self.yesButton = PrimaryPushButton(self.tr("OK"))
        self.saveButton = PushButton(self.tr('Save'))
        self.cancelButton = PushButton(self.tr("Cancel"))

        self.__initWidget()
        self.__initLayout()

    def __initLayout(self):
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.addWidget(self.splashesImg, alignment=Qt.AlignCenter)

        self.buttonsLayout.setContentsMargins(14, 14, 14, 22)
        self.buttonsLayout.setSpacing(12)
        self.buttonsLayout.addWidget(
            self.splashesNameLabel, stretch=0, alignment=Qt.AlignCenter)
        self.buttonsLayout.addWidget(
            self.pager, stretch=0, alignment=Qt.AlignCenter)
        self.buttonsGroup.setLayout(self.buttonsLayout)

        self.vBoxLayout.setContentsMargins(1, 0, 1, 0)
        self.vBoxLayout.setSpacing(0)

        self.vBoxLayout.addWidget(self.viewWidget)
        self.vBoxLayout.addWidget(self.buttonsGroup)

    def __initWidget(self):
        self.splashesImg.setFixedSize(384, 216)
        self.splashesNameLabel.setFont(QFont('Microsoft YaHei', 13))
        self.pager.setPreviousButtonDisplayMode(
            PipsScrollButtonDisplayMode.ALWAYS)
        self.pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.pager.setPageNumber(len(self.skinList))
        self.pager.currentIndexChanged.connect(self.__onChangeSplashes)
        self.__initPagerIndex()

        self.buttonsGroup.setObjectName("buttonsGroup")
        self.viewWidget.setObjectName("viewWidget")

    def __initPagerIndex(self):
        if not self.skinId:
            self.pager.setCurrentIndex(0)
            return

        for i, item in enumerate(self.skinList):
            if item[1]['skinId'] == self.skinId:
                self.pager.setCurrentIndex(i)
                return

        self.pager.setCurrentIndex(0)

    @asyncSlot(int)
    async def __onChangeSplashes(self, idx):
        skinItem = self.skinList[idx]
        self.splashesNameLabel.setText(skinItem[0])

        url = await connector.getChampionSplashes(skinItem[1], False)
        self.splashesImg.setPicture(url)

        self.selectedChanged.emit(skinItem[1]['skinId'], skinItem[0])


class SplashesFlyout(FlyoutViewBase):

    def __init__(self, champions: dict, skinId, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.skinWidget = SplashesSelectWidget(champions, skinId)

        self.vBoxLayout.addWidget(self.skinWidget)
