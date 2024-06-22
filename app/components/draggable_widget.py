from typing import List

from PyQt5.QtCore import (QPoint, Qt, QRect, QPropertyAnimation, QEasingCurve)
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (QVBoxLayout, QFrame)


from app.components.animation_frame import CardWidget
from app.common.style_sheet import StyleSheet


class DraggableItem(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.slideAni = QPropertyAnimation(self, b'pos', self)

    def sizeHint(self):
        raise NotImplementedError()

    def slideTo(self, y: int, duration=250):
        self.slideAni.setStartValue(self.pos())
        self.slideAni.setEndValue(QPoint(self.x(), y))
        self.slideAni.setDuration(duration)
        self.slideAni.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.slideAni.start()


class ItemsDraggableWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.items: List[DraggableItem] = []

        self.dragPos = QPoint()
        self.isDragging = False
        self.currentIndex = -1

        self.vBoxLayout = QVBoxLayout(self)

        self.__initLayout()
        StyleSheet.DRAGGABLE_WIDGET.apply(self)

    def __initLayout(self):
        self.vBoxLayout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.vBoxLayout.setContentsMargins(11, 11, 11, 11)
        self.vBoxLayout.setSpacing(6)

    def _addItem(self, item: DraggableItem):
        item.pressed.connect(self.__onItemPressed)

        self.items.append(item)
        self.vBoxLayout.addWidget(item)

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

    def _removeItem(self, item: DraggableItem):
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

        self.repaint()

    def __onItemPressed(self):
        item: DraggableItem = self.sender()
        item.raise_()

        index = self.items.index(item)
        self.setCurrentIndex(index)

    def setCurrentIndex(self, index: int):
        self.currentIndex = index

    def getCurrentIndex(self):
        return self.currentIndex

    def count(self):
        return len(self.items)

    def tabItem(self, index: int) -> DraggableItem:
        return self.items[index]

    def tabRect(self, index: int) -> QRect:
        y = 0

        for i in range(index):
            y += self.tabItem(i).height()
            y += self.vBoxLayout.spacing()

        rect = self.tabItem(index).geometry()
        rect.moveTop(y + self.vBoxLayout.contentsMargins().top() + 1)

        return rect
