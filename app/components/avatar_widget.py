from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QImage, QBrush, QColor

from qfluentwidgets import NavigationWidget, isDarkTheme


class NavigationAvatarWidget(NavigationWidget):
    """ Avatar widget """

    def __init__(self, avatar: str, name: str, parent=None):
        super().__init__(isSelectable=False, parent=parent)

        self.name = name
        self.avatar = QImage(avatar).scaled(24, 24, Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform
                               | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # draw background
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # draw avatar
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)

            painter.drawText(QRect(44, -1, 255, 36), Qt.AlignVCenter,
                             self.name)
            self.setStyleSheet(
                "NavigationWidget{font: 14px 'Segoe UI', 'Microsoft YaHei'}")
