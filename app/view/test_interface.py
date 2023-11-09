import qframelesswindow
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import SmoothScrollArea
from pyecharts.charts import Bar
from pyecharts import options as opts
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from qframelesswindow.webengine import FramelessWebEngineView
from pyecharts.faker import Faker


class TestInterface(SmoothScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.browser = FramelessWebEngineView(self.window())
        # self.browser = QWebEngineView(self)
        self.browser.load(QUrl.fromLocalFile(self.get_bar_chart()))
        # self.browser.load(QUrl("https://qfluentwidgets.com/"))
        self.hBoxLayout.addWidget(self.browser)

    def get_bar_chart(self):
        return (Bar()
                .add_xaxis(Faker.choose())
                .add_yaxis("商家A", Faker.values())
                .add_yaxis("商家B", Faker.values())
                .reversal_axis()
                .set_series_opts(label_opts=opts.LabelOpts(position="right"))
                .set_global_opts(title_opts=opts.TitleOpts(title="Bar-翻转 XY 轴"))
                .render())

        # bar = Bar()
        # bar.add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        # bar.add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
        # bar.set_global_opts(title_opts=opts.TitleOpts(title="主标题", subtitle="副标题"))
        # return bar.render()
