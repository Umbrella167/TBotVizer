import json
import dearpygui.dearpygui as dpg
import pickle
from utils.node_utils.BaseNode import BaseNode

class DecodeMessage(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"msg": None}
        self.output_data = {"res": None}

    def calc(self):
        super().calc()
        if self.input_data["msg"] is None:
            return
        self.output_data["res"] = json.dumps(pickle.loads(self.input_data["msg"]), indent=4, ensure_ascii=False)
        dpg.configure_item(self.output_text["res"], multiline=True, width=-1)


