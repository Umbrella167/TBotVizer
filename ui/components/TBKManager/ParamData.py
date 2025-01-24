import os
from .TBKManager import tbk_manager


class ParamData:
    def __init__(self, prefix, name, type=None, info=None, default_value=None):
        self.tbk_manager = tbk_manager
        self.prefix = prefix
        self.name = name

        # 使用新的属性访问方法
        self._type = type or self.tbk_manager.get(param=os.path.join(self.prefix, self.name, "__t__")) or "Unknown"
        self._info = info or self.tbk_manager.get(param=os.path.join(self.prefix, self.name, "__i__")) or "Custom param"
        self._value = default_value or self.tbk_manager.get(param=os.path.join(self.prefix, self.name, "__v__")) or "None"

        self.init_param()

    def init_param(self):
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__v__"), value=self._value)
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__t__"), value=self._type)
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__i__"), value=self._info)

    def __call__(self):
        return self._value

    @property
    def value(self):
        self._value = self.tbk_manager.get(param=os.path.join(self.prefix, self.name, "__v__"))
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__v__"), value=self._value)

    @property
    def type(self):
        self._type = self.tbk_manager.get(param=os.path.join(self.prefix, self.name, "__t__"))
        return self._type

    @type.setter
    def type(self, type_value):
        self._type = type_value
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__t__"), value=self._type)

    @property
    def info(self):
        self._info = self.tbk_manager.get(param=os.path.join(self.prefix, self.name, "__i__"))
        return self._info

    @info.setter
    def info(self, info_value):
        self._info = info_value
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__i__"), value=self._info)