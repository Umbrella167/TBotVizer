class TypeParams:
    def __init__(self):
        self.intname = [
            "int",
            "int32",
            "int64",
            "int16",
            "int8",
            "uint",
            "uint32",
            "uint64",
            "uint16",
            "uint8",
            "整形",
            "整数形",
        ]
        self.floatname = [
            "float",
            "double",
            "float32",
            "float64",
            "浮点",
            "浮点数",
            "浮点型",
            "单浮点",
            "双浮点",
            "单精度",
            "双精度",
        ]
        self.boolname = ["bool", "布尔", "布尔值"]
        self.enumname = ["enum", "枚举", "list", "列表"]


class LanguageParams:
    def __init__(self):
        self._language_settings = {
            "en": {
                "dark_theme": "Dark",
                "light_theme": "Light",
                "theme_menu": "Themes",
                "chineseS_menu": "中文简体",
                "english_menu": "English",
                "language_label": "language",
                "view_menu": "View",
            },
            "zh": {
                "dark_theme": "黑暗",
                "light_theme": "明亮",
                "theme_menu": "主题",
                "chineseS_menu": "中文简体",
                "english_menu": "English",
                "language_label": "语言",
                "view_menu": "视图",
            },
        }

    def __getitem__(self, lang):
        return self._language_settings.get(lang)

language = LanguageParams()


