import dearpygui.dearpygui as dpg

from utils.node_utils.types.BaseType import BaseType


class CONFIG(BaseType):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        dpg.hide_item(self.tag)

