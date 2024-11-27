import threading
import time


import dearpygui.dearpygui as dpg

from ui.boxes.BaseBox import BaseBox
from utils.ClientLogManager import client_logger
from utils.Utils import item_auto_resize, get_all_subclasses
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
        self.nodes = {}
        self.box_count = {}
        self.link_func = {}
        self.node_threads = {}
        self.input_mutex = {}

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
            # 链接两个节点时的回调
            callback=self.link_callback,
            # 断开两个节点时的回调
            # delink_callback=lambda sender, app_data: dpg.delete_item(app_data),
            delink_callback=self.delink_callback,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            parent=self.node_group,
        )
        with dpg.node(label="Tips: 拖动左侧节点到视窗以使用函数", parent=self.node_editor, use_internal_label=True,
                      show=True, draggable=False):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(width=1)
        item_auto_resize(self.func_window, self.tag, 0, 0.15, 200, 300)

    def update(self):
        for k, node in self.nodes.items():
            if node not in self.node_threads:
                def node_thread():
                    while True:
                        node.calc()
                        time.sleep(0.01)
                # 创建线程并启动
                thread = threading.Thread(target=node_thread)
                thread.daemon = True  # 设置为守护线程，确保主程序退出时线程自动结束
                self.node_threads[node] = thread
                try:
                    thread.start()
                except:
                    client_logger.log("INFO", "Node thread stop!")

        for k, func in self.link_func.items():
            func()

    def new_node(self, sender, cls, user_data):
        instance = cls(parent=self.node_editor)
        instance.create()

        # node的tag和实例的对应表
        self.nodes[instance.tag] = instance
        self.box_count[cls] = self.box_count.setdefault(cls, 0) + 1

    def link_callback(self, sender, app_data):
        def create_link_function(input_ins, input_label, output_ins, output_label):
            def link_function():
                input_ins.input_data[input_label] = output_ins.output_data[output_label]
            return link_function

        if app_data[1] in self.input_mutex.values():
            # 如果input已被连接，则不连接
            client_logger.log("ERROR", "Node input has been connected!")
            return
        # 0是output,1是input
        # node的实例化类
        output_ins = self.nodes[dpg.get_item_parent(app_data[0])]
        input_ins = self.nodes[dpg.get_item_parent(app_data[1])]
        # text 的 tag
        output_tag = dpg.get_item_user_data(app_data[0])
        input_tag = dpg.get_item_user_data(app_data[1])
        # 标签
        output_label = output_ins.output_text[output_tag]
        input_label = input_ins.input_text[input_tag]
        link = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        # 建立函数
        self.link_func[link] = create_link_function(input_ins, input_label, output_ins, output_label)
        self.input_mutex[link] = app_data[1]

    def delink_callback(self, sender, app_data):
        # 删除函数
        del self.link_func[app_data]
        del self.input_mutex[app_data]
        dpg.delete_item(app_data)
