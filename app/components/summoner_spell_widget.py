from PyQt5.QtCore import (Qt, pyqtSignal)
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QFrame, QGridLayout)
from app.common.qfluentwidgets import (FlyoutViewBase)


from app.components.champion_icon_widget import SummonerSpellButton


class SummonerSpellSelectFlyout(FlyoutViewBase):
    def __init__(self, spells: dict, parent: QWidget = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.selectWidget = SummonerSpellSelectWidget(spells)
        self.selectWidget.spellClicked.connect(self.__onSpellClicked)
        self.vBoxLayout.addWidget(self.selectWidget)

    def __onSpellClicked(self):
        self.close()


class SummonerSpellSelectWidget(QFrame):
    spellClicked = pyqtSignal(int)

    def __init__(self, spells: dict, parent: QWidget = None):
        super().__init__(parent)

        self.gridLayout = QGridLayout(self)
        self.spells = spells

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        for i, [id, icon] in enumerate(self.spells.items()):
            button = SummonerSpellButton(icon, id)

            button.setFixedSize(40, 40)
            button.clicked.connect(lambda i: self.spellClicked.emit(i))

            self.gridLayout.addWidget(button, i // 4, i % 4, Qt.AlignCenter)

    def __initLayout(self):
        self.gridLayout.setHorizontalSpacing(15)
        self.gridLayout.setVerticalSpacing(15)
        self.gridLayout.setContentsMargins(15, 15, 15, 15)
