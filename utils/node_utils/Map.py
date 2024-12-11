from utils.Utils import convert_to_float
from utils.node_utils.BaseNode import BaseNode


class Map(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "vx":                   {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": 0}},
            "vy":                   {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": 0}},
            "alphax":               {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": 0}},
            "original_upper":       {"attribute_type": "CONFIG", "data_type": "STRINPUT", "user_data": {"value": 1}},
            "original_lower":       {"attribute_type": "CONFIG", "data_type": "STRINPUT", "user_data": {"value": -1}},
            "upper":                {"attribute_type": "CONFIG", "data_type": "STRINPUT", "user_data": {"value": 2000}},
            "lower":                {"attribute_type": "CONFIG", "data_type": "STRINPUT", "user_data": {"value": -2000}},
            "mapped_value":         {"attribute_type": "OUTPUT", "data_type": "STRINPUT", "user_data": {"value": []}},
            "pos":                  {"attribute_type": "CONFIG","data_type": "CONFIG","user_data":{"value": None}},
        }
        kwargs["init_data"] = kwargs["init_data"] or default_init_data
        super().__init__(**kwargs)

    def func(self):
        vx = convert_to_float(self.data["vx"]["user_data"]["value"])
        vy = convert_to_float(self.data["vy"]["user_data"]["value"])
        alphax = convert_to_float(self.data["alphax"]["user_data"]["value"])
        original_upper = convert_to_float(self.data["original_upper"]["user_data"]["value"])
        original_lower = convert_to_float(self.data["original_lower"]["user_data"]["value"])
        upper = convert_to_float(self.data["upper"]["user_data"]["value"])
        lower = convert_to_float(self.data["lower"]["user_data"]["value"])

        if original_upper <= original_lower or upper < lower:
            self.data["mapped_value"]["user_data"]["value"] = None
            return

        def map_value(value):
            if value is None:
                return None
            normalized_value = (value - original_lower) / (original_upper - original_lower)
            normalized_value = max(0, min(1, normalized_value))
            return lower + normalized_value * (upper - lower)

        self.data["mapped_value"]["user_data"]["value"] = [
            map_value(vx),
            map_value(vy),
            alphax*6,
        ]
