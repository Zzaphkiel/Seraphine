import sys

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QHBoxLayout
from PyQt5.QtGui import QPixmap, QPen, QPainter, QPainterPath, QColor, QFont

from app.components.champion_icon_widget import RoundIcon


class RoundLevelIcon(QWidget):

    def __init__(self,
                 icon,
                 diameter,
                 overscaled,
                 borderWidth,
                 level,
                 fontSize=10,
                 parent=None) -> None:
        super().__init__(parent)
        self.image = QPixmap(icon)
        self.overscaled = overscaled
        self.borderWidth = borderWidth
        self.level = level
        self.fontSize = fontSize

        self.setFixedSize(diameter, diameter)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        image = self.image.scaled(self.width() + self.overscaled,
                                  self.height() + self.overscaled,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        image.scroll(
            -self.overscaled // 2, -self.overscaled // 2, image.rect()
        )

        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, image)

        painter.setPen(
            QPen(QColor(120, 90, 40), self.borderWidth, Qt.SolidLine))

        painter.drawArc(0, 0, self.width(), self.height(), 320 * 16, 260 * 16)

        painter.setFont(QFont('Arial', self.fontSize))
        text_rect = QRectF(0, self.height() * 0.7, self.width(), self.height() * 0.3)

        painter.drawText(text_rect, Qt.AlignCenter, str(self.level))

        return super().paintEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Round Icon Demo")
    window.setGeometry(100, 100, 600, 400)

    widget = QWidget(window)
    window.setCentralWidget(widget)

    layout = QHBoxLayout(widget)

    icon1 = RoundLevelIcon("../resource/images/unranked.png", 40, 4, 4, 123)
    icon1.setParent(window)

    icon2 = RoundIcon("../resource/images/unranked.png", 40, 4, 4)
    icon2.setParent(window)

    layout.addWidget(icon1)
    layout.addWidget(icon2)
    window.show()
    sys.exit(app.exec())
