import time

import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from utils.ClientLogManager import client_logger
from utils.Utils import item_auto_resize, get_all_subclasses
from utils.new_node_test import *


class NewNodeBox(BaseBox):
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 整体布局
        self.group = None
        # 左侧按钮布局
        self.func_window = None
        self.collapsing_header = None
        self.func_button = {}
        # 右侧节点布局
        self.node_window = None
        self.node_group = None
        self.node_editor = None
        self.static_node = None
        # 基础属性
        self.all_node_class = get_all_subclasses(BaseNode)
        # 当前时间(用于时间同步)
        self.now_time = time.time()
        # 记录节点
        self.nodes = {}

    def on_create(self):
        dpg.configure_item(self.tag, label="NewNodeBox")
        self.group = dpg.add_group(horizontal=True, parent=self.tag)
        # 添加方法列表
        self.func_window = dpg.add_child_window(parent=self.group)
        self.collapsing_header = dpg.add_collapsing_header(label="Math Functions", parent=self.func_window,
                                                           default_open=True)
        # 添加cls按钮，并设置拖拽事件
        for cls in self.all_node_class:
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
            # 链接两个节点时的回调
            callback=self.link_callback,
            # 断开两个节点时的回调
            # delink_callback=lambda sender, app_data: dpg.delete_item(app_data),
            delink_callback=self.delink_callback,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            parent=self.node_group,
        )
        # 创建固定节点（用于定位）
        self.static_node = dpg.add_node(
            label="Tips: 拖动左侧节点到视窗以使用函数",
            parent=self.node_editor,
            use_internal_label=True,
            show=True, draggable=False)
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, parent=self.static_node):
            dpg.add_spacer(width=1)
        item_auto_resize(self.func_window, self.tag, 0, 0.15, 200, 300)

    def key_release_handler(self, sender, app_data, user_data):
        if dpg.is_key_released(dpg.mvKey_Delete):
            for node_tag in dpg.get_selected_nodes(self.node_editor):
                if node_tag == self.static_node:
                    continue
                self.delete_node(node_tag)

    def update(self):
        self.now_time = time.time()
        for tag, node in self.nodes.items():
            try:
                node.calc()
            except Exception as e:
                # self.delete_node(tag)
                client_logger.log("ERROR", f"{node} calc failed!", e=e)


    def new_node(self, sender, cls, user_data):
        instance = cls(parent=self)
        instance.update()
        # node_tag和实例的对应表
        self.nodes[instance.tag] = instance
        # self.box_count[cls] = self.box_count.setdefault(cls, 0) + 1

    def delete_node(self, node_tag):
        # 删除node
        client_logger.log("INFO", f"Delete the node {dpg.get_item_label(node_tag)}:{node_tag}")
        del self.nodes[node_tag]
        dpg.delete_item(node_tag)

    def link_callback(self, sender, app_data):
        # 输入输出
        output = dpg.get_item_user_data(app_data[0])
        input = dpg.get_item_user_data(app_data[1])
        # node的实例化类
        output_node = self.nodes[dpg.get_item_parent(app_data[0])]
        output_node.link_item.setdefault(output.name, []).append(input)
        # 链接时刷新一次数据
        input.info["data"] = output.info["data"]
        link = dpg.add_node_link(app_data[0], app_data[1], parent=sender, user_data=(output_node, output, input))


    def delink_callback(self, sender, app_data):
        output_node, output, input = dpg.get_item_user_data(app_data)
        output_node.link_item[output.name] = [i for i in output_node.link_item[output.name] if i != input]
        dpg.delete_item(app_data)
