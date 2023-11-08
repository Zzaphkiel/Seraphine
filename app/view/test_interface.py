import qframelesswindow
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import SmoothScrollArea
from pyecharts.charts import Bar
from pyecharts import options as opts
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from qframelesswindow.webengine import FramelessWebEngineView
class TestInterface(SmoothScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.browser = FramelessWebEngineView(self.window())
        # self.browser = QWebEngineView(self)
        # self.browser.load(QUrl.fromLocalFile(self.get_bar_chart()))
        self.browser.load(QUrl("https://qfluentwidgets.com/"))
        self.hBoxLayout.addWidget(self.browser)

    def get_bar_chart(self):
        bar = Bar()
        bar.add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        bar.add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
        bar.set_global_opts(title_opts=opts.TitleOpts(title="主标题", subtitle="副标题"))
        return bar.render()
