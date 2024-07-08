'''
PyQt-Fluent-Widgets without Ads.
'''

import sys

sys.stdout = None
from qfluentwidgets import *
from qfluentwidgets.components.widgets.line_edit import CompleterMenu, LineEditButton
from qfluentwidgets.common.animation import BackgroundAnimationWidget
from qfluentwidgets.common.animation import BackgroundColorObject
from qfluentwidgets.window.fluent_window import FluentWindowBase
from qfluentwidgets.window.stacked_widget import StackedWidget
from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qframelesswindow import SvgTitleBarButton
sys.stdout = sys.__stdout__