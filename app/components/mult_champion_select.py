from PyQt5.QtCore import QPoint, Qt, pyqtSignal, QSize, QRectF, QRect, pyqtProperty
from PyQt5.QtGui import QIcon, QCloseEvent, QColor, QPainter, QMouseEvent
from PyQt5.QtWidgets import (QVBoxLayout, QFrame, QWidget, QHBoxLayout, QLabel,
                             QStackedWidget)

from copy import deepcopy
from typing import Dict, List, Union

from app.common.qfluentwidgets import (
    SingleDirectionScrollArea, TransparentToolButton, isDarkTheme, TabCloseButtonDisplayMode,
    FluentIcon, FluentStyleSheet, FluentIconBase, TabItem, qrouter, SmoothMode, SmoothScrollArea)


def checkIndex(*default):
    """ decorator for index checking

    Parameters
    ----------
    *default:
        the default value returned when an index overflow
    """

    def outer(func):

        def inner(tabBar, index: int, *args, **kwargs):
            if 0 <= index < len(tabBar.items):
                return func(tabBar, index, *args, **kwargs)

            value = deepcopy(default)
            if len(value) == 0:
                return None
            elif len(value) == 1:
                return value[0]

            return value

        return inner

    return outer


class TabToolButton(TransparentToolButton):
    """ Tab tool button """

    def _postInit(self):
        self.setFixedSize(32, 24)
        self.setIconSize(QSize(12, 12))

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        color = '#eaeaea' if isDarkTheme() else '#484848'
        icon = icon.icon(color=color)
        super()._drawIcon(icon, painter, rect, state)


class TabBar(SingleDirectionScrollArea):
    """ Tab bar """

    currentChanged = pyqtSignal(int)
    tabBarClicked = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)
    tabAddRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent, orient=Qt.Orientation.Vertical)

        self.items = []
        self.itemMap = {}

        self._currentIndex = -1

        self._isMovable = False
        self._isScrollable = False
        self._isTabShadowEnabled = True

        self._tabMaxWidth = 240
        self._tabMinWidth = 64

        self.dragPos = QPoint()
        self.isDraging = False

        self.lightSelectedBackgroundColor = QColor(249, 249, 249)
        self.darkSelectedBackgroundColor = QColor(40, 40, 40)
        self.closeButtonDisplayMode = TabCloseButtonDisplayMode.ALWAYS

        self.view = QWidget(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.itemLayout = QHBoxLayout()
        self.widgetLayout = QHBoxLayout()

        self.addButton = TabToolButton(FluentIcon.ADD, self)

        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(46)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMaximumSize)

        self.addButton.clicked.connect(self.tabAddRequested)

        self.view.setObjectName('view')
        FluentStyleSheet.TAB_VIEW.apply(self)
        FluentStyleSheet.TAB_VIEW.apply(self.view)

        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.itemLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.widgetLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.itemLayout.setContentsMargins(5, 5, 5, 5)
        self.widgetLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.itemLayout.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)

        self.hBoxLayout.setSpacing(0)
        self.itemLayout.setSpacing(0)

        self.hBoxLayout.addLayout(self.itemLayout)
        self.hBoxLayout.addSpacing(3)

        self.widgetLayout.addWidget(self.addButton, 0, Qt.AlignLeft)
        self.hBoxLayout.addLayout(self.widgetLayout)
        self.hBoxLayout.addStretch(1)

    def setAddButtonVisible(self, isVisible: bool):
        self.addButton.setVisible(isVisible)

    def addTab(self, routeKey: str, text: str, icon: Union[QIcon, str, FluentIconBase] = None, onClick=None):
        """ add tab

        Parameters
        ----------
        routeKey: str
            the unique name of tab item

        text: str
            the text of tab item

        text: str
            the icon of tab item

        onClick: callable
            the slot connected to item clicked signal
        """
        return self.insertTab(-1, routeKey, text, icon, onClick)

    def insertTab(self, index: int, routeKey: str, text: str, icon: Union[QIcon, str, FluentIconBase] = None,
                  onClick=None):
        """ insert tab

        Parameters
        ----------
        index: int
            the insert position of tab item

        routeKey: str
            the unique name of tab item

        text: str
            the text of tab item

        text: str
            the icon of tab item

        onClick: callable
            the slot connected to item clicked signal
        """
        if routeKey in self.itemMap:
            raise ValueError(f"The route key `{routeKey}` is duplicated.")

        if index == -1:
            index = len(self.items)

        # adjust current index
        if index <= self.currentIndex() and self.currentIndex() >= 0:
            self._currentIndex += 1

        item = TabItem(text, self.view, icon)
        item.setRouteKey(routeKey)

        # set the size of tab
        w = self.tabMaximumWidth() if self.isScrollable() else self.tabMinimumWidth()
        item.setMinimumWidth(w)
        item.setMaximumWidth(self.tabMaximumWidth())

        item.setShadowEnabled(self.isTabShadowEnabled())
        item.setCloseButtonDisplayMode(self.closeButtonDisplayMode)
        item.setSelectedBackgroundColor(
            self.lightSelectedBackgroundColor, self.darkSelectedBackgroundColor)

        item.pressed.connect(self._onItemPressed)
        item.closed.connect(
            lambda: self.tabCloseRequested.emit(self.items.index(item)))
        if onClick:
            item.pressed.connect(onClick)

        self.itemLayout.insertWidget(index, item, 1)
        self.items.insert(index, item)
        self.itemMap[routeKey] = item

        if len(self.items) == 1:
            self.setCurrentIndex(0)

        return item

    def removeTab(self, index: int):
        if not 0 <= index < len(self.items):
            return

        # adjust current index
        if index < self.currentIndex():
            self._currentIndex -= 1
        elif index == self.currentIndex():
            if self.currentIndex() > 0:
                self.setCurrentIndex(self.currentIndex() - 1)
                self.currentChanged.emit(self.currentIndex())
            elif len(self.items) == 1:
                self._currentIndex = -1
            else:
                self.setCurrentIndex(1)
                self._currentIndex = 0
                self.currentChanged.emit(0)

        # remove tab
        item = self.items.pop(index)
        self.itemMap.pop(item.routeKey())
        self.hBoxLayout.removeWidget(item)
        qrouter.remove(item.routeKey())
        item.deleteLater()

        # remove shadow
        self.update()

    def removeTabByKey(self, routeKey: str):
        if routeKey not in self.itemMap:
            return

        self.removeTab(self.items.index(self.tab(routeKey)))

    def setCurrentIndex(self, index: int):
        """ set current index """
        if index == self._currentIndex:
            return

        if self.currentIndex() >= 0:
            self.items[self.currentIndex()].setSelected(False)

        self._currentIndex = index
        self.items[index].setSelected(True)

    def setCurrentTab(self, routeKey: str):
        if routeKey not in self.itemMap:
            return

        self.setCurrentIndex(self.items.index(self.tab(routeKey)))

    def currentIndex(self):
        return self._currentIndex

    def currentTab(self):
        return self.tabItem(self.currentIndex())

    def _onItemPressed(self):
        for item in self.items:
            item.setSelected(item is self.sender())

        index = self.items.index(self.sender())
        self.tabBarClicked.emit(index)

        if index != self.currentIndex():
            self.setCurrentIndex(index)
            self.currentChanged.emit(index)

    def setCloseButtonDisplayMode(self, mode: TabCloseButtonDisplayMode):
        """ set close button display mode """
        if mode == self.closeButtonDisplayMode:
            return

        self.closeButtonDisplayMode = mode
        for item in self.items:
            item.setCloseButtonDisplayMode(mode)

    @checkIndex()
    def tabItem(self, index: int):
        return self.items[index]

    def tab(self, routeKey: str):
        return self.itemMap.get(routeKey, None)

    def tabRegion(self) -> QRect:
        """ return the bounding rect of all tabs """
        return self.itemLayout.geometry()

    @checkIndex()
    def tabRect(self, index: int):
        """ return the visual rectangle of the tab at position index """
        x = 0
        for i in range(index):
            x += self.tabItem(i).width()

        rect = self.tabItem(index).geometry()
        rect.moveLeft(x)
        return rect

    @checkIndex('')
    def tabText(self, index: int):
        return self.tabItem(index).text()

    @checkIndex()
    def tabIcon(self, index: int):
        return self.tabItem(index).icon()

    @checkIndex('')
    def tabToolTip(self, index: int):
        return self.tabItem(index).toolTip()

    def setTabsClosable(self, isClosable: bool):
        """ set whether the tab is closable """
        if isClosable:
            self.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ALWAYS)
        else:
            self.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.NEVER)

    def tabsClosable(self):
        return self.closeButtonDisplayMode != TabCloseButtonDisplayMode.NEVER

    @checkIndex()
    def setTabIcon(self, index: int, icon: Union[QIcon, FluentIconBase, str]):
        """ set tab icon """
        self.tabItem(index).setIcon(icon)

    @checkIndex()
    def setTabText(self, index: int, text: str):
        """ set tab text """
        self.tabItem(index).setText(text)

    @checkIndex()
    def setTabVisible(self, index: int, isVisible: bool):
        """ set the visibility of tab """
        self.tabItem(index).setVisible(isVisible)

        if isVisible and self.currentIndex() < 0:
            self.setCurrentIndex(0)
        elif not isVisible:
            if self.currentIndex() > 0:
                self.setCurrentIndex(self.currentIndex() - 1)
                self.currentChanged.emit(self.currentIndex())
            elif len(self.items) == 1:
                self._currentIndex = -1
            else:
                self.setCurrentIndex(1)
                self._currentIndex = 0
                self.currentChanged.emit(0)

    @checkIndex()
    def setTabTextColor(self, index: int, color: QColor):
        """ set the text color of tab item """
        self.tabItem(index).setTextColor(color)

    @checkIndex()
    def setTabToolTip(self, index: int, toolTip: str):
        """ set tool tip of tab """
        self.tabItem(index).setToolTip(toolTip)

    def setTabSelectedBackgroundColor(self, light: QColor, dark: QColor):
        """ set the background in selected state """
        self.lightSelectedBackgroundColor = QColor(light)
        self.darkSelectedBackgroundColor = QColor(dark)

        for item in self.items:
            item.setSelectedBackgroundColor(light, dark)

    def setTabShadowEnabled(self, isEnabled: bool):
        """ set whether the shadow of tab is enabled """
        if isEnabled == self.isTabShadowEnabled():
            return

        self._isTabShadowEnabled = isEnabled
        for item in self.items:
            item.setShadowEnabled(isEnabled)

    def isTabShadowEnabled(self):
        return self._isTabShadowEnabled

    def paintEvent(self, e):
        painter = QPainter(self.viewport())
        painter.setRenderHints(QPainter.Antialiasing)

        # draw separators
        if isDarkTheme():
            color = QColor(255, 255, 255, 21)
        else:
            color = QColor(0, 0, 0, 15)

        painter.setPen(color)

        for i, item in enumerate(self.items):
            canDraw = not (item.isHover or item.isSelected)
            if i < len(self.items) - 1:
                nextItem = self.items[i + 1]
                if nextItem.isHover or nextItem.isSelected:
                    canDraw = False

            if canDraw:
                x = item.geometry().right()
                y = self.height() // 2 - 8
                painter.drawLine(x, y, x, y + 16)

    def setMovable(self, movable: bool):
        self._isMovable = movable

    def isMovable(self):
        return self._isMovable

    def setScrollable(self, scrollable: bool):
        self._isScrollable = scrollable
        w = self._tabMaxWidth if scrollable else self._tabMinWidth
        for item in self.items:
            item.setMinimumWidth(w)

    def setTabMaximumWidth(self, width: int):
        """ set the maximum width of tab """
        if width == self._tabMaxWidth:
            return

        self._tabMaxWidth = width
        for item in self.items:
            item.setMaximumWidth(width)

    def setTabMinimumWidth(self, width: int):
        """ set the minimum width of tab """
        if width == self._tabMinWidth:
            return

        self._tabMinWidth = width

        if not self.isScrollable():
            for item in self.items:
                item.setMinimumWidth(width)

    def tabMaximumWidth(self):
        return self._tabMaxWidth

    def tabMinimumWidth(self):
        return self._tabMinWidth

    def isScrollable(self):
        return self._isScrollable

    def count(self):
        """ returns the number of tabs """
        return len(self.items)

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        if not self.isMovable() or e.button() != Qt.LeftButton or \
                not self.itemLayout.geometry().contains(e.pos()):
            return

        self.dragPos = e.pos()

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)

        if not self.isMovable() or self.count() <= 1 or not self.itemLayout.geometry().contains(e.pos()):
            return

        index = self.currentIndex()
        item = self.tabItem(index)
        dx = e.pos().x() - self.dragPos.x()
        self.dragPos = e.pos()

        # first tab can't move left
        if index == 0 and dx < 0 and item.x() <= 0:
            return

        # last tab can't move right
        if index == self.count() - 1 and dx > 0 and item.geometry().right() >= self.itemLayout.sizeHint().width():
            return

        item.move(item.x() + dx, item.y())
        self.isDraging = True

        # move the left sibling item to right
        if dx < 0 and index > 0:
            siblingIndex = index - 1

            if item.x() < self.tabItem(siblingIndex).geometry().center().x():
                self._swapItem(siblingIndex)

        # move the right sibling item to left
        elif dx > 0 and index < self.count() - 1:
            siblingIndex = index + 1

            if item.geometry().right() > self.tabItem(siblingIndex).geometry().center().x():
                self._swapItem(siblingIndex)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)

        if not self.isMovable() or not self.isDraging:
            return

        self.isDraging = False

        item = self.tabItem(self.currentIndex())
        x = self.tabRect(self.currentIndex()).x()
        duration = int(abs(item.x() - x) * 250 / item.width())
        item.slideTo(x, duration)
        item.slideAni.finished.connect(self._adjustLayout)

    def _adjustLayout(self):
        self.sender().disconnect()

        for item in self.items:
            self.itemLayout.removeWidget(item)

        for item in self.items:
            self.itemLayout.addWidget(item)

    def _swapItem(self, index: int):
        items = self.items
        swappedItem = self.tabItem(index)
        x = self.tabRect(self.currentIndex()).x()

        items[self.currentIndex()], items[index] = items[index], items[self.currentIndex()]
        self._currentIndex = index
        swappedItem.slideTo(x)

    movable = pyqtProperty(bool, isMovable, setMovable)
    scrollable = pyqtProperty(bool, isScrollable, setScrollable)
    tabMaxWidth = pyqtProperty(int, tabMaximumWidth, setTabMaximumWidth)
    tabMinWidth = pyqtProperty(int, tabMinimumWidth, setTabMinimumWidth)
    tabShadowEnabled = pyqtProperty(
        bool, isTabShadowEnabled, setTabShadowEnabled)
