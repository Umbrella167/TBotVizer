from api.TBKApi import TBKApi
from ui import LayoutManager as LayoutManager


class UiData:
    def __init__(self):
        self.layout_manager = LayoutManager.LayoutManager()
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


class TBKData:
    def __init__(self, tbkapi: TBKApi):
        self._TBKApi = tbkapi
        self._param_data = self._TBKApi.get_param()
        self._message_data = self._TBKApi.get_message()

    def update(self):
        pass
        # self._param_data = self._TBKApi.get_param()
        # self._message_data = self._TBKApi.get_message()

    @property
    def param_data(self):
        self._old_param_data = self._param_data
        self._param_data = self._TBKApi.get_param()
        return self._param_data

    @property
    def message_data(self):
        self._old_message_data = self._message_data
        self._message_data = self._TBKApi.get_message()
        return self._message_data

    def put_param(self, param, value):
        self._TBKApi.put_param(param, value)
