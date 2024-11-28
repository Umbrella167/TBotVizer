from utils.Utils import convert_to_float
from utils.node_utils.BaseFunc import BaseFunc

class Mul(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"x": None, "y": None}
        self.output_data = {"res": None}

    def calc(self):
        super().calc()
        self.output_data["res"] = convert_to_float(self.input_data["x"]) * convert_to_float(self.input_data["y"])