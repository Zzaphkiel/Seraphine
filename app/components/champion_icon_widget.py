from PyQt5.QtCore import QEvent, Qt, pyqtSignal, QRectF, QSize
from PyQt5.QtGui import (QColor, QMouseEvent, QPainter, QPainterPath, QLinearGradient, QGradient,
                         QPen, QPixmap, qGray, qAlpha, qRgba)
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QGraphicsOpacityEffect

from app.common.qfluentwidgets import isDarkTheme

import time


class RoundIcon(QFrame):
    def __init__(self, icon=None, diameter=None, overscaled=0,
                 borderWidth=1, drawBackground=False, enabled=True, parent=None) -> None:
        super().__init__(parent)
        self.image = QPixmap(icon)

        self.overscaled = overscaled
        self.borderWidth = borderWidth
        self.drawBackground = drawBackground
        self.enabled = enabled

        self.havePic = icon != None

        self.setFixedSize(diameter, diameter)

    def paintEvent(self, event) -> None:
        if not self.havePic:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.image.width() - 2*self.overscaled
        height = self.image.height() - 2*self.overscaled

        image = self.image.copy(
            self.overscaled, self.overscaled, width, height)

        size = self.size() * self.devicePixelRatioF()
        image: QPixmap = image.scaled(size,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())

        painter.setClipPath(path)

        if not self.enabled:
            painter.setOpacity(0.15)

        if self.drawBackground:
            painter.save()
            painter.setBrush(QColor(0, 0, 0))
            painter.drawEllipse(0, 0, self.width(), self.height())
            painter.restore()

        painter.drawPixmap(self.rect(), image)

        if self.borderWidth != 0 and self.enabled:
            painter.save()
            painter.setPen(
                QPen(QColor(120, 90, 40), self.borderWidth, Qt.SolidLine))
            painter.drawEllipse(0, 0, self.width(), self.height())
            painter.restore()

        return super().paintEvent(event)

    def setIcon(self, icon):
        self.havePic = True
        self.image = QPixmap(icon)

        self.repaint()

    def setEnabeld(self, enabled):
        self.enabled = enabled

        self.repaint()


class RoundIconButton(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, icon, diameter, overscaled, borderWidth, championName, championId, parent=None) -> None:
        super().__init__(parent)

        self.image = QPixmap(icon)

        self.borderWidth = borderWidth
        self.overscaled = overscaled

        self.championName: str = championName
        self.championId = championId

        self.isPressed = False
        self.isHover = False

        self.setFixedSize(diameter, diameter)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)

        width = self.image.width() - 2*self.overscaled
        height = self.image.height() - 2*self.overscaled

        image = self.image.copy(
            self.overscaled, self.overscaled, width, height)

        size = self.size() * self.devicePixelRatioF()
        image = image.scaled(size,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)

        if self.isPressed:
            painter.setOpacity(0.63)
        elif self.isHover:
            painter.setOpacity(0.80)
        else:
            painter.setOpacity(1)

        painter.drawPixmap(self.rect(), image)

        painter.setPen(
            QPen(QColor(120, 90, 40), self.borderWidth, Qt.SolidLine))
        painter.drawEllipse(0, 0, self.width(), self.height())

        return super().paintEvent(event)

    def enterEvent(self, a0: QEvent) -> None:
        self.isHover = True
        self.update()
        return super().enterEvent(a0)

    def leaveEvent(self, a0: QEvent) -> None:
        self.isHover = False
        self.update()
        return super().leaveEvent(a0)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        self.isPressed = True
        self.update()
        return super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        self.isPressed = False
        self.update()
        ret = super().mouseReleaseEvent(a0)
        self.clicked.emit(self.championId)
        return ret


class TopRoundedLabel(QLabel):
    def __init__(self, imagePath=None, radius=4.0, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap(imagePath))

        self.havePic = imagePath != None
        self.radius = radius

        self.opacity = QGraphicsOpacityEffect(opacity=1)
        self.setGraphicsEffect(self.opacity)

    def paintEvent(self, e):
        if not self.havePic:
            return super().paintEvent(e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        pixmap = self.pixmap().scaled(
            self.size()*self.devicePixelRatioF(),
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        path = QPainterPath()

        topPath = QPainterPath()
        topRect = QRectF(self.rect().x(), self.rect().y(),
                         self.rect().width(), self.rect().height())
        topPath.addRoundedRect(topRect, self.radius, self.radius)

        bottomPath = QPainterPath()
        bottomRect = QRectF(self.rect().x(), self.rect().y() + self.rect().height() / 2,
                            self.rect().width(), self.rect().height() / 2)
        bottomPath.addRect(bottomRect)

        path = topPath.united(bottomPath)
        painter.setClipPath(path)

        grad = QLinearGradient(0, 0, 0, self.rect().height())
        grad.setColorAt(0.65, Qt.GlobalColor.black)
        grad.setColorAt(1, Qt.GlobalColor.transparent)
        self.opacity.setOpacityMask(grad)

        painter.drawPixmap(self.rect(), pixmap)

    def setPicture(self, imagePath):
        self.havePic = True

        self.setPixmap(QPixmap(imagePath))
        self.repaint()

    def setRedius(self, radius):
        self.radius = radius
        self.repaint()

    def setText(self, text):
        self.havePic = False

        return super().setText(text)


class RoundedLabel(QLabel):
    def __init__(self, imagePath=None, radius=4.0, borderWidth=2, borderColor: QColor = None, drawBackground=False, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap(imagePath))

        self.havePic = imagePath != None
        self.radius = radius
        self.borderWidth = borderWidth
        self.borderColor = borderColor if borderColor else QColor(120, 90, 40)
        self.drawBackground = drawBackground

    def paintEvent(self, e):
        if not self.havePic:
            return super().paintEvent(e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        pixmap = self.pixmap().scaled(
            self.size()*self.devicePixelRatioF(),
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)

        painter.setClipPath(path)

        if self.drawBackground:
            painter.save()
            painter.setBrush(QColor(0, 0, 0))
            painter.setOpacity(0.8)
            painter.drawRoundedRect(
                QRectF(self.rect()), self.radius, self.radius)
            painter.restore()

        painter.drawPixmap(self.rect(), pixmap)

        if self.borderWidth != 0:
            painter.setPen(
                QPen(self.borderColor, self.borderWidth, Qt.SolidLine))

            painter.drawRoundedRect(
                QRectF(self.rect()), self.radius, self.radius)

    def setPicture(self, imagePath):
        self.havePic = True

        self.setPixmap(QPixmap(imagePath))
        self.repaint()

    def setRedius(self, radius):
        self.radius = radius
        self.repaint()

    def setText(self, text):
        self.havePic = False

        return super().setText(text)
