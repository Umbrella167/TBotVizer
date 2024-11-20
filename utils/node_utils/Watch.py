# import random
#
# from utils.node_utils.Base import BaseFunc
#
# class RandomInt(BaseFunc):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.input_data = {"upper": None, "lower": None}
#         self._input_type = {"upper": "int", "lower": "int"}
#         self.output_data = {"res": None}
#         self._output_type = {"res": "int"}
#
#     def calc(self):
#         self.output_data["res"] = random.randint(self.input_data["lower"], self.input_data["upper"])