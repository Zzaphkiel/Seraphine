from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QImage, QPainterPath
from PyQt5.QtCore import Qt

from ..common.qfluentwidgets import ProgressRing, ToolTipFilter, ToolTipPosition


class RoundAvatar(QWidget):

    def __init__(self,
                 icon,
                 xpSinceLastLevel,
                 xpUntilNextLevel,
                 diameter=100,
                 sep=20,
                 parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.sep = sep

        self.image = QImage(icon)

        self.setFixedSize(self.diameter, self.diameter)

        self.xpSinceLastLevel = xpSinceLastLevel
        self.xpUntilNextLevel = xpUntilNextLevel

        self.progressRing = ProgressRing(self)
        self.progressRing.setTextVisible(False)
        self.progressRing.setFixedSize(self.diameter, self.diameter)

        self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")
        self.installEventFilter(ToolTipFilter(self, 250, ToolTipPosition.TOP))
        raise DeprecationWarning(
            "The Widget is deprecated due to abnormal recursion causing high CPU usage. Please use the "
            "RoundLevelAvatar class instead."
        )

    def paintEvent(self, event):
        # FIXME
        #  setVal 会触发当前控件重绘, 导致无限递归paintEvent
        self.progressRing.setVal(self.xpSinceLastLevel * 100 //
                                 self.xpUntilNextLevel if self.xpUntilNextLevel != 0 else 1)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scaledImage = self.image.scaled(
            self.width() - self.sep,
            self.height() - self.sep,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding)

        clipPath = QPainterPath()
        clipPath.addEllipse(self.sep // 2, self.sep // 2,
                            self.width() - self.sep,
                            self.height() - self.sep)

        painter.setClipPath(clipPath)
        painter.drawImage(self.sep // 2, self.sep // 2, scaledImage)

    def updateIcon(self, icon, xpSinceLastLevel, xpUntilNextLevel):
        self.image = QImage(icon)
        self.xpSinceLastLevel = xpSinceLastLevel
        self.xpUntilNextLevel = xpUntilNextLevel

        self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")
        self.repaint()
