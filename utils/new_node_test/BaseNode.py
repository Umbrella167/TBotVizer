import copy
import dearpygui.dearpygui as dpg

from utils.Utils import get_mouse_relative_pos
from utils.new_node_test.types import *


class BaseNode:
    def __init__(self, parent):
        """
        self.data = {
            "x": {"attribute_type":"input", "data_type": "float", "data": 0},
            "res": {"attribute_type":"output", "data_type": "float", "data": 0},
            "pos": {"attribute_type":"none", "data_type": "config", "data": [0, 0]},
        }
        """
        self.data = {
            "pos": {"attribute_type": None, "data_type": "CONFIG", "data": [0, 0]},
        }
        self.old_data = None
        self.instanced_item = {}
        self.link_item = {}
        self.width = 200
        self.parent = parent
        self.label = self.__class__.__name__
        # 鼠标拖拽位置
        self.pos = get_mouse_relative_pos(self.parent.node_editor)
        self.tag = dpg.add_node(label=self.label, pos=self.pos, parent=self.parent.node_editor)

    # 更新节点
    def update(self):
        # for i in self.instanced_item:
        #     pass
        for name, info in self.data.items():
            if name not in self.instanced_item:
                # 如果没有被创建
                data_type = info["data_type"]
                if data_type == "FLOAT":
                    self.instanced_item[name] = FLOAT(data=(name, info), parent=self)
                elif data_type == "CONFIG":
                    # self.instanced_item[name] = CONFIG((name, info), self)
                    self.instanced_item[name] = None
            else:
                # 如果已经被创建，则更新数据
                if self.old_data is None:
                    return
                # :TODO 这里这个类型改变还没验证是否有问题
                if self.old_data[name]['data_type'] != info["data_type"]:
                    self.instanced_item[name] = FLOAT(data=(name, info), parent=self)
                # 数据更新
                if self.old_data[name]['data'] != info['data']:
                    # 更新自己的节点
                    self.instanced_item[name].update()
                    # 更新链接的节点
                    for _, infos in self.link_item.items():
                        for i in infos:
                            i.info["data"] = info["data"]

                # # 如果节点被删除
                # if name not in self.data:
                #     to_delete.append(name)

        self.extra()

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


