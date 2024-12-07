import copy
import time
import hashlib

import dearpygui.dearpygui as dpg

from utils.Utils import get_mouse_relative_pos
from utils.new_node_test import types

class BaseNode:
    def __init__(self, parent, identifier=None, init_data=None, **kwargs):
        self.width = 200
        """
        data = {
            "x": {
                "attribute_type": "INPUT",
                "data_type": "FLOAT",
                "user_data":
                    {"value": 0}
            },
            "res": {
                "attribute_type": "OUTPUT",
                "data_type": "FLOAT",
                "user_data": {"value": 0}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data":
                    {"value": None}
            }
        }
        """
        self.data = init_data or {
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data":
                    {"value": None}
            },
        }
        self.old_data = None
        self.instanced_item = {}
        self.parent = parent
        self.label = self.__class__.__name__
        self.pos = get_mouse_relative_pos(self.parent.node_editor)
        if self.data["pos"]["user_data"]["value"] is not None:
            self.pos = self.data["pos"]["user_data"]["value"]
        self.tag = dpg.add_node(label=self.label, pos=self.pos, parent=self.parent.node_editor)
        self.identifier = identifier or hashlib.md5(f"{str(time.time())}{self.__class__.__name__}".encode('utf-8')).hexdigest()

    # 更新节点
    def update(self):
        for name, info in self.data.items():
            if name not in self.instanced_item:
                # 如果没有被创建
                self.add_attr(name, info)
            else:
                # 如果已经被创建，则更新数据
                if self.old_data is None:
                    return
                # 数据更新
                if self.old_data[name]["user_data"]["value"] != info["user_data"]["value"]:
                    # 更新自己的节点
                    self.instanced_item[name].update()
        self.extra()

    def flash_node(self):
        pass

    # 在最后一行添加节点
    def add_attr(self, name, info):
        data_type = TYPES[info["data_type"]]
        if callable(data_type):
            self.instanced_item[name] = data_type(name=name, info=info, parent=self)

    def extra(self):
        pass

    def func(self):
        pass

    def calc(self):
        if self.old_data == self.data:
            return
        self.func()
        self.update()
        self.old_data = copy.deepcopy(self.data)


TYPES = {
    "FLOAT": types.FLOAT,
    "CONFIG": types.CONFIG,
    "DEL": None,
}
