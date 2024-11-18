from utils.node_utils.BaseFunc import BaseFunc


class Add(BaseFunc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"x": None, "y": None}
        # self.input_type = {"x": "float", "y": "float"}
        self.output_data = {"res": None}
        # self.output_type = {"res": "float", "res2": "float"}

    def calc(self):
        res = 0
        for i in self.input_data.keys():
            value = self.input_data[i]
            if value is None:
                value = 0
            res += value
        self.output_data["res"] = res
        return res


