import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from ..common.qfluentwidgets import CheckBox
from typing import List, Tuple


# TODO GameInfoInterface添加筛选功能

class ModeFilterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.selected: List[int] = []

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)

        self.rankSoloCheckBox = CheckBox(self.tr("Ranked solo"))
        self.rankFlexCheckBox = CheckBox(self.tr("Ranked Flex"))
        self.normalCheckBox = CheckBox(self.tr("Normal"))
        self.aramCheckBox = CheckBox(self.tr("A.R.A.M."))

        self.checkBoxDict = {
            self.rankSoloCheckBox: 420,  # 单双排
            self.rankFlexCheckBox: 440,  # 灵活组排
            self.normalCheckBox: 430,    # 匹配模式
            self.aramCheckBox: 450       # 大乱斗
        }

        for checkBox, num in self.checkBoxDict.items():
            checkBox.stateChanged.connect(
                lambda state, num=num: self.updateSelected(state, num))

        self.vBoxLayout.addWidget(
            self.rankSoloCheckBox, alignment=Qt.AlignLeft)
        self.vBoxLayout.addWidget(
            self.rankFlexCheckBox, alignment=Qt.AlignLeft)
        self.vBoxLayout.addWidget(
            self.normalCheckBox, alignment=Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.aramCheckBox, alignment=Qt.AlignLeft)

        self.setLayout(self.vBoxLayout)

    def updateSelected(self, state, num, callback=None):
        if state == Qt.Checked:
            if num not in self.selected:
                self.selected.append(num)
        else:
            if num in self.selected:
                self.selected.remove(num)

        if callback:
            callback()

    def setCallback(self, func):
        """
        @param func: check box状态改变时回调该方法
        @return:
        """
        for checkBox, num in self.checkBoxDict.items():
            checkBox.stateChanged.connect(
                lambda state, num=num, func=func: self.updateSelected(state, num, func))

    def getFilterMode(self) -> Tuple[int]:
        """
        获取选中的模式
        @return:
        @rtype: Tuple[int]
        """
        return set(self.selected)

    def setCheckBoxState(self, data: tuple):
        """
        设置复选框状态
        @param data:
        @return:
        """
        for checkBox, num in self.checkBoxDict.items():
            if num in data:
                checkBox.setChecked(True)
            else:
                checkBox.setChecked(False)


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = ModeFilterWidget()
    w.show()
    app.exec_()
