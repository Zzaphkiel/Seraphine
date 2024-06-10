import sys

from PyQt5.QtCore import (
    Qt, QRectF, QPoint, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve)
from PyQt5.QtGui import QHideEvent, QPainter, QPainterPath, QPen, QFont, QPixmap, QColor
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow, QHBoxLayout,
                             QLabel, QVBoxLayout, QGridLayout, QFrame, QGraphicsDropShadowEffect)

from app.lol.aram import AramHome
from app.common.qfluentwidgets import (ProgressRing, ToolTipFilter, ToolTipPosition, isDarkTheme,
                                       themeColor, FlyoutViewBase, TextWrap)
from app.components.color_label import ColorLabel
from app.common.style_sheet import StyleSheet


class ProgressArc(ProgressRing):
    def __init__(self, parent=None, useAni=True, text="", fontSize=10):
        self.text = text
        self.fontSize = fontSize
        self.drawVal = 0
        super().__init__(parent, useAni=useAni)

    def paintEvent(self, e):
        # 有值取值, 没值保持; self.val 在控件刚实例化时, 前几次update可能会为0
        self.drawVal = self.val or self.drawVal
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
                 aramInfo=None,
                 parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.sep = .3 * diameter
        self.iconPath = icon

        self.image = QPixmap(self.iconPath)

        self.setFixedSize(self.diameter, self.diameter)

        self.xpSinceLastLevel = xpSinceLastLevel
        self.xpUntilNextLevel = xpUntilNextLevel
        self.progressRing = ProgressArc(
            self, text=text, fontSize=int(.1 * diameter))
        self.progressRing.setTextVisible(False)
        self.progressRing.setFixedSize(self.diameter, self.diameter)

        # self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")
        self.installEventFilter(ToolTipFilter(self, 250, ToolTipPosition.TOP))
        self.paintXpSinceLastLevel = None
        self.paintXpUntilNextLevel = None
        self.callUpdate = False

        self.mFlyout = None
        self.aramInfo = aramInfo

        # Note 如果你希望测试大乱斗的数据弹框, 参考这个 -- By Hpero4
        # self.aramInfo = AramHome.getInfoByChampionId("75")

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
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)

        if 'champion' in self.iconPath:
            scaledImage = scaledImage.scaled(self.width() - int(self.sep) + 8,
                                             self.height() - int(self.sep) + 8,
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            scaledImage.scroll(-4, -4, scaledImage.rect())

        clipPath = QPainterPath()
        clipPath.addEllipse(self.sep // 2, self.sep // 2,
                            self.width() - self.sep,
                            self.height() - self.sep)

        painter.setClipPath(clipPath)
        painter.drawPixmap(int(self.sep // 2), int(self.sep // 2), scaledImage)

    def updateIcon(self, icon: str, xpSinceLastLevel=None, xpUntilNextLevel=None, text=""):
        self.iconPath = icon
        self.image = QPixmap(self.iconPath)

        if xpSinceLastLevel is not None and xpUntilNextLevel is not None:
            self.xpSinceLastLevel = xpSinceLastLevel
            self.xpUntilNextLevel = xpUntilNextLevel

            # self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")

        if text:
            self.progressRing.text = text

        self.callUpdate = True
        self.repaint()

    def updateAramInfo(self, info):
        self.aramInfo = info
        if self.mFlyout:
            self.mFlyout.updateInfo(info)
            self.mFlyout.hide()
            self.mFlyout.show()

    def enterEvent(self, a0):
        if self.aramInfo:
            if not self.mFlyout:
                self.mFlyout = AramFlyout(
                    info=self.aramInfo,
                    target=self,
                )
                self.mFlyout.show()

        super().enterEvent(a0)

    def leaveEvent(self, a0):
        if self.aramInfo:
            if self.mFlyout:
                self.mFlyout.fadeOut()
                self.mFlyout = None


class AramFlyout(QWidget):
    def __init__(self, info, target: QWidget, parent=None):
        super().__init__(parent)

        self.target = target

        self.hBoxLayout = QHBoxLayout(self)
        self.view = AramFlyoutView(info, target, parent)
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
        self.opacityAni = QPropertyAnimation(
            self, b'windowOpacity', self.parent())
        self.slideAni = QPropertyAnimation(self, b'pos', self.parent())

        self.opacityAni.setDuration(187)
        self.slideAni.setDuration(187)

        self.opacityAni.setEasingCurve(QEasingCurve.InOutQuad)
        self.slideAni.setEasingCurve(QEasingCurve.InOutQuad)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)

        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(self.opacityAni)
        self.aniGroup.addAnimation(self.slideAni)

    def showEvent(self, e):
        pos = self.calcPoints()

        self.slideAni.setStartValue(pos + QPoint(10, 0))
        self.slideAni.setEndValue(pos)

        self.aniGroup.start()

        return super().showEvent(e)

    def fadeOut(self):
        fadeOutAniGroup = QParallelAnimationGroup(self)

        opacityAni = QPropertyAnimation(self, b'windowOpacity', self.parent())
        opacityAni.setStartValue(1)
        opacityAni.setEndValue(0)
        opacityAni.setDuration(120)

        slideAni = QPropertyAnimation(self, b'pos', self.parent())
        slideAni.setStartValue(self.pos())
        slideAni.setEndValue(self.pos() + QPoint(10, 0))
        slideAni.setDuration(120)

        fadeOutAniGroup.addAnimation(opacityAni)
        fadeOutAniGroup.addAnimation(slideAni)

        fadeOutAniGroup.finished.connect(self.close)
        fadeOutAniGroup.start()

    def calcPoints(self):
        pos = self.target.mapToGlobal(QPoint())
        x, y = pos.x(), pos.y()

        hintWidth = self.sizeHint().width()
        hintHeight = self.sizeHint().height()

        x += self.target.width() // 2 - hintWidth // 2
        y += self.target.height() // 2 - hintHeight // 2

        dx = -hintWidth // 2 - 45
        if x + dx < -15:
            dx = -dx

        return QPoint(x + dx, y)

    def updateInfo(self, info):
        self.view.updateInfo()


class AramFlyoutView(FlyoutViewBase):
    def __init__(self, info, target: QWidget, parent=None):
        super().__init__(parent=parent)

        self.info = info
        self.target = target

        self.damageDealt = 0
        self.damageReceived = 0
        self.healingIncrease = 0
        self.shieldIncrease = 0
        self.abilityHaste = 0
        self.tenacity = 0
        self.description = ""
        self.catName = ""

        self.vBoxLayout = QVBoxLayout(self)
        self.gridBox = QGridLayout()

        self.titleLabel = QLabel(parent=self)  # 英雄名字(带称号)
        self.damageDealtLabel = QLabel(
            self.tr('Damage Dealt: '), parent=self)  # 造成伤害的权重
        self.damageReceivedLabel = QLabel(
            self.tr('Damage Received: '), parent=self)  # 受到伤害的权重
        self.healingIncreaseLabel = QLabel(
            self.tr('Healing Increase: '), parent=self)  # 治疗增益的权重
        self.shieldIncreaseLabel = QLabel(
            self.tr('Shield Increase: '), parent=self)  # 护盾增益的权重
        self.abilityHasteLabel = QLabel(
            self.tr('Ability Haste: '), parent=self)  # 技能急速的权重, 是正向属性, 值越大cd越短
        self.tenacityLabel = QLabel(
            self.tr('Tenacity: '), parent=self)  # 韧性的权重

        self.damageDealtValueLabel = ColorLabel(parent=self)  # 造成伤害的权重
        self.damageReceivedValueLabel = ColorLabel(parent=self)  # 受到伤害的权重
        self.healingIncreaseValueLabel = ColorLabel(parent=self)  # 治疗增益的权重
        self.shieldIncreaseValueLabel = ColorLabel(parent=self)  # 护盾增益的权重
        self.abilityHasteValueLabel = ColorLabel(
            parent=self)  # 技能急速的权重, 是正向属性, 值越大cd越短
        self.tenacityValueLabel = ColorLabel(parent=self)  # 韧性的权重

        self.descriptionLabel = QLabel(parent=self)  # 额外调整
        self.powerByLabel = QLabel(self.tr("Powered by: jddld.com"))

        self.updateInfo(info)

        self.__initWidgets()

        StyleSheet.ARAM_FLYOUT.apply(self)

    def __initWidgets(self):
        self.titleLabel.setObjectName("titleLabel")

        self.damageDealtLabel.setObjectName("damageDealtLabel")
        self.damageReceivedLabel.setObjectName("damageReceivedLabel")
        self.healingIncreaseLabel.setObjectName("healingIncreaseLabel")
        self.shieldIncreaseLabel.setObjectName("shieldIncreaseLabel")
        self.abilityHasteLabel.setObjectName("abilityHasteLabel")
        self.tenacityLabel.setObjectName("tenacityLabel")

        self.damageDealtValueLabel.setObjectName("damageDealtValueLabel")
        self.damageReceivedValueLabel.setObjectName("damageReceivedValueLabel")
        self.healingIncreaseValueLabel.setObjectName(
            "healingIncreaseValueLabel")
        self.shieldIncreaseValueLabel.setObjectName("shieldIncreaseValueLabel")
        self.abilityHasteValueLabel.setObjectName("abilityHasteValueLabel")
        self.tenacityValueLabel.setObjectName("tenacityValueLabel")

        self.descriptionLabel.setObjectName("descriptionLabel")
        self.powerByLabel.setObjectName("powerByLabel")

        self.titleLabel.setVisible(True)
        self.damageDealtLabel.setVisible(True)
        self.damageReceivedLabel.setVisible(True)
        self.healingIncreaseLabel.setVisible(True)
        self.shieldIncreaseLabel.setVisible(True)
        self.abilityHasteLabel.setVisible(True)
        self.tenacityLabel.setVisible(True)

        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.powerByLabel.setAlignment(Qt.AlignCenter)
        self.descriptionLabel.setWordWrap(True)

        self.__initLayout()

    def __initLayout(self):

        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.vBoxLayout.setContentsMargins(16, 12, 16, 12)
        self.vBoxLayout.setSpacing(16)
        self.gridBox.setHorizontalSpacing(20)
        self.gridBox.setVerticalSpacing(4)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.gridBox)
        self.vBoxLayout.addWidget(self.descriptionLabel)
        self.vBoxLayout.addWidget(self.powerByLabel)

        self.gridBox.addWidget(self.damageDealtLabel, 0, 0, Qt.AlignLeft)
        self.gridBox.addWidget(self.damageDealtValueLabel, 0, 1, Qt.AlignRight)
        self.gridBox.addWidget(self.damageReceivedLabel, 0, 2, Qt.AlignLeft)
        self.gridBox.addWidget(
            self.damageReceivedValueLabel, 0, 3, Qt.AlignRight)
        self.gridBox.addWidget(self.healingIncreaseLabel, 1, 0, Qt.AlignLeft)
        self.gridBox.addWidget(
            self.healingIncreaseValueLabel, 1, 1, Qt.AlignRight)
        self.gridBox.addWidget(self.shieldIncreaseLabel, 1, 2, Qt.AlignLeft)
        self.gridBox.addWidget(
            self.shieldIncreaseValueLabel, 1, 3, Qt.AlignRight)
        self.gridBox.addWidget(self.abilityHasteLabel, 2, 0, Qt.AlignLeft)
        self.gridBox.addWidget(
            self.abilityHasteValueLabel, 2, 1, Qt.AlignRight)
        self.gridBox.addWidget(self.tenacityLabel, 2, 2, Qt.AlignLeft)
        self.gridBox.addWidget(self.tenacityValueLabel, 2, 3, Qt.AlignRight)

    def __updateStyle(self):
        """
        数据更新时调用一下, 把样式更新
        """
        self.descriptionLabel.setVisible(bool(self.description))

        self.damageDealtValueLabel.setType(
            self.__getColor(self.damageDealt, 100))
        self.damageReceivedValueLabel.setType(
            self.__getColor(self.damageReceived, 100, False))
        self.healingIncreaseValueLabel.setType(
            self.__getColor(self.healingIncrease, 100))
        self.shieldIncreaseValueLabel.setType(
            self.__getColor(self.shieldIncrease, 100))
        self.abilityHasteValueLabel.setType(
            self.__getColor(self.abilityHaste, 0))
        self.tenacityValueLabel.setType(
            self.__getColor(self.tenacity, 0))

    def __getColor(self, val, criterion, isPositive=True) -> str:
        """
        isPositive: 用于标记该属性是否积极(越大越好)
        """
        # 如果值越小越好, 交换一下条件, 让低的标记为绿色
        if not isPositive:
            val, criterion = criterion, val

        if val > criterion:
            return 'win'  # 绿色
        elif val < criterion:
            return 'lose'  # 红色

        return "text"

    def updateInfo(self, info):
        self.catName = info.get("catname", "").replace("-", " - ")
        self.damageDealt = int(info.get("zcsh", "100"))
        self.damageReceived = int(info.get("sdsh", "100"))
        self.healingIncrease = int(info.get("zlxl", "100"))
        self.shieldIncrease = int(info.get("hdxn", "100"))
        self.abilityHaste = int(info.get("jnjs", "0"))
        self.tenacity = int(info.get("renxing", "0"))
        self.description = info.get("description", "")

        if self.description:
            self.description = self.description.replace(
                "(", "（").replace(")", "）")

        self.titleLabel.setText(self.catName)
        self.damageDealtValueLabel.setText(f"{self.damageDealt}%")
        self.damageReceivedValueLabel.setText(f"{self.damageReceived}%")
        self.healingIncreaseValueLabel.setText(f"{self.healingIncrease}%")
        self.shieldIncreaseValueLabel.setText(f"{self.shieldIncrease}%")
        self.abilityHasteValueLabel.setText(f"{self.abilityHaste}")
        self.tenacityValueLabel.setText(f"{self.tenacity}")

        self.__updateStyle()

    def showEvent(self, e):
        super().showEvent(e)
        self.adjustSize()

        if self.description:
            self.descriptionLabel.setText(self.description)


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

    layout.addWidget(icon1)
    window.show()
    sys.exit(app.exec())
