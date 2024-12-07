import dearpygui.dearpygui as dpg

from utils.new_node_test.types.BaseType import BaseType


class FLOAT(BaseType):
    width = 200

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.input_text = dpg.add_input_text(
            label=self.name,
            width=200,
            callback=self.input_callback,
            parent=self.tag,
            readonly=self.is_output
        )
        dpg.set_item_user_data(self.tag, self)
        dpg.set_value(self.input_text, self.info["user_data"]["value"])

    # 当input被手动改变触发的callback
    def input_callback(self, sender, app_data):
        self.parent.data[self.name]["user_data"]["value"] = app_data

    def update(self):
        dpg.set_value(self.input_text, self.parent.data[self.name]["user_data"]["value"])
