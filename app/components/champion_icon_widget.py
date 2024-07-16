from PyQt5.QtCore import QEvent, Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QLabel


class RoundIcon(QFrame):
    def __init__(self, icon=None, diameter=None, overscaled=None, borderWidth=None, parent=None) -> None:
        super().__init__(parent)

        self.image = QPixmap(icon)
        self.overscaled = overscaled
        self.borderWidth = borderWidth

        self.setFixedSize(diameter, diameter)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        image = self.image.scaled(self.width() + self.overscaled,
                                  self.height() + self.overscaled,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        image.scroll(-self.overscaled // 2, -
                     self.overscaled // 2, image.rect())

        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, image)

        painter.setPen(
            QPen(QColor(120, 90, 40), self.borderWidth, Qt.SolidLine))
        painter.drawEllipse(0, 0, self.width(), self.height())

        return super().paintEvent(event)

    def setIcon(self, icon):
        self.image = QPixmap(icon)
        self.repaint()


class RoundIconButton(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, icon, diameter, overscaled, borderWidth, championName, championId, parent=None) -> None:
        super().__init__(parent)

        self.image = QPixmap(icon)
        self.overscaled = overscaled
        self.borderWidth = borderWidth

        self.championName: str = championName
        self.championId = championId

        self.isPressed = False
        self.isHover = False

        self.setFixedSize(diameter, diameter)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        image = self.image.scaled(self.width() + self.overscaled,
                                  self.height() + self.overscaled,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        image.scroll(-self.overscaled // 2, -
                     self.overscaled // 2, image.rect())

        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)

        if self.isPressed:
            painter.setOpacity(0.63)
        elif self.isHover:
            painter.setOpacity(0.80)
        else:
            painter.setOpacity(1)

        painter.drawPixmap(0, 0, image)

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
        self.clicked.emit(self.championId)
        return super().mouseReleaseEvent(a0)


class RoundedLabel(QLabel):
    def __init__(self, imagePath=None, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap(imagePath))

        self.havePic = imagePath != None
        self.radius = 5.0
        self.borderWidth = 2

    def paintEvent(self, e):
        if not self.havePic:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        pixmap = self.pixmap().scaled(
            self.size()*self.devicePixelRatioF(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)
        painter.setClipPath(path)
        painter.drawPixmap(self.rect(), pixmap)

        painter.setPen(
            QPen(QColor(120, 90, 40), self.borderWidth, Qt.SolidLine))
        painter.drawRoundedRect(QRectF(self.rect()), self.radius, self.radius)

    def setPicture(self, imagePath):
        self.havePic = True

        self.setPixmap(QPixmap(imagePath))
        self.repaint()

    def setRedius(self, radius):
        self.radius = radius
        self.repaint()
