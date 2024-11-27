class BaseConfig:
    def __init__(self, label="UnknownTag", tag="UnknownTag", width: int = 1920, height: int = 1080, theme: str = "dark",
                 font_size: int = 10, language: str = "zh", son_tags: list = None):
        # self._width = width
        # self._height = width
        self.tag = tag
        self.label = label

        # self.tbk_data = da
        self.son_tags = son_tags

        self.theme = theme
        self.font_size = font_size
        self.language = language
