import dearpygui.dearpygui as dpg
import pickle
import json

from config.DynamicConfig import RUN_TIME
from utils.ClientLogManager import client_logger
from api.NewTBKApi import tbk_manager
from utils.node_utils.BaseNode import BaseNode
from utils.Utils import convert_to_float

class Subscriber(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "puuid": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": None}
            },
            "name": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": None}
            },
            "msg_name": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": None}
            },
            "msg": {
                "attribute_type": "OUTPUT",
                "data_type": "MULTILINEINPUT",
                "user_data": {"value": None}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data": {"value": None}
            },
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)
        self.current_info = None
        self.automatic = True

    def func(self):
        # 获取输入数据
        puuid = self.data["puuid"]["user_data"].get("value")
        name = self.data["name"]["user_data"].get("value")
        msg_name = self.data["msg_name"]["user_data"].get("value")
        # 获取新的订阅信息
        info = {
            "puuid": puuid,
            "name": name,
            "msg_name": msg_name,
            "tag": self.tag
        }
        # 如果订阅信息发生变化，则重新订阅
        if info != self.current_info:
            # 如果有现有的订阅器，先移除其回调
            if self.current_info is not None:
                tbk_manager.unsubscribe(self.current_info)
            # 如果新的订阅信息有效，则创建新的订阅
            if puuid is not None and name is not None and msg_name is not None:
                self.suber = tbk_manager.subscriber(
                    info=info,
                    callback=self.callback,
                )
                self.current_info = info  # 更新当前订阅信息
            else:
                # 如果任何参数为空，则清除订阅
                self.current_info = None

    def callback(self, msg):
        self.data["msg"]["user_data"]["value"] = self.decode_msg(msg)

    def decode_msg(self, msg):
        try:
            res = pickle.loads(msg)
        except Exception as e:
            # client_logger.log("ERROR", "Msg decode error", e)
            return msg
        return res

    def extra(self):
        dpg.configure_item(self.tag, drop_callback=self.drop_callback)

    def drop_callback(self, sender, app_data, user_data):
        app_data = app_data[0]
        self.data["puuid"]["user_data"]["value"] = app_data["puuid"]
        self.data["name"]["user_data"]["value"] = app_data["name"]
        self.data["msg_name"]["user_data"]["value"] = app_data["msg_name"]


class Publisher(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "name": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": "MOTOR_CONTROL"}
            },
            "msg_name": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": "RPM"}
            },
            "msg_type": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": "list"}
            },
            "frequency": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": 0.01}
            },
            "msg": {
                "attribute_type": "INPUT",
                "data_type": "STRINPUT",
                "user_data": {"value": None}
            },
            "pos": {
                "attribute_type": "CONFIG",
                "data_type": "CONFIG",
                "user_data": {"value": None}
            }
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)
        self.is_create = False
        self.puber = None
        self.info = None
        self.automatic = True

    def func(self):
        # 获取输入数据
        name = self.data["name"]["user_data"].get("value")
        msg_name = self.data["msg_name"]["user_data"].get("value")
        msg_type = self.data["msg_type"]["user_data"].get("value")
        frequency = convert_to_float(self.data["frequency"]["user_data"].get("value"))
        msg = self.data["msg"]["user_data"].get("value")

        # 设置最小频率为 0.01
        if frequency == 0:
            frequency = 0.01

        if name and msg_name and msg_type:
            # 如果三者不为空则创建 Publisher
            info = {
                "name": str(name),
                "msg_name": msg_name,
                "msg_type": msg_type,
            }
            # ep = tbkpy.EPInfo()
            # ep.name = str(name)
            # ep.msg_name = msg_name
            # ep.msg_type = msg_type
            if self.info != info:
                self.puber = tbk_manager.publisher(info)
                self.info = info
            self.is_create = True
        else:
            # 如果有一个为空则清除 Publisher
            self.puber = None
            self.is_create = False

        # 发布消息
        if (self.parent.now_time - RUN_TIME) % frequency < 0.01 and self.is_create:
            if self.puber:
                self.puber.publish(pickle.dumps(msg))
