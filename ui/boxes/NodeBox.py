import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from utils.Utils import item_auto_resize, get_all_subclasses, get_mouse_relative_pos
from utils.node_utils import *


class NodeBaseBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.funcs = get_all_subclasses(BaseFunc)
        self.group = None
        self.collapsing_header = None
        self.func_window = None
        self.func_button = {}
        self.node_window = None
        self.node_group = None
        self.node_editor = None
        self.nodes = []
        self.box_count = {}


    def create(self):
        self.check_and_create_window()
        if self.label is None:
            dpg.configure_item(self.tag, label="NodeBaseBox")

        self.group = dpg.add_group(horizontal=True, parent=self.tag)
        # 添加方法列表
        self.func_window = dpg.add_child_window(parent=self.group)
        self.collapsing_header = dpg.add_collapsing_header(label="Math Functions", parent=self.func_window)
        # 添加cls按钮，并设置拖拽事件
        for cls in self.funcs:
            cls_name = cls.__name__
            self.func_button[cls_name] = dpg.add_button(
                label=cls_name,
                parent=self.collapsing_header,
                width=-1,
            )
            # 设置拖拽传输的数据和标签
            with dpg.drag_payload(parent=self.func_button[cls_name], drag_data=cls, payload_type="Function"):
                dpg.add_text(cls.__name__)

        # 绘制节点图像
        self.node_window = dpg.add_child_window(parent=self.group)
        self.node_group = dpg.add_group(
            parent=self.node_window,
            # drop_callback=lambda sender, app_data, user_data: print(sender, app_data, user_data),
            drop_callback=self.new_node,
            payload_type="Function"
        )
        self.node_editor = dpg.add_node_editor(
            callback=lambda sender, app_data: dpg.add_node_link(app_data[0], app_data[1], parent=sender),
            delink_callback=lambda sender, app_data: dpg.delete_item(app_data),
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            parent=self.node_group,
        )

        # # 这里假设我们要获取所有属性字段的类型
        # # 可以通过其他方式来获取类定义的信息
        # print(f"{cls.__name__} has input_data keys: {[key for key in cls().input_data.keys()]}")
        # print(f"{cls.__name__} has output_data keys: {[key for key in cls().output_data.keys()]}")

        with dpg.node(label="Node 1", pos=[10, 10], parent=self.node_editor):
            with dpg.node_attribute():
                dpg.add_input_float(label="F1", width=150)
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_input_float(label="F2", width=150)

        with dpg.node(label="Node 2", pos=[300, 10], parent=self.node_editor):
            with dpg.node_attribute() as na2:
                dpg.add_input_float(label="F3", width=200)

            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_input_float(label="F4", width=200)

        with dpg.node(label="Node 3", pos=[25, 150], parent=self.node_editor):
            with dpg.node_attribute():
                dpg.add_input_text(label="T5", width=200)
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_simple_plot(label="Node Plot", default_value=(0.3, 0.9, 2.5, 8.9), width=200, height=80,
                                    histogram=True)

        item_auto_resize(self.func_window, self.tag, 0, 0.15, 200, 300)

    def update(self):
        for node in self.nodes:
            node.calc()

    def new_node(self, sender, cls, user_data):
        instance = cls(parent=self.node_editor)
        self.nodes.append(instance)
        self.box_count[cls] = self.box_count.setdefault(cls, 0) + 1
        instance.create()

