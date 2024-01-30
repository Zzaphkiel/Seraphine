import sys

from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QHBoxLayout
from PyQt5.QtGui import QPainter, QImage, QPainterPath, QPen, QFont
from PyQt5.QtCore import Qt, QRectF

from ..common.qfluentwidgets import ProgressRing, ToolTipFilter, ToolTipPosition, isDarkTheme, themeColor

from app.components.profile_icon_widget import RoundAvatar


class ProgressArc(ProgressRing):
    def __init__(self, parent=None, useAni=True, text="", fontSize=10):
        self.text = text
        self.fontSize = fontSize
        self.drawVal = 0
        super().__init__(parent, useAni=useAni)

    def paintEvent(self, e):
        self.drawVal = self.val or self.drawVal  # 有值取值, 没值保持; self.val 在控件刚实例化时, 前几次update可能会为0
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth  # circle thickness
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # draw background
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, cap=Qt.RoundCap, join=Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, 315 * 16, 270 * 16)

        if self.maximum() <= self.minimum():
            return

        # draw bar
        pen.setColor(themeColor())
        painter.setPen(pen)
        degree = int(self.drawVal / (self.maximum() - self.minimum()) * 270)
        painter.drawArc(rc, -135 * 16, -degree * 16)
        painter.setFont(QFont('Microsoft YaHei', self.fontSize, QFont.Bold))
        text_rect = QRectF(0, self.height() * 0.85,
                           self.width(), self.height() * 0.15)

        painter.drawText(text_rect, Qt.AlignCenter, f"Lv.{self.text}")


class RoundLevelAvatar(QWidget):
    def __init__(self,
                 icon,
                 xpSinceLastLevel,
                 xpUntilNextLevel,
                 diameter=100,
                 text="",
                 parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.sep = .3 * diameter

        self.image = QImage(icon)

        self.setFixedSize(self.diameter, self.diameter)

        self.xpSinceLastLevel = xpSinceLastLevel
        self.xpUntilNextLevel = xpUntilNextLevel
        self.progressRing = ProgressArc(
            self, text=text, fontSize=int(.1*diameter))
        self.progressRing.setTextVisible(False)
        self.progressRing.setFixedSize(self.diameter, self.diameter)

        self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")
        self.installEventFilter(ToolTipFilter(self, 250, ToolTipPosition.TOP))
        self.paintXpSinceLastLevel = None
        self.paintXpUntilNextLevel = None
        self.callUpdate = False


    def paintEvent(self, event):
        if self.paintXpSinceLastLevel != self.xpSinceLastLevel or self.paintXpUntilNextLevel != self.xpUntilNextLevel or self.callUpdate:
            self.progressRing.setVal(self.xpSinceLastLevel * 100 //
                                     self.xpUntilNextLevel if self.xpSinceLastLevel != 0 else 1)
            self.paintXpUntilNextLevel = self.xpUntilNextLevel
            self.paintXpSinceLastLevel = self.xpSinceLastLevel
            self.callUpdate = False

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scaledImage = self.image.scaled(
            self.width() - int(self.sep),
            self.height() - int(self.sep),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding)

        clipPath = QPainterPath()
        clipPath.addEllipse(self.sep // 2, self.sep // 2,
                            self.width() - self.sep,
                            self.height() - self.sep)

        painter.setClipPath(clipPath)
        painter.drawImage(int(self.sep // 2), int(self.sep // 2), scaledImage)

    def updateIcon(self, icon: str, xpSinceLastLevel=None, xpUntilNextLevel=None, text=""):
        self.image = QImage(icon)
        if xpSinceLastLevel is not None and xpUntilNextLevel is not None:
            self.xpSinceLastLevel = xpSinceLastLevel
            self.xpUntilNextLevel = xpUntilNextLevel

            self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")

        if text:
            self.progressRing.text = text

        self.callUpdate = True
        self.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Round Icon Demo")
    window.setGeometry(100, 100, 600, 400)

    widget = QWidget(window)
    window.setCentralWidget(widget)

    layout = QHBoxLayout(widget)

    icon1 = RoundLevelAvatar("../resource/images/logo.png",
                             75,
                             100,
                             diameter=70)
    icon1.setParent(window)

    icon2 = RoundAvatar("../resource/images/logo.png",
                        40,
                        100,
                        diameter=70)
    icon2.setParent(window)

    layout.addWidget(icon1)
    layout.addWidget(icon2)
    window.show()
    sys.exit(app.exec())
