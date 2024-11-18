import dearpygui.dearpygui as dpg
import asyncio

from utils.Utils import get_mouse_relative_pos


class BaseFunc:
    def __init__(self, parent, label=None, pos=None):
        self.input_data = {}
        self.input_type = {}
        self.output_data = {}
        self.output_type = {}
        self.label = label
        self.pos = pos
        self.width = 200
        self.parent = parent
        self.output = {}

        if self.label is None:
            self.label = self.__class__.__name__
        if pos is None:
            # 获取鼠标拖拽位置
            self.pos = get_mouse_relative_pos(self.parent)

    # 默认的生成方式
    def create(self):
        input_params = [key for key in self.input_data.keys()]
        output_params = [key for key in self.output_data.keys()]
        with dpg.node(label=self.label, pos=self.pos, parent=self.parent):
            for i in input_params:
                with dpg.node_attribute():
                    with dpg.group():
                        dpg.add_spacer(width=self.width)
                        dpg.add_text(label=i, default_value=i)
            for o in output_params:
                with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                    with dpg.group():
                        self.output[o] = dpg.add_input_text(label=o, width=self.width, readonly=True)

    def calc(self):
        pass
