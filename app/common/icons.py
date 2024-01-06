from enum import Enum

from qfluentwidgets import getIconColor, Theme, FluentIconBase
from PyQt5.QtGui import QIcon


class Icon(FluentIconBase, Enum):
    PERSON = 'Person'
    GAME = 'Game'
    SEARCH = 'Search'
    FOLDER = 'Folder'
    DESKTOPRIGHT = 'DesktopRight'
    BRUSH = 'Brush'
    PALETTE = 'Palette'
    CIRCLERIGHT = 'CircleRight'
    ZOOMFIT = 'ZoomFit'
    LANGUAGE = 'Language'
    WRENCH = 'Wrench'
    HOME = 'Home'
    SLIDESEARCH = 'SlideSearch'
    CHEVRONLEFT = "ChevronLeft"
    CHEVRONRIGHT = "ChevronRight"
    COPY = 'Copy'
    COMMENT = 'Comment'
    VIDEO_PERSON = 'VideoPerson'
    PERSON_BOARD = 'PersonBoard'
    CERTIFICATE = 'Certificate'
    PERSONAVAILABLE = 'PersonAvailable'
    STAROFF = 'StarOff'
    TEXTEDIT = 'TextEdit'
    CIRCLEMARK = 'CircleMark'
    TROPHY = 'Trophy'
    FEEDBACK = 'Feedback'
    INFO = 'Info'
    DELETE = 'Delete'
    BLUR = 'Blur'
    GITHUB = 'Github'
    EYES = "Eyes"
    CHECK = 'Check'
    EXIT = 'Exit'
    LOCK = 'Lock'
    TEAM = 'Team'
    SETTING = 'Setting'
    FILTER = 'Filter'
    UPDATE = 'Update'
    CONNECTION = "Connection"
    PAGE = 'Page'
    ARROWCIRCLE = 'ArrowCircle'
    SCALEFIT = 'ScaleFit'

    def path(self, theme=Theme.AUTO):
        return f'./app/resource/icons/{self.value}_{getIconColor(theme)}.svg'
