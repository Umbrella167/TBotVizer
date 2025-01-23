import os


class ParamData:
    def __init__(self, prefix, name, type, tbk_manager, default_value="None"):
        self.tbk_manager = tbk_manager
        self.prefix = prefix
        self.name = name
        self.type = type
        self._value = default_value

        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__v__"), value=self._value)
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__t__"), value=self.type)
        self.tbk_manager.put(param=os.path.join(self.prefix, self.name, "__i__"),
                             value="Custom param")

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
