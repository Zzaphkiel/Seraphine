from PyQt5.QtCore import Qt, QEvent, QAbstractItemModel, pyqtSignal, QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QCompleter, QAction, QWidget, QHBoxLayout, QListWidgetItem, QPushButton
from PyQt5.uic.properties import QtCore, QtGui
from qfluentwidgets import SearchLineEdit as QSearchLineEdit, PushButton, Icon, FluentIcon, TransparentToolButton, Theme
from qfluentwidgets.components.widgets.line_edit import CompleterMenu, LineEditButton

from app.common.config import cfg


class MyItemWidget(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.text)
        event.ignore()


class MyCompleterMenu(CompleterMenu):

    def __onDelBtnClicked(self, action):
        historyList = cfg.get(cfg.searchHistory).split(",")
        historyList.remove(action.text())
        self.close()
        cfg.set(cfg.searchHistory, ",".join(historyList))
        self.lineEdit.refreshCompleter()

    def addAction(self, action: QAction):
        """ add action to menu

        Parameters
        ----------
        action: QAction
            menu action
        """
        item: QListWidgetItem = self._createActionItem(action)

        text = action.text()
        hLayout = QHBoxLayout()
        hLayout.setAlignment(Qt.AlignRight)
        hLayout.setContentsMargins(0, 0, 0, 0)
        delBtn = LineEditButton(FluentIcon.CLOSE, self)
        delBtn.setFixedSize(self.itemHeight - 7, self.itemHeight - 7)
        delBtn.setIconSize(QSize(self.itemHeight - 23, self.itemHeight - 23))
        delBtn.clicked.connect(lambda _, x=action: self.__onDelBtnClicked(x))
        hLayout.addWidget(delBtn)

        w = MyItemWidget(text)
        w.clicked.connect(self.__onItemSelected)
        w.setLayout(hLayout)
        self.view.addItem(item)
        self.view.setItemWidget(item, w)
        self.adjustSize()

    def eventFilter(self, obj, e):
        if e.type() != QEvent.KeyPress:
            return super().eventFilter(obj, e)

        # redirect input to line edit
        self.lineEdit.event(e)
        self.view.event(e)

        if e.key() == Qt.Key_Escape:
            self.close()
        if e.key() in [Qt.Key_Enter, Qt.Key_Return]:
            if self.isVisible():
                self.close()

            self.lineEdit.searchButton.click()

        return True

    def setCompletion(self, model: QAbstractItemModel):
        """ set the completion model """
        items = []
        for i in range(model.rowCount()):
            for j in range(model.columnCount()):
                items.append(model.data(model.index(i, j)))

        if self.items == items and self.isVisible():
            return False

        self.clear()
        self.items = items

        # add items
        for i in items:
            self.addAction(QAction(i, triggered=lambda c, x=i: self.__onItemSelected(x)))

        return True

    def __onItemSelected(self, text):
        self.lineEdit.setText(text)
        self.activated.emit(text)
        self.close()
        self.lineEdit.searchButton.click()


class SearchLineEdit(QSearchLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        completer = QCompleter([], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(10)
        completer.setCompletionRole(Qt.DisplayRole)
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(completer)

    def refreshCompleter(self):
        self._showCompleterMenu()

    def _showCompleterMenu(self):
        if not self.completer():
            return

        model = cfg.get(cfg.searchHistory)
        if not model:
            return

        model = model.split(",")
        self.completer().model().setStringList(model)

        # create menu
        if not self._completerMenu:
            self._completerMenu = MyCompleterMenu(self)
            self._completerMenu.activated.connect(self._completer.activated)

        # add menu items
        changed = self._completerMenu.setCompletion(self.completer().completionModel())
        self._completerMenu.setMaxVisibleItems(self.completer().maxVisibleItems())

        # show menu
        if changed:
            self._completerMenu.popup()

    def focusInEvent(self, e):
        self._showCompleterMenu()
        super().focusInEvent(e)
