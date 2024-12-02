from utils.Utils import convert_to_float
from utils.node_utils.BaseNode import BaseNode
import dearpygui.dearpygui as dpg

class Add(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"x": None, "y": None}
        self.output_data = {"res": None}

    def calc(self):
        super().calc()
        self.output_data["res"] = sum(convert_to_float(self.input_data[key]) for key in self.input_data)


    # def extra(self):
    #     self.attribute["test"] = dpg.add_node_attribute(parent=self.tag)
    #     dpg.add_plot(width=self.width,height=300, parent=self.attribute["test"])
