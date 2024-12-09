import copy
import time
import hashlib

import dearpygui.dearpygui as dpg

from utils.Utils import get_mouse_relative_pos
from utils.node_utils import types


class BaseNode:
    def __init__(self, parent, identifier=None, init_data=None, **kwargs):
        self.width = 200
        self.parent = parent
        self.label = self.__class__.__name__
        self.automatic = False
        """
        data = {
            "x": {
                "attribute_type": "INPUT",
                "data_type": "StrInput",
                "user_data":
                    {"value": 0}
            },
            "res": {
                "attribute_type": "OUTPUT",
                "data_type": "StrInput",
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
        # TODO： 部分user_data并未完全修改完
        self.data = init_data
        self.data["pos"] = self.data.get("pos", None) or {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data":
                    {"value": get_mouse_relative_pos(self.parent.node_editor)}
            }
        self.old_data = None
        self.instanced_item = {}
        self.pos = self.data.get("pos", {}).get("user_data", {}).get("value") or get_mouse_relative_pos(self.parent.node_editor)
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
        # TODO:这个func会一直运算，如果要节省计算资源则需要自行在node内判断

        if not self.automatic and self.old_data == self.data:
            return
        self.func()
        self.update()
        self.old_data = copy.deepcopy(self.data)


TYPES = {
    "STRINPUT": types.StrInput,
    "MULTILINEINPUT": types.MultilineInput,
    "CONFIG": types.CONFIG,
    "SLIDER": types.Slider,
    "DEL": None,
}
