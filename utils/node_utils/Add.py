from utils.node_utils.BaseFunc import BaseFunc


class Add(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"x": None, "y": None}
        self.output_data = {"res": None}

    def calc(self):
        super().calc()
        self.output_data["res"] = sum(self._convert_to_float(self.input_data[key]) for key in self.input_data)

    def _convert_to_float(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0
