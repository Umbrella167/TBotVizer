import dearpygui.dearpygui as dpg

from utils.new_node_test.types.BaseType import BaseType


class CONFIG(BaseType):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        dpg.hide_item(self.tag)

