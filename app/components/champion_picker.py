from PyQt5.QtCore import pyqtSignal, QRect, QRectF, Qt
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QPen, QColor, QFont
from PyQt5.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from qfluentwidgets import SmoothScrollArea, FlowLayout, FlyoutAnimationType, Flyout

from app.lol.connector import connector


class ChampionAvatar(QFrame):
    _ordinal = 1

    on_click = pyqtSignal(int)

    checked = False

    def set_ordinal(self, ordinal: int):
        self._ordinal = ordinal

    def __init__(self, champion, parent=None):
        super().__init__(parent)
        self._champion_pixmap = QPixmap(champion["icon"])
        self._champion_id = champion["id"]

        self.setFixedSize(80, 80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawPixmap(QRect(0, 0, self.width(), self.height()), self._champion_pixmap)

        if self.checked:
            path = QPainterPath()
            path.addEllipse(QRectF(2, 2, self.width() - 4, self.height() - 4))
            painter.setPen(QPen(QColor(191, 151, 65), 3))
            painter.drawPath(path)
            painter.drawLine(0, 0, 0, 15)
            painter.drawLine(0, 0, 15, 0)
            painter.drawLine(0, self.height(), 0, self.height() - 15)
            painter.drawLine(0, self.height(), 15, self.height())
            painter.drawLine(self.width(), 0, self.width() - 15, 0)
            painter.drawLine(self.width(), 0, self.width(), 15)
            painter.drawLine(self.width(), self.height(), self.width(), self.height() - 15)
            painter.drawLine(self.width(), self.height(), self.width() - 15, self.height())

            font = QFont()
            font.setPointSize(22)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(QColor(255, 255, 255), 4))
            text = str(self._ordinal)
            fm = painter.fontMetrics()
            text_width = fm.width(text)
            text_height = fm.height()
            painter.drawText((self.width() - text_width) // 2, self.height() // 2 + text_height, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.checked = ~self.checked
            self.update()

            self.on_click.emit(self._champion_id)


class ChampionPickerView(QWidget):
    selected = pyqtSignal(list)

    def __init__(self, champion_ids, parent=None):
        super().__init__(parent)
        self._champion_ids = champion_ids
        self.checked_champion_ids = []
        self._champion_widgets = []
        self.ordinal = 1

        self.setFixedSize(600, 600)
        # self.setStyleSheet("background-color: rgb(0, 0, 0);")

        layout_main = QVBoxLayout(self)

        scroll_area = SmoothScrollArea()
        scroll_area.setWidgetResizable(True)
        widget_champion_list = QWidget()
        layout_champion_list = FlowLayout(widget_champion_list)
        for cid in self._champion_ids:
            champion_widget = ChampionAvatar({"id": cid, "icon": f"app/resource/game/champion icons/{cid}.png"},
                                             parent=self)
            champion_widget.on_click.connect(self._onclick_champion)
            self._champion_widgets.append(champion_widget)
            layout_champion_list.addWidget(champion_widget)
        scroll_area.setWidget(widget_champion_list)
        layout_main.addWidget(scroll_area)

        layout_btn = QHBoxLayout()
        btn_ok = QPushButton("ok")
        btn_ok.clicked.connect(self._onclick_ok)
        layout_btn.addWidget(btn_ok)
        btn_cancel = QPushButton("cancel")
        btn_cancel.clicked.connect(self._onclick_cancel)
        layout_btn.addWidget(btn_cancel)
        layout_main.addLayout(layout_btn)

    def _onclick_champion(self, champion_id):
        if champion_id in self.checked_champion_ids:
            self.checked_champion_ids.remove(champion_id)
        else:
            self.checked_champion_ids.append(champion_id)

        for widget in self._champion_widgets:
            if widget._champion_id == champion_id:
                widget.set_ordinal(len(self.checked_champion_ids))
                break

    def _onclick_ok(self):
        self.selected.emit(self.checked_champion_ids)
        self.close()

    def _onclick_cancel(self):
        self.close()


class ChampionPicker(QPushButton):
    selected = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setText("选择你的英雄")

        self.clicked.connect(self._onclick)

    def _onclick(self):
        view = ChampionPickerView(connector.manager.champs.keys())
        view.selected.connect(lambda l: self.selected.emit(l))
        Flyout.make(view, self, self.window(), FlyoutAnimationType.SLIDE_RIGHT)
