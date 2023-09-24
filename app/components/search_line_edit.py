from PyQt5.QtCore import Qt, QEvent, QAbstractItemModel
from PyQt5.QtWidgets import QCompleter, QAction
from PyQt5.uic.properties import QtCore, QtGui
from qfluentwidgets import SearchLineEdit as QSearchLineEdit
from qfluentwidgets.components.widgets.line_edit import CompleterMenu

from app.common.config import cfg


class MyCompleterMenu(CompleterMenu):

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
        self.lineEdit.searchButton.click()


class SearchLineEdit(QSearchLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        completer = QCompleter([], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(10)
        completer.setFilterMode(Qt.MatchFlag.MatchFixedString)
        completer.setCompletionRole(Qt.DisplayRole)
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(completer)

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
