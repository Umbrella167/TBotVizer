from utils.Utils import convert_to_float
from utils.new_node_test.BaseNode import BaseNode


class Add(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = {
            "x": {"attribute_type": "INPUT", "data_type": "FLOAT", "data": 0},
            "y": {"attribute_type": "INPUT", "data_type": "FLOAT", "data": 0},
            "res": {"attribute_type": "OUTPUT", "data_type": "FLOAT", "data": 0},
            "pos": {"attribute_type": None, "data_type": "CONFIG", "data": [0, 0]},
        }

    def func(self):
        self.data["res"]["data"] = convert_to_float(self.data["x"]["data"]) + convert_to_float(self.data["y"]["data"])

