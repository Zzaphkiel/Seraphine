# coding:utf-8
import argparse
import json
import sys
import os
import threading
import time

import psutil
from PyQt5.QtCore import Qt, QLocale, QTranslator
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.hook import start_hook
from app.view.main_window import MainWindow
from app.common.config import cfg

parser = argparse.ArgumentParser()

parser.add_argument("-p", "--pid", help="master process PID")

args = parser.parse_args()

if __name__ == '__main__':
    # 传 PID参数 则拉起子进程, 否则运行 GUI
    if args.pid:
        def _():
            while True:
                with open(fr"{os.getcwd()}\app\config\config.json", "r", encoding="utf-8") as f:
                    js = json.loads(f.read())
                    if not js.get("Functions", {}).get("ForceDisconnection"):
                        os._exit(0)  # 关闭了该设置

                for proc in psutil.process_iter():
                    if proc.pid == int(args.pid):
                        break
                else:
                    os._exit(0)  # 随主进程退出
                time.sleep(.3)
        threading.Thread(target=_, daemon=True).start()
        start_hook()
    else:
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
