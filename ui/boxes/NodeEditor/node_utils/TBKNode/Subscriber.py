import dearpygui.dearpygui as dpg

from ui.components.TBKManager import tbk_manager
from ui.boxes.NodeEditor.node_utils import BaseNode
from utils.network.CommunicationManager import CommunicationManager


class Subscriber(BaseNode):
    def __init__(self, **kwargs):
        default_init_data = {
            "puuid": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "name": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "msg_name": {"attribute_type": "INPUT", "data_type": "STRINPUT", "user_data": {"value": None}},
            "msg": {"attribute_type": "OUTPUT", "data_type": "MULTILINEINPUT", "user_data": {"value": None}},
            "pos": {"attribute_type": "CONFIG", "data_type": "CONFIG", "user_data": {"value": None}},
        }
        kwargs["init_data"] = kwargs.get("init_data") or default_init_data
        super().__init__(**kwargs)
        self.cm = CommunicationManager(tbk_manager)
        self.current_info = None
        self.automatic = True

    def func(self):
        # 获取输入数据
        puuid = self.data["puuid"]["user_data"].get("value")
        name = self.data["name"]["user_data"].get("value")
        msg_name = self.data["msg_name"]["user_data"].get("value")
        # 获取新的订阅信息
        info = {"puuid": puuid, "name": name, "msg_name": msg_name, "tag": self.tag}
        # 如果订阅信息发生变化，则重新订阅
        if info != self.current_info:
            # 如果有现有的订阅器，先移除其回调
            if self.current_info is not None:
                self.cm.unsubscribe(
                    name=name,
                    msg_name=msg_name,
                    tag=self.tag,
                )
            # 如果新的订阅信息有效，则创建新的订阅
            if puuid is not None and name is not None and msg_name is not None:
                self.cm.subscriber(name=name, msg_name=msg_name, tag=self.tag, callback=self.callback)
                self.current_info = info  # 更新当前订阅信息
            else:
                # 如果任何参数为空，则清除订阅
                self.current_info = None

    def callback(self, msg):
        self.data["msg"]["user_data"]["value"] = msg

    def extra(self):
        dpg.configure_item(self.tag, drop_callback=self.drop_callback)

    def drop_callback(self, sender, app_data, user_data):
        app_data = app_data[0]
        self.data["puuid"]["user_data"]["value"] = app_data["puuid"]
        self.data["name"]["user_data"]["value"] = app_data["name"]
        self.data["msg_name"]["user_data"]["value"] = app_data["msg_name"]
