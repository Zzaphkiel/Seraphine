from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPen, QPainter, QPainterPath, QColor


class RoundIcon(QWidget):

    def __init__(self,
                 icon,
                 diameter,
                 overscaled,
                 borderWidth,
                 parent=None) -> None:
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
        image.scroll(-self.overscaled / 2, -self.overscaled / 2, image.rect())

        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, image)

        painter.setPen(
            QPen(QColor(120, 90, 40), self.borderWidth, Qt.SolidLine))
        painter.drawEllipse(0, 0, self.width(), self.height())

        return super().paintEvent(event)