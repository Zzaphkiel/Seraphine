import darkdetect
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from pyecharts.charts import Bar
from pyecharts.globals import ThemeType
from qfluentwidgets import Theme
from qframelesswindow.webengine import FramelessWebEngineView
from pyecharts import options as opts

from app.common.config import cfg


class GameDetailChartWidget(QWidget):
    loadHtml = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = None
        self.hBoxLayout = QHBoxLayout(self)
        self.browser = FramelessWebEngineView(self.window())
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)
        self.browser.page().setBackgroundColor(Qt.transparent)
        self.browser.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, False)
        self.browser.setGeometry(0, 0, self.width(), self.height())
        self.setStyleSheet("border: none;")
        self.hBoxLayout.addWidget(self.browser)

        self.loadHtml.connect(self.onLoadHtml)

    def onLoadHtml(self, path):
        self.browser.load(QUrl.fromLocalFile(path))

    def refresh(self):
        self.initChartHtml(self.game)

    def initChartHtml(self, game):
        """
        该方法耗时, 不建议在UI线程执行

        执行完成后自动更新到 browser
        """
        self.game = game

        t = cfg.get(cfg.themeMode)

        if t == Theme.AUTO:
            t = darkdetect.theme()

        if t == Theme.DARK:
            chartTheme = ThemeType.DARK
            legendBackgroundcolor = "#FFFFFF11"
        else:
            chartTheme = ThemeType.WHITE
            legendBackgroundcolor = "#00000006"

        bar = Bar(
            init_opts=opts.InitOpts(
                width="100%",
                height="100vh",
                theme=chartTheme,
                bg_color="#00000000",
            )
        )

        # 名称
        bar.add_xaxis([s['summonerName'] for team in game['teams'].values() for s in team["summoners"]][::-1])

        # 数据
        keys = ['totalDamageDealtToChampions', 'trueDamageDealtToChampions', 'magicDamageDealtToChampions',
                'physicalDamageDealtToChampions', 'totalDamageTaken', 'trueDamageTaken', 'magicalDamageTaken',
                'physicalDamageTaken', 'totalHealingDone', 'damageSelfMitigated', 'totalMinionsKilled', 'goldEarned',
                'visionScore']
        for k in keys:
            bar.add_yaxis(
                self.tr(k),
                [s['chartData'][k] for team in game['teams'].values() for s in team["summoners"]][::-1],
                gap="0%"
            )

        result = (
            bar
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right"))
            .set_global_opts(
                yaxis_opts=opts.AxisOpts(is_show=False),
                legend_opts=opts.LegendOpts(
                    border_radius=5,
                    selected_map={k: False for k in keys[1:]},
                    type_='scroll',
                    background_color=legendBackgroundcolor
                ),
            )
            .render())

        self.loadHtml.emit(result)
