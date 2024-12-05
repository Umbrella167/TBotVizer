import dearpygui.dearpygui as dpg
import pickle
import json

from utils.ClientLogManager import client_logger
from utils.DataProcessor import tbk_data
from utils.node_utils.BaseNode import BaseNode


class Subscriber(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.suber = None
        self.current_subscription = None
        self.callback_manager = {}
        self.input_data = {"puuid": None, "name": None, "msg_name": None}
        self.output_data = {"msg": None}

    def calc(self):
        super().calc()
        puuid = self.input_data.get("puuid")
        name = self.input_data.get("name")
        msg_name = self.input_data.get("msg_name")
        # 获取新的订阅信息
        new_subscription = (puuid, name, msg_name)
        # 如果订阅信息发生变化，则重新订阅
        if new_subscription != self.current_subscription:
            # 如果有现有的订阅器，先移除其回调
            if self.current_subscription in self.callback_manager:
                self.remove_callback(self.current_subscription)
            # 如果新的订阅信息有效，则创建新的订阅
            if puuid is not None and name is not None and msg_name is not None:
                self.suber = tbk_data.Subscriber(
                    info={
                        "puuid": puuid,
                        "name": name,
                        "msg_name": msg_name,
                        "tag": self.tag
                    },
                    callback=self.create_callback(new_subscription),
                )
                dpg.configure_item(self.output_text["msg"], multiline=True, width=400)
                self.current_subscription = new_subscription  # 更新当前订阅信息
            else:
                # 如果任何参数为空，则清除订阅
                self.current_subscription = None

    def create_callback(self, subscription):
        def callback(msg):
            if subscription in self.callback_manager:
                self.output_data["msg"] = self.decode_msg(msg)
        # 将回调函数与订阅信息绑定
        self.callback_manager[subscription] = callback
        return callback

    def remove_callback(self, subscription):
        if subscription in self.callback_manager:
            # 将回调从管理器中移除
            self.callback_manager.pop(subscription)

    def extra(self):
        dpg.configure_item(self.tag, drop_callback=self.drop_callback)

    def drop_callback(self, sender, app_data, user_data):
        app_data = app_data[0]
        self.input_data["puuid"] = app_data["puuid"]
        self.input_data["name"] = app_data["name"]
        self.input_data["msg_name"] = app_data["msg_name"]

    def decode_msg(self, msg):
        try:
            res = json.dumps(pickle.loads(msg), indent=4, ensure_ascii=False)
        except Exception as e:
            client_logger.log("ERROR", "Msg decode error", e)
            return "ERROR"
        return res

