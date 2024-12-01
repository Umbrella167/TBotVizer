import dearpygui.dearpygui as dpg

from utils.DataProcessor import tbk_data
from utils.node_utils.BaseNode import BaseNode


class Subscriber(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_data = {"puuid": None, "name": None, "msg_name": None}
        self.output_data = {"msg": None}

    def calc(self):
        super().calc()
        puuid = self.input_data.get("puuid")
        name = self.input_data.get("name")
        msg_name = self.input_data.get("msg_name")

        # 检查是否有任意一个为 None
        if puuid is not None and name is not None and msg_name is not None:
            tbk_data.Subscriber(
                info={
                    "puuid": puuid,
                    "name": name,
                    "msg_name": msg_name,
                    "tag": self.tag
                },
                callback=self.subscriber_callback,
            )

    def extra(self):
        dpg.configure_item(self.tag, drop_callback=self.drop_callback)

    def drop_callback(self,sender, app_data, user_data):
        app_data = app_data[0]
        self.input_data["puuid"] = app_data["puuid"]
        self.input_data["name"] = app_data["name"]
        self.input_data["msg_name"] = app_data["msg_name"]

    def subscriber_callback(self, msg):
        self.output_data["msg"] = msg
