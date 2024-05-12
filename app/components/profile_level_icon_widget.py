import sys

from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QFont, QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QHBoxLayout, QLabel, QVBoxLayout, QGridLayout

from ..common.qfluentwidgets import ProgressRing, ToolTipFilter, ToolTipPosition, isDarkTheme, themeColor, \
    FlyoutViewBase, TextWrap


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
                    parent=self.window()
                )
                self.mFlyout.show()
                # TODO Animation -- By Hpero4
                # aM = FlyoutAnimationManager.make(FlyoutAnimationType.SLIDE_LEFT, self.mFlyout)
                # target = aM.position(self)
                # aM.exec(target)
        super().enterEvent(a0)

    def leaveEvent(self, a0):
        if self.aramInfo:
            if self.mFlyout:
                self.mFlyout.close()
                self.mFlyout = None


class AramFlyout(FlyoutViewBase):
    def __init__(self, info, target, parent=None):
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

        self.titleLabel = QLabel(self)  # 英雄名字(带称号)
        self.damageDealtLabel = QLabel(self.tr('Damage Dealt'), self)  # 造成伤害的权重
        self.damageReceivedLabel = QLabel(self.tr('Damage Received'), self)  # 受到伤害的权重
        self.healingIncreaseLabel = QLabel(self.tr('Healing Increase'), self)  # 治疗增益的权重
        self.shieldIncreaseLabel = QLabel(self.tr('Shield Increase'), self)  # 护盾增益的权重
        self.abilityHasteLabel = QLabel(self.tr('Ability Haste'), self)  # 技能急速的权重, 是正向属性, 值越大cd越短
        self.tenacityLabel = QLabel(self.tr('Tenacity'), self)  # 韧性的权重

        self.damageDealtValueLabel = QLabel(self)  # 造成伤害的权重
        self.damageReceivedValueLabel = QLabel(self)  # 受到伤害的权重
        self.healingIncreaseValueLabel = QLabel(self)  # 治疗增益的权重
        self.shieldIncreaseValueLabel = QLabel(self)  # 护盾增益的权重
        self.abilityHasteValueLabel = QLabel(self)  # 技能急速的权重, 是正向属性, 值越大cd越短
        self.tenacityValueLabel = QLabel(self)  # 韧性的权重

        self.descriptionLabel = QLabel(self)  # 额外调整
        self.powerByLabel = QLabel("Power By jddld.com", self)

        self.updateInfo(info)

        self.__initWidgets()

    def calcPoints(self):
        pos = self.target.mapToGlobal(QPoint())
        windowPos = self.window().mapToGlobal(QPoint())
        x = pos.x() + self.target.width() // 2 - self.sizeHint().width() // 2 - windowPos.x()
        y = pos.y() - self.sizeHint().height() - 12 - windowPos.y()

        if x < 5:
            x = 5

        return QPoint(x, y)

    def __initWidgets(self):
        self.titleLabel.setVisible(True)
        self.damageDealtLabel.setVisible(True)
        self.damageReceivedLabel.setVisible(True)
        self.healingIncreaseLabel.setVisible(True)
        self.shieldIncreaseLabel.setVisible(True)
        self.abilityHasteLabel.setVisible(True)
        self.tenacityLabel.setVisible(True)

        self.descriptionLabel.setStyleSheet("border-top: 1px solid rgba(0, 0, 0, 80);")
        self.powerByLabel.setStyleSheet("color: rgba(0, 0, 0, 70);")

        self.titleLabel.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.powerByLabel.setAlignment(Qt.AlignCenter)
        self.descriptionLabel.setFont(QFont('Microsoft YaHei', 9))
        self.powerByLabel.setFont(QFont('Microsoft YaHei', 8))

        self.damageDealtLabel.setFont(QFont("Source Code Pro", 9, QFont.Bold))
        self.damageReceivedLabel.setFont(QFont("Source Code Pro", 9, QFont.Bold))
        self.healingIncreaseLabel.setFont(QFont("Source Code Pro", 9, QFont.Bold))
        self.shieldIncreaseLabel.setFont(QFont("Source Code Pro", 9, QFont.Bold))
        self.abilityHasteLabel.setFont(QFont("Source Code Pro", 9, QFont.Bold))
        self.tenacityLabel.setFont(QFont("Source Code Pro", 9, QFont.Bold))

        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.vBoxLayout.setContentsMargins(10, 8, 10, 8)
        self.vBoxLayout.setSpacing(2)
        self.gridBox.setHorizontalSpacing(10)
        self.gridBox.setVerticalSpacing(4)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.gridBox)
        self.vBoxLayout.addWidget(self.descriptionLabel)
        self.vBoxLayout.addWidget(self.powerByLabel)

        self.gridBox.addWidget(self.damageDealtLabel, 0, 0, Qt.AlignLeft)
        self.gridBox.addWidget(self.damageDealtValueLabel, 0, 1, Qt.AlignRight)
        self.gridBox.addWidget(self.damageReceivedLabel, 0, 2, Qt.AlignLeft)
        self.gridBox.addWidget(self.damageReceivedValueLabel, 0, 3, Qt.AlignRight)
        self.gridBox.addWidget(self.healingIncreaseLabel, 1, 0, Qt.AlignLeft)
        self.gridBox.addWidget(self.healingIncreaseValueLabel, 1, 1, Qt.AlignRight)
        self.gridBox.addWidget(self.shieldIncreaseLabel, 1, 2, Qt.AlignLeft)
        self.gridBox.addWidget(self.shieldIncreaseValueLabel, 1, 3, Qt.AlignRight)
        self.gridBox.addWidget(self.abilityHasteLabel, 2, 0, Qt.AlignLeft)
        self.gridBox.addWidget(self.abilityHasteValueLabel, 2, 1, Qt.AlignRight)
        self.gridBox.addWidget(self.tenacityLabel, 2, 2, Qt.AlignLeft)
        self.gridBox.addWidget(self.tenacityValueLabel, 2, 3, Qt.AlignRight)

        self.setLayout(self.vBoxLayout)

    def __updateStyle(self):
        """
        数据更新时调用一下, 把样式更新
        """
        self.descriptionLabel.setVisible(bool(self.description))
        self.damageDealtValueLabel.setStyleSheet(self.__getColor(self.damageDealt, 100))
        self.damageReceivedValueLabel.setStyleSheet(self.__getColor(self.damageReceived, 100, False))
        self.healingIncreaseValueLabel.setStyleSheet(self.__getColor(self.healingIncrease, 100))
        self.shieldIncreaseValueLabel.setStyleSheet(self.__getColor(self.shieldIncrease, 100))
        self.abilityHasteValueLabel.setStyleSheet(self.__getColor(self.abilityHaste, 0))
        self.tenacityValueLabel.setStyleSheet(self.__getColor(self.tenacity, 0))

    def __getColor(self, val, criterion, isPositive=True) -> str:
        """
        isPositive: 用于标记该属性是否积极(越大越好)
        """
        # 如果值越小越好, 交换一下条件, 让低的标记为绿色
        if not isPositive:
            val, criterion = criterion, val

        if val > criterion:
            return "color: #2aae0f;"  # 绿色
        elif val < criterion:
            return "color: #d0021b;"  # 红色

        return ""

    def updateInfo(self, info):
        self.catName = info.get("catname", "")
        self.damageDealt = int(info.get("zcsh", "100"))
        self.damageReceived = int(info.get("sdsh", "100"))
        self.healingIncrease = int(info.get("zlxl", "100"))
        self.shieldIncrease = int(info.get("hdxn", "100"))
        self.abilityHaste = int(info.get("jnjs", "0"))
        self.tenacity = int(info.get("renxing", "0"))
        self.description = info.get("description", "")

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
            w = self.vBoxLayout.sizeHint().width() * .16
            self.descriptionLabel.setText(TextWrap.wrap(self.description, int(w), False)[0])
        self.move(self.calcPoints())


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
