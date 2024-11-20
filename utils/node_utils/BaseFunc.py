import dearpygui.dearpygui as dpg

from utils.Utils import get_mouse_relative_pos

class BaseFunc:
    def __init__(self, parent, label=None, pos=None):
        self.input_data = {}
        self.input_type = {}
        self.old_input_data = {}
        self.output_data = {}
        self.output_type = {}
        self.old_output_data = {}
        self.label = label
        self.pos = pos
        self.width = 200
        self.parent = parent
        self.output_text = {}
        self.input_text = {}
        self.attribute = {}
        self.tag = None

        if self.label is None:
            self.label = self.__class__.__name__
        if pos is None:
            # 获取鼠标拖拽位置
            self.pos = get_mouse_relative_pos(self.parent)

    # 默认的生成方式
    def create(self):
        input_params = [key for key in self.input_data.keys()]
        output_params = [key for key in self.output_data.keys()]
        self.tag = dpg.add_node(label=self.label, pos=self.pos, parent=self.parent)
        for i in input_params:
            self.attribute[i] = dpg.add_node_attribute(parent=self.tag)
            self.input_text[i] = dpg.add_input_text(label=i, width=self.width, callback=self.input_callback,
                                                    parent=self.attribute[i])
            dpg.set_item_user_data(self.attribute[i], self.input_text[i])
            # print(i, self.input_text[i])
            # 建立双向索引
            self.input_text[self.input_text[i]] = i
        for o in output_params:
            self.attribute[o] = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Output, parent=self.tag,
                                                       user_data=self.output_data[o])
            self.output_text[o] = dpg.add_input_text(label=o, width=self.width, parent=self.attribute[o], readonly=True)
            dpg.set_item_user_data(self.attribute[o], self.output_text[o])
            # print(o, self.output_text[o])
            self.output_text[self.output_text[o]] = o

    def calc(self):
        if self.old_input_data != self.input_data:
            self.input_data_callback()
        if self.old_output_data != self.output_data:
            self.output_data_callback()

    # 当input被手动改变触发的callback
    def input_callback(self, sender, app_data):
        self.input_data[self.input_text[sender]] = app_data

    # 当输入的值被改变时
    def input_data_callback(self):
        for i in self.input_data:
            dpg.configure_item(self.input_text[i], default_value=self.input_data[i])
        self.old_input_data = self.input_data.copy()

    # 当输出的值被改变时
    def output_data_callback(self):
        for o in self.output_data:
            dpg.configure_item(self.output_text[o], default_value=self.output_data[o])
        self.old_output_data = self.output_data.copy()
