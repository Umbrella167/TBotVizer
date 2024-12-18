import json
import time
import copy

import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from utils.Utils import item_auto_resize, get_all_subclasses
from utils.node_utils import *


class NodeBox(BaseBox):
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
        self.generate_add_methods()
        # 当前时间(用于时间同步)
        self.now_time = time.time()
        # 记录节点
        self.nodes = {}
        # 记录链接
        self.links = {}
        # 布局文件
        self.layout_file = "static/layout/node_layout.json"

    def create(self):
        dpg.configure_item(self.tag, label="NodeBox")
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
            with dpg.drag_payload(parent=self.func_button[cls_name], drag_data=cls_name, payload_type="Function"):
                dpg.add_text(cls_name)

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
            callback=self.new_link,
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
        self.init_nodes()

    def init_nodes(self):
        try:
            with open(self.layout_file, "r") as f:
                node_layout = json.loads(f.read())
                for identifier, node_info in node_layout["node"].items():
                    cls_name, data = node_info
                    try:
                        self.new_node("system", cls_name, (identifier, data))
                    except Exception as e:
                        client_logger.log("WARNING", f"Node {cls_name} init failed", e)
                self.update()
                for link in node_layout["link"]:
                    output_id, output_name, input_id, input_name = link
                    for n in self.nodes.values():
                        if n.identifier == output_id:
                            output_node = n
                        if n.identifier == input_id:
                            input_node = n
                    try:
                        self.new_link("system", (output_node.instanced_item[output_name].tag, input_node.instanced_item[input_name].tag))
                    except Exception as e:
                        client_logger.log("WARNING", f"Link {output_name}->{input_name} init failed", e)
        except Exception as e:
            client_logger.log("WARNING", "Node layout init file failed!")

    def key_release_handler(self, sender, app_data, user_data):
        if dpg.is_key_released(dpg.mvKey_Delete):
            for node_tag in dpg.get_selected_nodes(self.node_editor):
                if node_tag == self.static_node:
                    continue
                self.delete_node(node_tag)
        if dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_released(dpg.mvKey_S):
            node_layout = {
                "node": {},
                "link": []
            }
            for node in self.nodes.values():
                node.data["pos"]["user_data"]["value"] = dpg.get_item_pos(node.tag)
                node_layout["node"][node.identifier] = (node.__class__.__name__, node.data)
            for link in self.links.values():
                node_layout["link"].append(link)
            with open(self.layout_file, "w+") as f:
                f.write(json.dumps(node_layout))
                f.flush()

    def update(self):
        self.now_time = time.time()
        self.update_node_editor()

    def update_node_editor(self):
        # 更新节点
        for tag, node in self.nodes.items():
            try:
                node.calc()
            except Exception as e:
                # self.delete_node(tag)
                client_logger.log("ERROR", f"{node} calc failed!", e=e)

    def new_node(self, sender, cls_name, user_data):
        identifier, init_data = user_data or (None, None)
        method_name = f"add_{cls_name}"
        instance_func = getattr(self, method_name, None)
        instance = instance_func(parent=self, identifier=identifier, init_data=init_data)
        self.nodes[instance.tag] = instance

    def delete_node(self, node_tag):
        # 删除node
        client_logger.log("INFO", f"Delete the node {dpg.get_item_label(node_tag)}:{node_tag}")
        del self.nodes[node_tag]
        dpg.delete_item(node_tag)

    def new_link(self, sender, app_data):
        output_tag = app_data[0]
        input_tag = app_data[1]
        # 输入输出
        output_attr = dpg.get_item_user_data(output_tag)
        input_attr = dpg.get_item_user_data(input_tag)
        # node的实例化类
        output_node = self.nodes[dpg.get_item_parent(output_tag)]
        input_node = self.nodes[dpg.get_item_parent(input_tag)]
        link = dpg.add_node_link(output_tag, input_tag, parent=self.node_editor,
                                 user_data=(input_node, input_attr.name))
        self.links[link] = (output_node.identifier, output_attr.name, input_node.identifier, input_attr.name)
        input_node.data[input_attr.name]["user_data"] = output_node.data[output_attr.name]["user_data"]

    def delink_callback(self, sender, app_data):
        input_node, name = dpg.get_item_user_data(app_data)
        input_node.data[name] = copy.deepcopy(input_node.data[name])
        del self.links[app_data]
        dpg.delete_item(app_data)

    def generate_add_methods(self):
        for cls in self.all_node_class:
            method_name = f"add_{cls.__name__}"

            # 使用闭包捕获cls
            def add_method(self, cls=cls, **kwargs):
                try:
                    instance = cls(**kwargs)
                    return instance
                except Exception as e:
                    client_logger.log("WARNING", f"Unable to instantiate node {cls}", e=e)

            # 将生成的方法绑定到当前实例
            setattr(self, method_name, add_method.__get__(self))
