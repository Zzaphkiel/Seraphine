import json

import qframelesswindow
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import SmoothScrollArea
from pyecharts.charts import Bar
from pyecharts import options as opts
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from qframelesswindow.webengine import FramelessWebEngineView
from pyecharts.faker import Faker

from app.lol import tools


class TestInterface(SmoothScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        # self.browser = FramelessWebEngineView(self.window())
        self.browser = QWebEngineView(self.window())
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)
        # self.browser = QWebEngineView(self)
        self.browser.load(QUrl.fromLocalFile(self.get_bar_chart()))
        # self.browser.load(QUrl("https://qfluentwidgets.com/"))
        self.browser.page().setBackgroundColor(Qt.transparent)
        self.browser.setAttribute(Qt.WA_StyledBackground)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("border: none;")
        # self.browser.setAttribute(Qt.WA_TranslucentBackground)
        # self.browser.setStyleSheet("background:transparent")
        self.hBoxLayout.addWidget(self.browser)


    def get_bar_chart(self):
        # data = tools.processGameDetailData("d1892d1c-d79d-5543-b4f7-58a93256c6b5",
        #                                    json.loads(open(r"detail.json", "r", encoding="utf-8").read()), True)
        #
        # bar = Bar()
        #
        # # 名称
        # bar.add_xaxis([s['summonerName'] for team in data['teams'].values() for s in team["summoners"]])
        #
        # # 数据
        # keys = ['totalDamageDealtToChampions', 'trueDamageDealtToChampions', 'magicDamageDealtToChampions',
        #         'physicalDamageDealtToChampions', 'totalDamageTaken', 'trueDamageTaken', 'magicalDamageTaken',
        #         'physicalDamageTaken', 'totalHealingDone', 'damageSelfMitigated', 'totalMinionsKilled', 'goldEarned',
        #         'visionScore']
        # for k in keys:
        #     bar.add_yaxis(
        #         self.tr(k),
        #         [s['chartData'][k] for team in data['teams'].values() for s in team["summoners"]],
        #         gap="0%"
        #     )
        #
        # return (bar
        #         .reversal_axis()
        #         .set_series_opts(label_opts=opts.LabelOpts(position="right"))
        #         .set_global_opts(
        #             # title_opts=opts.TitleOpts(title="Bar-显示 ToolBox"),
        #             # toolbox_opts=opts.ToolboxOpts(),
        #             legend_opts=opts.LegendOpts(
        #                 selected_map={
        #                     k: False for k in keys[1:]
        #                 },
        #                 type_='scroll'
        #                 # orient="vertical",
        #                 # pos_left="left",
        #                 # pos_top="middle"
        #             ),
        #         )
        #         .render())

        bar = Bar()
        bar.add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        bar.add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
        bar.set_global_opts(title_opts=opts.TitleOpts(title="主标题", subtitle="副标题"))
        return bar.render()
