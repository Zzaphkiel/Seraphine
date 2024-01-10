# coding:utf-8
import sys
import os

from qfluentwidgets import FluentTranslator
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTranslator

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.common.config import cfg
from app.view.main_window import MainWindow


if __name__ == '__main__':
    

    if cfg.get(cfg.dpiScale) == "Auto":
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    else:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    locale = cfg.get(cfg.language).value
    translator = FluentTranslator(locale)
    lolHelperTranslator = QTranslator()
    lolHelperTranslator.load(locale, "Seraphine", ".", "./app/resource/i18n")

    app.installTranslator(translator)
    app.installTranslator(lolHelperTranslator)

    w = MainWindow()
    w.show()

    app.exec_()
