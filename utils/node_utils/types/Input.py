import dearpygui.dearpygui as dpg

from utils.Utils import convert_to_float
from utils.node_utils.types.BaseType import BaseType


class BaseInput(BaseType):
    width = 200

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_text = dpg.add_input_text(
            label=self.name,
            width=200,
            callback=self.input_callback,
            parent=self.tag,
            readonly=True if self.is_output else False,
        )
        dpg.set_item_user_data(self.tag, self)
        dpg.set_value(self.input_text, self.info["user_data"]["value"])

    # 当input被手动改变触发的callback
    def input_callback(self, sender, app_data):
        self.parent.data[self.name]["user_data"]["value"] = app_data

    def update(self):
        dpg.set_value(self.input_text, self.parent.data[self.name]["user_data"]["value"])


class StrInput(BaseInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MultilineInput(BaseInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        dpg.configure_item(self.input_text, readonly=False, multiline=True, width=400)


class Slider(BaseType):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slider = dpg.add_slider_double(
            width=200,
            parent=self.tag,
            default_value=0,
            min_value=0,
            max_value=100,
            callback=self.input_callback,
        )
        dpg.set_item_user_data(self.tag, self)
        dpg.set_value(self.slider, self.info["user_data"]["value"])

    # 当input被手动改变触发的callback
    def input_callback(self, sender, app_data):
        self.parent.data[self.name]["user_data"]["value"] = app_data

    def update(self):
        dpg.set_value(self.slider, convert_to_float(self.parent.data[self.name]["user_data"]["value"]))
