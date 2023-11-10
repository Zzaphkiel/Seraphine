from PyQt5.QtWidgets import QLabel
from qfluentwidgets import (MessageBox, MessageBoxBase, SmoothScrollArea, SubtitleLabel, BodyLabel, TextEdit, TitleLabel,
                            CheckBox)

from app.common.config import VERSION, cfg


class UpdateMessageBox(MessageBoxBase):
    def __init__(self, info, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(self.tr('Update detected'), self)
        self.titleLabel.setContentsMargins(5, 0, 5, 0)

        self.content = BodyLabel(self.tr(
            "current: v") + VERSION + self.tr(", ") + self.tr("new: v") + info.get("tag_name")[1:], self)

        self.content.setContentsMargins(8, 0, 5, 0)

        textEdit = TextEdit(self)
        textEdit.setFixedWidth(int(self.width() * .6))
        textEdit.setMarkdown(info.get("body"))
        textEdit.setReadOnly(True)

        checkBox = CheckBox()
        checkBox.setText(self.tr("Don't remind me again"))
        checkBox.clicked.connect(lambda: cfg.set(
            cfg.enableCheckUpdate, not checkBox.isChecked(), True))

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content)
        self.viewLayout.addWidget(textEdit)
        self.viewLayout.addWidget(checkBox)

        self.yesButton.setText(self.tr("Download"))
        self.cancelButton.setText(self.tr("Ok"))
