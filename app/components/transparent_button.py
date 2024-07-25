from typing import Union

from PyQt5.QtCore import pyqtSignal, QSize, QRectF
from PyQt5.QtWidgets import QPushButton, QWidget, QApplication
from PyQt5.QtGui import QPainter, QIcon


from app.common.style_sheet import StyleSheet
from app.common.qfluentwidgets import (
    ToolButton, drawIcon, setFont, FluentIconBase)


class TransparentToggleButton(ToolButton):
    changed = pyqtSignal(int)

    def __init__(self, icon1, icon2, parent=None):
        super().__init__(parent=parent)

        self.icons = [icon1, icon2]
        self.currentIcon = 0

        self.setIcon(icon1)

        self.clicked.connect(self.__onButtonClicked)

    def toggle(self):
        new = 1 - self.currentIcon
        self.currentIcon = new
        self.setIcon(self.icons[new])

        return new

    def __onButtonClicked(self):
        new = self.toggle()

        self.changed.emit(new)

    def setCurrentIcon(self, index):
        if self.currentIcon == index:
            return

        self.setIcon(self.icons[index])
        self.currentIcon = index


class TransparentButton(QPushButton):
    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(parent)
        self.isPressed = False
        self.isHover = False
        self.setIconSize(QSize(16, 16))
        self.setIcon(None)
        setFont(self)
        self._postInit()
        self.setText(text)

        StyleSheet.TRANSPARENT_BUTTON.apply(self)

    def _postInit(self):
        pass

    def setIcon(self, icon: Union[QIcon, str, FluentIconBase]):
        self.setProperty('hasIcon', icon is not None)
        self.setStyle(QApplication.style())
        self._icon = icon or QIcon()
        self.update()

    def setProperty(self, name: str, value) -> bool:
        if name != 'icon':
            return super().setProperty(name, value)

        self.setIcon(value)
        return True

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """ draw icon """
        drawIcon(icon, painter, rect, state)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.icon().isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isEnabled():
            painter.setOpacity(0.3628)
        elif self.isPressed:
            painter.setOpacity(0.786)

        w, h = self.iconSize().width(), self.iconSize().height()
        y = (self.height() - h) / 2
        mw = self.minimumSizeHint().width()
        if mw > 0:
            x = 12 + (self.width() - mw) // 2
        else:
            x = 12

        if self.isRightToLeft():
            x = self.width() - w - x

        self._drawIcon(self._icon, painter, QRectF(x, y, w, h))


class PrimaryButton(TransparentButton):
    pass
