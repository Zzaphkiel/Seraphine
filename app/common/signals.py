from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget


class SignalBus(QObject):
    # listener:
    tasklistNotFound = pyqtSignal()

    lolClientStarted = pyqtSignal(int)
    lolClientEnded = pyqtSignal()

    terminateListeners = pyqtSignal()

    # connector:
    lcuApiExceptionRaised = pyqtSignal(str, BaseException)
    currentSummonerProfileChanged = pyqtSignal(dict)
    gameStatusChanged = pyqtSignal(str)
    champSelectChanged = pyqtSignal(dict)

    # career_interface
    careerGameBarClicked = pyqtSignal(str)

    # search_interface:
    gameTabClicked = pyqtSignal(QWidget)

    # jumps:
    toCareerInterface = pyqtSignal(str)
    toSearchInterface = pyqtSignal(str)

    # style:
    customColorChanged = pyqtSignal(str)


signalBus = SignalBus()
