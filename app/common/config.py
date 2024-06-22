from enum import Enum
import os
import sys

from PyQt5.QtCore import QLocale

from .qfluentwidgets import (qconfig, QConfig, ConfigItem, FolderValidator, BoolValidator,
                             OptionsConfigItem, OptionsValidator, ConfigSerializer,
                             RangeConfigItem, RangeValidator, EnumSerializer, ColorConfigItem)


class Language(Enum):
    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):

    def serialize(self, language: Language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != 'Auto' else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    lolFolder = ConfigItem("General", "LolPath", [])
    enableStartLolWithApp = ConfigItem("General", "EnableStartLolWithApp",
                                       False, BoolValidator())

    micaEnabled = ConfigItem(
        "Personalization", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem("Personalization",
                                 "DpiScale",
                                 "Auto",
                                 OptionsValidator(
                                     [1, 1.25, 1.5, 1.75, 2, "Auto"]),
                                 restart=True)

    language = OptionsConfigItem("Personalization",
                                 "Language",
                                 Language.AUTO,
                                 OptionsValidator(Language),
                                 LanguageSerializer(),
                                 restart=True)

    winCardColor = ColorConfigItem(
        "Personalization", "WinCardColor", '#2839b01b')
    loseCardColor = ColorConfigItem(
        "Personalization", "LoseCardColor", '#28d3190c')
    remakeCardColor = ColorConfigItem(
        "Personalization", "RemakeCardColor", '#28a2a2a2')

    careerGamesNumber = RangeConfigItem("Functions", "CareerGamesNumber", 20,
                                        RangeValidator(10, 100))
    apiConcurrencyNumber = RangeConfigItem("Functions", "ApiConcurrencyNumber", 1,
                                           RangeValidator(1, 20), restart=True)

    gameInfoFilter = ConfigItem(
        "Functions", "GameInfoFilter", False, BoolValidator())

    showTierInGameInfo = ConfigItem("Functions", "ShowTierInGameInfo", False,
                                    BoolValidator())
    enableAutoAcceptMatching = ConfigItem("Functions",
                                          "EnableAutoAcceptMatching", False,
                                          BoolValidator())
    enableAutoReconnect = ConfigItem("Functions",
                                     "EnableAutoReconnect", False,
                                     BoolValidator())

    autoAcceptMatchingDelay = RangeConfigItem(
        "Functions", "AutoAcceptMatchingDelay", 0, RangeValidator(0, 11))

    enableAutoSelectTimeoutCompleted = ConfigItem("Functions",
                                                  "EnableAutoSelectTimeoutCompleted", False,
                                                  BoolValidator())

    enableRandomSkin = ConfigItem(
        "Functions", "enableRandomSkin", False, BoolValidator())

    enableAutoSelectChampion = ConfigItem(
        "Functions", "EnableAutoSelectChampion", False, BoolValidator())
    autoSelectChampion = ConfigItem(
        "Functions", "AutoSelectChampion", [])
    autoSelectChampionTop = ConfigItem(
        "Functions", "AutoSelectChampionTop", [])
    autoSelectChampionJug = ConfigItem(
        "Functions", "AutoSelectChampionJug", [])
    autoSelectChampionMid = ConfigItem(
        "Functions", "AutoSelectChampionMid", [])
    autoSelectChampionBot = ConfigItem(
        "Functions", "AutoSelectChampionBot", [])
    autoSelectChampionSup = ConfigItem(
        "Functions", "AutoSelectChampionSup", [])

    enableAutoBanChampion = ConfigItem(
        "Functions", "EnableAutoBanChampion", False, BoolValidator())
    autoBanChampion = ConfigItem(
        "Functions", "AutoBanChampion", [])
    autoBanChampionTop = ConfigItem(
        "Functions", "AutoBanChampionTop", [])
    autoBanChampionJug = ConfigItem(
        "Functions", "AutoBanChampionJug", [])
    autoBanChampionMid = ConfigItem(
        "Functions", "AutoBanChampionMid", [])
    autoBanChampionBot = ConfigItem(
        "Functions", "AutoBanChampionBot", [])
    autoBanChampionSup = ConfigItem(
        "Functions", "AutoBanChampionSup", [])

    autoBanDelay = RangeConfigItem(
        "Functions", "AutoBanDelay", 0, RangeValidator(0, 25))
    pretentBan = ConfigItem("Functions", "PrententBan", False, BoolValidator())

    autoAcceptCeilSwap = ConfigItem(
        "Functions", "AutoAcceptCeilSwap", False, BoolValidator())
    autoAcceptChampTrade = ConfigItem(
        "Functions", "AutoAcceptChampTrade", False, BoolValidator())

    lastNoticeSha = ConfigItem("Other", "LastNoticeSha", "")

    enableCloseToTray = ConfigItem(
        "General", "EnableCloseToTray", None, OptionsValidator([None, True, False]))

    searchHistory = ConfigItem(
        "Other", "SearchHistory", ""
    )

    enableGameStartMinimize = ConfigItem("General",
                                         "EnableGameStartMinimize", False,
                                         BoolValidator())

    enableCheckUpdate = ConfigItem("General",
                                   "EnableCheckUpdate", True,
                                   BoolValidator())

    logLevel = OptionsConfigItem(
        "General", "LogLevel", 40, OptionsValidator([10, 20, 30, 40]), restart=True)

    enableProxy = ConfigItem("General", "EnableProxy", False, BoolValidator())
    proxyAddr = ConfigItem("General", "HttpProxy", "")


YEAR = 2023
AUTHOR = "Zzaphkiel"
VERSION = "0.13.0"
BETA = "0.13.1-beta1"
FEEDBACK_URL = "https://github.com/Zzaphkiel/Seraphine/issues?q=is%3Aissue"
GITHUB_URL = "https://github.com/Zzaphkiel/Seraphine"
LOCAL_PATH = f"{os.getenv('APPDATA')}\\Seraphine"

cfg = Config()
qconfig.load(f"{LOCAL_PATH}\\config.json", cfg)
