import dearpygui.dearpygui as dpg

from ui.boxes.NodeEditor.types.BaseType import BaseType


class CONFIG(BaseType):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        dpg.hide_item(self.tag)

