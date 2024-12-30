from utils.Utils import convert_to_float
from utils.node_utils.BaseNode import BaseNode


class Add(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "x": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
            "y": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
            "res": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data":
                    {"value": None}
            }
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)

    def func(self):
        self.data["res"]["user_data"]["value"] = convert_to_float(self.data["x"]["user_data"]["value"]) + convert_to_float(self.data["y"]["user_data"]["value"])


class Mul(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "x": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
            "y": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data":
                    {"value": 0}
            },
            "res": {
                "attribute_type": "OUTPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data":
                    {"value": None}
            }
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)

    def func(self):
        self.data["res"]["user_data"]["value"] = convert_to_float(
            self.data["x"]["user_data"]["value"]) + convert_to_float(self.data["y"]["user_data"]["value"])
