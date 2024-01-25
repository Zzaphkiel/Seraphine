import sys

sys.stdout = None
from qfluentwidgets import *
from qfluentwidgets.components.widgets.line_edit import CompleterMenu, LineEditButton
sys.stdout = sys.__stdout__