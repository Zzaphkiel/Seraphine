from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    # From connector
    lcuApiExceptionRaised = pyqtSignal(str, BaseException)
    currentSummonerProfileChanged = pyqtSignal(dict)
    gameStatusChanged = pyqtSignal(str)
    champSelectChanged = pyqtSignal(dict)

    # From career_interface
    careerTeammateSummonerNameClicked = pyqtSignal(str)


signalBus = SignalBus()
