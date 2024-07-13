from enum import Enum
from typing import Tuple
import traceback

from PyQt5.QtGui import QColor, QClipboard
from PyQt5.QtCore import QObject
from app.common.qfluentwidgets import StyleSheetBase, Theme, qconfig, isDarkTheme

from app.common.config import cfg
from app.common.signals import signalBus


class StyleSheet(StyleSheetBase, Enum):
    SETTING_INTERFACE = 'setting_interface'
    MAIN_WINDOW = 'main_window'
    CAREER_INTERFACE = 'career_interface'
    START_INTERFACE = 'start_interface'
    SEARCH_INTERFACE = 'search_interface'
    GAME_INFO_INTERFACE = 'game_info_interface'
    AUXILIARY_INTERFACE = 'auxiliary_interface'

    OPGG_TIER_INTERFACE = 'opgg_tier_interface'
    OPGG_BUILD_INTERFACE = 'opgg_build_interface'
    OPGG_WAITING_INTERFACE = 'opgg_waiting_interface'
    OPGG_ERROR_INTERFACE = "opgg_error_interface"

    ARAM_FLYOUT = 'aram_flyout'
    DRAGGABLE_WIDGET = 'draggable_widget'
    CHAMPIONS_SELECT_WIDGET = 'champions_select_widget'
    TRANSPARENT_BUTTON = 'transparent_button'

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f'app/resource/qss/{theme.value.lower()}/{self.value}.qss'


class ColorChangeable(QObject):
    '''
    继承该基类的实例，会响应 `signalBus.customColorChanged` 信号，若对应 `type`
    的颜色有更新，该实例会自动更新为相应新的颜色

    继承该类需要重写 `setColor()` 方法，针对实例本体类型的不同（如 `QLabel`、`QFrame`，或其他什么东西）
    来更新自己的颜色
    '''

    def __init__(self, type: str = None):
        # 允许初始化时 type 为空
        if type:
            self.type = type
            colorManager.regiesterWidget(self)

            # 更新自己的颜色
            c1, c2, c3, c4 = self.__getColors()
            self.setColor(c1, c2, c3, c4)
        else:
            self.type = None

        # 如果自己被析构了，就将自己 manager 中记录的自己的引用给删了
        self.destroyed.connect(lambda: colorManager.removeWidget(self))

    def __getColors(self):
        return colorManager.getColor(self.type)

    def setColor(self, c1: QColor, c2: QColor, c3: QColor, c4: QColor):
        raise NotImplementedError()

    def setType(self, type: str = None):
        if self.type:
            colorManager.removeWidget(self)

        self.type = type
        if not type:
            return

        colorManager.regiesterWidget(self)
        c1, c2, c3, c4 = self.__getColors()
        self.setColor(c1, c2, c3, c4)


class __ColorManager():
    def __init__(self):
        # {"type": {'func': func, 'widgets': []}}
        self.items = {}
        signalBus.customColorChanged.connect(self.__updateColor)
        qconfig.themeChanged.connect(self.__updateAllColor)

    # 新建颜色 type 以及颜色的计算方法
    def registerColor(self, type: str):
        def wrapper(func):
            self.items[type] = {
                'func': func,
                'widgets': [],
            }

            return func
        return wrapper

    def regiesterWidget(self, widget: ColorChangeable):
        """将 widget 与 widget 的颜色记录起来，颜色有更新的时候可以找到所有对应 widget"""
        self.items[widget.type]['widgets'].append(widget)

    def removeWidget(self, widget: ColorChangeable):
        if not widget.type:
            return

        self.items[widget.type]['widgets'].remove(widget)

    def __updateAllColor(self):
        for i in self.items.values():
            widgets: list[ColorChangeable] = i['widgets']
            c1, c2, c3, c4 = i['func']()

            for widget in widgets:
                widget.setColor(c1, c2, c3, c4)

    def __updateColor(self, type):
        """`signalBus.customColorChanged` 触发时，更新对应 `type` 的所有 widget 的颜色"""
        widgets: list[ColorChangeable] = self.items[type]['widgets']
        c1, c2, c3, c4 = self.items[type]['func']()

        for widget in widgets:
            widget.setColor(c1, c2, c3, c4)

    def getColor(self, type: str):
        '''
        返回 `type` 对应的颜色本体、悬停颜色以及鼠标按下颜色
        '''
        return self.items[type]['func']()


colorManager = __ColorManager()

# 有关胜负等一切组件的颜色


@colorManager.registerColor('win')
def __getWinColor():
    color = cfg.get(cfg.winCardColor)
    return __getStyleSheetColor(color)


@colorManager.registerColor('lose')
def __getLoseColor():
    color = cfg.get(cfg.loseCardColor)
    return __getStyleSheetColor(color)


@colorManager.registerColor('remake')
def __getRemakeColor():
    color = cfg.get(cfg.remakeCardColor)
    return __getStyleSheetColor(color)


# 动画背景组件的默认颜色
@colorManager.registerColor('default')
def __getDefaultColor():
    color = QColor(233, 233, 233, 13 if isDarkTheme() else 170)
    c1 = QColor(243, 243, 243, 21 if isDarkTheme() else 127)
    c2 = QColor(255, 255, 255, 8 if isDarkTheme() else 64)
    c3 = QColor(255, 255, 255, 20) if isDarkTheme(
    ) else QColor(0, 0, 0, 25)

    return color, c1, c2, c3


# 文字组件的颜色
@colorManager.registerColor("text")
def __getTextColor():
    color = QColor('white') if isDarkTheme() else QColor('black')
    return color, color, color, color


# 对局信息界面提示组队的颜色
@colorManager.registerColor('team1')
def __getTeam1Color():
    # TODO: 开放用户自定义设置
    color = QColor.fromRgb(255, 176, 27, 39)
    return __getStyleSheetColor(color)


@colorManager.registerColor('team2')
def __getTeam2Color():
    # TODO: 开放用户自定义设置
    color = QColor.fromRgb(255, 51, 153, 39)
    return __getStyleSheetColor(color)


# OPGG 英雄梯队中英雄卡片的颜色
@colorManager.registerColor('tier0')
def __getTier0Color():
    color = QColor.fromRgb(232, 64, 87, 39)
    return __getStyleSheetColor(color)


@colorManager.registerColor('tier1')
def __getTier1Color():
    color = QColor.fromRgb(0, 147, 255, 39)
    return __getStyleSheetColor(color)


@colorManager.registerColor('tier2')
def __getTier2Color():
    color = QColor.fromRgb(0, 187, 163, 39)
    return __getStyleSheetColor(color)


@colorManager.registerColor('tier3')
def __getTier3Color():
    color = QColor.fromRgb(255, 185, 0, 39)
    return __getStyleSheetColor(color)


@colorManager.registerColor('tier4')
def __getTier4Color():
    color = QColor.fromRgb(154, 164, 175, 39)
    return __getStyleSheetColor(color)


@colorManager.registerColor('tier5')
def __getTier5Color():
    color = QColor.fromRgb(168, 138, 103, 39)
    return __getStyleSheetColor(color)


def __getStyleSheetColor(color: QColor):
    '''
    返回主颜色、鼠标悬停颜色、鼠标按下颜色以及边框颜色
    '''
    r, g, b, a = color.getRgb()

    f1, f2 = 1.1, 0.9
    r1, g1, b1 = min(r * f1, 255), min(g * f1, 255), min(b * f1, 255)
    r2, g2, b2 = min(r * f2, 255), min(g * f2, 255), min(b * f2, 255)
    a1, a2 = min(a + 25, 255), min(a + 50, 255)

    c1 = QColor.fromRgb(r1, g1, b1, a1)
    c2 = QColor.fromRgb(r2, g2, b2, a2)
    c3 = QColor.fromRgb(r, g, b, min(a+130, 255))

    return color, c1, c2, c3
