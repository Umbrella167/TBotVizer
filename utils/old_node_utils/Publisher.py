import pickle
import dearpygui.dearpygui as dpg

import tbkpy._core as tbkpy

from config.SystemConfig import run_time
from utils.Utils import convert_to_float
from utils.node_utils.BaseNode import BaseNode


class Publisher(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {
            "name": "RPM",
            "msg_name": "MOTOR_CONTROL_",
            "msg_type": "list",
            "frequency(s)": 0.01,
            "msg": None
        }
        self.is_create = False
        self.puber = None
        self.info = None

    def calc(self):
        super().calc()
        name = self.input_data.get("name")
        msg_name = self.input_data.get("msg_name")
        msg_type = self.input_data.get("msg_type")
        frequency = convert_to_float(self.input_data.get("frequency(s)"))
        msg = self.input_data.get("msg")

        if frequency == 0:
            frequency = 0.01

        if name is not None and msg_name is not None and msg_type:
            # 如果三者接不为空则创建
            info = (name, msg_name, msg_type)
            ep = tbkpy.EPInfo()
            ep.name = str(name)
            ep.msg_name = msg_name
            ep.msg_type = msg_type
            if self.info != info:
                self.puber = tbkpy.Publisher(ep)
                self.info = info
            self.is_create = True
            dpg.configure_item(self.input_text["msg"], multiline=True, width=400)
        else:
            # 如果有一个为空则删除
            self.puber = None
            self.is_create = False

        if (self.parent.now_time - run_time) % frequency < 0.01 and self.is_create:
            self.puber.publish(pickle.dumps(msg))
