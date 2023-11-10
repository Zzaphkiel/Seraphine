from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from pyecharts.charts import Bar
from qframelesswindow.webengine import FramelessWebEngineView
from pyecharts import options as opts


class GameDetailChartWidget(QWidget):
    loadHtml = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.browser = FramelessWebEngineView(self.window())
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)
        self.browser.page().setBackgroundColor(Qt.transparent)
        self.setStyleSheet("border: none;")
        self.hBoxLayout.addWidget(self.browser)

        self.loadHtml.connect(self.onLoadHtml)

    def onLoadHtml(self, path):
        self.browser.load(QUrl.fromLocalFile(path))

    def initChartHtml(self, game):
        """
        该方法耗时, 不建议在UI线程执行

        执行完成后自动更新到 browser
        """
        bar = Bar()

        # 名称
        bar.add_xaxis([s['summonerName'] for team in game['teams'].values() for s in team["summoners"]])

        # 数据
        keys = ['totalDamageDealtToChampions', 'trueDamageDealtToChampions', 'magicDamageDealtToChampions',
                'physicalDamageDealtToChampions', 'totalDamageTaken', 'trueDamageTaken', 'magicalDamageTaken',
                'physicalDamageTaken', 'totalHealingDone', 'damageSelfMitigated', 'totalMinionsKilled', 'goldEarned',
                'visionScore']
        for k in keys:
            bar.add_yaxis(
                self.tr(k),
                [s['chartData'][k] for team in game['teams'].values() for s in team["summoners"]],
                gap="0%"
            )

        result = (bar
                  .reversal_axis()
                  .set_series_opts(label_opts=opts.LabelOpts(position="right"))
                  .set_global_opts(
                    legend_opts=opts.LegendOpts(
                        selected_map={k: False for k in keys[1:]},
                        type_='scroll'
                        ),
                    )
                  .render())

        self.loadHtml.emit(result)
