
from PyQt5.QtCore import (Qt, pyqtSignal, QSize)
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QSpacerItem,
                             QLabel, QWidget, QSizePolicy, QFileDialog)
from app.common.qfluentwidgets import (TransparentToolButton, FluentIcon, SearchLineEdit,
                                       FlowLayout, SmoothScrollArea, FlyoutViewBase,
                                       BodyLabel)


from app.common.style_sheet import StyleSheet
from app.components.champion_icon_widget import RoundIcon, RoundIconButton
from app.components.draggable_widget import DraggableItem, ItemsDraggableWidget


class PathTabItem(DraggableItem):
    closedRequested = pyqtSignal()

    def __init__(self, path: str, parent=None):
        super().__init__(parent=parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.label = BodyLabel(path)

        self.editButton = TransparentToolButton(FluentIcon.EDIT)
        self.closeButton = TransparentToolButton(FluentIcon.CLOSE)

        self.__intiWidget()
        self.__initLayout()

    def __intiWidget(self):
        self.setFixedSize(400, 44)
        self.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)

        self.editButton.setIconSize(QSize(12, 12))
        self.editButton.setFixedSize(QSize(26, 26))

        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setFixedSize(QSize(26, 26))

        self.closeButton.clicked.connect(self.closedRequested)
        self.editButton.clicked.connect(self.__onEditButtonClicked)

        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(13, 0, 13, 0)
        self.hBoxLayout.setSpacing(3)

        self.hBoxLayout.addWidget(
            self.label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        self.hBoxLayout.addSpacerItem(QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.hBoxLayout.addWidget(
            self.editButton, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(
            self.closeButton, alignment=Qt.AlignRight | Qt.AlignVCenter)

    def __onEditButtonClicked(self):
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"),
            self.label.text())

        if not path:
            return

        self.label.setText(path)

    def sizeHint(self):
        return QSize(250, 44)


class PathDraggableWidget(ItemsDraggableWidget):
    def __init__(self, paths: list, parent=None):
        super().__init__(parent=parent)
        self.__initWidget(paths)

    def __initWidget(self, paths):
        self.setFixedHeight(318)

        for path in paths:

            # 别问为什么要判断一下，我也不知道为什么
            if type(path) is not str:
                continue

            self.addItem(path)

    def addItem(self, path):
        item = PathTabItem(path)
        item.closedRequested.connect(lambda i=item: self.removeItem(item))

        self._addItem(item)

    def removeItem(self, item):
        if self.count() == 1:
            return

        self._removeItem(item)

    def getCurrentPaths(self):
        return [item.label.text() for item in self.items]
