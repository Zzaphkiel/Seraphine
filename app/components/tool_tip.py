
from PyQt5.QtCore import (
    Qt, QPoint, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve,
    QSize)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QWidget, QHBoxLayout,
                             QGraphicsDropShadowEffect)

from app.common.qfluentwidgets import (isDarkTheme, TransparentToolButton,
                                       FlyoutAnimationType, FluentIcon)
from app.common.icons import Icon


class CustomToolTip(QWidget):
    def __init__(self, view: QWidget, target: QWidget, parent=None):
        super().__init__(parent)
        self.target = target

        self.hBoxLayout = QHBoxLayout(self)
        self.view = view
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint |
                            Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.hBoxLayout.addWidget(self.view)
        self.hBoxLayout.setContentsMargins(15, 8, 15, 20)

        self.__initShadowEffect()
        self.__initAnimation()

    def __initShadowEffect(self, blurRadius=35, offset=(0, 8)):
        color = QColor(0, 0, 0, 80 if isDarkTheme() else 30)

        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)

        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def __initAnimation(self):
        self.inOpacityAni = QPropertyAnimation(
            self, b'windowOpacity', self.parent())
        self.inSlideAni = QPropertyAnimation(self, b'pos', self.parent())

        self.inOpacityAni.setDuration(187)
        self.inSlideAni.setDuration(187)

        self.inOpacityAni.setEasingCurve(QEasingCurve.InOutQuad)
        self.inSlideAni.setEasingCurve(QEasingCurve.InOutQuad)

        self.inOpacityAni.setStartValue(0)
        self.inOpacityAni.setEndValue(1)

        self.inAniGroup = QParallelAnimationGroup(self)
        self.inAniGroup.addAnimation(self.inOpacityAni)
        self.inAniGroup.addAnimation(self.inSlideAni)

        self.outAniGroup = QParallelAnimationGroup(self)

        self.outOpacityAni = QPropertyAnimation(
            self, b'windowOpacity', self.parent())
        self.outOpacityAni.setEasingCurve(QEasingCurve.InOutQuad)
        self.outOpacityAni.setStartValue(1)
        self.outOpacityAni.setEndValue(0)
        self.outOpacityAni.setDuration(120)

        self.outSlideAni = QPropertyAnimation(self, b'pos', self.parent())
        self.outSlideAni.setEasingCurve(QEasingCurve.InOutQuad)
        self.outSlideAni.setDuration(120)

        self.outAniGroup.addAnimation(self.outOpacityAni)
        self.outAniGroup.addAnimation(self.outSlideAni)

        self.outAniGroup.finished.connect(self.close)

    def showEvent(self, e):
        pos = self.getPosition()

        if self.animationType == FlyoutAnimationType.SLIDE_LEFT:
            self.inSlideAni.setStartValue(pos + QPoint(10, 0))
        else:
            self.inSlideAni.setStartValue(pos - QPoint(10, 0))

        self.inSlideAni.setEndValue(pos)
        self.inAniGroup.start()

        return super().showEvent(e)

    def fadeOut(self):
        self.outSlideAni.setStartValue(self.pos())

        if self.animationType == FlyoutAnimationType.SLIDE_LEFT:
            self.outSlideAni.setEndValue(self.pos() + QPoint(10, 0))
        else:
            self.outSlideAni.setEndValue(self.pos() - QPoint(10, 0))

        self.outAniGroup.finished.connect(self.close)
        self.outAniGroup.start()

    def getPosition(self):
        pos = self.target.mapToGlobal(QPoint())
        x, y = pos.x(), pos.y()

        hintWidth = self.sizeHint().width()
        hintHeight = self.sizeHint().height()

        x += self.target.width() // 2 - hintWidth // 2
        y += self.target.height() // 2 - hintHeight // 2

        dx = -hintWidth // 2 - 45

        self.animationType = FlyoutAnimationType.SLIDE_LEFT

        if x + dx < -15:
            self.animationType = FlyoutAnimationType.SLIDE_RIGHT
            dx = -dx

        return QPoint(x + dx, y)


class HelpButton(TransparentToolButton):
    def __init__(self, view: QWidget, parent: QWidget = None):
        super().__init__(Icon.QUESTION_CIRCLE, parent=parent)

        self.setFixedSize(QSize(26, 26))
        self.setFixedSize(QSize(16, 16))

        self.view = view
        self.mToolTip = None

    def enterEvent(self, e):
        if self.mToolTip:
            return

        self.mToolTip = CustomToolTip(self.view, self)
        self.mToolTip.show()

        return super().enterEvent(e)

    def leaveEvent(self, a0):
        if not self.mToolTip:
            return

        self.mToolTip.fadeOut()
        self.mToolTip = None
