import time

import dearpygui.dearpygui as dpg
import numpy as np

from ui.boxes.BaseBox import BaseBox
from ui.components.TBKManager.TBKManager import TBKManager


class DemoBox(BaseBox):
    # only = True 表示只能创建一个实例
    only = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input = None
        self.suber = None
        self.puber = None
        self.data = self.data or np.zeros(3)
        self.tbk_manager = TBKManager("DemoBox")

    def create(self):
        # create 会自动创建dpg窗口， 窗口拥有tag，获取的方法是 self.tag
        self.input = dpg.add_input_text(parent=self.tag, default_value=self.data.tolist())
        self.puber = self.tbk_manager.publisher(name="name", msg_name="msg_name", msg_type=self.tbk_manager.all_types.ByteMultiArray)
        self.suber = self.tbk_manager.subscriber(name="name", msg_name="msg_name", tag=self.tag, callback=lambda m: dpg.set_value(item=self.input, value=m))
        # 创建按钮
        dpg.add_button(label="test", parent=self.tag, callback=lambda :self.puber.publish(f"test{time.time()}"))

    def destroy(self):
        # 销毁之前可以做的事情
        super().destroy()  # 真正销毁Box

    def update(self):
        self.data = np.array(dpg.get_value(self.input))
