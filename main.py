# coding:utf-8
import sys
import os

import asyncio
from qasync import QApplication, QEventLoop
from app.common.qfluentwidgets import FluentTranslator
from PyQt5.QtCore import Qt, QTranslator

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.common.config import cfg, VERSION
from app.view.main_window import MainWindow


def main():
    args = sys.argv
    if len(args) == 2 and args[1] in ['--version', '-v']:
        print(VERSION)
        return


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

    eventLoop = QEventLoop(app)
    asyncio.set_event_loop(eventLoop)

    appCloseEvent = asyncio.Event()
    app.aboutToQuit.connect(appCloseEvent.set)

    locale = cfg.get(cfg.language).value
    translator = FluentTranslator(locale)
    lolHelperTranslator = QTranslator()
    lolHelperTranslator.load(locale, "Seraphine", ".", "./app/resource/i18n")

    app.installTranslator(translator)
    app.installTranslator(lolHelperTranslator)

    w = MainWindow()
    w.show()

    eventLoop.run_until_complete(appCloseEvent.wait())
    eventLoop.close()


if __name__ == '__main__':
    main()
