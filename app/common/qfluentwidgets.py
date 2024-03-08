'''
PyQt-Fluent-Widgets without Ads.
'''

import sys

sys.stdout = None
from qfluentwidgets import *
from qfluentwidgets.components.widgets.line_edit import CompleterMenu, LineEditButton
from qfluentwidgets.common.animation import BackgroundAnimationWidget
from qfluentwidgets.common.animation import BackgroundColorObject
sys.stdout = sys.__stdout__