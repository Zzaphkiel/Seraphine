from typing import List
import sys

from PyQt5.QtCore import (QPoint, Qt, pyqtSignal, QSize,
                          QRect, QPropertyAnimation, QEasingCurve)
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (QVBoxLayout, QFrame, QHBoxLayout,
                             QLabel, QApplication, QWidget, QCompleter)
from app.common.qfluentwidgets import (TransparentToolButton, FluentIcon, ToolButton,
                                       SearchLineEdit, FlowLayout, SmoothScrollArea,
                                       FlyoutViewBase, TeachingTipView)


from app.common.style_sheet import StyleSheet
from app.components.animation_frame import CardWidget
from app.components.champion_icon_widget import RoundIcon, RoundIconButton

from app.lol.connector import connector
from app.lol.champions import ChampionAlias


class ChampionTabItem(CardWidget):
    closed = pyqtSignal()

    def __init__(self, icon, name, championId, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.icon = RoundIcon(icon, 26, 2, 2)
        self.name = QLabel(name)
        self.championId = championId

        self.closeButton = TransparentToolButton(FluentIcon.CLOSE)

        self.slideAni = QPropertyAnimation(self, b'pos', self)

        self.__initWidgets()
        self.__initLayout()

    def __initWidgets(self):
        self.setFixedSize(141, 44)
        self.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)

        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setFixedSize(QSize(26, 26))
        self.closeButton.clicked.connect(self.closed)

        self.setMinimumWidth(200)
        self.name.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(10, 8, 4, 8)
        self.hBoxLayout.addWidget(self.icon)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.name)
        self.hBoxLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)

    def slideTo(self, y: int, duration=250):
        self.slideAni.setStartValue(self.pos())
        self.slideAni.setEndValue(QPoint(self.x(), y))
        self.slideAni.setDuration(duration)
        self.slideAni.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.slideAni.start()

    def sizeHint(self):
        return QSize(141, 44)


class ItemsDraggableWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.items: List[ChampionTabItem] = []

        self.dragPos = QPoint()
        self.isDragging = False
        self.currentIndex = -1

        self.vBoxLayout = QVBoxLayout(self)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.setFixedHeight(318)
        self.setFixedWidth(224)

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.vBoxLayout.setContentsMargins(11, 11, 11, 11)
        self.vBoxLayout.setSpacing(6)

    def addItem(self, icon, name, championId):
        item = ChampionTabItem(icon, name, championId)

        item.pressed.connect(self.__onItemPressed)
        item.closed.connect(lambda i=item: self.removeItem(i))

        self.items.append(item)
        self.vBoxLayout.addWidget(item)

    def getCurrentChampionIds(self):
        return [item.championId for item in self.items]

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)

        if e.button() != Qt.MouseButton.LeftButton or \
                not self.vBoxLayout.geometry().contains(e.pos()):
            return

        self.dragPos = e.pos()

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)

        if not self.vBoxLayout.geometry().contains(e.pos()) or \
                self.count() <= 1:
            return

        index = self.getCurrentIndex()
        if index == -1:
            return

        item = self.tabItem(index)

        dy = e.pos().y() - self.dragPos.y()
        self.dragPos = e.pos()

        if index == 0 and dy < 0 and item.y() <= 0:
            return

        if index == self.count() - 1 and dy > 0 and \
                item.geometry().bottom() >= self.height() - 1:
            return

        item.move(item.x(), item.y() + dy)
        self.isDragging = True

        if dy < 0 and index > 0:
            siblingIndex = index - 1
            siblingItem = self.tabItem(siblingIndex)

            if item.y() < siblingItem.geometry().center().y():
                self.__swapItem(siblingIndex)

        if dy > 0 and index < self.count() - 1:
            siblingIndex = index + 1
            siblingItem = self.tabItem(siblingIndex)

            if item.geometry().bottom() > siblingItem.geometry().center().y():
                self.__swapItem(siblingIndex)

    def mouseReleaseEvent(self, e: QMouseEvent):
        super().mouseReleaseEvent(e)

        if not self.isDragging:
            return

        self.isDragging = False

        item = self.tabItem(self.getCurrentIndex())
        y = self.tabRect(self.getCurrentIndex()).y()

        # duration = int(abs(item.y() - y) * 250 / item.height())
        duration = 250

        item.slideTo(y, duration)
        item.slideAni.finished.connect(self.__adjustLayout)

        self.setCurrentIndex(-1)

    def removeItem(self, item: ChampionTabItem):
        index = self.items.index(item)

        self.items.pop(index)
        self.vBoxLayout.removeWidget(item)

        item.deleteLater()
        self.update()

    def __swapItem(self, index):
        items = self.items
        swappedItem = self.tabItem(index)

        y = self.tabRect(self.getCurrentIndex()).y()

        items[self.getCurrentIndex()], items[index] = \
            items[index], items[self.getCurrentIndex()]
        self.setCurrentIndex(index)
        swappedItem.slideTo(y)

    def __adjustLayout(self):
        self.sender().disconnect()

        for item in self.items:
            self.vBoxLayout.removeWidget(item)

        for item in self.items:
            self.vBoxLayout.addWidget(item)

    def __onItemPressed(self):
        item: ChampionTabItem = self.sender()
        item.raise_()

        index = self.items.index(item)
        self.setCurrentIndex(index)

    def setCurrentIndex(self, index: int):
        self.currentIndex = index

    def getCurrentIndex(self):
        return self.currentIndex

    def count(self):
        return len(self.items)

    def tabItem(self, index: int) -> ChampionTabItem:
        return self.items[index]

    def tabRect(self, index: int) -> QRect:
        y = 0

        for i in range(index):
            y += self.tabItem(i).height()
            y += self.vBoxLayout.spacing()

        rect = self.tabItem(index).geometry()
        rect.moveTop(y + self.vBoxLayout.contentsMargins().top() + 1)

        return rect


class ChampionsSelectWidget(QWidget):
    championClicked = pyqtSignal(int)

    def __init__(self, champions: dict, parent: QWidget = None):
        super().__init__(parent=parent)

        self.champions = champions

        self.searchLineEdit = SearchLineEdit()

        self.vBoxLayout = QVBoxLayout(self)
        self.scrollArea = SmoothScrollArea()
        self.scrollWidget = QWidget()
        self.championsShowLayout = FlowLayout(needAni=False)

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.scrollArea.setObjectName("scrollArea")
        self.scrollWidget.setObjectName("scrollWidget")

        for i, [name, icon] in self.champions.items():
            button = RoundIconButton(icon, 38, 4, 2, name, i)
            button.clicked.connect(self.championClicked)

            self.championsShowLayout.addWidget(button)

        self.searchLineEdit.textChanged.connect(self.__onSearchLineTextChanged)

    def __initLayout(self):
        self.championsShowLayout.setHorizontalSpacing(7)
        self.championsShowLayout.setVerticalSpacing(7)
        self.championsShowLayout.setContentsMargins(5, 5, 5, 5)

        self.scrollWidget.setLayout(self.championsShowLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setViewportMargins(1, 1, 5, 1)

        self.scrollArea.setFixedSize(330, 279)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.searchLineEdit)
        self.vBoxLayout.addWidget(self.scrollArea)

    def __onSearchLineTextChanged(self, text: str):
        for i in reversed(range(self.championsShowLayout.count())):
            widget = self.championsShowLayout.itemAt(i).widget()

            self.championsShowLayout.removeWidget(widget)
            widget.deleteLater()

        champions = self.__getChampionIdsByAlias(text)

        for i in champions:
            champion = self.champions[i]
            name = champion[0]
            icon = champion[1]

            button = RoundIconButton(icon, 38, 4, 2, name, i)
            button.clicked.connect(self.championClicked)

            self.championsShowLayout.addWidget(button)

        self.championsShowLayout.update()

    def __getChampionIdsByAlias(self, alias):
        if ChampionAlias.isAvailable():
            return ChampionAlias.getChampionIdsByAliasFuzzily(alias)
        else:
            return [id for id, [name, _] in self.champions.items()
                    if alias in name]


class MultiChampionSelectWidget(QWidget):
    def __init__(self, champions: dict, selected: list, parent=None):
        super().__init__(parent=parent)

        self.hBoxLayout = QHBoxLayout(self)

        self.itemsDraggableWidget = ItemsDraggableWidget()
        self.championsSelectWidget = ChampionsSelectWidget(champions)
        self.champions: dict = champions
        self.selected = selected

        self.__initWidget()
        self.__initLayout()

        StyleSheet.CHAMPION_SELECT_WIDGET.apply(self)

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

        StyleSheet.CHAMPION_SELECT_WIDGET.apply(self)
