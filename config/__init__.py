class BaseConfig:
    def __init__(self, width:int=1920, height:int=1080, theme:str="dark", font_size:int=10, language:str="zh"):
        self._width = width
        self._height = width

        self._theme = theme
        self._font_size = font_size
        self._language = language