from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig


class StyleSheet(StyleSheetBase, Enum):
    SETTING_INTERFACE = 'setting_interface'
    MAIN_WINDOW = 'main_window'
    CAREER_INTERFACE = 'career_interface'
    START_INTERFACE = 'start_interface'
    SEARCH_INTERFACE = 'search_interface'
    GAME_INFO_INTERFACE = 'game_info_interface'
    AUXILIARY_INTERFACE = 'auxiliary_interface'

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f'app/resource/qss/{theme.value.lower()}/{self.value}.qss'